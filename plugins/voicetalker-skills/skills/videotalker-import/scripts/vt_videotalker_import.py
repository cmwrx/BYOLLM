#!/usr/bin/env python3
"""videotalker-import: turn a VideoTalker scene list into a vt-video-manifest.v1 for a VoiceTalker Scribe.

    python3 -I vt_videotalker_import.py build <scene-list.json> <scribe.json> <out-manifest.md>
            [--project-dir DIR] [--prefer final|draft] [--map map.json]
    python3 -I vt_videotalker_import.py check <manifest.md|.json> <scribe.json>

Reads VideoTalker's video-scene.json (shared/video-scene-schema.ts, schemaVersion 2.x). Standard library only
(Python 3.8+); ffprobe is used when present to read each file's real length and size.
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys

FENCE = chr(96) * 3
SCHEMA = "vt-video-manifest.v1"
TYPES = (".mp4", ".webm")
FUZZY = 0.92


def die(msg):
    sys.exit("STOP: " + msg)


# ------------------------------------------------------------------ text matching
def words(text):
    t = (text or "").lower()
    t = re.sub(r";p[\d.]+", " ", t)                       # VoiceTalker pause markers
    t = re.sub(r"<[a-z -]+>", " ", t)                     # Gemini inline tags
    t = t.replace("®", "").replace("™", "").replace("©", "")
    t = re.sub(r"[‘’]", "'", t)
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return t.split()


def scene_text(scene):
    """What the Scribe's narration for this scene says: dialogue lines in order, else the narration."""
    lines = [d.get("text", "") for d in (scene.get("dialogue") or []) if d.get("text")]
    return " ".join(lines) if lines else (scene.get("narration") or "")


def flat_clips(scribe):
    out = []
    for s in scribe["scenes"]:
        for c in s["clips"]:
            out.append({"clipId": c["clipId"], "scene": s["title"], "words": words(c["text"]), "text": c["text"]})
    return out


def match_span(target, clips, start):
    """First run of consecutive clips (at or after index `start`) whose words make up `target`. Exact first, then a close fuzzy match."""
    n = len(target)
    if n == 0:
        return None
    for exact in (True, False):
        for i in range(start, len(clips)):
            acc, j = [], i
            while j < len(clips) and len(acc) < n:
                acc += clips[j]["words"]
                j += 1
                if exact and acc == target:
                    return i, j - 1, 1.0
                if not exact and len(acc) >= n * 0.9 and len(acc) <= n * 1.1:
                    r = difflib.SequenceMatcher(None, acc, target).ratio()
                    if r >= FUZZY:
                        return i, j - 1, r
                if len(acc) > n * 1.15:
                    break
    return None


# ------------------------------------------------------------------ files
def probe(path):
    exe = shutil.which("ffprobe")
    if not exe:
        return {}
    try:
        r = subprocess.run([exe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration,size",
                            "-of", "json", path], capture_output=True, text=True, timeout=60)
        j = json.loads(r.stdout or "{}")
        st = (j.get("streams") or [{}])[0]
        fm = j.get("format", {})
        return {"width": st.get("width"), "height": st.get("height"),
                "durationSeconds": round(float(fm["duration"]), 2) if fm.get("duration") else None,
                "sizeBytes": int(fm["size"]) if fm.get("size") else None}
    except Exception:
        return {}


def project_dir(scene_file, given):
    if given:
        return os.path.abspath(given)
    d = os.path.dirname(os.path.abspath(scene_file))          # <project>/ingest/scene
    if os.path.basename(d) == "scene" and os.path.basename(os.path.dirname(d)) == "ingest":
        return os.path.dirname(os.path.dirname(d))
    die("cannot find the project folder from the scene file's location; pass --project-dir <projectsRoot>/<projectName>")


def find_video(scene, outdir, prefer):
    g = scene.get("generation") or {}
    final = (g.get("output") or {}).get("fileName")
    draft = (g.get("draft") or {}).get("outputFileName")
    cands = [("final", final), ("draft", draft)] if prefer == "final" else [("draft", draft), ("final", final)]
    for kind, name in cands:
        if name:
            p = os.path.join(outdir, name)
            if os.path.isfile(p):
                return kind, p
    return None, None


def rel_or_abs(path, base):
    """Relative to the manifest's folder when the video sits under it, else the full path (a '../../..' chain breaks when the folder moves)."""
    rel = os.path.relpath(path, base)
    return path if rel.startswith("..") else rel


def cut_title(scene):
    return re.sub(r"\s+", " ", ("%s %s" % (scene.get("shotId", ""), scene.get("title", ""))).strip())


# ------------------------------------------------------------------ build
def build(scene_file, scribe_file, out_file, opts):
    sl = json.load(open(scene_file, encoding="utf-8"))
    if not str(sl.get("schemaVersion", "")).startswith("2"):
        die("not a VideoTalker video-scene file (schemaVersion %r, expected 2.x)" % sl.get("schemaVersion"))
    scribe = json.load(open(scribe_file, encoding="utf-8"))
    if scribe.get("schemaVersion") != "scribe.teleprompter.v1":
        die("the target is not a scribe.teleprompter.v1 Scribe")
    proj = project_dir(scene_file, opts.get("project-dir"))
    outdir = os.path.join(proj, "output", "scenes")
    if not os.path.isdir(outdir):
        die("no output/scenes folder at " + outdir)
    clips = flat_clips(scribe)
    index = {c["clipId"]: i for i, c in enumerate(clips)}
    manual = json.load(open(opts["map"], encoding="utf-8")) if opts.get("map") else {}
    cuts, unplaced, notes = [], [], []
    cursor = 0
    taken = set()
    for sc in sl["scenes"]:
        shot = sc.get("shotId", "scene-%s" % sc.get("sceneNumber"))
        if sc.get("continuousRef"):
            unplaced.append({"shotId": shot, "reason": "a continuous-scene slot (its segments are not scenes); map it by hand"})
            continue
        kind, path = find_video(sc, outdir, opts.get("prefer", "final"))
        if not path:
            unplaced.append({"shotId": shot, "reason": "no video file in output/scenes for this scene (not generated yet)"})
            continue
        # which clips does this scene sit on
        span = None
        how = ""
        if shot in manual:
            m = manual[shot]
            ids = [m] if isinstance(m, str) else list(m)
            bad = [i for i in ids if i not in index]
            if bad:
                die("--map names clips that are not in the Scribe: %s" % bad)
            span = (index[ids[0]], index[ids[-1]], 1.0)
            how = "map file"
        else:
            tgt = words(scene_text(sc))
            if not tgt:
                unplaced.append({"shotId": shot, "reason": "no narration or dialogue, so no Scribe clip to attach to (add it to --map to place it)"})
                continue
            span = match_span(tgt, clips, cursor)
            how = "text match"
        if not span:
            unplaced.append({"shotId": shot, "reason": "no run of Scribe clips carries this scene's narration (the Scribe's words differ)"})
            continue
        a, b, ratio = span
        if any(clips[i]["clipId"] in taken for i in range(a, b + 1)):
            unplaced.append({"shotId": shot, "reason": "its clips already belong to an earlier scene"})
            continue
        for i in range(a, b + 1):
            taken.add(clips[i]["clipId"])
        cursor = b + 1
        meta = probe(path)
        g = sc.get("generation") or {}
        runs = [r.get("actualMedia") for r in g.get("runs", []) if r.get("actualMedia")]
        if not meta and runs:
            am = runs[-1]
            meta = {"width": am.get("width"), "height": am.get("height"), "durationSeconds": am.get("durationSeconds")}
        cut = {
            "cutId": "V%02d" % (len(cuts) + 1),
            "shotId": shot,
            "title": cut_title(sc),
            "attach": "clip",
            "clipId": clips[a]["clipId"],
            "clipIds": [clips[i]["clipId"] for i in range(a, b + 1)],
            "file": rel_or_abs(path, os.path.dirname(os.path.abspath(out_file))),
            "fileKind": kind,
            "mediaType": "video",
            "durationSeconds": meta.get("durationSeconds") or sc.get("durationSeconds"),
            "width": meta.get("width"),
            "height": meta.get("height"),
            "sizeBytes": meta.get("sizeBytes"),
            "matchedBy": how if ratio >= 1.0 else "%s (%.0f%% like)" % (how, ratio * 100),
        }
        warns = problems(cut)
        if kind == "draft":
            warns.append("draft file (%sp), not the final render" % (cut["height"] or "?"))
        if warns:
            cut["warnings"] = warns
        cuts.append(cut)
    if not cuts:
        die("no scene could be placed on a Scribe clip; nothing to write")
    man = {
        "schema": SCHEMA,
        "sourceScribe": {"scriptId": scribe.get("scriptId"), "version": scribe.get("version"), "title": scribe.get("title")},
        "source": {"kind": "videotalker-scene-list", "file": os.path.basename(scene_file), "projectName": sl.get("projectName"),
                   "schemaVersion": sl.get("schemaVersion"), "sceneCount": len(sl["scenes"])},
        "cuts": cuts,
        "unplaced": unplaced,
    }
    write_md(man, out_file)
    return man


def problems(cut):
    out = []
    if os.path.splitext(cut["file"])[1].lower() not in TYPES:
        out.append("file type must be .mp4 or .webm")
    return out


def write_md(man, out_file):
    L = ["# Video cut sheet for %s" % (man["sourceScribe"].get("title") or man["sourceScribe"]["scriptId"]), ""]
    L.append("Source: VideoTalker scene list `%s` (project %s, %d scenes). Target Scribe `%s` %s." % (
        man["source"]["file"], man["source"]["projectName"], man["source"]["sceneCount"], man["sourceScribe"]["scriptId"], man["sourceScribe"].get("version") or ""))
    L += ["", "| Cut | Shot | Attaches to clip | Covers | File | Length | Size | Note |", "|---|---|---|---|---|---|---|---|"]
    for c in man["cuts"]:
        L.append("| %s | %s | %s | %s | `%s` | %s | %s | %s |" % (
            c["cutId"], c["shotId"], c["clipId"], c["clipIds"][0] + (" to " + c["clipIds"][-1] if len(c["clipIds"]) > 1 else ""), c["file"],
            ("%.1f s" % c["durationSeconds"]) if c.get("durationSeconds") else "?",
            ("%dx%d" % (c["width"], c["height"])) if c.get("width") else "?",
            "; ".join(c.get("warnings", [])) or c["matchedBy"]))
    if man["unplaced"]:
        L += ["", "## Not placed", ""] + ["- %s: %s" % (u["shotId"], u["reason"]) for u in man["unplaced"]]
    L += ["", "```json", json.dumps(man, indent=2, ensure_ascii=False), "```", ""]
    open(out_file, "w", encoding="utf-8").write("\n".join(L))


# ------------------------------------------------------------------ check
def check(manifest_file, scribe_file):
    text = open(manifest_file, encoding="utf-8").read()
    if manifest_file.lower().endswith(".json"):
        man = json.loads(text)
    else:
        blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
        if not blocks:
            die("no json block")
        man = json.loads(blocks[-1])
    scribe = json.load(open(scribe_file, encoding="utf-8"))
    ok = True

    def bad(m):
        nonlocal ok
        ok = False
        print("FAIL", m)

    if man.get("schema") != SCHEMA:
        bad("schema")
    if man["sourceScribe"]["scriptId"] != scribe.get("scriptId"):
        bad("scriptId differs from the Scribe")
    index = {c["clipId"]: i for i, c in enumerate(flat_clips(scribe))}
    base = os.path.dirname(os.path.abspath(manifest_file))
    seen_clip, seen_id, last = set(), set(), -1
    for c in man["cuts"]:
        if c["cutId"] in seen_id:
            bad("duplicate cutId " + c["cutId"])
        seen_id.add(c["cutId"])
        for i in c["clipIds"]:
            if i not in index:
                bad("%s: clip %s is not in the Scribe" % (c["cutId"], i))
            elif i in seen_clip:
                bad("%s: clip %s is used by two cuts" % (c["cutId"], i))
            seen_clip.add(i)
        if c["clipId"] != c["clipIds"][0]:
            bad(c["cutId"] + ": clipId must be the first of clipIds")
        if c["clipId"] in index:
            if index[c["clipId"]] <= last:
                bad("%s: cuts are not in Scribe order" % c["cutId"])
            last = index[c["clipId"]]
        if not os.path.isfile(os.path.normpath(os.path.join(base, c["file"]))):
            bad("%s: file missing: %s" % (c["cutId"], c["file"]))
        for p in problems(c):
            bad("%s: %s" % (c["cutId"], p))
        if c.get("attach") != "clip":
            bad(c["cutId"] + ": this importer attaches to clips")
    print("cuts", len(man["cuts"]), "| not placed", len(man["unplaced"]), "| drafts", sum(1 for c in man["cuts"] if c.get("fileKind") == "draft"))
    print("RESULT", "PASS" if ok else "FAIL")


def main(argv):
    a = list(argv)
    opts = {}
    for flag in ("project-dir", "prefer", "map"):
        k = "--" + flag
        if k in a:
            i = a.index(k)
            opts[flag] = a[i + 1]
            del a[i:i + 2]
    if opts.get("prefer", "final") not in ("final", "draft"):
        sys.exit(__doc__)
    if a and a[0] == "build" and len(a) == 4:
        if os.path.abspath(a[3]) in (os.path.abspath(a[1]), os.path.abspath(a[2])):
            die("never overwrite an input")
        man = build(a[1], a[2], a[3], opts)
        print("wrote", a[3], "| cuts", len(man["cuts"]), "| not placed", len(man["unplaced"]))
    elif a and a[0] == "check" and len(a) == 3:
        check(a[1], a[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
