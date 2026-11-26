#!/usr/bin/env python3
"""image-manifest: check the media plan of a vt-image-manifest.v2 manifest against its Scribe.

    python3 -I check_plan.py <manifest.md|.json> <scribe.json>

The plan says, for each scene or clip, which media it gets (generated, capture, upload, video, placeholder) or none.
Media are all optional: a clip with no entry simply keeps what is already on screen. Standard library only (Python 3.8+).
"""
import json
import os
import re
import sys

FENCE = chr(96) * 3
KINDS = ("generated", "capture", "upload", "video", "placeholder", "none")
SCOPES = ("global", "scene", "clip")
EXT = {".mp4": "video", ".webm": "video", ".mp3": "audio", ".png": "picture", ".jpg": "picture", ".jpeg": "picture",
       ".webp": "picture", ".gif": "picture", ".svg": "svg"}


def load_manifest(path):
    text = open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
    if not blocks:
        sys.exit("FAIL the manifest has no json block")
    return json.loads(blocks[-1])


def plain(text):
    """Clip words as spoken: pause markers removed, whitespace collapsed."""
    return " ".join(re.sub(r";p[\d.]+", "", text).split())


def norm(s):
    """Lowercase words only: '&' reads as 'and', punctuation and case ignored (same rule as the capture step)."""
    s = s.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    man = load_manifest(argv[0])
    scribe = json.load(open(argv[1], encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(argv[0]))
    ok = True

    def bad(msg):
        nonlocal ok
        ok = False
        print("FAIL", msg)

    if man.get("schema") != "vt-image-manifest.v2":
        sys.exit("FAIL schema must be vt-image-manifest.v2")
    if man["sourceScribe"]["scriptId"] != scribe["scriptId"]:
        bad("manifest is for scriptId %r, Scribe is %r" % (man["sourceScribe"]["scriptId"], scribe["scriptId"]))
    scenes = {s["sceneId"]: s for s in scribe["scenes"]}
    clips = {c["clipId"]: c for s in scribe["scenes"] for c in s["clips"]}
    order = {cid: n for n, cid in enumerate(c["clipId"] for s in scribe["scenes"] for c in s["clips"])}
    clip_scene = {c["clipId"]: s["sceneId"] for s in scribe["scenes"] for c in s["clips"]}
    cuts = {k["cutId"]: k for k in man.get("cuts", [])}
    plan = man.get("plan")
    if not isinstance(plan, list) or not plan:
        sys.exit("FAIL the manifest has no plan list")

    ids, places, counts = set(), {}, {k: 0 for k in KINDS}
    generated_cuts = set()
    for e in plan:
        eid = e.get("entryId", "?")
        if eid in ids:
            bad("duplicate entryId " + eid)
        ids.add(eid)
        scope, kind = e.get("scope"), e.get("kind")
        if scope not in SCOPES:
            bad("%s: scope must be one of %s" % (eid, SCOPES))
            continue
        if kind not in KINDS:
            bad("%s: kind must be one of %s" % (eid, KINDS))
            continue
        counts[kind] += 1
        if scope == "clip":
            if e.get("clipId") not in clips:
                bad("%s: clip %r is not in the Scribe" % (eid, e.get("clipId")))
                continue
            place = ("clip", e["clipId"])
        elif scope == "scene":
            if e.get("sceneId") not in scenes:
                bad("%s: scene %r is not in the Scribe" % (eid, e.get("sceneId")))
                continue
            place = ("scene", e["sceneId"])
        else:
            place = ("global", "")
        if place in places:
            bad("%s and %s are on the same place %s" % (places[place], eid, place))
        places[place] = eid

        if kind == "generated":
            cut = cuts.get(e.get("cutId"))
            if not cut:
                bad("%s: generated entry names cut %r, which is not in cuts" % (eid, e.get("cutId")))
            else:
                generated_cuts.add(cut["cutId"])
                want = e["clipId"] if scope == "clip" else scenes[e["sceneId"]]["clips"][0]["clipId"] if scope == "scene" else None
                if want and cut["clipId"] != want:
                    bad("%s: cut %s sits on %s, the plan entry is on %s" % (eid, cut["cutId"], cut["clipId"], want))
        elif kind == "capture" or (kind == "video" and e.get("source") == "capture"):
            if scope != "clip":
                bad("%s: a capture is tied to the words of one clip, so scope must be clip" % eid)
                continue
            ms = e.get("mustShow")
            if not isinstance(ms, list) or not ms or not all(isinstance(x, str) and x.strip() for x in ms):
                bad("%s: a capture needs mustShow, a non-empty list of the page labels that must be visible" % eid)
            if e.get("words") != plain(clips[e["clipId"]]["text"]):
                bad("%s: words must equal the clip's spoken words exactly" % eid)
            spoken = " " + norm(plain(clips[e["clipId"]]["text"])) + " "
            for ph in (ms if isinstance(ms, list) else []):
                if isinstance(ph, str) and (" " + norm(ph) + " ") not in spoken:
                    bad("%s: mustShow %r is not in the words of this clip; a shot may only show what its clip speaks about" % (eid, ph))
            fr = e.get("frame", {})
            if fr.get("width") != 1920 or fr.get("height") != 1080:
                bad("%s: frame must be 1920 x 1080" % eid)
            if not e.get("page"):
                bad("%s: a capture needs page (the address of the page to capture)" % eid)
        if kind in ("upload", "video") and e.get("source") != "capture":
            f = e.get("file", "")
            ext = os.path.splitext(f)[1].lower()
            if ext not in EXT:
                bad("%s: file type %s is not one of %s" % (eid, ext or "(none)", ", ".join(sorted(EXT))))
            elif not os.path.isfile(f if os.path.isabs(f) else os.path.join(base, f)):
                bad("%s: file not found: %s" % (eid, f))
            elif e.get("mediaType") and e["mediaType"] != EXT[ext]:
                bad("%s: mediaType %s does not match the file type %s" % (eid, e["mediaType"], EXT[ext]))
        if kind == "placeholder" and e.get("wantKind") not in (None, "generated", "capture", "upload", "video"):
            bad("%s: wantKind must be generated, capture, upload, video or empty" % eid)
        sp = e.get("span")
        if sp:
            if scope == "global":
                bad("%s: a global entry already covers everything; it has no span" % eid)
            elif sp.get("toClipId") not in clips:
                bad("%s: span.toClipId %r is not in the Scribe" % (eid, sp.get("toClipId")))
            else:
                start = e["clipId"] if scope == "clip" else scenes[e["sceneId"]]["clips"][0]["clipId"]
                if order[sp["toClipId"]] < order[start]:
                    bad("%s: span ends before it starts" % eid)
                for p2, e2 in places.items():
                    if e2 != eid and p2[0] == "clip" and order[start] < order[p2[1]] <= order[sp["toClipId"]]:
                        print("NOTE  %s starts inside the span of %s: it replaces it from that clip on" % (e2, eid))
        if kind == "none" and any(k in e for k in ("file", "cutId", "mustShow", "span")):
            bad("%s: a none entry carries nothing else" % eid)

    for cid in cuts:
        if cid not in generated_cuts:
            bad("cut %s is in cuts but no plan entry uses it" % cid)

    starts = {p[1] for p in places if p[0] == "clip"}
    scene_starts = {p[1] for p in places if p[0] == "scene"}
    covered = len(starts) + len(scene_starts)
    print("plan entries", len(plan), " ".join("%s %d" % (k, counts[k]) for k in KINDS))
    print("clips", len(clips), "scenes", len(scenes), "entries on clips", len(starts), "on scenes", len(scene_starts),
          "global", 1 if ("global", "") in places else 0)
    print("clips with no entry (keep what is on screen):", len(clips) - len(starts))
    print("RESULT", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
