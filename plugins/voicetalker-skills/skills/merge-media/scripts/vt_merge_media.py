#!/usr/bin/env python3
"""merge-media: merge every kind of media from a media plan into a VoiceTalker Scribe, in one pass.

    python3 -I vt_merge_media.py merge <scribe.json> <manifest.md|.json> <out.json> [--replace-library]
    python3 -I vt_merge_media.py check <scribe.json> <manifest.md|.json> <out.json>

The manifest is vt-image-manifest.v2 (a plan), v1 (generated pictures only), or a vt-video-manifest.v1 media cut sheet (read as video and upload entries). Per plan entry:
  generated   -> imagePrompt (+ referenceNames) on the clip of its cut
  capture, upload, video (approved or with a file) -> backgroundImageId = "file:<path>" on the clip, scene or Scribe
  none        -> backgroundImageId = "none"
  placeholder -> nothing is written
An entry with span.toClipId stays on screen through that clip: the next clip without an entry of its own gets "none".
Standard library only (Python 3.8+). Never overwrites the Scribe or the manifest. With --replace-library a place that holds a library picture is overwritten (the pictures stay in the library); without it the merge stops and asks. A merge that would change nothing writes no file and raises no version, so it can be repeated safely.
VoiceTalker loads the file: paths itself.
"""
import hashlib
import json
import os
import re
import sys

FENCE = chr(96) * 3
EXT = {".mp4": "video", ".webm": "video", ".mp3": "audio", ".png": "picture", ".jpg": "picture", ".jpeg": "picture",
       ".webp": "picture", ".gif": "picture", ".svg": "picture"}
SENTENCE = (" Clips that start a picture carry an imagePrompt and referenceNames; scenes and clips that show a screen shot, picture, SVG, video or sound"
            " carry a file: path in backgroundImageId, which VoiceTalker loads; VoiceTalker generates the image IDs.")
OVERLAY = [("backgroundOverlayEnabled", False), ("backgroundOverlayLeadSeconds", 0.3), ("backgroundOverlayStyle", "fade")]


def die(msg):
    sys.exit("STOP: " + msg)


def load_manifest(path):
    text = open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        m = json.loads(text)
    else:
        blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
        if not blocks:
            die("the manifest has no json block")
        m = json.loads(blocks[-1])
    if m.get("schema") == "vt-video-manifest.v1":
        return from_cut_sheet(m)
    if m.get("schema") not in ("vt-image-manifest.v1", "vt-image-manifest.v2"):
        die("not a vt-image-manifest.v1 or .v2 manifest, or a vt-video-manifest.v1 cut sheet")
    return m


def from_cut_sheet(m):
    """A media cut sheet (screen-cap-video, videotalker-import) read as a plan: one video or upload entry per cut."""
    plan = []
    for cut in m["cuts"]:
        e = {"entryId": cut["cutId"], "scope": cut["attach"], "kind": "video" if cut.get("mediaType", "video") == "video" else "upload", "file": cut["file"]}
        if cut["attach"] == "scene":
            e["sceneId"] = cut["sceneId"]
        elif cut["attach"] == "clip":
            e["clipId"] = cut["clipId"]
            ids = cut.get("clipIds") or []
            if len(ids) > 1:
                e["span"] = {"toClipId": ids[-1]}
        for k in ("mediaType", "durationSeconds"):
            if k in cut:
                e[k] = cut[k]
        plan.append(e)
    return {"schema": "vt-image-manifest.v2", "sourceScribe": m["sourceScribe"], "cuts": [], "plan": plan}


def bump(version):
    m = re.match(r"^(v?)(\d+(?:\.\d+)*)$", version or "")
    if not m:
        return "v1.01"
    parts = m.group(2).split(".")
    parts[-1] = str(int(parts[-1]) + 1).zfill(len(parts[-1]))
    return m.group(1) + ".".join(parts)


def plan_of(man):
    """The plan as a list of entries. A v1 manifest becomes one generated entry per cut."""
    if man["schema"] == "vt-image-manifest.v1":
        return [{"entryId": k["cutId"], "scope": "clip", "clipId": k["clipId"], "kind": "generated", "cutId": k["cutId"]} for k in man["cuts"]]
    return man["plan"]


def file_of(e, manifest_dir, out_dir):
    """('file:<path relative to the merged Scribe's folder>', absolute path) or None when the entry has no file yet."""
    f = e.get("file")
    if not f:
        return None
    absf = f if os.path.isabs(f) else os.path.normpath(os.path.join(manifest_dir, f))
    ext = os.path.splitext(absf)[1].lower()
    if ext not in EXT:
        die("%s: file type %s is not one of %s" % (e["entryId"], ext or "(none)", ", ".join(sorted(EXT))))
    return "file:" + os.path.relpath(absf, out_dir).replace(os.sep, "/"), absf


def decide(src, man, manifest_dir, out_dir):
    """Work out every change without applying it: [(kind, place, value)], plus warnings and pending entries."""
    scenes = {s["sceneId"]: s for s in src["scenes"]}
    clips = {c["clipId"]: c for s in src["scenes"] for c in s["clips"]}
    order = [c["clipId"] for s in src["scenes"] for c in s["clips"]]
    pos = {cid: i for i, cid in enumerate(order)}
    cuts = {k["cutId"]: k for k in man.get("cuts", [])}
    bg, prompts, pending, warns, entry_clips = {}, {}, [], [], set()
    plan = plan_of(man)
    for e in plan:
        kind, scope = e["kind"], e["scope"]
        place = ("global", "") if scope == "global" else ("scene", e["sceneId"]) if scope == "scene" else ("clip", e["clipId"])
        if place[0] == "scene" and place[1] not in scenes or place[0] == "clip" and place[1] not in clips:
            die("%s: %s %r is not in the Scribe" % (e["entryId"], place[0], place[1]))
        if place[0] == "clip":
            entry_clips.add(place[1])
        if kind == "placeholder":
            pending.append("%s (%s %s): placeholder, nothing written" % (e["entryId"], place[0], place[1] or "-"))
        elif kind == "none":
            bg[place] = "none"
        elif kind == "generated":
            cut = cuts.get(e["cutId"])
            if not cut:
                die("%s: cut %r is not in the manifest" % (e["entryId"], e["cutId"]))
            if cut["clipId"] not in clips:
                die("%s: clip %r is not in the Scribe" % (e["entryId"], cut["clipId"]))
            prompts[cut["clipId"]] = cut
        else:                                                           # capture, upload, video
            if kind == "capture" and e.get("status") != "approved":
                pending.append("%s (%s %s): capture not approved yet (%s), nothing written" % (e["entryId"], place[0], place[1], e.get("status", "not taken")))
                continue
            fv = file_of(e, manifest_dir, out_dir)
            if not fv:
                pending.append("%s (%s %s): no file yet, nothing written" % (e["entryId"], place[0], place[1] or "-"))
                continue
            val, absf = fv
            if not os.path.isfile(absf):
                die("%s: file missing: %s" % (e["entryId"], absf))
            bg[place] = val
            if val.startswith("file:../"):
                warns.append("%s: %s is outside the Scribe's folder; copy it under that folder so VoiceTalker can load it" % (e["entryId"], val))
            sp = e.get("span")
            if sp and place[0] != "global":
                start = e.get("clipId") or scenes[e["sceneId"]]["clips"][0]["clipId"]
                end = sp["toClipId"]
                nxt = order[pos[end] + 1] if pos[end] + 1 < len(order) else None
                if nxt and nxt not in {x.get("clipId") for x in plan if x["scope"] == "clip"} and not clips[nxt].get("backgroundImageId"):
                    bg.setdefault(("clip", nxt), "none")
                    warns.append("%s: runs through %s, so %s gets none to end it" % (e["entryId"], end, nxt))
                est_words = sum(len(re.sub(r";p[\d.]+", "", clips[c]["text"]).split()) for c in order[pos[start]:pos[end] + 1])
                est = est_words / float(src.get("settings", {}).get("defaultScrollWpm", 145)) * 60
                dur = e.get("durationSeconds")
                if EXT.get(os.path.splitext(absf)[1].lower()) == "video" and dur and abs(est - dur) > 0.75 + 0.1 * est:
                    warns.append("%s: the narration under it is about %.1f s, the video is %.1f s" % (e["entryId"], est, dur))
    return bg, prompts, pending, warns, entry_clips


def merge(src, man, manifest_dir, out_dir, replace_library=False):
    if man["sourceScribe"]["scriptId"] != src["scriptId"]:
        die("manifest is for scriptId %r, Scribe is %r" % (man["sourceScribe"]["scriptId"], src["scriptId"]))
    bg, prompts, pending, warns, _ = decide(src, man, manifest_dir, out_dir)
    out = {}
    for k, v in src.items():
        if k in ("imageNames", "referenceImages"):
            continue
        out[k] = v
        if k == "description":
            out["imageNames"] = src.get("imageNames", {})
            out["referenceImages"] = src.get("referenceImages", {})
    if "description" not in src:
        out["imageNames"] = src.get("imageNames", {})
        out["referenceImages"] = src.get("referenceImages", {})
    out["version"] = bump(src.get("version", "v1.00"))
    if SENTENCE.strip() not in out.get("description", ""):
        out["description"] = out.get("description", "") + SENTENCE
    out["settings"] = json.loads(json.dumps(src["settings"]))
    if man["schema"] == "vt-image-manifest.v1" or prompts:
        for k, v in OVERLAY:
            out["settings"].setdefault(k, v)
    out["scenes"] = json.loads(json.dumps(src["scenes"]))
    scenes = {s["sceneId"]: s for s in out["scenes"]}
    clips = {c["clipId"]: c for s in out["scenes"] for c in s["clips"]}
    blocked, replaced = [], []
    for (lvl, key), val in bg.items():
        target = out["settings"] if lvl == "global" else scenes[key] if lvl == "scene" else clips[key]
        cur = target.get("backgroundImageId", "")
        if cur and cur != "none" and not cur.startswith("file:"):
            if not replace_library:
                blocked.append("%s %s already holds the generated picture %r" % (lvl, key or "-", cur))
                continue
            replaced.append("%s %s: library picture %s replaced" % (lvl, key or "-", cur))   # the owner approved replacing them (--replace-library)
        target["backgroundImageId"] = val
    for cid, cut in prompts.items():
        c = clips[cid]
        if c.get("backgroundImageId") and not c["backgroundImageId"].startswith("file:") and c["backgroundImageId"] != "none":
            blocked.append("clip %s already has a generated picture; its new prompt would be left unattached" % cid)
            continue
        c.pop("imagePrompt", None)
        c.pop("referenceNames", None)
        c["imagePrompt"] = cut["prompt"]
        if cut.get("referenceNames"):
            c["referenceNames"] = list(cut["referenceNames"])
    if blocked:
        die("ask the user before replacing these: " + "; ".join(blocked))
    warns = warns + replaced
    return out, pending, warns


def check(src, out, man, manifest_dir, out_dir):
    ok = True

    def bad(msg):
        nonlocal ok
        ok = False
        print("FAIL", msg)

    if out.get("schemaVersion") != "scribe.teleprompter.v1":
        bad("schemaVersion")
    bg, prompts, pending, warns, _ = decide(src, man, manifest_dir, out_dir)
    for k in set(src) | set(out):
        if k not in ("version", "description", "settings", "scenes", "imageNames", "referenceImages") and src.get(k) != out.get(k):
            bad("root key changed: " + k)
    if out.get("version") == src.get("version"):
        bad("version not raised")
    for k, v in src["settings"].items():
        if k != "backgroundImageId" and out["settings"].get(k) != v:
            bad("setting changed: " + k)
    if ("global", "") in bg:
        if out["settings"].get("backgroundImageId") != bg[("global", "")]:
            bad("settings backgroundImageId should be %r" % bg[("global", "")])
    elif out["settings"].get("backgroundImageId", "") != src["settings"].get("backgroundImageId", ""):
        bad("settings backgroundImageId changed")
    if len(src["scenes"]) != len(out["scenes"]):
        bad("scene count")
    n_bg = n_pr = 0
    for sa, sb in zip(src["scenes"], out["scenes"]):
        if {k: v for k, v in sa.items() if k not in ("backgroundImageId", "clips")} != {k: v for k, v in sb.items() if k not in ("backgroundImageId", "clips")}:
            bad("scene fields changed " + sa["sceneId"])
        want = bg.get(("scene", sa["sceneId"]))
        if want is not None:
            n_bg += 1
            if sb.get("backgroundImageId") != want:
                bad("scene %s should be %r, is %r" % (sa["sceneId"], want, sb.get("backgroundImageId")))
        elif sa.get("backgroundImageId", "") != sb.get("backgroundImageId", ""):
            bad("scene backgroundImageId changed on %s, which the plan does not name" % sa["sceneId"])
        if len(sa["clips"]) != len(sb["clips"]):
            bad("clip count " + sa["sceneId"])
        for ca, cb in zip(sa["clips"], sb["clips"]):
            cid = ca["clipId"]
            if {k: v for k, v in cb.items() if k not in ("backgroundImageId", "imagePrompt", "referenceNames")} != {k: v for k, v in ca.items() if k not in ("backgroundImageId", "imagePrompt", "referenceNames")}:
                bad("clip fields changed " + cid)
            w = bg.get(("clip", cid))
            if w is not None:
                n_bg += 1
                if cb.get("backgroundImageId") != w:
                    bad("clip %s should be %r, is %r" % (cid, w, cb.get("backgroundImageId")))
            elif ca.get("backgroundImageId", "") != cb.get("backgroundImageId", ""):
                bad("backgroundImageId changed on %s, which the plan does not name" % cid)
            if cid in prompts:
                n_pr += 1
                if cb.get("imagePrompt") != prompts[cid]["prompt"]:
                    bad("prompt differs from the manifest on " + cid)
                if (cb.get("referenceNames") or []) != (prompts[cid].get("referenceNames") or []):
                    bad("referenceNames differ from the manifest on " + cid)
            else:
                for f in ("imagePrompt", "referenceNames"):
                    if ca.get(f) != cb.get(f):
                        bad("%s changed on %s, which the plan does not name" % (f, cid))
            v = cb.get("backgroundImageId", "")
            if w is not None and v.startswith("file:") and not os.path.isfile(os.path.normpath(os.path.join(out_dir, v[5:]))):
                bad("file missing for %s: %s" % (cid, v))
    print("places with a picture, video or none:", n_bg, "| generated prompts:", n_pr, "| pending entries:", len(pending))
    for p in pending:
        print("  PENDING", p)
    for w in warns:
        print("  WARN", w)
    print("RESULT", "PASS" if ok else "FAIL")


def main(argv):
    a = list(argv)
    replace_library = "--replace-library" in a
    a = [x for x in a if x != "--replace-library"]
    if len(a) != 4 or a[0] not in ("merge", "check"):
        sys.exit(__doc__)
    mode, scribe, manifest, outp = a
    src = json.load(open(scribe, encoding="utf-8"))
    if src.get("schemaVersion") != "scribe.teleprompter.v1":
        die("the Scribe is not scribe.teleprompter.v1")
    man = load_manifest(manifest)
    manifest_dir = os.path.dirname(os.path.abspath(manifest))
    out_dir = os.path.dirname(os.path.abspath(outp))
    if mode == "merge":
        if os.path.abspath(outp) in (os.path.abspath(scribe), os.path.abspath(manifest)):
            die("never overwrite the source or the manifest")
        h = hashlib.sha256(open(scribe, "rb").read()).hexdigest()
        hm = hashlib.sha256(open(manifest, "rb").read()).hexdigest()
        out, pending, warns = merge(src, man, manifest_dir, out_dir, replace_library)
        same = lambda d: {k: v for k, v in d.items() if k not in ("version", "description")}
        if same(out) == same(src):                       # re-running a merge that changes nothing must not make a new version
            print("NO CHANGE: the Scribe already holds everything the plan says; no new file and no new version were written")
            for p in pending:
                print("PENDING", p)
            for w in warns:
                print("WARN", w)
            return
        open(outp, "w", encoding="utf-8").write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        if h != hashlib.sha256(open(scribe, "rb").read()).hexdigest() or hm != hashlib.sha256(open(manifest, "rb").read()).hexdigest():
            sys.exit("FAIL a source file changed")
        print("wrote", outp)
        for p in pending:
            print("PENDING", p)
        for w in warns:
            print("WARN", w)
    else:
        check(src, json.load(open(outp, encoding="utf-8")), man, manifest_dir, out_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
