#!/usr/bin/env python3
"""Character-drift and undefined-actor check for VoiceTalker image prompts.

Usage: python3 -I check_drift.py <scribe.json | manifest.md> <cast.md> [--staging studio|story|mini-play] [--scribe <scribe.json>]
(--scribe is required when the first argument is a manifest, so every clip can be checked in playback order)

Reads the image prompts from a Scribe (clips with imagePrompt) or from a Step 2 manifest (its last json block)
and the cast from the cast file (its last json block, schema vt-cast.v1). Prints RESULT PASS only when:
  R1  every cast person drawn in a prompt is listed in referenceNames, and every person name listed is drawn
  R2  no person, hand, face, crowd, child, silhouette or other body or figure appears that is not a named cast character
  R3  (studio staging only) actors are never alone: every picture that shows a cast person shows the whole cast together in the same studio shot.
      Story staging (play, drama, storyboard, film, comic) skips R3: pictures show only the people in that moment of that scene.
      The staging is --staging, else the "staging" field of the manifest json block, else the cast file's "staging", else studio.
  R4  the first picture of a person name has no baked-in lettering, unless it sits on the clip where that person first speaks
  R5  every picture of a cast person carries the anti-drift clause
  R6  a cast person who has a supplied reference photo is written as "exactly as in the attached reference photo"
  R7  the Avoid text forbids unnamed people
  R10 SPEAKER VISIBLE: on every clip spoken by an on-screen cast character, the picture in effect (the clip's own picture or the one carried
      from an earlier clip) names that speaker. A character never speaks off screen, in an empty room or over someone else's picture.
  R11 CONVERSATION KEPT: the picture in effect on a clip also names the cast character who spoke the clip just before it, when both clips
      are in the same scene. Nobody is removed from an exchange. Narrator clips are exempt from both rules.
  R9  (Scribe only) FIRST-SPEAKS RULE: the clip where a cast person first speaks carries a picture that lists that person, and the
      first picture that lists their name (their reference image) is on that clip OR EARLIER (a narrator may introduce the person
      visibly before they speak). No voice is ever introduced by an invisible character.
  R8  (Scribe only) the supplied reference photo is attached: referenceImages[name] points to an image whose
      imageNames file name is the cast file's referenceImage
"""
import json, os, re, sys

FENCE = chr(96) * 3
DRIFT = "same face, hair, build and clothing as the attached reference image"
PHOTO_PHRASE = "exactly as in the attached reference photo"
ANY = re.compile(r"\b(person|people|crowd|crowds|audience|child|children|kid|kids|silhouette|silhouettes|someone|somebody|man|men|woman|women|staff|human|humans|worker|workers|attendee|attendees|passenger|passengers|customer|customers|caller|callers|patient|patients)\b", re.I)
BODY = re.compile(r"(?<![-\w])(body|bodies|face|faces|head|heads|hand|hands|finger|fingers|arm|arms|leg|legs|figure|figures)(?![-\w])", re.I)


def last_json(text):
    blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
    if not blocks:
        sys.exit("FAIL no json block in the cast or manifest file")
    return json.loads(blocks[-1])


def load_prompts(path):
    """Returns (list of dicts with cutId, clipId, refs, prompt), the scribe or None."""
    if path.endswith(".json"):
        s = json.load(open(path, encoding="utf-8"))
        out = []
        for sc in s["scenes"]:
            for c in sc["clips"]:
                if c.get("imagePrompt"):
                    m = re.search(r"Cut ([A-Z0-9-]+):", c["imagePrompt"])
                    out.append({"cutId": m.group(1) if m else c["clipId"], "clipId": c["clipId"],
                                "refs": c.get("referenceNames", []), "prompt": c["imagePrompt"]})
        return out, s
    m = last_json(open(path, encoding="utf-8").read())
    return [{"cutId": k["cutId"], "clipId": k["clipId"], "refs": k.get("referenceNames", []), "prompt": k["prompt"]} for k in m["cuts"]], None


def segment(prompt, start, end):
    a = prompt.find(start)
    if a < 0:
        return ""
    a += len(start)
    b = prompt.find(end, a)
    return prompt[a:b if b >= 0 else len(prompt)]


def drop_negations(text):
    # sentences that start with "No " ("No people and no hands.") state what is absent
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(p for p in parts if not re.match(r"^\s*No\b", p))


def option(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def staging_of(argv, source_path, cast):
    if "--staging" in argv:
        return argv[argv.index("--staging") + 1]
    if source_path.endswith(".md"):
        found = last_json(open(source_path, encoding="utf-8").read()).get("staging")
        if found:
            return found
    return cast.get("staging") or "studio"


def main():
    prompts, scribe = load_prompts(sys.argv[1])
    cast = last_json(open(sys.argv[2], encoding="utf-8").read())
    staging = staging_of(sys.argv, sys.argv[1], cast)
    scribe_for_order = scribe
    if scribe_for_order is None and option(sys.argv, "--scribe"):
        scribe_for_order = json.load(open(option(sys.argv, "--scribe"), encoding="utf-8"))
    people = [c for c in cast["characters"] if c.get("type") == "character" and c.get("onScreen") and c.get("referenceName")]
    by_ref = {c["referenceName"]: c for c in people}
    ok = True

    def bad(code, cut, msg):
        nonlocal ok
        ok = False
        print("FAIL %s %s: %s" % (code, cut, msg))

    first_seen = {}
    for p in prompts:
        cut, text, refs = p["cutId"], p["prompt"], p["refs"]
        shot = segment(text, "Shot:", "Characters:")
        chars = segment(text, "Characters:", "Setting:")
        setting = segment(text, "Setting:", "One clear focal moment")
        drawn = [c["referenceName"] for c in people if re.search(r"\b%s\b" % re.escape(c["speaker"]), shot + " " + chars)]
        person_refs = [r for r in refs if r in by_ref]
        for r in drawn:
            if r not in refs:
                bad("R1", cut, "%s is drawn but not listed in referenceNames" % r)
        for r in person_refs:
            if r not in drawn:
                bad("R1", cut, "%s is listed in referenceNames but not drawn" % r)
        scan = drop_negations(shot + " " + setting)
        for m in ANY.finditer(scan):
            bad("R2", cut, "unnamed person word %r" % m.group(0))
        if not drawn:
            for m in BODY.finditer(scan):
                bad("R2", cut, "body or face word %r in a picture with no cast member" % m.group(0))
        for r in person_refs:
            first_seen.setdefault(r, (cut, person_refs, text))
        if person_refs:
            if DRIFT not in text:
                bad("R5", cut, "anti-drift clause missing")
            for r in person_refs:
                c = by_ref[r]
                if c.get("referenceImage") and (PHOTO_PHRASE not in chars or "not described here" in text):
                    bad("R6", cut, "%s must be written as '%s'" % (r, PHOTO_PHRASE))
        avoid = segment(text, "Avoid:", "Fill the whole frame")
        if "any person, hand, body part" not in avoid and "extra people beyond those named" not in avoid:
            bad("R7", cut, "Avoid text does not forbid unnamed people")

    first_speaker_clip, first_clip_of_cut = {}, {p["cutId"]: p["clipId"] for p in prompts}
    if scribe is not None:
        for sc in scribe["scenes"]:
            for c in sc["clips"]:
                for ch in people:
                    if c["speaker"] == ch["speaker"]:
                        first_speaker_clip.setdefault(ch["referenceName"], c["clipId"])

    everyone = sorted(c["referenceName"] for c in people)
    for p in prompts:
        shown = sorted(r for r in p["refs"] if r in by_ref)
        if staging == "studio" and shown and shown != everyone:
            bad("R3", p["cutId"], "shows %s without %s; actors are never alone, the whole cast is in the studio together" % (", ".join(shown), ", ".join(r for r in everyone if r not in shown)))
    for r, (cut, plist, text) in first_seen.items():
        if "Lettering" in text and not (scribe is not None and first_speaker_clip.get(r) == first_clip_of_cut.get(cut)):
            bad("R4", cut, "first picture of %s carries baked-in lettering" % r)

    if scribe is not None:
        for ch in people:
            r = ch["referenceName"]
            clip = first_speaker_clip.get(r)
            if not clip:
                continue                                  # a cast person who never speaks is not covered by this rule
            by_clip = {p["clipId"]: p for p in prompts}
            first_pic = first_seen.get(r)
            if clip not in by_clip or r not in by_clip[clip]["refs"]:
                bad("R9", clip, "%s first speaks here but this clip has no picture listing %s (a voice must never be invisible)" % (ch["speaker"], r))
            elif first_pic:
                order_of = {c["clipId"]: n for n, c in enumerate(c for sc in scribe["scenes"] for c in sc["clips"])}
                if order_of.get(first_clip_of_cut.get(first_pic[0]), 10 ** 9) > order_of.get(clip, -1):
                    bad("R9", clip, "the first picture of %s is on %s, after the clip where %s first speaks" % (r, first_clip_of_cut.get(first_pic[0]), ch["speaker"]))

    # R10 and R11: walk the clips in playback order, tracking the picture in effect.
    if scribe_for_order is None:
        bad("R10", "-", "give --scribe <scribe.json> so every speaking clip can be checked in playback order")
    else:
        pic_by_clip = {p["clipId"]: p for p in prompts}
        speaker_ref = {c["speaker"]: c["referenceName"] for c in people}
        current, prev_ref, prev_scene = None, None, None
        for sc in scribe_for_order["scenes"]:
            for c in sc["clips"]:
                if c["clipId"] in pic_by_clip:
                    current = pic_by_clip[c["clipId"]]
                shown = [r for r in (current["refs"] if current else []) if r in by_ref]
                need = speaker_ref.get(c["speaker"])
                if need:
                    where = current["cutId"] if current else "no picture"
                    if need not in shown:
                        bad("R10", c["clipId"], "%s speaks but the picture in effect (%s) names %s" % (c["speaker"], where, ", ".join(shown) or "nobody"))
                    elif prev_ref and prev_scene == sc["sceneId"] and prev_ref != need and prev_ref not in shown:
                        bad("R11", c["clipId"], "%s answers %s but the picture in effect (%s) does not keep %s in frame" % (c["speaker"], prev_ref, where, prev_ref))
                prev_ref, prev_scene = need, sc["sceneId"]

    gates = []
    if scribe is not None:
        names = scribe.get("imageNames", {})
        refimgs = scribe.get("referenceImages", {})
        for c in people:
            photo = c.get("referenceImage")
            if not photo:
                continue
            rid = refimgs.get(c["referenceName"])
            if not rid or os.path.basename(names.get(rid, "")) != os.path.basename(photo):
                gates.append(c["referenceName"])
                ok = False
                print("GATE R8 %s: the supplied photo %s is not attached as the reference (referenceImages[%s] = %s)" % (c["referenceName"], photo, c["referenceName"], rid))
    print("staging %s; prompts checked %d, people in cast %d, first pictures %s" % (staging, len(prompts), len(people), {r: v[0] for r, v in first_seen.items()}))
    if gates:
        print("PENDING owner step: import the photo into the Image Library and press 'Use this image as the reference' for: " + ", ".join(gates))
    print("RESULT", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
