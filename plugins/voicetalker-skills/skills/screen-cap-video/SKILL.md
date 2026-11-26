---
name: screen-cap-video
version: 3.2.8
description: >-
  OPTIONAL (not numbered; runs after Step 1, or after Step 3 and a VoiceTalker run). Reads a Scribe and records
  the live app as MP4 video that matches the narration: a virtual camera zooms and pans to the part of the screen
  each clip describes, with optional highlights (border, glow, spotlight, marker, arrow, underline, ripple). Clip
  lengths come from a completed VoiceTalker run when you have one, else from the word count. Asks where to store
  the files first, then short option questions (files per clip, per scene or one single MP4; 16:9 or 9:16; camera;
  effects; colour; frame rate). The person signs in by hand; it never types a password, never sends a message,
  never submits a form, and it closes the browser and debug session when done. It also writes the media cut
  sheet (vt-video-manifest.v1) that merge-media reads, so the videos can be attached to the
  Scribe's scenes or clips. Needs python3, Pillow, ffmpeg, Google Chrome and the screen-cap skill. It never edits the Scribe.
---

# VoiceTalker Screen Cap Video, optional (v3.2.8)

> **Numbering (v3.0 pipeline):** the steps are 1 characters (optional), 2 scribe, 3 `image-manifest` (the media plan), 4 `screen-cap` and `screen-cap-video`, 5 `merge-media`, 6 load in VoiceTalker. Where this skill says "Step 2" for the image manifest or "Step 3" for the merge, read Step 3 and Step 5.


Companion to `screen-cap` (stills). Same pipeline position: it sits beside Steps 1 to 3 and reads the Scribe they produce. Output: MP4 files (no audio; VoiceTalker adds the narration), `<project>-video-plan.md`, and the video cut sheet `<project>-video-manifest.md` (section 5a) that `merge-media` reads.

**Apply every rule in section 1 of `screen-cap`** (never fake the app; the person signs in, you never do; read-only on the app; speaker off and mic paused; no personal data in pictures; no "does not show" notes; scene and clip numbers, never IDs; tell the person before the first capture; ask where to store the files first; close what you opened). They are not repeated here. The extra rules:

1. **Frame by frame, never screen-recorded.** The camera and the effects are computed for each frame, so the video is smooth, sharp at any zoom, and repeatable.
2. **Effects mark, they never change the app.** Effects are an overlay that is removed after each beat. Nothing is clicked, sent or saved.
3. **No audio track.** The narration is VoiceTalker's job.
4. **Lengths match the narration.** Each clip's video is exactly as long as the clip (real or estimated, section 3).
5. **Show the source of every length.** Say how many clips use a real length and how many an estimate.

## 1. Requirements (check first, say what is missing)

`python3` with Pillow, the Python picture library used to read and arrange the video frames (check: `python3 -c "import PIL; print(PIL.__version__)"`; install: `python3 -m pip install Pillow`), `ffmpeg` and `ffprobe` (`ffmpeg -version`; macOS `brew install ffmpeg`), Google Chrome, and the `screen-cap` skill installed next to this one (its `cdpcap.py` is the browser driver; this skill's `cdpvideo.py` imports it and never copies it). Do not use an embedded or preview browser pane. Rendering runs at roughly 15 to 25 frames a second, so a 5-minute tour at 30 fps takes about 8 to 15 minutes; run long renders in the background, one file at a time, and say so.

## 2. Questions (one at a time, each with a proposed answer; skip what the person already told you)

If the person says "defaults" or "you choose", use the proposals and say so.

1. **Where to store the files?** (always first) Propose `<Scribe folder>/video/`. Create it only after the answer.
2. **How many files?** (a) **one MP4 per scene** (proposed), (b) **one MP4 per clip**, (c) **one single MP4** for the whole Scribe. Say: per-scene and single files hold the camera still on clips that have nothing to show (such as host clips that use their own pictures), so they keep the Scribe's timing; per-clip files only exist for clips that show the app.
3. **Orientation?** **16:9 landscape, 1920×1080** (proposed) or **9:16 portrait, 1080×1920**. Portrait records the app's phone layout (a 540×960 window), so its elements sit differently from the desktop page: say so.
4. **Clip lengths?** "Do you have a completed VoiceTalker run (the `…-completed.json` or the transcript `.txt`)? Give me its path, or say no." With it, real lengths; without, estimates from the clips' pace (the `wpm` written in their style) plus half a second. Both can mix: real where available, estimate for the rest.
5. **Camera?** **zoom and pan** (proposed: the camera glides to each described part), **zoom with cuts**, or **static** (whole page, effects only). Then the zoom (**tight**, **medium** proposed, **gentle**) and the glide time (**0.9 s** proposed; **0.6** quick; **1.4** slow).
6. **Effects?** Any mix of: **border** (outline), **glow** (pulsing halo), **spotlight** (dims everything except the part), **marker** (translucent highlighter fill), **arrow** (points at the part), **underline** (draws under it), **ripple** (a click-style ring), or **none**. Propose **spotlight + border** for areas (cards, panels) and **glow + arrow** for small controls (icons, buttons); say that any beat can differ.
7. **Colour?** Propose amber `#ffb000`; offer the app's brand colour if you can read it from the page.
8. **Frame rate and fades?** **30 fps** (proposed; 24 is faster to render, 60 is smoother), and a **0.3 s fade** in and out at the start and end of each file (or none).

## 3. Read the Scribe, work out the lengths, write the video plan

1. Read the Scribe. Decide which clips show the app (the narration describes a part of the screen; a `file:` background that is a screen shot is the usual sign). Ask only if it is unclear which clips to cover.
2. **Lengths:** `python3 -I <skill folder>/cdpvideo.py durations <scribe.json> [--completed <run.json>] [--transcript <run.txt>]` prints how many clips are real and how many estimated and the total. In a script, `durations(...)` returns `{clipId: (seconds, "real" or "estimate")}`; use it for every beat.
3. For each such clip decide: the **target** (the page elements the camera frames and the effects mark), the **state** to put the app in (open a menu or dialog, type text that is never sent, hover a card, scroll a panel), what to **tear down** afterwards, and the **effects**. Inspect the page first (list its buttons, ids and classes and boxes); never guess a selector. States that need a real reply or the microphone are not captured: list them and ask.
4. Write `<project>-video-plan.md` next to the Scribe: one line per beat, in order: `Scene N, clip M (x.x s, real|estimate): what the camera shows, the state, the effects`. Add the file list that the answers to questions 1 and 2 produce (full paths). No other columns, no notes about what is missing. Show it and wait for the person's yes.

## 4. Record

All scripts live in the session scratch folder:

```python
import sys; sys.path.insert(0, "<folder of cdpvideo.py>")
from cdpvideo import *
```

1. **Open Chrome and sign in** exactly as in `screen-cap` section 4 (`cdpcap.py launch`, the person signs in, you confirm). Silence the app.
2. **Connect at the right size**: `p = Page(match="<host>", width=1920, height=1080, dpr=1)` for landscape, `width=540, height=960` for portrait. (`dpr=1` is right: the camera renders at full output resolution by itself.)
3. **Build the beats** from the plan: `Beat(dur, targets="[document.querySelector('#id'), ...]", setup=[...JS...], teardown=[...JS...], effects=["spotlight","border"], color=None, pad=60, minw=560, zoom=True, hold=False, label="Scene 3, clip 2")`. `minw` is the narrowest camera window in page pixels (small icons about 480 to 560, a column or panel 700, a wide bar 1400). A clip with nothing to show is `Beat(dur, hold=True)`.
4. **Plan the files**: `plan_files(scribe_path, {clipId: Beat}, mode, out_dir)` with mode `"clip"`, `"scene"` or `"single"` returns `[(path, beats)]`; it names the files `<name>-s02-c07.mp4`, `<name>-scene-02.mp4` and `<name>-tour.mp4` and fills clips without a beat with holds.
5. **Render each file**: `render(p, beats, path, fps=30, size=(1920,1080), color="#ffb000", move=0.9, fade=0.3)`. For portrait use `size=(1080,1920)`. Render one file per call and print progress; if a render stops, close the tab, open a fresh one, check the person is still signed in, and redo only that file.
6. **Check every file**: `python3 -I <skill folder>/cdpvideo.py check <file.mp4> <expected seconds> [WxH]` (size, length within 0.15 s, no blank frames; it prints `RESULT PASS`), then make a contact sheet (`cdpvideo.py sheet <file.mp4> <out.png> 8`) and **look at it**, and open a few frames at full size: the described part is large and clear; effects are on the right part and gone when the beat ends; nothing is cut in half that matters; no real personal data; no stray overlay. Re-render weak beats. Say plainly what is still weak.

## 5a. Write the video cut sheet (after the files are checked)

The cut sheet (`vt-video-manifest.v1`) says where each file attaches in the Scribe, so `merge-media` can write `file:<path>` into its `backgroundImageId`. Nothing needs asking: the mode the files were rendered with decides it (one file per scene attaches to that **scene**, and its clips inherit it; one per clip attaches to that **clip**; the single file attaches to the **whole Scribe**). Run, with that mode:

```
python3 -I <skill folder>/cdpvideo.py manifest <scribe.json> <video folder> <Scribe folder>/<project>-video-manifest.md --mode scene|clip|single
```

In a script: `manifest(scribe_path, video_dir, out_path, mode="scene")`. It reads each file's real length and size with ffprobe, lists each scene or clip that has no video under **No video**, and stores each file's path relative to the cut sheet. Save it next to the Scribe, and keep the videos under the Scribe's folder (for example `video/`) so VoiceTalker can find them. Never overwrite a file that is there; if one exists, write the next name and say so. The Scribe is not changed, and VoiceTalker (not this skill) loads the videos and stores them like pictures, against your file storage; the video portal is never used for this.

## 5. Close the browser and the debug session (always, last)

Exactly as in `screen-cap` section 6: `python3 -I <screen-cap skill folder>/cdpcap.py close <scratch>/chrome-profile <port> --delete-profile`, confirm it printed `closed:`, and do it also when a check failed or you stop part-way.

## 6. Report

- Where the videos and the plan are (full paths), how many files, their total length, and that the Scribe was not changed.
- The cut sheet path, how many videos it lists and which scenes or clips have no video; and that `merge-media` is the next step.
- The plan as one line per beat (scene and clip numbers, never IDs); how many lengths were real and how many estimated.
- The `check` output for each file and what was checked by eye.
- The options used (files, orientation, camera, effects, colour, frame rate), and anything not covered and why.
- That the browser and debug session were closed.
- What the person does next: run `merge-media` on the Scribe with the cut sheet (it writes a `file:` path into `backgroundImageId`); then open the merged Scribe in VoiceTalker, which loads the files and stores them like pictures, against your file storage. Do not claim a video plays until it has been played in VoiceTalker.

## 7. Boundaries

The words, voices and picture prompts belong to Steps 1 to 3; still shots belong to `screen-cap`. This skill records and checks video; it does not generate pictures, edit the Scribe or the app, upload the videos, sign in, send anything, record sound, commit or publish.
