---
name: comic-strip
description: >-
  Create complete VoiceTalker comic-strip Scribes from a user-supplied panel script
  or comic idea, with mandatory intro and outro, strict panel ordering, dialogue,
  speaker-specific TTS provider/voice assignments, supported prosody tags, and
  complete scribe.teleprompter.v1 JSON when requested. Use for numbered comic issues,
  including short humorous strips and serialized illustrated dialogue.
version: 3.2.8
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


# VoiceTalker — Comic Strip Scribe Skill

## Purpose

Turn any supplied comic strip, script, storyboard, or approved concept into a complete VoiceTalker comic-strip Scribe. **Every issue must contain a separate INTRO and OUTRO** in addition to all its numbered comic panels. Do not treat the first panel as the intro or the last panel as the outro. This skill assembles the Scribe and specifies spoken performance; actor-persona design and image creation/integration remain separate skills.

**Cardinal rule: NO UNREQUESTED CHANGES.**

## Input and creative scope

Accept a creator-authored script or creator-approved request to draft one. Preserve the original dialogue, scene order, actor names, plot, and specified voices unless the user requests a change. For an unnamed role, assign a clear functional name based on context. Do not invent extra people merely to fill a cast quota.

Collect or infer only the information actually needed: series title, issue number and title, ordered panels, dialogue/speakers, next-issue title if supplied, existing provider/voice choices, and any supplied asset IDs. If the next-issue title is not provided, close without making up a sequel title.

The skill works for any number of panels. **Five panels in the example are illustrative, not a software or creative maximum.**

## Mandatory production sequence

1. **INTRO** — a separately numbered scene before Panel 1. An Announcer introduces the series, issue number and issue title. If no approved title exists, use a clear editable placeholder rather than silently inventing a canonical title.
2. **Panel 1 through Panel N** — every approved panel in exact order. Each panel is a distinct Scribe scene; each spoken turn is a separate Scribe clip with its own identified speaker.
3. **OUTRO** — a separately numbered scene after Panel N. The Announcer closes the current issue and introduces the next issue **only when the next title is supplied or approved**. Otherwise use a neutral closing such as "End of Issue Number One."

Do not remove intro/outro when condensing dialogue or adapting a short-form comic. If a user explicitly asks for additional interstitials or sponsorship segments, insert them at the exact approved locations and preserve every panel.

### Required scene ledger

Before producing the JSON, provide or internally verify a compact ledger:

| Ordinal | Scene type | Source label | Required content |
|---|---|---|---|
| 1 | Intro | INTRO | Series name, issue number, issue title; Announcer |
| 2 ... N+1 | Comic panels | Panel 1 ... Panel N | Every spoken line in exact order |
| N+2 | Outro | OUTRO | Issue closure; optional approved next-issue tease |

For the five-panel example, there must be **seven scenes**: INTRO, five panels, and OUTRO.

## Voice and speaker rules

Preserve the explicit example voice allocations unless the user supplies replacements:

| Speaker | Provider | Voice |
|---|---|---|
| Announcer | Gemini / Google | Charon |
| Ruth | OpenAI | Coral |
| Owen | Gemini / Google | Puck |
| Theo | OpenAI | Onyx |
| Lena | Gemini / Google | Aoede |

These are example defaults **for the supplied strip only**, not mandatory casting for other comic projects. Confirm voice availability in the target account/model; do not silently substitute a different voice or pretend every voice works with every provider. New comic strips may use any supported and approved cast.

Use the current VoiceTalker Help for supported Voice Style fields: `voiceAffect`, `tone`, `pacing`, `emotion`, `pronunciation`, `pauses`, `emphasis`, `delivery`. Use clip-local direction where the mood changes. Avoid creating separate actor/persona documents in this skill; use the 1–3 actor or 4+ actor skill when requested.

## Voice tags and pauses

- Preserve VoiceTalker's supported end-of-clip pause syntax such as `;p1` and `;p1.5`. The marker is control text, not spoken narration.
- Respect exact supported Gemini vocal tags from current Help, including `<short pause>`, `<long pause>`, `<whispers>`, `<sighs>`, `<chuckles>`, `<laugh>`, and `<gasp>` where valid for the selected Google voice.
- **Do not carry Gemini inline tags into OpenAI clips as if they were supported.** For OpenAI, express the requested effect through `ttsInstructions` and/or the eight Voice Style fields; preserve intended spoken dialogue.
- When adapting user-supplied tags, preserve the creative intent and explain any provider-compatibility conversion outside the Scribe file.
- Do not automatically add exaggerated pauses to a brief comic; check comedic timing in actual playback.

## Canonical example — Issue No. 1

Use this sample as a **structural reference**, not a compulsory story or universal cast.

### INTRO

**Announcer (Gemini Charon):** `<Your Series Title>. Issue Number One: <Your Title>.`

### Panel 1 — Opening

**Ruth (OpenAI Coral):** `Good morning… the oven is already warm. ;p1`

### Panel 2 — The Customer

**Owen (Gemini Puck):** `<short pause> Is it ready yet?`

**Ruth (OpenAI Coral):** `Not yet — ten more minutes. ;p1`

**Owen (Gemini Puck):** `<sighs> Ten minutes is a very long time.`

**Theo (OpenAI Onyx):** `It is exactly ten minutes. Not eleven. Not nine.`

### Panel 3 — The Rush

**Lena (Gemini Aoede):** `<whispers> Don't tell anyone, but the line is out the door.`

**Theo (OpenAI Onyx):** `Out the door? It's AROUND THE CORNER.`

**Ruth (OpenAI Coral):** `Everybody stay calm… one loaf at a time. ;p1.5`

### Panel 4 — The Secret

**Lena (Gemini Aoede):** `<long pause> I brought you something.`

**Owen (Gemini Puck):** `<chuckles> Is that my grandmother's recipe?`

**Lena (Gemini Aoede):** `<laugh> Maybe. ;p1.5`

**Theo (OpenAI Onyx):** `Hmm… cinnamon. And — something else. ;p1`

### Panel 5 — Closing Time

**Ruth (OpenAI Coral):** `Last loaf. Who wants it?`

**Theo (OpenAI Onyx):** `Me. No — wait — you take it.`

**Lena (Gemini Aoede):** `<gasp> Really?`

### OUTRO

**Announcer (Gemini Charon):** `End of Issue Number One. Continued in Issue Number Two: <Next Title>.`

**Expected for this sample:** 7 scenes and 16 spoken clips (intro 1 + panels 1/4/3/4/3 + outro 1). Count carefully for each new production.

## Scribe JSON creation

When asked to create the finished Scribe, use the current **Scribe creation skill** and an actual compatible `scribe.teleprompter.v1` reference export. Preserve full root metadata, presentation `settings`, scene/clip fields and root `tts` where present. Do not emit a truncated schematic in place of a working Scribe.

- Assign a unique `sceneId` to INTRO, every Panel and OUTRO. Keep `ordinal` contiguous.
- Give each dialogue turn one unique `clipId`, contiguous within-scene clip ordinals, correct `speaker`, `ttsProvider` and `ttsVoice`.
- Maintain exact words and sequence unless a change is approved. Provider compatibility adjustments to inline instructions must be explicit.
- Keep `backgroundImageId` empty until a **real** asset is uploaded and its media-library ID is known. Planning cut IDs are not valid background-image IDs.
- Preserve the distinction between scenes, clips, and images: one panel scene can use one scene-root image for all its clips, or approved clip-specific overrides.
- Do not invent extra JSON properties for comic issue metadata or CTA behavior without schema confirmation.
- Do not omit the INTRO, OUTRO, or any specified interstitials.

## Artwork and orientation handoff

Use the separate **image manifest skill** to plan approved artwork for **INTRO, every Panel and OUTRO**, in exact Scribe order. Use the **existing-image skill** when the creator already owns photographs, illustrations or screenshots. Use the actor skill for character visual-persona specifications. Do not create image files or image prompts unless the user explicitly requests the separate image workflow.

Specify the chosen orientation as either **16:9 landscape** (e.g., 1920 × 1080) or **9:16 portrait** (e.g., 1080 × 1920). If both are requested, plan both variants per scene. Protect caption-safe space and avoid assuming one crop fits both. Honor any creator-specified exact pixel dimensions over these examples.

## Production checks

Before delivery verify:

1. Intro and outro exist **as distinct scenes**.
2. All numbered panels exist, in strict order, once each.
3. Every supplied spoken turn exists once and belongs to the right speaker.
4. The title and issue number match the approved source; sequel title is only used if supplied.
5. Provider, selected voice and TTS instructions are internally consistent; Google tags are not silently placed in OpenAI clips.
6. Pause markers are retained or compatibility-converted only with disclosure.
7. Exact panel count and clip count are correct.
8. Every scene/clip ID is unique, and all ordinals are coherent.
9. Image associations use real VoiceTalker media IDs or empty strings, never manifest labels.
10. Complete Scribe JSON parses and carries expected root TTS/settings from the approved base export.
11. Timing, pacing and emotional delivery are auditioned where possible; estimated duration is never asserted as verified.
12. No unrequested dialogue, actor, feature, ID, layout or content changes were made.

## Outputs

For a **skill request**, deliver this complete Markdown `SKILL.md` content as a download. For a **comic Scribe request**, deliver one complete valid `.json` Scribe file plus a brief count/validation summary. Supply actor specs and artwork plans only when the user separately asks.

**Never claim the comic is published or deployed.** The creator controls import, saving, rendering, Git and publishing.
