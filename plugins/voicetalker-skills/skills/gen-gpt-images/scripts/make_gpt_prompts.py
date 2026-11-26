#!/usr/bin/env python3
"""gen-gpt-images: turn a VoiceTalker image manifest into an indexed ChatGPT prompt set (JSON).

Standard library only (Python 3.8 or later). Reads vt-image-manifest v1 or v2 (the last json block of the .md),
never changes it. Usage:
  python3 -I make_gpt_prompts.py <manifest.md> <out.json> [--format jpg|png] [--cuts all|1,3,5|CUT-ID,CUT-ID]
                                 [--cast cast.md] [--max-attach 5]
Prints a summary and RESULT PASS or FAIL.
"""
import argparse, json, re, sys

FENCE = chr(96) * 3
ap = argparse.ArgumentParser()
ap.add_argument("manifest"); ap.add_argument("out")
ap.add_argument("--format", default="jpg", choices=["jpg", "png"])
ap.add_argument("--cuts", default="all")
ap.add_argument("--cast", default="")
ap.add_argument("--max-attach", type=int, default=5)
a = ap.parse_args()

md = open(a.manifest, encoding="utf-8").read()
blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, md, re.S)
if not blocks:
    sys.exit("FAIL no json block in the manifest")
m = json.loads(blocks[-1])
if not str(m.get("schema", "")).startswith("vt-image-manifest"):
    sys.exit("FAIL not an image manifest")
ok = True
def bad(msg):
    global ok; ok = False; print("FAIL", msg)

cuts = m["cuts"]
tok = m["aspectToken"]
ASPECT = {"16:9": "16:9 landscape, 1920x1080", "9:16": "9:16 portrait, 1080x1920", "1:1": "1:1 square, 1080x1080"}
ratio = next((r for r in ASPECT if tok.startswith(r)), None)
if not ratio: bad("unknown aspect token: " + tok); ratio = "16:9"
EXT = a.format
FMT = "JPG" if EXT == "jpg" else "PNG"

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return "-".join(s.split("-")[:6]) or "picture"

# index and filename of EVERY cut (so numbering never changes when a subset is chosen)
rows = []
for i, k in enumerate(cuts, 1):
    mm = re.search(r"Cut " + re.escape(k["cutId"]) + r":\s*(.*?)\.\s", k["prompt"])
    label = mm.group(1) if mm else k["cutId"]
    rows.append({"index": i, "cut": k, "file": "%02d-%s.%s" % (i, slug(label), EXT)})
by_cut = {r["cut"]["cutId"]: r for r in rows}

# key frame of each reference name = the file of its first picture
key_file = {}
for ref in m.get("references", []):
    r = by_cut.get(ref["firstCut"])
    if not r: bad("firstCut not in cuts: " + ref["firstCut"]); continue
    key_file[ref["name"]] = r["file"]

# choose cuts
sel = rows
if a.cuts != "all":
    want = [x.strip() for x in a.cuts.split(",") if x.strip()]
    sel = [r for r in rows if str(r["index"]) in want or r["cut"]["cutId"] in want]
    if len(sel) != len(want): bad("--cuts names something that is not in the manifest")
chosen = {r["cut"]["cutId"] for r in sel}

def attach_for(k):
    files = []
    for n in k.get("referenceNames", []):
        f = key_file.get(n)
        if f and f != by_cut[k["cutId"]]["file"] and f not in files: files.append(f)
    return files[: a.max_attach]

images = []
for r in sel:
    k = r["cut"]; p = k["prompt"]; att = attach_for(k)
    if att:
        lst = ", ".join(att)
        p = re.sub(r"the attached reference (image|photo)s?", "the attached picture" + ("s " if len(att) > 1 else " ") + lst, p)
        p = re.sub(r"[Mm]atch the attached reference images?\.", "Match the characters in the attached picture" + ("s " if len(att) > 1 else " ") + lst + " exactly.", p)
    else:
        p = p.replace(" as the attached reference image in every picture", " in every picture")
        p = re.sub(r"\s*[Mm]atch the attached reference images?\.", "", p)
    p = p.rstrip() + "\n\nOutput: one single image, %s, saved as %s." % (ASPECT[ratio], FMT)
    if not p.startswith(tok): bad("prompt lost the aspect token: " + k["cutId"])
    for n in k.get("referenceNames", []):
        if n not in key_file: bad("reference with no key frame: " + n)
    for f in att:
        src = next(x for x in rows if x["file"] == f)
        if src["cut"]["cutId"] not in chosen and a.cuts != "all":
            print("NOTE %s needs %s, which is not in your chosen set: attach the one you already made" % (r["file"], f))
    images.append({"index": r["index"], "filename": r["file"], "cutId": k["cutId"], "clipId": k["clipId"], "role": k["role"],
                   "attachBeforeGenerating": att, "chars": len(p), "prompt": p})

if len({i["filename"] for i in images}) != len(images): bad("duplicate filenames")
# generation order: key frames first, then the rest by index
keyset = set(key_file.values())
order = [i["filename"] for i in images if i["filename"] in keyset] + [i["filename"] for i in images if i["filename"] not in keyset]
done = set()
for fn in order:
    img = next(i for i in images if i["filename"] == fn)
    for f in img["attachBeforeGenerating"]:
        if f not in done and a.cuts == "all": bad("%s needs %s first" % (fn, f))
    done.add(fn)

style = ""
mm = re.search(r"^- Style:\s*(.+)$", md, re.M)
if mm: style = mm.group(1).strip()
looks = {}
if a.cast:
    cm = re.findall(FENCE + r"json\n(.*?)" + FENCE, open(a.cast, encoding="utf-8").read(), re.S)
    if cm:
        for c in json.loads(cm[-1]).get("characters", []):
            if c.get("referenceName") in key_file and c.get("imageDescription"):
                looks[c["referenceName"]] = c["imageDescription"]

out = {"project": m.get("project", ""), "format": {"aspectRatio": ratio, "size": ASPECT[ratio].split(", ")[1], "fileType": EXT, "count": len(images)},
       "howToUse": [
           "Use ONE ChatGPT conversation for the whole set so the look stays consistent.",
           "Generate the key frames first (generationOrder), approve each, and save it with the filename shown: they are the references for every later picture.",
           "For a picture that lists attachBeforeGenerating, attach those files to your message, then paste the prompt.",
           "Pictures with no attachment (cards, places, objects) are pasted alone. Check any lettering is spelled exactly.",
           "If ChatGPT returns another shape or format, reply: Regenerate as %s, %s, same image." % (ASPECT[ratio], FMT),
           "Save each result under the filename shown. Merge or load them in VoiceTalker as your own pictures."],
       "consistency": {"style": style, "keyFrames": key_file, "looks": looks},
       "generationOrder": order, "images": images}
json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False); open(a.out, "a").write("\n")
print("images", len(images), "key frames", len(key_file), "longest prompt", max([i["chars"] for i in images] or [0]))
for i in images: print("  %-40s attach: %s" % (i["filename"], ", ".join(i["attachBeforeGenerating"]) or "-"))
print("RESULT", "PASS" if ok else "FAIL")
