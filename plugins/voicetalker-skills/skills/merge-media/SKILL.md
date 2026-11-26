---
name: merge-media
version: 3.2.8
description: >-
  STEP 5 (merge). One merge for every kind of media. Reads the media plan (vt-image-manifest.v2, or a v1
  manifest of generated pictures) and writes a new Scribe: generated pictures become an imagePrompt (+
  referenceNames) on their clip, screen shots, uploaded pictures, SVGs, mp3s and mp4s become a file: path in
  backgroundImageId on the clip, scene or whole Scribe the plan names, and a none entry ends a picture on
  purpose. Placeholders and screen shots not yet approved are reported as pending and never written. Leaves
  every word, voice and ID untouched, warns when a video and the narration under it differ in length, runs a
  full check, and raises the version. Replaces merge-images and merge-videos.
  VoiceTalker loads the files itself (Step 6); this skill never uploads.
---

# VoiceTalker Merge Media, Step 5 (v3.2.8)

Pipeline: Step 3 `image-manifest` (the plan) → Step 4 `screen-cap` (screen shots), `screen-cap-video` (screen videos) → **Step 5 this skill** → Step 6 load the Scribe in VoiceTalker and run Batch Media.

One manifest, one pass, one new Scribe. **The user never opens the manifest**: the skills create it and read it.

## 1. How a Scribe holds media (what this skill writes)

- `imagePrompt` and `referenceNames` on a clip: a picture VoiceTalker's Batch Media will generate (the first picture that lists a reference name is that name's reference).
- `backgroundImageId` on the Scribe (`settings`), a scene or a clip: `file:<path>` for a screen shot, picture, SVG, mp3 or mp4 that VoiceTalker loads and stores like any picture, against the file storage allowance; `none` for no picture on purpose. A clip's value overrides its scene's, a scene's overrides the Scribe's, an empty value inherits, and a picture or video carries on over the clips and scenes after it until another one replaces it.
- The video portal is never used for any of this.

## 2. Rules

1. **No unrequested changes.** The result has exactly the source Scribe's words, speakers, voices, styles, IDs, ordinals, scene titles and settings. Only these change: `backgroundImageId`, `imagePrompt` and `referenceNames` at the places the plan names, `version`, one added sentence in `description`, and the three overlay keys in `settings` if a prompt is added and they are missing.
2. **Never overwrite** the source Scribe or the manifest. The result is a new file in the Scribe's folder (`…-v3.06.json` becomes `…-v3.07.json`).
3. **Never replace a generated picture.** If a place the plan names already holds a generated image (a library id), the script stops and lists it: ask the user. Only when the user says yes to replacing them, run again with `--replace-library`: the places are overwritten, each is listed as a WARN, and the pictures stay in the library. An earlier `file:` or `none` value is replaced, so the merge can be run again.
4. **Never write what is not ready.** A `placeholder`, a `capture` whose status is not `approved`, or an entry with no file yet writes nothing and is reported as PENDING.
5. A clip or scene the plan does not name is left exactly as it is.
6. A span (`span.toClipId`) keeps the media through that clip: the next clip, if it has no entry of its own and no picture of its own, gets `none` so the media does not run on. Every such `none` is listed as a WARN.
7. **Re-running is safe.** A merge that would change nothing writes no file and raises no version (it prints `NO CHANGE`), so it can be repeated after any single repair. To fix one item: repair that entry in the plan (`plan_repair.py` in `image-manifest`), then merge again onto the latest merged Scribe; only the places the plan names are written.
8. The path written is relative to the folder the merged Scribe is saved in. A file outside that folder is warned about; copy it under the Scribe's folder.

## 3. Inputs

| Input | Required | Notes |
|---|---|---|
| Scribe JSON | Yes | `scribe.teleprompter.v1`. |
| Manifest | Yes | `vt-image-manifest.v2` (the plan) or v1, or a `vt-video-manifest.v1` media cut sheet (from `screen-cap-video` or `videotalker-import`; each cut is read as a video or upload entry). `.md` with the last ```json block, or plain `.json`. |

`sourceScribe.scriptId` in the manifest must equal the Scribe's `scriptId`, or the script stops.

## 4. Run it

The script is `scripts/vt_merge_media.py` (standard library only, Python 3.8+). Copy it to the scratchpad if the skill folder is read-only.

```
python3 -I scripts/vt_merge_media.py merge <scribe.json> <manifest> <out.json>
python3 -I scripts/vt_merge_media.py check <scribe.json> <manifest> <out.json>
```

Save `<out.json>` in the Scribe's folder with the next version. Do not report success until `check` prints `RESULT PASS`. The check proves: nothing changed except the places the plan names; each holds exactly the value the plan says; every `file:` path exists; prompts equal the manifest's; the version was raised.

## 5. Report

- The output file (full path), the version, and that the source Scribe and the manifest were not changed.
- Counts: places set to a file, set to `none`, generated prompts; the `check` output; every WARN (video length against narration, outside-folder files, automatic `none`).
- Everything PENDING (placeholders, screen shots not approved) and every scene or clip left without media, said plainly.
- **Next, in VoiceTalker (Step 6):** open the merged Scribe. For pictures and videos named by `file:` press **Load picture or video** (one button loads both) in the Batch Media window or the scene or clip, and choose the Scribe's folder; then **Batch Media** makes the generated pictures. Play it and save. Not verified here: that VoiceTalker plays an mp4 or mp3 from a `file:` path.

## 6. Boundaries

The words, voices, prompts and shots belong to the earlier steps. This skill places and checks; it does not generate, upload, encode, convert or play anything, edit the manifest, change the app, commit or publish.
