# VoiceTalker Frame Validation and Acceptance Specification

## Structural audit (no image generation required)

Compare input and output canonical scene/clip ordering, IDs and all existing source fields. Compare audio/TTS and script metadata by value. Preserve intro, title, all promos, commercial/ad slots, transitions, credits, outro and their exact text. Ensure frames are nested under original clips without extra dialogue clips. Valid ratios: 16:9, 9:16, 1:1. Frames in a clip share resolution. Record any existing different explicit frame count instead of coercing it.

## Image QC (requires actual images and an external script)

1. Decode the actual images and check dimensions, color space, orientation, hashes, and the selected aspect ratio. Apply static-region checks to matched derivatives. For an intentional cut between shots, review screen direction, character identity, and story continuity.
2. Build a *static region mask* from approved motion regions (actor arm/face, rain, ripples, monitor, lightning, reveal layers); exclude these plus declared whole-frame light changes if explicitly permitted. Record mask area and ensure nontrivial static area remains.
3. Compute pixel difference between static master and each derivative in the original image coordinate system. Suggested diagnostic metrics: mean absolute error and fraction of pixels whose channel change exceeds a selected threshold. Exact thresholds are project-configured, not magic constants.
4. Optionally estimate feature displacement/structural landmark positions of fixed architecture and horizon. Reject significant displacement per the project's approved tolerance. Do not declare passed without measured data.
5. If deterministic overlays are used, underlying pixels should be identical except overlay/mask regions. If AI edits redraw the entire background, reject failures or mark alignment unverified. Do not silently score the entire image with a perceptual similarity model and claim pixel alignment.
6. Inspect humanly for visual narrative, identity, lighting, fixed title placement, correct text, and subtle motion; this is a supplemental visual check, not a substitute for pixel QC.

## Actor and bubble QC

Coordinate origin: top-left of **original uncropped final frame**; normalized x=px/width, y=py/height. Valid 0<=x,y<=1. Match intended speaker by named actor reference and speech context, not just any face. Track distinct actor IDs. If speaker offscreen, mouth occluded, narrator, announcer, or match ambiguous, mouth is null plus status/reason; captions may be substituted when authorized.

Measure mouth against each final frame independently. Record final-image dimensions, detection evidence and verification state. Never derive from a prompt. Transform source normalized anchor through actual renderer fit/crop to display-space overlay coordinates; preserve user-verified overrides. Bubble geometry must remain on-screen and avoid the speaker's face; bubble tail terminates near the selected speaker's mouth. Long speech must not be silently segmented. Bubble disabled does not remove speaker/actor registry or audio.

## Title/overlay QC

Titles are separate exact overlays where possible. Validate exact characters, title art asset, font reference if known, fixed rectangle, anchor and safe zones. F1/F2/F3 reveals use the same graphic with cumulative alpha/clip masks; no redraw. All credits, sponsor/promos/ads and required texts remain as supplied. Never invent branding.

## Audio and runtime truth

Frame changes share the clip’s narration clock. Preserve the clip’s existing background and voice settings. Confirm the target build supports native frames before reporting a playable handoff.

## Native VoiceTalker proof

1. Choose a short sequence with a visible change and a final hold. Reuse approved stills first. Check that each picture reveals the intended action at its cue.
2. Generate or load the narration for the current script. Measure cut points in that take. Divide each cut time by the clip audio duration to get its frame boundary. For example, cuts at 2 and 5 seconds in an 8-second take produce intervals 0–0.25, 0.25–0.625 and 0.625–1. For a single still, use 0–1. Use provisional fractions until the take is available.
3. In a versioned Scribe, write one `frames[]` entry per interval with a stable `frameId`, consecutive `ordinal`, `startFraction`, `endFraction`, and a resolvable still-image `backgroundImageId`. Adjacent intervals share a boundary. A file reference uses `file:<relative path>` and must be attached in VoiceTalker before playback. Check inherited pictures after changing the number of frames in a preceding clip, since inheritance uses frame position.
4. If keeping the companion manifest current, set the clip’s `flipbookPolicy.frameCount` to the planned number of frames. Use `validate_manifest.py` for manifest structure and the app’s frame preflight for native timing and picture loading.
5. Open the versioned Scribe, load its named pictures, and play the proof with the intended audio. Record a short MP4 in the intended aspect ratio and compare its frame order, cut timing, and final hold against playback. Note separately which checks were run and passed. For 1.08.5 recording acceptance, the approved tolerance is ±2 video frames at 30 fps.

## Release gate

A frame set is accepted only when required files exist, exact aspect ratio confirmed, applicable alignment metrics run and passing, coordinator metadata measured or explicitly unavailable with reason, and source coverage verified. A failed/unverified set does not advance `n` cursor. Document uncertainty plainly and preserve previous accepted state.
