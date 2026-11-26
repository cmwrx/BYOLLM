#!/usr/bin/env python3
"""image-manifest: repair a media plan (vt-image-manifest.v2) without rebuilding it.

    python3 -I plan_repair.py list   <manifest>
    python3 -I plan_repair.py sync   <manifest> <scribe.json>
    python3 -I plan_repair.py patch  <manifest> <entryId> '<json of the fields to change>'
    python3 -I plan_repair.py add    <manifest> '<json of the new entry>'
    python3 -I plan_repair.py remove <manifest> <entryId>

Every other entry keeps its status, file and fields. A plan is never rebuilt to fix one entry.
  sync   compares each entry with the Scribe as it is NOW: a capture whose clip words changed gets its words updated and its
         status set to stale (it must be retaken); an entry whose clip is gone is reported (never deleted); labels in mustShow
         that the new words no longer name are reported; a generated entry whose clip words changed is reported (its prompt may
         need rewriting). The manifest's sourceScribe.version is brought up to date.
  patch  changes the named fields of one entry. Changing a capture's words, mustShow or page sets its status to retake.
  add    adds one entry (entryId is made if missing). remove deletes one entry and says which cut, if any, it leaves unused.
Standard library only (Python 3.8+).
"""
import json
import re
import sys

FENCE = chr(96) * 3
CAPTURE_FIELDS = ("words", "mustShow", "page", "frame", "clipId")


def load_manifest(path):
    text = open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
    if not blocks:
        sys.exit("FAIL the manifest has no json block")
    return json.loads(blocks[-1])


def save_manifest(path, m):
    body = json.dumps(m, indent=2, ensure_ascii=False)
    if path.lower().endswith(".json"):
        open(path, "w", encoding="utf-8").write(body + "\n")
        return
    text = open(path, encoding="utf-8").read()
    a = text.rfind(FENCE + "json\n")
    b = text.find(FENCE, a + 8)
    open(path, "w", encoding="utf-8").write(text[:a] + FENCE + "json\n" + body + "\n" + text[b:])


def plain(text):
    return " ".join(re.sub(r";p[\d.]+", "", text).split())


def norm(s):
    s = s.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def find(m, entry_id):
    for e in m["plan"]:
        if e["entryId"] == entry_id:
            return e
    sys.exit("FAIL no entry %s in the plan" % entry_id)


def is_capture(e):
    return e.get("kind") == "capture" or (e.get("kind") == "video" and e.get("source") == "capture")


def cmd_list(m):
    for e in m["plan"]:
        where = e.get("clipId") or e.get("sceneId") or "(whole Scribe)"
        print("%-5s %-9s %-14s %-9s %s" % (e["entryId"], e["kind"], where, e.get("status", "-"), ", ".join(e.get("mustShow", [])) or e.get("file", "")))


def cmd_sync(m, scribe):
    clips = {c["clipId"]: c for s in scribe["scenes"] for c in s["clips"]}
    scenes = {s["sceneId"] for s in scribe["scenes"]}
    changed = orphan = stale = 0
    for e in m["plan"]:
        place = e.get("clipId") if e["scope"] == "clip" else e.get("sceneId") if e["scope"] == "scene" else None
        if e["scope"] == "clip" and place not in clips or e["scope"] == "scene" and place not in scenes:
            print("ORPHAN  %s: %s %s is not in the Scribe any more (the entry is kept; remove or patch it)" % (e["entryId"], e["scope"], place))
            orphan += 1
            continue
        if e["scope"] != "clip":
            continue
        now = plain(clips[place]["text"])
        if "words" in e and e["words"] != now:
            changed += 1
            e["words"] = now
            if is_capture(e):
                e["status"] = "stale"
                e.pop("file", None)
                stale += 1
                print("STALE   %s: the words of %s changed; retake this shot" % (e["entryId"], place))
            else:
                print("CHANGED %s: the words of %s changed" % (e["entryId"], place))
        if is_capture(e):
            spoken = " " + norm(now) + " "
            for ph in e.get("mustShow", []):
                if (" " + norm(ph) + " ") not in spoken:
                    print("LABEL   %s: %r is no longer in the words; patch mustShow" % (e["entryId"], ph))
        elif e["kind"] == "generated":
            cut = next((k for k in m.get("cuts", []) if k["cutId"] == e.get("cutId")), None)
            if cut and cut.get("words") not in (None, now) and "words" not in e:
                print("PROMPT  %s: the words of %s changed; check the prompt of %s" % (e["entryId"], place, cut["cutId"]))
    m["sourceScribe"]["version"] = scribe.get("version", m["sourceScribe"].get("version"))
    print("sync done: %d changed, %d stale, %d orphan, entries kept %d" % (changed, stale, orphan, len(m["plan"])))


def cmd_patch(m, entry_id, patch):
    e = find(m, entry_id)
    fields = json.loads(patch)
    if "entryId" in fields and fields["entryId"] != entry_id:
        sys.exit("FAIL an entry keeps its entryId")
    if is_capture(e) and any(k in fields and fields[k] != e.get(k) for k in CAPTURE_FIELDS):
        e["status"] = "retake"
        e.pop("file", None)
        print("%s: its shot must be retaken (status retake)" % entry_id)
    e.update(fields)
    print("patched", entry_id)


def cmd_add(m, entry):
    e = json.loads(entry)
    if "entryId" not in e:
        used = [int(x["entryId"][1:]) for x in m["plan"] if re.fullmatch(r"M\d+", x["entryId"])]
        e["entryId"] = "M%02d" % (max(used or [0]) + 1)
    if any(x["entryId"] == e["entryId"] for x in m["plan"]):
        sys.exit("FAIL entryId %s already exists" % e["entryId"])
    m["plan"].append(e)
    print("added", e["entryId"])


def cmd_remove(m, entry_id):
    e = find(m, entry_id)
    m["plan"].remove(e)
    print("removed", entry_id)
    cid = e.get("cutId")
    if cid and not any(x.get("cutId") == cid for x in m["plan"]):
        print("NOTE    cut %s is now unused; remove it from cuts if its picture is no longer wanted" % cid)


def main(a):
    if len(a) < 2 or a[0] not in ("list", "sync", "patch", "add", "remove"):
        sys.exit(__doc__)
    cmd, path = a[0], a[1]
    m = load_manifest(path)
    if m.get("schema") != "vt-image-manifest.v2":
        sys.exit("FAIL not a vt-image-manifest.v2 manifest")
    if cmd == "list":
        return cmd_list(m)
    if cmd == "sync":
        cmd_sync(m, json.load(open(a[2], encoding="utf-8")))
    elif cmd == "patch":
        cmd_patch(m, a[2], a[3])
    elif cmd == "add":
        cmd_add(m, a[2])
    else:
        cmd_remove(m, a[2])
    save_manifest(path, m)


if __name__ == "__main__":
    main(sys.argv[1:])
