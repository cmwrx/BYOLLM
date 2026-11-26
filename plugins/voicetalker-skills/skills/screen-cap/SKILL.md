---
name: screen-cap
version: 3.2.8
description: >-
  STEP 4 (screen shots). Reads the media plan (vt-image-manifest.v2, written by image-manifest) and takes
  every screen shot the plan asks for from ANY web app or site the person opens, in a separate Chrome at full 1920x1080
  sharpness. Each shot is tied to the words of its clip: the skill finds the named parts (the plan's mustShow labels)
  on the live page, crops tight around them, and PROVES by geometry that every one of them is inside the picture
  before it shows the shot. It then asks the person about THAT shot (keep, retake, point at another part, skip) before
  it moves to the next. Approved shots are recorded in the manifest for the merge step. The person signs in by hand;
  the skill never types a password, never sends a message, never submits a form. Needs python3, Pillow and Google
  Chrome. It never edits the Scribe.
---

# VoiceTalker Screen Cap, Step 4 (v3.2.8)

Pipeline: Step 1 `characters` (optional) → Step 2 `scribe` → Step 3 `image-manifest` (the media plan) → **Step 4 this skill** (screen shots; generated pictures are made later by Batch Media; screen **videos** are the separate skill `screen-cap-video`) → Step 5 merge the media into the Scribe → Step 6 load it in VoiceTalker.

Input: the manifest from Step 3 (required: it holds the `capture` entries) and the Scribe it was made for. **Works on any web app or site**: the labels come from the live page itself, never from a built-in list. Output: one PNG per approved capture entry (1920 x 1080), and the manifest updated with each entry's `file` and `status`.

## 1. Rules

1. **No unrequested changes.** Never edit the Scribe, the app, the person's account data or any file you were given, except that this skill records each shot's `file` and `status` in the manifest (and nothing else in it).
2. **Never fake the app.** Only real captures of the running app. Never draw, mock up or generate an app screen.
3. **The person signs in, you never do.** Never type or paste a password, token or cookie. Never read the profile's cookies. Open the capture Chrome, ask the person to sign in in that window, and wait for them to say so.
4. **Read-only on the app.** Capture states by opening menus, dialogs and forms, hovering, and typing text that is **never sent**. Never press Send, Submit, Save, Email, a card that starts a conversation, or anything that writes to the person's account. If a state needs a real reply, ask first, one question, and say what it will add to their history.
5. **No audio, no ambient pollution.** Before any capture turn the app's speaker off and pause its microphone. Put back any setting you changed before you finish.
6. **Privacy in pictures.** A real name, email, phone number or account detail must never appear in a shot. Replace it for the capture only, in the page (never saved or submitted), with a neutral sample, and say so in the report. Check every shot by eye for personal data.
7. **One shot, one clip, one set of words.** A shot shows the parts its clip speaks about (`mustShow`) and is never reused for another clip's words.
8. **A shot is only valid if every `mustShow` part is in it.** The helper proves this by geometry; if a part is off the page, hidden, ambiguous or too far from the others to fit one 16:9 picture, **no picture is saved**. Say exactly which part is the problem and ask the person what to do. Never keep a shot that is missing a named part, and never put a different part in its place.
9. **Ask after EVERY shot, for ALL shots, before the next one.** See section 4. Never batch the questions at the end and never decide a shot silently.
10. **No notes about what a shot does not show.** Never write "does not show" or gap notes anywhere.
11. **Name clips by scene and number.** Tell the person "Scene 3, clip 7", never a clip ID or image ID.
12. **Tell the person before the first capture** what you will do, what they must do (sign in, open the page), and what the capture will touch. Then proceed.
13. **Ask where to store the files first** and save only there. Propose `<manifest folder>/sshots/`, one file per entry named `<entryId>-s<scene>-c<clip>.png`.
14. **Close what you opened.** When the work is done (or stopped), close the capture Chrome and its debug session (section 6) and confirm it is gone. Never touch the person's own Chrome.
15. Say where the shots were saved (full paths) and that no input file other than the manifest was changed.

## 2. Requirements (check first, say what is missing)

`python3` with Pillow, the Python picture library that crops and saves each shot (check: `python3 -c "import PIL; print(PIL.__version__)"`; install: `python3 -m pip install Pillow`, or `python3 -m pip install --user Pillow` if pip says the environment is externally managed), Google Chrome, and the helper `cdpcap.py` in this skill's folder (`~/.claude/skills/screen-cap/cdpcap.py`, or `~/.agents/skills/...` on Codex; inside the `voicetalker-skills` plugin, `skills/screen-cap/` in the plugin's folder). Standard library plus Pillow. **Do not use an embedded or preview browser pane for the captures:** they return small screenshots that are blurry when scaled to 1920×1080.

## 3. Read the plan

1. Read the manifest's `plan`. The shots to take are the entries with `kind` `capture` (a `video` entry with `source: "capture"` belongs to `screen-cap-video`). List them in order as `Scene N, clip M: <the clip's words> - must show: <mustShow>` and show the count. Entries with a status of `approved` and a file that still exists are skipped unless the person names them (see the section below on running it again). The skill can be run again and again, for one shot or all.
2. If a capture has no `page`, or the plan has none, ask one question: the address of the page to capture.
3. **Ask where to store the files** (rule 13). Wait for the answer, then create the folder.

### Highlight ring

A small control can be made to stand out: set `ring: true` on the entry (or `ring: ["<label>", ...]` to ring only those parts); `ringExtra: ["<page label>"]` rings a part the page names differently from the words, for example the rail's Load/Save when the clip says Load and Save (`plan_repair.py patch`). The helper draws an amber ring around each named part for the capture only (nothing is clicked or changed) and removes it right after the shot.

### Parts the words do not name

`alsoShow: ["<page label>"]` adds parts that must be in the picture and are proven like the others, although the clip's words do not name them (`mustShow` may only hold phrases the clip speaks).

### A part that sits where the captions will run

Set `frame.mode` to `"center"` and the named parts (rings included) are cut out alone, as real pixels, and placed in the middle of a plain 1920 x 1080 picture in the page's own background colour (`groupWidth` sets how wide, 1500 by default). Use it for a part at the very bottom of the screen, such as the Victor dock, where the StoryTelling caption line covers it in the finished video. The picture is a layout of a real capture, never a drawing of the app.

### Run it again, for one shot or all (re-entrant)

Any run can start from any state of the plan. `python3 -I cdpcap.py status <manifest>` shows every capture entry and where it stands (approved, pending, retake, stale, skipped). `python3 -I cdpcap.py queue <manifest>` prints the entries to shoot now: those not approved, or approved whose file is gone. Approved shots are never in the queue unless named.
- **Repair one or a few shots:** `cdpcap.py queue <manifest> M07 M09` prints exactly those; or `cdpcap.py retake <manifest> M07` puts a shot back in the queue (its file is forgotten, never deleted). Then run section 4 for the queue only.
- **After the Scribe's words were edited:** `plan_repair.py sync` (in `image-manifest`) marks the changed clips `stale`; the queue then holds exactly those.
- **Repair everything:** `queue` with no ids; every entry that is not approved is taken, in plan order, and each is still confirmed with the person.

## 4. Capture, one shot at a time, with the person's answer after each

1. **Open Chrome** with a throwaway profile on the page: `python3 -I cdpcap.py launch <scratch>/chrome-profile <url>`. Say what it is: a separate window, none of the person's real Chrome data. Ask them to sign in there, open the page the plan needs, and tell you when done. **Put the capture window in full screen (the green button, or `cdpcap.py fullscreen --match <host>`) before the first shot**, the way the Runner is run before it is recorded; the pictures are always rendered at 1920 x 1080, so this changes the window, not the pixels. **Silence the app** (rule 5).
2. **For each capture entry, in order:**
   1. Put the page in the state the clip needs (open a menu, dialog, tab, select a clip, type text that is never sent). The clip's words say which. If you cannot tell, ask the person to set it up in the capture window.
   2. Take the shot: `python3 -I cdpcap.py shoot <manifest> <entryId> <out.png> --match <host>`. It prints JSON.
      - `"ok": true` → every `mustShow` part was found and lies inside the saved 1920 x 1080 picture (`crop`, `zoom`, `boxes` say where).
      - `"ok": false` with `missing` → those labels are not visible on the page right now. Do not guess a different part. Tell the person which labels, and ask: open or scroll to them and retry, change the entry's `mustShow`, give this clip no screen shot, or skip.
      - `"ok": false` with `ambiguous` → a label matches several parts of the page; show the boxes and ask which one. Record the answer as `prefer` on the entry (`{"<label>": "largest"}`, `"smallest"` or a number: the position by size, 0 = smallest, or `"top"`, `"bottom"`, `"left"`, `"right"` for the match nearest that edge, set with `plan_repair.py patch`) and shoot again.
      - `"reason": "too far apart"` → the named parts do not fit one 16:9 picture; ask whether to drop one of them from `mustShow` or split the clip's shot.
   3. **Look at the picture** (open it at full size): the named parts are large and clear; no real personal data; no stray overlay; nothing cut in half that matters.
   4. **Ask the person about this shot**, one question, with the picture, the clip's words and the `mustShow` list in front of them:
      > Scene N, clip M: "<words>". Shows: <mustShow>.
      > **1. Keep it**  **2. Retake it** (after you change the page)  **3. Point at another part** (give the label)  **4. No screen shot for this clip**  **5. Stop here** (the rest stays pending)
   5. Record the answer: `python3 -I cdpcap.py mark <manifest> <entryId> approved <file>` for 1 (`retake` and `skipped` for 2 and 4; for 3, change the entry's `mustShow` in the manifest with the person's label, then shoot again).
   6. Revert any state you set up, then go to the next entry. **Never shoot the next one before the person has answered about this one.**
3. Every entry ends as `approved`, `retake` or `skipped`. Entries left at `retake` or not taken stay pending and are reported as pending, never as done.

## 5. Check (run it, show the result)

```
python3 -I <skill folder>/cdpcap.py checkplan <manifest>
```

It prints `RESULT PASS` only when every capture entry is approved, its file exists, is exactly 1920×1080, is not blank, and is not the same picture as another entry. A skipped entry is reported as `PENDING` and makes the result FAIL until the person changes that entry to `none` in the plan (rerun Step 3 for that clip) or takes the shot. Then look at a contact sheet of the approved shots (a mixed sheet is fine, then open any weak one at full size) and say plainly which are still weak.

## 6. Close the browser and the debug session (always, last)

1. When the shots pass, or the person stops the work, run: `python3 -I <skill folder>/cdpcap.py close <scratch>/chrome-profile <port> --delete-profile`. It asks Chrome to quit over the debug protocol, ends any process still using this throwaway profile (never any other Chrome), checks that the debug port no longer answers, and removes the profile folder. It prints `closed: ...` or `FAIL`; on FAIL say so and tell the person what is still running.
2. Do this before the report, also when a check failed, and also if you stop part-way. Pass `--delete-profile` unless the person wants to keep the sign-in for a re-capture.

## 7. Report

- Where the shots are (full paths), the number approved, retaken, skipped and pending, and that the Scribe was not changed (the manifest was updated with each shot's file and status).
- One line per shot (scene and clip numbers, never IDs): what it shows and the answer the person gave.
- The `checkplan` output and what was checked by eye.
- Anything not captured and why, anything added to the person's account, and any sample values used in a form.
- **Next:** run the merge step (`merge-media`) with the manifest and the Scribe, then load the merged Scribe in VoiceTalker.
- That the capture Chrome and its debug session were closed and the throwaway profile removed.

## 8. Older Scribes without a media plan (legacy)

A Scribe that only has `file:<path>` values and a hand-written shot list can still be captured: use `cdpcap.py check <scribe.json> --min-distinct N` and the library (`Page`, `box`, `grab`, `isolate`) as in v1.1. Rules 1 to 6, 8, 9 and 14 still apply, and every shot still gets the per-shot question. New work always goes through the media plan.

## 9. Boundaries

The words, voices and picture prompts belong to Steps 2 and 3. This skill captures, proves and checks screen shots; it does not generate pictures, edit the Scribe or the app, sign in, send anything, commit or publish.
