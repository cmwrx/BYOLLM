---
name: gen-gpt-images
version: 3.2.8
description: >-
  Export ChatGPT image prompts from a VoiceTalker media manifest, or generate image files from a manifest,
  an exported VoiceTalker prompt set, or an AdSlides JSON prompt pack. Use for VoiceTalker and AdSlides
  image generation, including batches with key-frame references and exact output dimensions.
---

# VoiceTalker Gen GPT Images (v3.2.8)

Use the named input and the user's requested outcome to select a workflow:

- **Generate images:** use section 7 when the user asks to generate, render, or make pictures, or invokes this skill with a ready-to-run prompt set and no other requested output.
- **Export prompts:** use sections 1–5 when the user asks for a prompt set or invokes this skill with a media manifest and no other requested output.

A VoiceTalker media manifest comes from `image-manifest`. The export workflow preserves the prompts and records which key frames to attach. The generation workflow can consume that export or an AdSlides prompt pack directly.

## 1. Rules

1. **No unrequested changes.** Prompts are copied from the manifest. The script only (a) swaps the words
   "the attached reference image" for the real file names to attach, (b) removes the attach wording from a picture
   that has nothing to attach, and (c) adds one last line: `Output: one single image, <ratio and size>, saved as
   <JPG or PNG>.` Nothing else changes.
2. **Ask one question at a time**, each with numbered options and a proposed answer first, and wait for the answer.
   Skip a question the person has already answered. Remember answers within the session.
3. **Never guess a file.** Ask for the manifest path. Read only files the person names (the manifest, the optional
   cast file). Do not search the disk.
4. **Count first.** Say how many pictures the manifest holds before asking which to include. If the person gives a
   different number ("all 10" when it holds 8), say so and ask which they mean; never invent pictures.
5. **ChatGPT facts to state, not to work around.** There is no automatic hand-off: the person pastes each prompt into
   ChatGPT and attaches the named files. ChatGPT may not hold a face as exactly as VoiceTalker's reference system;
   re-attaching the key frame and saying "match these people exactly" is the fix. If ChatGPT returns a different shape
   or format, the reply to send is in the file's `howToUse`.
6. State where the JSON was saved (full path), and that the manifest was not changed.

## 2. Questions (one at a time, skip what is settled)

1. **The manifest.** "Which image manifest? (path to `<project>-image-manifest.md`)" Required. After reading it, say:
   `<N> pictures, <K> key frames (<names>), aspect <ratio>.`
2. **Which pictures?** `1` all N (proposed), `2` only some (give the numbers or cut IDs), `3` Cancel.
   Warn that the numbers and file names keep the manifest's order even when only some are chosen.
3. **File type.** `1` JPG (proposed), `2` PNG.
4. **Cast file (optional).** "A cast file adds each character's exact look to the file's consistency block.
   `1` use `<remembered cast file>`, `2` another file, `3` none."
5. **Save to.** Propose the manifest's folder and the file name `<project>-chatgpt-prompts.json`:
   `1` yes, `2` another folder or name.

Ask nothing else. The aspect ratio always comes from the manifest (16:9, 9:16 or 1:1); to change it, run
`image-manifest` again.

## 3. Run

Confirm in one line, `Run gen-gpt-images on <manifest>: <n> pictures, <jpg|png>?`, with `1 Run`, `2 Change something`,
`3 Cancel`. Then run (Python 3.8 or later; run it from the skill folder, which sits next to this file):

```
python3 -I scripts/make_gpt_prompts.py <manifest.md> <out.json> --format jpg|png [--cuts all|1,3,5|CUT-ID,CUT-ID] [--cast <cast.md>]
```

The script prints the image list with what to attach to each one, and `RESULT PASS` or `RESULT FAIL`. Report `FAIL`
lines to the person and do not describe the file as finished. Python missing: say so, give the install steps from
`docs/VOICETALKERS/SKILLS/README.md` ("Before you start"), and stop.

## 4. What the file holds

```json
{
  "project": "...",
  "format": { "aspectRatio": "16:9", "size": "1920x1080", "fileType": "jpg", "count": 8 },
  "howToUse": [ "..." ],
  "consistency": { "style": "...", "keyFrames": { "elena": "02-....jpg" }, "looks": { "elena": "..." } },
  "generationOrder": [ "02-....jpg", "01-....jpg", "03-....jpg" ],
  "images": [
    { "index": 3, "filename": "03-....jpg", "cutId": "...", "clipId": "...", "role": "key",
      "attachBeforeGenerating": [ "02-....jpg" ], "chars": 1662, "prompt": "16:9 landscape image (1920x1080), ..." }
  ]
}
```

- **Key frame** = the first picture of each reference name (the manifest's `firstCut`). It is made first and every
  later picture that shows that name lists its file under `attachBeforeGenerating`.
- Cards, places and objects with no reference names have nothing to attach.
- File names are `NN-short-label.jpg` (or `.png`), numbered by the manifest order.

## 5. Report

Full path of the JSON; the counts (pictures, key frames, longest prompt); the file type and ratio; the generation
order in one line; what was not checked (that ChatGPT's results match, which only the person can see). Say the next
step: make the key frames first in one ChatGPT conversation, approve them, then the rest, then load the pictures in
VoiceTalker as the person's own pictures, or run `merge-media` with an `upload` plan. Show the menu
again if the person came from `menu`.

## 6. Boundaries

Read the named input, any named cast or reference files, and existing candidate outputs needed to resume. Write new outputs under the chosen destination. Leave the input, Scribe, manifest and cast intact.

## 7. Generate image files

1. **Read the input and determine the batch.** For a VoiceTalker media manifest, run the bundled exporter into a temporary file, using the requested selection and format or its defaults. For an exported prompt set, use its `images`, `format`, and `generationOrder`. For `voicetalker.adslides.image_prompt_pack`, traverse the supplied templates and each template's slides in `sequence_index` order. Use each `visual_prompt` together with the shared image-model style and composition rules. Preserve the declared size and format. Keep overlay suggestions and ad copy outside the generated pixels.
2. **Determine file names and destination.** Use the requested destination or a dedicated batch directory under the current project's `output/imagegen/`. Keep exported file names. For AdSlides, use the template key as a subfolder and `<sequence_index>-<scene_role>.png` for each slide. Reject unsafe path components and duplicate output paths before generating. If resuming, reuse an existing output only when it matches the named input, prompt and requested format. Use a versioned filename for other collisions.
3. **Render through the host's image-generation tool.** In Codex use the built-in ImageGen tool and follow its skill guidance when available. Issue one generation call per requested image. For VoiceTalker exports, generate key frames first and attach the actual files listed in `attachBeforeGenerating` to dependent calls. If a required reference fails, report affected images and continue independent work. If the host has no image-generation tool, report the blocker and offer prompt export.
4. **Verify and save.** Inspect each result against its scene and composition requirements. Verify the decoded file format and dimensions. When the generated aspect ratio matches but pixel dimensions differ, resize proportionally to the requested dimensions. Retry mismatched framing or subject with a targeted prompt correction. Save one final per prompt, preserving successful outputs if another image fails.
5. **Report the result.** Give the full output path, counts by template or batch, verified format and dimensions, and any missing or reused images. Keep the prompts traceable to their source entries.
