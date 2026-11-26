---
name: gen-frames-manifest
version: 3.2.8
description: Author, generate, validate, and time VoiceTalker flipbooks and image-frame manifests with complete broadcast preservation, master-derived flipbook frames, actor/mouth coordinates, and optional speech bubbles. Supports 16:9, 9:16, 1:1 and sequential n navigation.
---

# VoiceTalker gen-frames-manifest

**Version:** 3.2.8  
**Scope:** Portable Scribe image-manifest authoring and image asset workflow.  
**Priority:** Complete preservation of user material, verifiable image continuity, and truthful runtime compatibility.

## 1. Source-of-truth and cardinal preservation

1. Read the **complete** source Scribe and/or latest approved image manifest before any generation, editing or installation. Never reconstruct a supposedly complete document from a short summary. If source files are absent, identify the absence instead of inventing content.
2. Preserve **every** scene, clip, ordered ID, speaker, dialogue (`text` and/or `dialogue` as applicable), TTS voice/provider/instructions, all eight prosody/style properties, timestamps and durations, image IDs, scene images, media attachments, translations, organization, script settings, metadata, and unrelated properties. Never delete, consolidate, rename, rewrite, omit, or silently repair existing fields.
3. Preserve the *entire TV/broadcast program*: **cold open / series tease, title / intro, story scenes, all promo interstitials, all commercial/ad interstitials, transitions, and closing credits / outro**. An interstitial is a normal scene/clip in manifest order; never skip it during generation or `n` traversal. Existing ad/promo content and placeholders remain verbatim. Do not replace a placeholder with invented marketing copy.
4. One dialogue clip retains **one continuous TTS/audio source**. An image sequence is nested under that clip in `frames[]` (when runtime-supported) or provided in a **companion manifest**. Do not split clip audio into multiple dialogue clips merely to hold frames.
5. Default to **three separately saved frames per clip**. Count overrides are allowed only when explicitly requested. Record overrides; never assume every source has exactly three if it says otherwise.
6. Preserve the original file unchanged; produce a versioned derivative with source provenance and an audit of unchanged scene/clip/audio content. Never mutate production Scribe or upload changes unrequested.
7. The skill must remain **portable** across models, image generators, runtimes and story genres. Never hardcode Beowulf, Viking scenery, characters, or other project-specific visual content. Modernized stories must remain modern when specified.

## 2. Optional initial parameter intake

Ask concise setup questions **only when the user asks for setup** or when required source/format data cannot be inferred. Otherwise inherit prior choices. Never interrupt an active `n` sequence with repeated questions.

- Input: complete Scribe JSON or existing image manifest and any existing images.
- Output aspect ratio: **16:9 default**, or **9:16**, or **1:1**. Every frame within a clip must have the same exact dimensions. Defaults are 1920×1080 / 1080×1920 / 1080×1080 respectively (standard resolution; 4K is not used); generation may use smaller exact-ratio sizes if tooling requires. Report actual output sizes honestly.
- Frame plan: three matched frames per clip by default. For a requested selective flipbook, choose single-frame holds for quiet clips and frame changes for specific story beats. Record the planned count for each clip.
- Image generator and editing pathway: supplied master image, single generated master, masked image edit, deterministic overlay/composite, or explicitly approved alternative.
- Project premise/era, setting, character design, reference images, camera/lens, baseline light/weather, permitted motion, scene-specific props.
- Title and graphics: verbatim strings, exact approved typography, placement/safe zones, background plate vs overlay, reveal timing.
- Speech bubbles: enable/disable, font/placement/style, full-clip text vs approved timed excerpts. Speaker-mouth detection is mandatory metadata workflow regardless of whether bubble display is enabled.
- Output formats: per-frame PNG by default, manifest JSON, optional ZIP and QC report. Paths are outputs, not assumed URLs.
- Optional validation thresholds/masks. Defaults must be explicitly disclosed, not represented as universal passing tolerances.

Store choices in `generationPolicy` and retain them for subsequent clips unless user changes them.

## 3. Inventory: every scene and broadcast element

Iterate the actual `scenes[]` array in ordinal order; then every `clips[]` element in original order. Maintain a ledger with: `sceneId`, scene ordinal, title/category, `clipId`, clip ordinal, speaker, audio/text source, frame count, asset IDs, status, and adjacent IDs.

Categorize but **do not remove or rewrite**: cold-open tease; opening title; narrative; promotional interstitial 1, 2, etc.; commercial/ad interstitials; closing title/credits/outro. Distinguish on-screen dialogue, offscreen speech, narration and broadcast announcer. Titles/brand images may be separate overlay layers, but those scene/clip entries must still exist and be rendered.

For the Beowulf v1.09 regression fixture: 15 scenes, 66 clips, three frames per clip, 198 frame slots. Expected broadcast scenes: `broadcast-intro`, `scene-000` title, `broadcast-promo-01`, `broadcast-ad-01`, `broadcast-promo-02`, `broadcast-outro`. Verify the actual source before applying these identifiers.

## 4. One master composition for each clip

This is a **mandatory invariant**:

> Use one master composition per matched sequence and derive its additional frames from it, rejecting any that fail alignment. A single-frame hold has only its master. Explicit cuts between existing shots are editorial cuts and are checked for story and spatial continuity.

1. Author **one specific master prompt** for that clip, using the true scene and line of dialogue, modern/historical premise, shot geography, character references, facial identity, costume, actor blocking, lens, camera position, architecture, fixed foreground/background, physical props, base lighting and weather.
2. Create/approve master F1 **once** and store stable `masterCompositionId`, master asset ID and source image/hash where available. Reuse that **actual image** for downstream frames. Repeating the same prompt is **not** sufficient.
3. F2 is derived from the approved master/F1; F3 continues the F2 state (prefer deterministic layers on top of the same master). For progressive effects, keep a cumulative effect state. Never redraw titles or reset to a different independent composition.
4. Save each generated frame as a standalone complete image file. Each file must fill the selected aspect ratio.
5. Keep camera, architecture, framing, horizon, fixed objects, baseline character identity/wardrobe, visible art and fixed title geometry constant. Preserve stationary areas as closely as the chosen workflow permits; **do not claim pixel-perfect preservation from generative edits**.
6. For reliable alignment, preferentially use **masked editing** for local changes and **pixel-preserving deterministic compositing** for rain, lightning, glow, title reveals and captions. Mask/overlay assets must be separate layers with exact placement. Full-frame generation edits are lower-confidence and must pass independent QC.
7. Describe explicit **per-frame changes** (e.g. F1 baseline rain, F2 rain streak overlay plus small distant lightning, F3 rain accumulation and lightning recedes). No vague "more motion". Characters may have subtle directed movement only if their affected regions are masked/verified. If whole-frame lightning changes illumination, declare a global lighting mask and do not treat those pixels as protected for pixel-diff QC.
8. A locked **camera does not mean all visible pixels stay identical**: explicitly distinguish static image areas from motion/effect areas and exempt only legitimate masks from static-region difference checks.

## 5. Titles, title reveal and all broadcast cards

Required titles must be exact to source/user request: program title, series subtitle, episode number/name, promo/ad labels where authored, end-card text and credits. Do not invent a title, logo, copyright, sponsor, announcer copy or new branding. Prefer **VoiceTalker overlay text** or separate transparent PNG graphics to generative typography. Store exact string, font ID/name (if known), size, alignment, normalized anchor, bounding box, safe-zone and display/reveal schedule. If font or coordinates aren't provided, flag for approval; no unverified claims about typography.

**Reveal sequence:** F1/F2/F3 share one fixed title graphic; cumulative opacity or clipping reveals it without changing letters, kerning, color, size or position. For overlays, preserve the scene background plate; do not burn in text unless requested. Promos, ads, opening and outro may use no visible speaking actor and can display titles/captions instead. Preserve exact contents of each segment including placeholders.

## 6. Actor, mouth and speech-bubble coordinator (MANDATORY metadata workflow)

Coordinate **every** clip and **every frame** with the original `clip.speaker` and visible actors.

- Maintain a `characterRegistry` / actor reference set with stable actor IDs, speaking character names/aliases, on-screen identity references, costume/position and scene continuity. Never infer actor identity merely by choosing the closest face.
- Match `clip.speaker` to the intended on-screen actor; when two or more people appear, resolve which one speaks using clip dialogue, scene blocking and actor references. If unresolved, mark `speakerMatchStatus: ambiguous` and leave mouth coordinates `null`.
- **Analyze the final rendered image for each frame**, never derive mouth coordinates from text prompts or an earlier frame. Detect the mouth center (or approved lip/tail anchor) in source-image coordinates. Record original image width/height, pixel `x`,`y` (optional), **normalized `x`,`y` in [0,1]**, top-left origin, `actorId`, `speaker`, `status` (measured / manually_verified / unavailable / ambiguous), detection method and evidence reference. Do not invent confidence values.
- Every F1/F2/F3 has independent mouth metadata even if all three images show a stationary actor. When a frame contains no face, the speaker is offscreen, narrator, announcer, hidden by a mask, or too ambiguous, use `mouthAnchor: null` / `mouthCoordinates: null` and an explicit reason. **Never fabricate coordinates.**
- Provide per-frame `speechBubble` properties: enabled, `textSource` (default `clip.text`; use `clip.dialogue` only if that is the actual source), optional exact text override only by user direction, bubble anchor and bounding box, `tailTarget` as the measured speaking mouth, normalized coordinates and origin, safe-zone inset, style/font where provided, overlap/collision state, placement mode (auto / user_approved / hidden), and verification state.
- Use real rendered-image facial bounds and frame-safe bounds to select a readable bubble location. Avoid speaker face/eyes and important scene content; prefer a consistent side for an actor across the three frames when possible. If bubble text would be too long, flag text layout or request an approved segmentation rule; **do not silently rewrite or split dialogue**.
- Apply the *actual renderer's* image-fit `contain`/`cover` transform, crop/pan and aspect ratio when converting source-image normalized mouth/bubble coordinates into display/video overlay coordinates. Recalculate placement after any crop or frame replacement. Bubble and tail are VoiceTalker overlays, **not baked into image assets** unless user expressly requests otherwise.
- For narration/offscreen dialogue, speech bubbles may be disabled while an exact caption/title overlay may be authored. Preserve announcer audio. Distinguish "bubble not needed" from "mouth detection failed".
- Replacing a frame image **invalidates** previously measured mouth/bubble anchors until rechecked. Allow manual override of actor, mouth, bubble location, tail and visibility and persist the approved values across edit/save/load/export.
- Coordinator runs **after** final image generation and **before** final approval. Never label unmeasured coordinates "verified". Human review is supported and required when automatic detection is uncertain.

## 7. Timing, frames, Scribe compatibility, persistence and CRUD

- The VoiceTalker 1.08.5 implementation in the project source plays stills from each clip’s `frames[]` using the narration clock. Check the target build before preparing a native Scribe. Treat playback and MP4 capture as separate checks.
- For a manifest-only request or a build without native support, deliver a **companion manifest** with the original scene, clip and frame IDs. For a requested native handoff, write approved references and timing into a versioned copy of the Scribe. The [timing and recording procedure](references/qc-and-acceptance.md#native-voicetalker-proof) covers both the handoff and the proof.
- Preserve original `backgroundImageId` and all legacy image fields as-is for backward compatibility. One image references one frame, frames nest under a clip; **one uninterrupted TTS generation and playback timeline per original clip**.
- Use `startFraction` and `endFraction` for native cuts. A hold has one frame spanning 0 to 1. Derive cut fractions from cues in the actual narration take. Use equal fractions as provisional timing before the audio is available. Audio continues through frame changes.
- Record durable scene/clip/frame/master IDs, image assets/overlays, prompt/version, provenance, generation status, source asset hashes where available, authoring decisions and QC state. Save/load/export must round-trip all fields. Preserve existing CDN/media publishing and scene movie attachment behavior.
- Permit create/read/update/delete, replace, duplicate, reorder and retime **frames** without changing unrelated clip fields. Replacements invalidate image-derived coordinates; deletion must not delete an asset shared by other frames. Track orphan cleanup/cache invalidation in implementation specs without assuming services.
- All existing scene media, dialogs, transitions and story content remain untouched unless user explicitly authorizes edits.

## 8. Image-generation and frame-output workflow

1. Resolve the next exact scene/clip and inspect the dialogue and neighboring clips. Identify broadcast-specific title/overlay or actor behavior.
2. Reuse any approved scene/character references and generate/accept one master F1 in chosen aspect ratio.
3. For matched motion, derive each additional frame from the same master and advance the approved effect state. For a hold, use F1 alone. For a planned editorial cut, select the approved still for the cue.
4. Composite exact titles/graphics separately; preserve same placement and letter shapes across frames.
5. Export one full-size file per generated frame, using PNG by default. Reuse compatible approved files such as JPGs. Check the actual dimensions of each asset.
6. Run independent structural/QC pixel validation (next section). **Reject and regenerate/repair failing frames before releasing assets or advancing the cursor**.
7. Run actor-mouth-speaker matching and bubble coordinate analysis for every finished frame, handle null/ambiguous/offscreen cases, and validate their placement.
8. Write versioned updated manifest/Scribe-compatible metadata; record hashes/status/evidence and manifest cursor only when successful. Produce a ZIP optionally, never as a replacement for individual images.

## 9. Independent image and metadata validation (hard quality gate)

The language model's visual impression is a supplement, **not proof** of pixel alignment. Use an external script for actual images:

- Confirm file existence, decoded image sizes, identical dimensions, exact chosen ratio, three independently saved images, correct clip IDs and correct image hash/provenance where available.
- Compare each F2/F3 with master F1 in **static-region masks only**. Pixel difference mean/changed-pixel fraction and optional registration/feature displacement should be calculated programmatically. A similarity score over entire image is not an alignment test if animated areas are allowed.
- Explicitly exclude documented animated masks and declared lighting masks from static-region comparison; report how much of the frame is excluded. If everything is excluded, QC is inconclusive and must not pass.
- Check title graphic bounding box and actual text content against an exact overlay specification; prefer programmatic overlays. Check speaker anchor/bubble values are within `[0,1]`, crop-transformed as specified, not invented, and that tail targets the selected speaker's mouth.
- Thresholds are **configurable policy**, not universal constants. Record threshold, measured metrics, masks, image hashes and pass/reject decision for each set. Missing artifacts or absent QC execution yield `unverified`, **never passed**.
- Reject substantial composition, perspective, title, geometry, actor identity or static-object drift. Do not release or advance a failed set. Frame F2/F3 generative redrawing can fail even when prompts demand alignment.
- JSON-only validation checks structural content, counts, references, preservation and coordinates; it **cannot** prove visual identity, mouth accuracy or fully functioning VoiceTalker playback.

## 10. Sequential `n` navigation and mnemonic indices

User sends only **`n`** (case-insensitive): render **the next clip in true manifest order**, all frames of that clip, not the next individual frame or the next entire scene. Start after the last **accepted/approved** clip. Retain source, output ratio, animation choices, actor/bubble settings and prior references. Never skip cold open, intro, promos, commercials/ads, credits, or outro. If an in-progress clip failed QC, retry it rather than advancing.

Label every set and every file by ordinals **`S#C#F#`** (e.g., S3C1F1, S3C1F2, S3C1F3) and include actual `sceneId`, `clipId`, `frameId`, scene title and speaker. Filename can be `s03c01f01.png` or the existing canonical frame filename; preserve source identifiers and map mnemonic names in metadata. If progress is unavailable or ambiguous, look at accepted set history and request the missing cursor only if necessary. Do not wrap at end of manifest silently.

## 11. Manifest metadata contract

For new fields, prefer `generationPolicy`, `clips[].flipbookPolicy`, `frames[].continuity`, `frames[].mouth` or `mouthAnchor`/`mouthCoordinates` and `frames[].speechBubble`. **Never delete or rename existing keys**; extend additive schemas and map when source shapes differ. Use `references/manifest-fields.json` as an illustrative template, not a claim about production Scribe support. Keep exact authoring dialogue. Store review/provenance and mask metadata. `imageStatus` distinguishes `not_generated`, `generated`, `rejected`, and `approved` when actually supported by evidence; validation status may be `unverified`.

## 12. Acceptance fixture and coverage audit

For the original Beowulf v1.09 regression fixture, verify **15 scenes / 66 original clips / 198 frames**, including 6 broadcast slots: `broadcast-intro` (cold open), `scene-000` (title), `broadcast-promo-01` (promo 1), `broadcast-ad-01` (commercial), `broadcast-promo-02` (promo 2), `broadcast-outro` (credits/end card). A selective derivative preserves the source scenes and clips. Its expected frame total comes from the approved per-clip plan.

Acceptance requires: preserved scene/clip IDs and all source dialogue, TTS/prosody/settings; no skipped broadcast slots; same chosen frame dimensions per clip; traceable derivation and mask-based QC for matched frames; continuity checks for intentional cuts; actor registry and per-frame measured/null mouth anchors; per-frame bubble overlay metadata; narrator/offscreen-safe handling; audio-duration-based timing; truthful runtime capability declaration; end-to-end delivery audit. Preserve and surface every unresolved/unknown item.

## 13. Required deliverables

- Complete versioned image manifest including every scene and clip, the planned frame counts, source and asset IDs, and applicable generation and review metadata. When native handoff is requested, include the versioned Scribe. Include a proof MP4 only when recording was requested and performed.
- Complete per-frame images and overlay assets **only when actual generation is requested/performed**.
- JSON structural validation report; image/pixel and mouth-coordinate QC report **only if actually run**. Otherwise `unverified` and identify missing evidence.
- Individual frame files with mnemonic indices, optional ZIP, and a cursor/progress record for `n`.
- No unrelated implementation, deployment, database migration, git commit or Git push without explicit instruction.

## 14. Canonical portable execution prompt

> Load the complete VoiceTalker Scribe and any existing image manifest. Preserve every existing scene, clip, text, voice, TTS/prosody, interstitial, intro, title, commercial/ad, promo, credits and outro and all unrelated metadata. Use the approved frame plan. Default to three matched full-frame images from a single master, with later frames advancing the same approved effect state. For requested selective timing, use a single still for a hold and approved images at each cut. Output separate images in the selected 16:9 (default), 9:16 or 1:1 format. Keep camera, architecture, actor identities, stationary objects and fixed graphic locations unchanged; use masks and deterministic overlays when possible, including exact VoiceTalker titles and other graphics. Define precise allowed motion and lighting changes for F1/F2/F3. Run external static-region pixel-difference validation on matched derivatives and reject drift beyond the declared policy; never claim pixel-perfect results from image prompts alone. After generating each final frame, identify the speaking actor from the clip speaker and character registry, measure that actor's mouth in normalized image coordinates or explicitly mark unavailable/ambiguous, and calculate optional speech-bubble placement/tail safe for that frame. Preserve continuous clip audio. Time cuts against the actual narration and write them into a versioned Scribe for a requested native handoff. For a build without native support, deliver the companion manifest and report its runtime status. Maintain scene/clip/frame indices S#C#F#, include all broadcast slots, and let `n` advance exactly one accepted clip at a time. Preserve all preexisting content; do not fabricate titles, coordinates, model confidence, imagery, timestamps, file status, validation evidence or implementation support.

## Reference files

- `references/manifest-fields.json`: illustrative expanded schema, including broadcaster slots and actor/bubble coordinator.
- `references/qc-and-acceptance.md`: deterministic mask-based QC, actor/crop coordinates, timing, and audit checklist.
- `scripts/validate_manifest.py`: portable standard-library JSON structural validator (not an image pixel comparison program).
