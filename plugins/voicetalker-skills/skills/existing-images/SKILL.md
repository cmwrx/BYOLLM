---
name: existing-images
version: 3.2.8
description: >-
  Align, audit, prepare and place creator-supplied existing photographs,
  screenshots, illustrations, product artwork, scans and other images into
  VoiceTalker Scribes without generating replacement imagery. Use for
  existing-image asset inventories, scene ROOT and clip image matching,
  faithful 16:9 landscape and 9:16 portrait adaptation, import handoff,
  background precedence and post-import QA. This skill does not create
  Scribe dialogue, actor personas, or new artistic images.
---

## MANDATORY HARD GATE — Provider, Model, Voice Compatibility (Help-verified)

**FAIL CLOSED. NEVER CROSS-POLLINATE MODELS AND VOICES.** This is a blocking production requirement, not a stylistic suggestion. Before outputting, importing, describing as ready, or validating a Scribe, inspect **every** root TTS configuration and **every** speaking clip. Do not assume an example's root model applies to clips whose provider differs.

The supplied *Scribe Voice Studio Help* explicitly documents these separations:

| Provider (`tts.provider` / clip `ttsProvider`) | Model family | Allowed voice selection |
| --- | --- | --- |
| `openai` | OpenAI TTS; Help documents `gpt-4o-mini-tts` | An actual supported **OpenAI** built-in voice (e.g. `coral`, `onyx`, `ballad`), with exact verified identifier |
| `google` | Google/Gemini TTS; reference export uses `gemini-3.8-flash-tts` | An actual supported **Gemini** voice (e.g. `Charon`, `Puck`, `Aoede`) or a *valid, accessible* Google custom voice ID |
| `Me` / human performance | Human clip, not generated model speech | Follow the actual `Me` representation shown in the supported schema; do **not** attach GPT or Gemini voice IDs to human speech |

**Absolute prohibitions:** no Gemini voice with OpenAI/GPT model; no OpenAI voice with Google/Gemini model; no Google custom voice ID assigned to OpenAI; no provider/model substitution because a voice name appears convenient; no literal `DEFAULT` presented as a verified provider voice identifier. The Help does not give license to guess unsupported model names, provider identifiers, or account-specific custom-voice IDs.

**Root-versus-clip trap:** The working reference Scribe has root `tts.provider`, `tts.model`, `tts.voice` and separate clip `ttsProvider`, `ttsVoice` but **no clip `ttsModel`**. A mixed-provider Scribe may therefore have a Google/Gemini root and OpenAI clips, or vice versa, **provided** the VoiceTalker application actually dispatches each clip to its own provider's supported TTS model. Never synthesize or add a made-up per-clip `ttsModel` field. In a *pure Gemini* Scribe, root `tts.provider=google` and root `tts.model=gemini-3.8-flash-tts` (when confirmed supported); in a *pure OpenAI* Scribe, root `tts.provider=openai` and root `tts.model=gpt-4o-mini-tts` (when confirmed supported). For **mixed** scripts, choose a compatible root fallback pair and ensure every clip has the correct explicit provider **and voice**. If provider-based model dispatch cannot be confirmed in the actual app, **report a BLOCKER and do not claim the script is runtime-valid**. Root model does not silently authorize a conflicting clip voice/provider combination.

**DEFAULT fallback:** When no voice is specified, write `DEFAULT` only in planning/persona/manifest records. For executable Scribe JSON, resolve to a **verified compatible provider+voice+model**, ideally the actual application/root TTS defaults confirmed by the provided Help plus a working Scribe export. `DEFAULT` must inherit a *complete compatible tuple*, not merely a voice name. If neither available nor verified, flag the unresolved voice and DO NOT promise playback readiness. Never replace an explicitly selected voice with a fallback.

**Provider-specific performance:** Gemini `<short pause>`, `<sighs>`, `<chuckles>` etc. are for Gemini clips only; OpenAI uses voice style/instructions and does not accept the same inline markup. Preserve `;p` controls only according to the current Help. Validate tags per clip provider, and preserve spoken meaning when compatibility requires changes (with disclosure).

**Required rejection audit for any Scribe-related deliverable:** check (1) root provider/model/voice are mutually compatible, (2) every clip `ttsProvider` and `ttsVoice` are a verified pair, (3) a Google voice never reaches OpenAI dispatch and vice versa, (4) custom voices are Google-only and their IDs actually available, (5) no invented clip model fields, (6) provider-specific inline tags are used only with the matching provider, (7) unresolved `DEFAULT` is not misrepresented as import-and-playback-tested, and (8) the entire source was read and all approved intro/outro/interstitials are intact. **Fail delivery and show exact scene/clip IDs for violations; do not auto-convert voices or models.**


## Shared DEFAULT voice and cross-skill rules (v3.2.8)

When no specific voice is supplied for a speaking role, assign **`DEFAULT`** in the speaker ledger, cast specifications and planning documentation. Preserve any user-specified voice unchanged. The same unspecified role must use the same fallback consistently; never fabricate a named voice or custom-voice ID.

For an importable `scribe.teleprompter.v1` file, **`DEFAULT` is a logical selection, not a proven TTS voice identifier**. Resolve it to the actual supported `tts.voice` and its provider from the user's compatible reference export or confirmed VoiceTalker configuration. Where the schema requires a concrete `ttsVoice`, populate that verified concrete voice, not an unverified literal `DEFAULT`. If no valid configuration is available, clearly flag the unresolved voice and do not claim the JSON has been playback-validated. Do not overwrite existing assigned clip voices.

Cross-skill boundary: Scribe skill owns full JSON, cast skills own actor/persona and prosody plans, comic skill owns ordered panels and mandatory separate INTRO/OUTRO, generated-image skill owns new-image manifest, and existing-image skill owns mapping/formatting of user images. Preserve IDs and approved interstitials. The two image paths support 16:9 and 9:16, honor exact supplied dimensions, and never confuse manifest labels with real VoiceTalker image IDs. Read the full supplied source and its required reference files with user-granted access before completion.


# VoiceTalker — Existing Image Integration

## Purpose

Use creator-supplied images, photographs, screenshots, artwork, diagrams and other existing media to support an approved VoiceTalker Scribe. Work with short VTAds, teaching, podcasts, audiobooks, illustrated serials, product demonstrations or any other Scribe. This workflow differs from the generated-image-manifest skill: existing assets are authoritative source material, not suggestions to replace with generated images.

**Cardinal rule: NO UNREQUESTED CHANGES.** Never alter the original files in place, generate substitute artwork, remove branding, retouch faces, obscure source text, change colors or rearrange approved content without express authorization. Maintain originals separately from any approved output derivative.

## Boundaries and companion skills

- `scribe` owns Scribe script/JSON creation and revision.
- `characters` owns actor personas and prosody (the cast file).
- `image-manifest` owns plans for *generated* images and can be used for new-image cut generation when expressly requested.
- **This skill** owns the inventory, matching, adaptation and media handoff for **existing** images. It does not independently generate artwork.
- Native VoiceTalker import/upload happens through the existing app controls; the skill creates prepared files and a mapping document, not fictitious media IDs or automatic database writes.

## Supported format targets — equal priority

| Orientation | Aspect | Typical exact output | Target use |
|---|---|---|---|
| Landscape | **16:9** | **1920 × 1080** | Desktop, YouTube, horizontal video and general Scribes |
| Portrait | **9:16** | **1080 × 1920** | TikTok, Reels, Shorts and mobile-first Scribes |

The user may supply an **alternative exact resolution**, and that supersedes these defaults. **Never change requested pixel dimensions without approval.** If a user explicitly specifies `19:9`, do **not** silently treat it as `16:9`; ask to confirm the intended ratio or honor their exact numeric target if clearly intentional. When a user context clearly says landscape from the Help, `16:9` is the supported standard. Avoid mixing storyboard square-panel dimensions with final 9:16 video output.

VoiceTalker's background is scaled to **cover**, so some display-edge crop is possible even from correctly-sized images. Plan a composition-safe region and check both runner and recorded output.

## Workflow

### 1. Identify inputs and permissions

Receive the approved Scribe scene and clip list (or the storyboard / lesson outline if JSON is not yet available), plus the existing image collection. Accept photos, screenshots, logos, illustrations, product images, diagrams, scans and hand-drawn art. Respect the user's labels and filenames. Verify usable files and image orientation, file type and dimensions before transformation; note missing or duplicate originals. Record copyright/permission concerns as unresolved instead of asserting ownership.

**Do not automatically invent scene names, import order or image meaning.** When the image-to-scene fit is unclear, use a short proposed mapping with an explicit REVIEW state.

### 2. Inventory the originals

For each image record the original filename, type, pixel size, apparent subject/purpose, provenance when provided, orientation, and target scene(s)/clip(s). Do not infer ownership from a filename. Keep a deterministic stable **planning ID** such as `LESSON-S03-ROOT` or `AD-S02-C04` without renaming original files unless user asks.

### 3. Construct the cut-to-image mapping

Start from the **complete approved Scribe**: intro, title, main scenes, interstitials, transitions and outro all count. Place every required scene/cut in correct order. Prefer **one ROOT image per visual scene**, with clip overrides only where the moment meaningfully changes. Some Scribes legitimately use no image or the global background. Do not generate filler images just to make a table complete. Record unmatched required cuts as **MISSING / NEEDS USER ASSET**.

VoiceTalker background hierarchy: clip-specific image overrides scene background; scene background overrides global background. Use actual scene/clip identifiers for pairing, and do not reorder/renumber the Scribe.

### 4. Choose adaptation per source image

For each requested orientation, choose the least destructive approach:

1. **Use as-is** if the source already fits the requested dimensions and is technically suitable.
2. **Resize proportionally** if only resolution differs; preserve geometry and text legibility.
3. **Pad / letterbox / pillarbox** to fit the target without removing information. Use an approved or unobtrusive solid/neutral backing, or approved blurred extension only when authorized.
4. **Crop intentionally** only when there is sufficient safe surplus area and no critical subject, diagram annotation, brand label, accessibility element, or screenshot UI is lost.
5. **Recompose via image editing tools** only when the user explicitly asks; this may involve generative expansion and must be labeled a modified derivative, never presented as unchanged source.

**Never stretch, squash or skew** to meet aspect ratio. A 16:9 screenshot cannot be converted to 9:16 by simple cropping without potentially losing essential UI. For instructional screenshots, preserve the entire meaningful interface and use padding/stacking (when approved), not clipped buttons or unreadable text. If 9:16 makes the source too small to read, propose a separate approved close-up/zoom cut rather than silently modifying contents.

### 5. Prepare both targets

Treat **16:9 and 9:16 as independent approved deliverables**, not one careless crop. Keep all originals immutable and use explicit filenames:

`<CUT-ID>--16x9.jpg` and `<CUT-ID>--9x16.jpg` for opaque photographic/background assets. When genuine transparency must be retained, save a PNG; JPG cannot carry transparency. Keep original logos as separate files rather than baking an unapproved mark into each scene.

Prefer proportion-preserving, non-generative resizing using trusted image tooling for exact dimensions. If an edit requires adding/removing objects, changing artistic style, generative fill/outpainting or other creative alterations, use an available image-editing tool with explicit user approval. Do not imply ChatGPT/Gemini tools preserve every pixel exactly after a generative edit. Verify output files programmatically for exact pixel dimensions and visually for correctness. Each output must be downloadable as a real file when produced.

For VoiceTalker uploads, the supplied Help lists JPG, PNG, SVG and GIF, maximum **15 MB per image**, subject to account storage. Check file size and upload eligibility. Use JPG for ordinary opaque backgrounds, PNG for transparent imagery and sharp text/diagrams where helpful; do not convert SVG to a degraded photo format unless necessary.

### 6. Produce the mapping/handoff manifest

Create a **separate Markdown document** with all cut IDs, scene and clip IDs, source filenames, derivative filenames, orientations, adaptation method and QA status. This manifest refers to existing assets; it is not permission to invoke the generated-image skill.

Required columns:

| Cut ID | Scene / Clip ID | Original File | 16:9 File | 9:16 File | Fit Method | Status |
|---|---|---|---|---|---|---|
| e.g. `AD-S01-ROOT` | `scene-001` | `pouring.jpg` | `AD-S01-ROOT--16x9.jpg` | `AD-S01-ROOT--9x16.jpg` | pad/crop approved | READY |

Use **READY / REVIEW / MISSING / FAILED** states without guessing outcomes. If only one orientation was requested, omit the other derivative from current deliverables but keep the workflow able to produce it later.

### 7. VoiceTalker integration handoff

- Open or create the Scribe in VoiceTalker using the supported File → **Open from File**, **New**, **Save to File**, **Save As to File**, and eligible **My Scribes** cloud-library paths as appropriate. This skill does **not** invent a programmatic DB import endpoint.
- Upload prepared imagery into the VoiceTalker Background and Logo controls.
- Assign a scene's ROOT image to its **scene Background** field; assign optional derivative/alternate to the **clip image** control.
- Upload gives real VoiceTalker asset identifiers. Planning cut IDs and filenames are **not** valid `backgroundImageId` values by themselves.
- For repeat use, preserve the image mapping and check inherited/global backgrounds. Never modify JSON IDs until the user supplies actual asset IDs and explicitly asks for the Scribe file to be patched.
- Save an approved version locally and, if entitled, to **My Scribes**. Saving is **not** publishing a video.

### 8. Validate the whole production

Check every required intro/outro/interstitial cut and all mapped scenes/clips once, in order. Inspect 16:9 and 9:16 separately, looking for cropped faces, lost UI controls, unreadable captions, cut-off product packaging, distorted artwork, misplaced logos and display-cover cropping. Confirm all output dimensions and file sizes and that source files remain untouched. Inspect VoiceTalker runner and recorded MP4 if available; do not claim display proof merely from static previews.

Return a concise list of differences, unresolved mappings and approved manual steps. **Do not make unrelated edits** to the Scribe content, voices or app code.

## Special cases

**Training screenshots:** Prioritize text readability. A single complex desktop screenshot may need a 16:9 full-screen view plus separate 9:16 close-up derivative(s) only if approved. Do not fabricate application UI or crop away the instruction's referenced controls.

**Advertisements:** Retain approved product photography, authentic brand markings and legible product details. Leave space for captions and CTA only through approved crop/padding/recomposition. Do not invent comparative or scarcity claims from the images.

**Illustrations and archival artwork:** Preserve original linework, colors, signatures, artist credits and period fidelity. Do not turn historical art into generative approximations without a direct request.

**Logos or assets with transparency:** Use PNG/SVG appropriately; JPEG outputs can be made with an approved background color when transparency is not needed, but not by silently substituting an arbitrary background.

**Mixed generated and existing assets:** Use this skill for the existing images and the generated-image skill for new images, merging only the approved cut-ID-to-asset mapping. There is no requirement that a Scribe use only one asset origin.

## Acceptance criteria

- Existing originals are untouched and accounted for.
- Every required cut is mapped or explicitly marked missing; no cut is skipped, duplicated or reordered.
- Both 16:9 landscape and 9:16 portrait are supported; exact approved pixels verified.
- No stretching, unreadable screenshot crop, unapproved visual edit or fabricated image introduced.
- File type, upload size and orientation are compatible with the supplied VoiceTalker Help.
- Separate Markdown mapping identifies every real prepared derivative.
- VoiceTalker media IDs are distinguished from manifest labels.
- Real files are supplied with clickable download links when actually generated.
- All unapproved scope or schema changes are excluded.

**Definition of done:** Approved existing imagery is ready to place into the right VoiceTalker scene/clip in each requested format, with complete, truthful asset mapping and no unintended alteration.
