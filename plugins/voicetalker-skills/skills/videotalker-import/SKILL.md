---
name: videotalker-import
version: 3.2.8
description: >-
  OPTIONAL (runs after Step 1, before merge-media). Reads a VideoTalker scene list (video-scene.json,
  schema 2.x: the cut list with each scene's narration, dialogue and generated video file) and a VoiceTalker Scribe,
  finds the Scribe clips that speak each scene's words, locates each scene's finished video in the VideoTalker
  project's output/scenes folder (final render, else draft), reads its real length and size with ffprobe, and writes
  a media cut sheet (vt-video-manifest.v1) plus a readable table, one cut per scene, each attached to the first
  clip that speaks it. It lists the scenes it could not place and
  checks the manifest. merge-media then merges the manifest into the Scribe. Never edits the scene list,
  the Scribe, or any video.
---

# VoiceTalker VideoTalker Import (v3.2.8)

VideoTalker (`<your VideoTalker project folder>`) generates one video per scene from a scene list. VoiceTalker voices a Scribe and, since 1.07, can play a video on a clip. This skill is the bridge: **VideoTalker scene list → vt-video-manifest.v1** (then `merge-media` → Scribe).

## 1. How VideoTalker stores what this skill reads (verified in its code)

- `shared/video-scene-schema.ts`: `video-scene.json` has `projectName`, `defaults`, `scenes[]` and `assembly`. Each scene has `sceneNumber`, `shotId` (for example `M3D-01`), `title`, `durationSeconds`, `narration`, `dialogue[]` (`{speaker, text}`), `onScreenText`, and `generation` with `output.fileName` (the final video), `draft.outputFileName` (the 360p draft, under `drafts/`), `status` and `runs[]` (with `actualMedia`: width, height, fps, durationSeconds).
- A scene may be a `continuousRef` pointer to a continuous lineage; those are not scenes and are listed as not placed.
- Folders are fixed per project: `<projectsRoot>/<projectName>/ingest/scene/<scene-list>.json` and the videos in `<projectsRoot>/<projectName>/output/scenes/` (drafts in `output/scenes/drafts/`, the stitched whole in `output/stitched/`). The importer derives the project folder from the scene file's location; otherwise pass `--project-dir`.
- Disk is the truth: a scene's `status` can say `not_generated` for the 1080p final while the file exists, so the importer looks for the **file**, final first, then the draft.

## 2. Inputs (ask only what is missing, one question at a time)

| Input | Required | Notes |
|---|---|---|
| VideoTalker scene list `.json` | Yes | schemaVersion 2.x. |
| Scribe `.json` | Yes | `scribe.teleprompter.v1`, made by `scribe` from the same words as the scene list's narration. |
| Where to write the manifest | Yes | Propose next to the Scribe: `<scriptName>-video-manifest.md`. Never overwrite an input. |
| Final or draft | No | `--prefer final` (default) or `draft`. A draft is used only when no final file exists, and is flagged. |

## 3. How scenes are matched to clips

1. For each scene (in order) the words to find are its dialogue lines (in order) or its narration. Pause markers (`;p01`), inline tags, ®/™ and punctuation are ignored.
2. The importer finds the first run of consecutive Scribe clips, at or after the previous scene's end, whose words equal those (exact), else are at least 92% alike. The first clip of the run **starts** the video (`clipId`); every clip of the run is in `clipIds`.
3. A scene with no narration or dialogue (an interstitial title shot), with no video file, or whose words are not in the Scribe is listed under **Not placed** with its reason; the manifest still works for the others.
4. To place a scene by hand (an interstitial, or a rewritten line), give `--map map.json`: `{"M3D-03": "clip-004-001"}` or `{"M3D-03": ["clip-004-001", "clip-004-002"]}`.

If many scenes are not placed because the Scribe's words differ from the scene list's, stop and tell the user: either re-run `scribe` on the scene list's narration, or use `--map`. Do not edit the Scribe here.

## 4. Run it

The script is bundled at `scripts/vt_videotalker_import.py` (standard library only, Python 3.8+; `ffprobe` is used when installed, otherwise the lengths come from the scene list's runs).

```
python3 -I scripts/vt_videotalker_import.py build <scene-list.json> <scribe.json> <out-manifest.md> \
    [--project-dir DIR] [--prefer final|draft] [--map map.json]
python3 -I scripts/vt_videotalker_import.py check <out-manifest.md> <scribe.json>
```

`check` must print `RESULT PASS`: schema, same `scriptId`, every clip in the Scribe, no clip used twice, cuts in Scribe order, every video file present, `.mp4`/`.webm`.

## 5. Look at the result

Open the table at the top of the manifest and check, by eye:

- each cut's clips really are that scene's words (the table shows the first and last clip);
- drafts are flagged: a 360p draft should be replaced by the final render in VideoTalker before the upload;
- the length of each video against its narration (the merge's check prints a warning when the narration is longer than the video);
- the Not placed list: say plainly which scenes will have no video and why.

## 6. Report

- The manifest path, the Scribe and scene list used (neither was changed), counts: cuts placed, not placed, drafts.
- The Not placed list with reasons, and the `check` output.
- **Next:** run `merge-media` with the cut sheet and the Scribe; it writes a `file:` path into the `backgroundImageId` of each cut's first clip (the video then carries on over the following clips like a picture; not yet verified in VoiceTalker). VoiceTalker loads the files and stores them like pictures, against your file storage (never the video portal). Copy or keep the videos under the Scribe's folder.

## 7. Boundaries

This skill reads and writes manifests. It does not generate or edit videos, run VideoTalker, change the scene list or the Scribe, upload anything, sign in, commit or publish.
