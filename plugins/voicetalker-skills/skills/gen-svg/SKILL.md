---
name: gen-svg
version: 3.2.8
description: >-
  OPTIONAL (not numbered; runs alone or after Step 0, 1 or 2). Makes animated SVG pictures that VoiceTalker can
  use as backgrounds: people, places, things, scenes and title cards. Reads any mix of a cast file (characters),
  a Scribe (scribe), an image manifest (image-manifest), your own PNG or
  JPG pictures, or a written description. Asks a few short questions (what to make, picture or description,
  size, motion, intensity, loop length, emotions, style), then writes one self-contained .svg per object, named
  after the object and its type with an optional emotion (for example hero-person.svg or hero-person-happy.svg),
  with a loop as long as the clip it is for or a number of seconds you choose, and a short list of what each
  file is and where it fits. It never edits the Scribe, the cast or the manifest, and it needs only standard
  python3, so it runs anywhere.
---

# VoiceTalker Gen SVG, optional (v3.2.8)

Pipeline: Step 0 `characters` (cast) → Step 1 `scribe` → Step 2 `image-manifest` → Step 3 `merge-media`. **This skill is optional and sits beside them.** It reads what they save and writes animated pictures you upload in VoiceTalker yourself. It can also run alone on a picture or a description.

Output: one `.svg` file for each object, and `<project>-svg-list.md`, a short list of what each file is and where it fits. Nothing is placed in the Scribe: VoiceTalker makes the real image IDs when you upload a file.

## 1. Rules

1. **No unrequested changes.** Never edit the Scribe, the cast file, the manifest, or any picture you were given. Every result is a new file. Do not make objects the user did not choose.
2. **Only SVG files and the list.** Never write an image ID, a `backgroundImageId`, or anything into a Scribe. The user uploads the files (section 9).
3. **Portable.** Everything here runs with standard `python3` (always `python3 -I`), no `pip install`, no network, no machine-specific paths or fonts, and the same instructions work in Claude Code, Codex and the Claude apps. The one optional extra is `fontTools` for turning lettering into outlines (section 7); without it, say so in the report.
4. **Self-contained SVG.** No `<script>`, no `foreignObject`, no event attributes (`onclick`...), no `@import`, no link to any outside file, font or picture (`href` and `url()` may only point inside the file or at a `data:` address). VoiceTalker plays CSS and SMIL animation in an SVG and does not run scripts.
5. **Animation is CSS `@keyframes` or SMIL only.** Every animation repeats forever (`infinite` or `repeatCount="indefinite"`), and its first and last keyframe are identical, so the loop has no jump.
6. **One loop length.** Every animation duration is the loop length divided by a whole number (section 6). The check script tests it.
7. **Invented people only.** A person is drawn from the cast `imageDescription` or the user's picture, never as a real person, and a fully invented person is described as not based on any real person. Never add a logo, brand or watermark that was not in the input.
8. **Small files.** Aim for under 1 MB each. VoiceTalker accepts up to 15 MB.
9. Say where the files were saved (full path) and that no input file was changed.

## 2. Inputs: any mix, at least one

| Input | What it gives | How many |
|---|---|---|
| Cast file `<project>-cast.md` | The people, places and things: `speaker`, `type` (`character`, `place`, `object`), `onScreen`, `referenceName`, `imageDescription`, `imageTag`, `emotionArc` (`at` and `emotion`), `prosody`, and the `world` style sentence. Read the last ```json block (`vt-cast.v1`). A character with `onScreen` false is never drawn. | one |
| Scribe JSON `<project>-scribe-v1.xx.json` | Scenes, clips, speakers, text, and clip times (for the loop length) | one |
| Image manifest `<project>-image-manifest.md` | Cut IDs, clips and `referenceNames` (where each object appears). Last ```json block (`vt-image-manifest.v1`). | one |
| PNG or JPG pictures | A picture to turn into an animated SVG | any number; one object per picture, or one `scene` for a picture of a whole place |
| A written description | Used when there is no picture and no cast entry | one per object |

Where the objects come from, in order: the cast file; else the manifest's reference names; else the Scribe's speakers; else the pictures; else the description. A picture or description the user gives for an object wins over the cast's `imageDescription`.

## 3. First: scan, then ask

1. Read every input given. List the objects found, one line each: name, type, where it came from, and the clips it appears on (from the manifest or Scribe) when known.
2. **Ask the user, one question at a time, each with a proposed answer** (so `yes` or `defaults` accepts it, and `defaults` accepts every remaining question). Skip a question already answered.
   1. **Which objects?** Default: every on-screen character, every place and every thing found.
   2. **Where does each look come from?** Default order: the user's picture, else the cast description, else a description the user gives.
   3. **Size.** 16:9 landscape, `viewBox="0 0 1920 1080"` (default), or 9:16 portrait, `viewBox="0 0 1080 1920"`.
   4. **Motion** for each type (section 5), and the **intensity**: subtle (default), medium or lively.
   5. **Loop length.** Default: the length of the clip the file is for. Or any number of seconds the user gives. An object used on several clips uses the longest of them unless the user says otherwise.
   6. **Emotions** (characters only). Default: `neutral` plus every emotion in that character's cast `emotionArc`. Each emotion is its own file.
   7. **Style sentence.** Default: the cast `world` sentence; without a cast, propose one sentence and show it.
   8. **Folder.** Default: `<project>-svg/` next to the first input file.
3. Show the plan: how many files, the names, the loop length for each. Then make them. Do not ask anything else.

## 4. Names: `<object>-<type>[-<emotion>].svg`

All lowercase letters, digits and single hyphens.

| Type | What it is | Example |
|---|---|---|
| `character` | A person or creature | `romeo-character-neutral.svg` |
| `place` | A location that comes back | `verona-place.svg` |
| `thing` | An important object | `ring-thing.svg` |
| `scene` | A one-off background for a moment | `balcony-scene.svg` |
| `title` | An opening or closing card | `intro-title.svg` |

- `<object>` is the cast `referenceName` (or the manifest reference name), so `romeo` means the same thing in every skill and every project. Without either, use a short name from the user and keep it the same everywhere.
- Only a `character` has an `<emotion>`: the cast emotion as one to three lowercase hyphenated words (`Rising bravado` becomes `rising-bravado`). Every character always has a `neutral` file.
- Never reuse a name for a different look. If a file already exists with the name, ask before replacing it.

## 5. Motion

Offer the motion that fits the type; the first row of each type is the default.

| Type | Options |
|---|---|
| `character` | Breathe and blink (a slow rise of the chest and a quick blink); plus speaking motion (the mouth opens and closes, or a pulse in time with speech); plus gesture sway (a slow shift of weight and a small hand movement) |
| `thing` | Float and bob; slow spin or tilt; glow pulse; sparkle or shimmer; still with a light shine |
| `place` | Drifting light or clouds; gentle drift of the layers (far layers move less); flicker (candles, lamps, fire); weather (rain, snow, mist) |
| `scene` | The same options as `place` |
| `title` | Glow pulse on the lettering; a light sweep across it; still |

**Intensity.** Subtle: movements of about 1 to 2 percent of the picture size, scale changes up to 2 percent. Medium: 3 to 5 percent, scale up to 5 percent. Lively: 6 to 9 percent, scale up to 9 percent. Never so fast that the picture strobes: no cycle shorter than 0.4 seconds, and no more than 3 flashes in any second.

**How an emotion shows** (characters), on top of the chosen motion: `neutral` plain light and an even breath; happy or excited, a warmer palette, a lifted head and a faster breath; angry, a red-orange rim light, lowered brows and a quicker, harder breath; sad or tender, cooler and softer colours, a lowered head and a slower breath; afraid, pale colours, raised shoulders and a quick shallow breath. For any other cast emotion, choose the nearest of these and say which in the list. The cast `prosody` (tone, pacing) sets the breath rate: a brisk speaker breathes faster.

CSS patterns (shown at subtle intensity; scale the numbers by the intensity):

```css
.f{transform-box:fill-box;transform-origin:center;animation:float 5s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.pulse{animation:glow 2.5s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:.6}50%{opacity:1}}
```

## 6. Loop length

The loop length `L` is the length of the clip the file is for, or the number of seconds the user gave.

- **From the Scribe.** If the clip has both `startTimestamp` and `endTimestamp`, `L` is their difference. Otherwise it is an estimate: the clip's words at 180 words a minute plus its `;pN` pauses. Run `python3 -I vt_svg_check.py cliplen <scribe.json> <clipId>` (section 8); it prints the seconds and says whether it used the clip times or the estimate. Say which one in the list, because an estimate can be a little off.
- **Several clips.** Use the longest, unless the user chooses another.
- **Seamless.** Every animation duration is `L / k` for a whole number `k`, and no shorter than 0.4 seconds. For example, with `L` = 12: 12 s, 6 s, 4 s, 3 s, 2 s, 1.5 s. A loop shorter than 1 second is flagged: ask whether to use a longer loop.
- Each `@keyframes` has the same state at its first and last keyframe.

## 7. Drawing the SVG

1. **Look** at the picture (or read the description). Note the size, the main shapes, colours, gradients and any lettering. Estimate coordinates on the canvas.
2. **Write a small Python script** (standard library only) that prints the SVG: shapes, gradients and `<defs>`, grouped so each moving part is its own `<g class="...">` with `transform-box:fill-box;transform-origin:center`. Many repeated parts (bars, stars, rain) are generated in a loop, each with its own `@keyframes` or `animation-delay`.
3. **Recreate; do not trace.** Match the layout, colours and proportions of the picture. Say in the list that the file is a recreation.
4. **Lettering.** If the picture has text and the user gives a font file (`.ttf` or `.otf`) and `python3 -I -c "import fontTools"` works, turn each line into outlines so no font is needed:

```python
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
def outline(font_path, text, x, baseline, size):
    f = TTFont(font_path); gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f["hmtx"]
    s = size / f["head"].unitsPerEm; pen = SVGPathPen(gs); cx = 0
    for ch in text:
        g = cm[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + cx * s, baseline)))
        cx += hm[g][0]
    return pen.getCommands()          # use as <path d="...">
```

   Without a font file or `fontTools`, write `<text>` with `font-family="Arial, Helvetica, sans-serif"` and say in the report that the lettering depends on the viewer's fonts. Never use a font that is only on one machine.
5. **Check** (section 8), then look at the result once if a viewer is available. Never claim the motion looks right without seeing it: say what was and was not looked at.

## 8. The check script

Save this as `vt_svg_check.py` in the session's scratch folder. Run:

```
python3 -I vt_svg_check.py check <loop_seconds> <file.svg> [<file.svg> ...]
python3 -I vt_svg_check.py cliplen <scribe.json> <clipId>
```

Do not report success until `check` prints `RESULT PASS` for every file.

```python
import json, re, sys, os
import xml.etree.ElementTree as ET

TYPES = ("character", "place", "thing", "scene", "title")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEYWORDS = {"linear", "ease", "ease-in", "ease-out", "ease-in-out", "infinite", "alternate", "alternate-reverse", "reverse", "normal",
            "both", "forwards", "backwards", "none", "paused", "running", "step-start", "step-end"}
TIME = re.compile(r"^(\d+(?:\.\d+)?|\.\d+)(ms|s)$")

def seconds(token):
    m = TIME.match(token.strip())
    return None if not m else float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)

def split_name(stem):
    parts = stem.split("-")
    for i, p in enumerate(parts):
        if i > 0 and p in TYPES:
            return "-".join(parts[:i]), p, "-".join(parts[i + 1:])
    return None

def keyframes(css):
    out = {}
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", css):
        depth, i = 1, m.end()
        while i < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0); i += 1
        body = css[m.end():i - 1]
        stops = {}
        for sel, decl in re.findall(r"([^{}]+)\{([^}]*)\}", body):
            for s in sel.split(","):
                s = s.strip().replace("from", "0%").replace("to", "100%")
                stops[s] = re.sub(r"\s+", "", decl)
        out[m.group(1)] = stops
    return out

def check_file(path, loop):
    ok, notes = True, []
    def bad(msg):
        nonlocal ok; ok = False; notes.append("FAIL " + msg)
    base = os.path.basename(path)
    if not base.endswith(".svg"): bad("not an .svg file")
    parts = split_name(base[:-4])
    if not parts or not NAME.match(base[:-4]): bad("name must be <object>-<type>[-<emotion>].svg with type one of %s" % ", ".join(TYPES))
    elif parts[2] and parts[1] != "character": bad("only a character has an emotion in its name")
    size = os.path.getsize(path)
    if size > 15 * 1024 * 1024: bad("over 15 MB")
    elif size > 1024 * 1024: notes.append("NOTE over 1 MB (%d KB)" % (size // 1024))
    text = open(path, encoding="utf-8").read()
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        bad("not valid XML: %s" % e); return ok, notes, size
    if not root.tag.endswith("svg"): bad("root element is not svg")
    if root.get("viewBox") not in ("0 0 1920 1080", "0 0 1080 1920"): bad('viewBox must be "0 0 1920 1080" or "0 0 1080 1920"')
    css = " ".join((el.text or "") for el in root.iter() if el.tag.endswith("style"))
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("script", "foreignObject"): bad("<%s> is not allowed" % tag)
        for k, v in el.attrib.items():
            kk = k.split("}")[-1]
            if kk.lower().startswith("on"): bad("event attribute %s is not allowed" % kk)
            if kk == "href" and not (v.startswith("#") or v.startswith("data:")): bad("outside link %s" % v[:40])
            if "url(" in v and not re.search(r"url\(\s*['\"]?(#|data:)", v): bad("outside url() in %s" % kk)
    if re.search(r"@import|url\(\s*['\"]?(?!#|data:)", css): bad("outside @import or url() in the CSS")
    kf = keyframes(css)
    used, durations = set(), []
    pool = css + ";" + ";".join(v for el in root.iter() for k, v in el.attrib.items() if k == "style")
    for decl in re.findall(r"(?<![\w-])animation\s*:\s*([^;}\"]+)", pool):
        decl = re.sub(r"\([^)]*\)", "()", decl)
        for one in decl.split(","):
            toks = one.split()
            d = next((seconds(t) for t in toks if seconds(t) is not None), None)
            name = next((t for t in toks if seconds(t) is None and t not in KEYWORDS and not re.match(r"^[\d.]+$", t) and t != "()"), None)
            if d is None: bad("animation without a duration: %s" % one.strip()[:50]); continue
            durations.append(d)
            if name: used.add(name)
            if "infinite" not in toks: bad("animation does not repeat forever: %s" % one.strip()[:50])
    if re.search(r"(?<![\w-])animation-(name|duration)\s*:", pool): bad("use the animation shorthand (name, duration, ... infinite)")
    for el in root.iter():
        if el.tag.split("}")[-1] in ("animate", "animateTransform", "animateMotion", "set"):
            d = seconds(el.get("dur", ""))
            if d is None: bad("SMIL element without dur")
            else: durations.append(d)
            if el.get("repeatCount") != "indefinite": bad("SMIL element does not repeat forever")
    if not durations: bad("no animation found")
    for d in sorted(set(durations)):
        k = loop / d if d else 0
        if d < 0.4 - 1e-9: bad("animation shorter than 0.4 s (%.3f)" % d)
        elif abs(k - round(k)) > 1e-3 or round(k) < 1: bad("duration %.3f s does not divide the %.3f s loop" % (d, loop))
    for n in sorted(used):
        if n not in kf: bad("animation %s has no @keyframes" % n)
        else:
            first, last = kf[n].get("0%"), kf[n].get("100%")
            if first is None or last is None: bad("@keyframes %s needs a 0% and a 100% keyframe" % n)
            elif first != last: bad("@keyframes %s: first and last keyframe differ, the loop would jump" % n)
    for n in sorted(set(kf) - used): notes.append("NOTE @keyframes %s is never used" % n)
    notes.append("%d animations, durations %s s" % (len(durations), ", ".join(sorted({"%g" % d for d in durations}, key=float)[:8])))
    return ok, notes, size

def stamp(v):
    m = re.match(r"^(\d+):(\d{2}):(\d{2})[.,](\d{1,3})$", (v or "").strip())
    return None if not m else int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4].ljust(3, "0")) / 1000

def cliplen(scribe, clip_id):
    d = json.load(open(scribe, encoding="utf-8"))
    for s in d["scenes"]:
        for c in s["clips"]:
            if c["clipId"] == clip_id:
                a, b = stamp(c.get("startTimestamp")), stamp(c.get("endTimestamp"))
                if a is not None and b is not None and b > a:
                    return b - a, "saved clip times"
                words = len(re.sub(r";p[\d.]+", "", c["text"]).split())
                pauses = sum(float(x) for x in re.findall(r";p(\d+(?:\.\d+)?)", c["text"]))
                return words / 180 * 60 + pauses, "ESTIMATE: %d words at 180 wpm plus %.1f s of pauses" % (words, pauses)
    sys.exit("clip %s not found" % clip_id)

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "check":
        loop, allok = float(sys.argv[2]), True
        for p in sys.argv[3:]:
            ok, notes, size = check_file(p, loop); allok &= ok
            print(os.path.basename(p), "(%d KB)" % (size // 1024))
            for n in notes: print("  " + n)
        print("RESULT", "PASS" if allok else "FAIL")
    elif len(sys.argv) == 4 and sys.argv[1] == "cliplen":
        secs, how = cliplen(sys.argv[2], sys.argv[3])
        print("%.3f seconds (%s)" % (secs, how))
    else:
        sys.exit(__doc__ or "usage: vt_svg_check.py check <loop_seconds> <file.svg>... | cliplen <scribe.json> <clipId>")
```

Also check by eye and say so: the lettering is spelled exactly as in the input, the picture matches the layout and colours, and the motion is what was chosen. If no viewer was available, say the motion was not seen.

## 9. The list and the report

Write `<project>-svg-list.md` next to the files: a header (project, inputs read, size, intensity, style sentence) and one table:

| File | Type | Object | Emotion | Motion | Loop (s) | KB | Made for (clips, cuts or scene) | Source |
|---|---|---|---|---|---|---|---|---|

"Made for" comes from the manifest or Scribe, and says `not assigned` when none was given. "Source" says picture, cast description or written description, and whether the loop length is from clip times or an estimate.

Report: where the files and the list are (full paths); that no input was changed; the table; the `RESULT PASS` lines; what was looked at and what was not; whether lettering is outlines or `<text>`; anything the user must decide.

**Next, in VoiceTalker:** open **Background and Logo**, press **Upload images**, choose the `.svg` files, then pick each one as the Global Background, in a scene's Background list, or with the image icon on a clip row. An animated SVG starts each time the runner opens. Nothing was tried inside VoiceTalker by this skill.

## 10. Boundaries

This skill makes animated pictures. It does not write or change Scribe words, voices or clips (Step 1), plan or write image prompts (Step 2), place anything in a Scribe (Step 3), generate audio or raster pictures, change the app, or publish.
