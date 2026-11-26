---
name: image-manifest
version: 3.2.8
description: >-
  THE MEDIA PLAN (runs after the Scribe, before any picture or video is made). Reads the Scribe, decides how it
  is staged (mini-play: a short staged play with every speaker on screen when they speak; studio: a podcast,
  interview or tutorial in one set; story: a play, film or comic across places and moments), and plans the media
  for every scene and clip: a generated picture, a screen shot of a named part of a page, the user's own
  picture, SVG or mp4, a captured video, a placeholder, or nothing, in any mix, all tied to the words of the
  clip. The user gives indexed assignments (clip 3 = screen shot) or rules (every 3rd clip, every named button,
  every key object, every scene, titles, intro, outro, interstitials) or accepts the proposed plan. It writes an
  image manifest (vt-image-manifest.v2): the plan, optional title and closing cards, key reference frames, and
  one FINAL image prompt per generated picture, each within 2,000 characters. It never edits the Scribe; the
  merge step places everything.
---

# VoiceTalker Image Manifest, the media plan (v3.2.8)

Pipeline: Step 1 (optional) `characters` (cast and prosody) → Step 2 ingest, then `scribe` (first-cut Scribe, no pictures) → **Step 3 this skill** (the media plan) → Step 4 screen shots and generated pictures, and, separately, screen videos → Step 5 merge the media into the Scribe → Step 6 load it in VoiceTalker and run Batch Media (generated, captured and uploaded media).

**Every kind of media is optional, per scene and per clip, in any sequence: generated picture, screen shot, uploaded picture or SVG, captured or uploaded video, sound, character definition, or none.** A scene or clip with no entry keeps whatever is already on screen. All media are tied to the words of the clip that speaks them; a video or picture may deliberately run on across following clips and scenes.

Input: the Scribe JSON (required), plus the optional cast file (`characters`), style notes, brand art, the user's own media files or the original text. Output: `<scriptName>-image-manifest.md`, a Markdown file for people that ends in one machine-readable JSON block (`vt-image-manifest.v2`, which the later steps read; **the user never has to open or edit it, the skills create it and read it themselves**). **The final prompts are written here, not in the merge step.**

## 1. Rules

1. **No unrequested changes.** Do not change the Scribe, its words, speakers, voices, IDs or scene order. Do not invent scenes. Do not add pictures the chosen strategy does not call for. Never add media the user did not choose or accept; `none` is a valid plan for any clip or scene and is never a gap to fill.
1a. **Ask one question at a time**, each with numbered options and a proposed answer, and wait for the answer.
2. **Facts of the app that decide how prompts must be written** (they come from the VoiceTalker code; do not work around them):
   - A prompt is **at most 2,000 characters**. Longer prompts are refused by the app. Aim for 1,200 to 1,800.
   - The app reads the **aspect ratio from the first 200 characters** of the prompt (`16:9`, `9:16` or `1:1`). Every prompt therefore **starts** with the canvas sentence. A prompt that does not start with it is generated in the wrong shape.
   - A picture can be generated using **up to 5 reference pictures** (`referenceNames`, at most 5 names per picture). Reference pictures must be `.jpg` or `.png`.
   - **The first picture, in playback order, that lists a reference name is that name's reference image.** There are no separate reference portraits to make first. Every later picture that lists the name is generated using it. The batch makes pictures in script order and each picture waits for the first picture of every name it lists.
   - A picture attaches to a clip. The picture on the **first clip of a scene is the scene's picture**; a later clip with its own picture replaces it from that clip on; clips without one keep showing the previous picture. **One picture = one clip = one generation.** A cut ID is never reused on a second clip.
   - Static stills only. No camera moves, no animation.
3. Do not write the real image IDs, file names or `backgroundImageId` values anywhere; VoiceTalker creates them.
4. State where the manifest was saved (full path) and that the Scribe was not changed.
5. **No character drift, no undefined actors (hard rules, checked by `check_drift.py`).**
   - **The cast is the complete list of people who may ever be drawn.** Every person, hand, face, child, crowd, silhouette or body part in any picture must be a named cast character whose reference name is listed on that picture. Never draw "a hand holding", "a child", "staff", "an audience" or any anonymous person. Pictures of objects, places and icons say so: `No person or body part appears.`
   - **Every picture that shows a cast person lists that person's reference name, and every listed person name is drawn.** A person who appears in a picture without the name, or a name on a picture without the person, is a defect.
   - **Speaker visibility (hard rule, every staging, checked as R10 and R11).** When a cast character speaks, that character is on screen. The picture in effect on every clip spoken by an on-screen cast character (the clip's own picture, or the picture carried over from an earlier clip) must name and show that speaker. In an exchange, nobody is removed from the frame: the picture on a clip also shows the cast character who spoke the clip just before it, when both clips are in the same scene. A clip may carry the previous picture only if that picture already names the speaker and the previous speaker; otherwise it gets its own picture. Narrator clips are exempt. A person appears only in a place they are in at that moment: never draw anyone in a room they are not in, and never leave a conversation happening in an empty room. At most 5 names per picture: keep the speaker, the previous speaker and the person addressed first.
   - **How people are staged depends on the staging (section 2, step 2).**
     - **Studio staging** (podcast, interview, panel, tutorial: the same people in the same set throughout). Actors are never alone, and the studio is always the same shot. Every picture that shows a cast person shows the whole cast together in one fixed studio shot (same room, table, camera and people). Make that master picture once, by editing one picture to add the next actor, and reuse it for every picture that shows a person; never make a separate picture of one actor in a different room. A topic picture with no person (a chart, an object) is not a studio shot.
     - **Story staging** (play, drama, comedy, storyboard, film, comic: scenes are different places and moments). A picture shows only the people who are in that moment of that scene, each one named and drawn exactly once, in that scene's own place. Scenes may be different rooms, times and camera angles (wide, medium, close-up, over the shoulder, group). A character's look never changes: the same reference name and the anti-drift clause hold it in every scene. Characters are not forced into one shared set, and nobody is drawn who is not in the moment.
   - **A cast person with a supplied reference photo** (`referenceImage` in the cast file) is written, in every picture, as `exactly as in the attached reference photo`, never as a text description of the face, and the photo must be attached as that name's reference before the batch (Step 3 reports the gate). A prompt that says a face is "not described here" is never delivered.
   - **A picture with baked-in lettering (title or closing card) is never the first picture of a person's name.**
   - Every picture of a cast person carries this clause: `Draw each named character exactly once, with the same face, hair, build and clothing as the attached reference image in every picture; never redesign, age, restyle or swap them, and add no other person.`

## 2. First: scan, count, then ask

1. Read the whole Scribe. List scenes and clips in order. Note `title`, `subtitle` and `closing` text from the INTRO and OUTRO scenes when the Scribe has them (Step 1's report gives them). **INTRO and OUTRO scenes are optional.** When the Scribe has neither, do not stop: ask question 3 below and wait. The manifest records the answer as `"cards"`: `scenes` (the Scribe has INTRO and OUTRO scenes), `first-last` (the cards sit on the first clip of the first scene and the first clip of the last scene) or `none`.
2. **Decide the staging, and say which and why.** Read the Scribe and choose one:
   - **`studio`**: a podcast, interview, panel, talk show, newscast or tutorial. Few speakers who stay in one fixed set; scenes are topics, with topic pictures (charts, objects) between them.
   - **`mini-play`**: a short staged play or comedy with a small cast (about 2 to 8 speaking characters, mostly dialogue, usually under 10 minutes). Staged like `story` (scenes are different places), with strategy P as the default and speaker visibility enforced on every spoken line.
   - **`story`**: a play, drama, comedy, audio drama, storyboard, film, comic or history. Speakers are characters; scenes are different places and moments; there are entrances, exits and stage directions.
   - **Mixed** (for example a documentary with re-enactments): decide scene by scene and list which scenes are which.
   A `productionType`-style hint in a supplied cast file, or the user's own words, win. Ask only when the signals conflict, as one short question. Write the staging in the manifest header and as `"staging"` in the JSON block; the drift check reads it.
3. **Cast file (optional).** If a cast file is supplied (`vt-cast.v1`), use it: its `world` sentence is the style sentence (do not ask question 2 about style), its on-screen characters, places and objects are the key subjects (with their `referenceName`), and for each its `imageDescription` is the full description (first picture) and its `imageTag` the short tag (later pictures), copied word for word. Characters with `onScreen` false are never drawn. A subject that ends up on only one picture still gets no name. Look in the Scribe for any on-screen speaker that the cast lacks and describe them yourself, listing them in the report.
4. Find the **key subjects**: each recurring character, place and important object. A subject is **key** when it will appear in two or more pictures. For each, find the clip where it is first introduced (an entrance, a first line, a first mention).
5. Compute the picture count for each strategy and show it. Every strategy also includes the title card and the closing card, unless `cards` is `none`. If the Scribe already carries image prompts or image names, say how many, and that merging a new manifest replaces them and generating pictures costs per image.
6. **Ask the user, then wait** (skip a question the user has already answered):

> **1. What should get a picture?**
> **A.** One reference image for each **scene** (N pictures)
> **B.** One image for each **clip** (N pictures)
> **C.** An image on each **key object introduced**: a picture at the start of every scene, plus one key picture where each key character, place or object is first introduced (N pictures, recommended for stories)
> **C+N.** Strategy C plus **N impact pictures** at the story's key moments: a punchline, reveal, turn, confrontation or emotional peak (N + the count of C)
> **P.** **Play**: strategy C plus every clip needed so that the speaker, and the person they answer, are always on screen (the fewest pictures that satisfy speaker visibility; N pictures, the default for a `mini-play`)
> **D.** Other: tell me the rule (for example, only every third scene, or only the characters)
>
> **2. Orientation?** 16:9 landscape (1920x1080) or 9:16 portrait (1080x1920)
>
> **3. Title and closing cards?** (asked only when the Scribe has no INTRO and no OUTRO scene; when it has them, the cards go on their first clips and nothing is asked)
> **A.** None. No title card and no closing card.
> **B.** A title card on the first clip of the first scene and a closing card on the first clip of the last scene. The Scribe is not changed. Take the title and subtitle from the Scribe's title unless the user gives them, and ask for the closing words (for example `The End`) if the user gave none.
> **C.** Add INTRO and OUTRO scenes first (stop; run Step 1 in normalize mode), then come back.
>
> **4. Which media, and how is it planned?** (section 3b; the strategy in question 1 only decides where generated pictures go)
> **A.** Propose a plan from the words: generated pictures by the strategy chosen above, a screen shot wherever the clip's words name something on a page the user wants shown (ask for the page address once), and nothing elsewhere. The user then changes any entry.
> **B.** The user gives the plan: indexed assignments (`clip 3 = screen shot`, `scene 4 = my video`) and/or rules (`every 3rd clip`, `every named button`, `every key object`, `every scene`, `titles and subtitles`, `intro and outro`, `interstitials between scenes`), with any mix.
> **C.** Placeholders only: reserve a place for every clip or scene that will get media and decide the kind later.
> **D.** No media at all in the manifest (words only).

If the user does not answer and says "you choose", use **P** for a `mini-play` (otherwise **C**), 16:9, question 4 = **A** and, when the Scribe has no INTRO and OUTRO, no cards (A), and say so. Also ask for, or propose, **one style sentence** if none was given (show the proposed sentence in the report; the user can change it and you regenerate). Ask nothing else.

## 3. Which clips get a picture

| Strategy | Pictures |
|---|---|
| Cards (unless `cards` is `none`) | The first clip of the first scene (title card) and the first clip of the last scene (closing card). With `cards` = `scenes` these are the INTRO and OUTRO scenes. |
| **A** scene | The first clip of every scene. |
| **B** clip | Every clip. Warn that this is the most expensive option and give the count. |
| **C** key | The first clip of every scene (the scene picture), plus the clip where each key subject is first introduced when that clip is not already a scene's first clip. A subject introduced in a scene's first clip is shown in that scene's picture. |
| **C+N** impact | Everything in C, plus N more clips chosen for effect: the moments where the story turns or lands (a punchline, a reveal, a decision, a confrontation, a kiss, a final beat). Spread them across the scenes, pick clips that are not already pictured, give each the role `impact`, and list in the manifest why each was chosen. |
| **P** play | Everything in C, then walk the clips in order tracking the picture in effect and who it names: a clip spoken by an on-screen cast character gets its own picture whenever the picture in effect does not already name that speaker and the speaker of the previous clip (same scene). Count them, show the count, and list for every such picture which rule forced it. |
| **D** other | Apply the user's rule exactly; restate it in the manifest so Step 3 and the user can see it. |

Within a scene, a narrator stage direction such as `Enter Sampson and Gregory, …` is the natural clip to carry an introduction picture.

## 3b. The media plan (every kind, every clip, one list)

The strategy table above says where **generated** pictures go. The **plan** is the full list of what every scene and clip shows. Each entry is on one place (`global`, one `scene` or one `clip`) and has a `kind`:

| kind | What it is | What it carries |
|---|---|---|
| `generated` | a picture VoiceTalker's Batch Media makes | `cutId` of an entry in `cuts` (the prompt, written as in sections 4 and 5) |
| `capture` | a screen shot of named parts of a page, taken in Step 4 | `words` (the clip's spoken words), `mustShow` (the labels that must be visible), `page`, `frame` |
| `upload` | the user's own picture, SVG, mp3 or mp4 | `file` (path next to the manifest), `mediaType` |
| `video` | a video: the user's own (`file`), or a captured one (`source: "capture"`, with `words`, `mustShow`, `page` like a capture) | `file` or the capture fields |
| `placeholder` | a reserved place; the kind is decided later | `wantKind` (or empty) |
| `none` | nothing on screen on purpose; this also ends a picture that would otherwise carry over | nothing else |

**Rules for building the plan:**

1. **Indexed assignments and rules both work, in any mix.** `clip 3 = capture`, `every 3rd clip = generated`, `every named button = capture`, `every key object = generated`, `every scene = generated`, titles, subtitles, intro, outro, interstitials. Write each rule that was used in `rules` (a record for the report) and expand it into plan entries; the plan list is what later steps read.
2. **A media entry may run on.** `span.toClipId` says the entry stays on screen until that clip (across scenes if the owner wants it); a later entry on any clip inside the span replaces it from that clip on. A `none` entry ends it.
3. **A capture is tied to the words of its clip, and it is not allowed to be vague.**
   - Scope is always `clip`. `words` is the clip's spoken words, copied exactly (pause markers removed).
   - `mustShow` is a list of phrases taken word for word from those words: the names of the parts, buttons, tabs, panels or headings the clip speaks about (`Create & Play`, `the rail`, `Selected Line`). A clip that names nothing on the page gets no capture; give it `none`, a generated picture, an upload, or leave it without an entry (it keeps what is on screen), as the user chooses.
   - Step 4 finds each phrase on the live page, frames the smallest tight crop that contains **all** of them, and proves by geometry that each one is inside the saved picture before it shows the shot to the user. Every capture picture is 1920 x 1080, with a minimum crop width so a small control is not blown up, and `frame` records that rule.
   - One shot is never reused to cover a different clip's words. Two clips that name the same part may each have their own entry.
4. **Placeholders and the user's choice.** For every entry the user can say accept, change the kind, or `none`. Never silently drop a clip's entry. Never overwrite media the Scribe already holds on a clip (a `file:` path or a picture id) without asking.
5. **The plan is checked against the Scribe by `check_plan.py`** (section 7): every entry is on a real scene or clip, every capture has `mustShow` and the exact words, every upload file exists, every span ends after it starts, every generated entry points at a cut that sits on the right clip.
6. **Sound and character definitions** stay what they already are: character definitions come from the cast file (Step 1), and sound effects and music are the Scribe's own per-clip sound settings. This skill does not plan them; if the user wants a sound on a clip, record it under `notes` of that entry and say it is placed by hand in VoiceTalker.

## 3c. Repairing a plan (re-entrant: one entry or the whole plan, never a rebuild)

Every step can be run again, in any order, on one item or on all. **Never rebuild a plan to fix one entry**: a rebuild loses the user's approved shots and answers. Use `plan_repair.py` (beside this file; standard library only):

```
python3 -I plan_repair.py list   <manifest>                               every entry and its status
python3 -I plan_repair.py sync   <manifest> <scribe.json>                 bring the plan up to date with the Scribe as it is now
python3 -I plan_repair.py patch  <manifest> <entryId> '<json fields>'     change one entry
python3 -I plan_repair.py add    <manifest> '<json of the entry>'         add one entry
python3 -I plan_repair.py remove <manifest> <entryId>                     remove one entry
```

- **The words of a clip were edited:** run `sync`. A capture whose clip words changed gets its words updated and is marked `stale` (it must be retaken; its old file is forgotten, never deleted). Every other entry keeps its status and file. Entries whose clip is gone are reported as ORPHAN and kept; labels in `mustShow` that the new words no longer name are reported as LABEL; a generated entry whose clip words changed is reported (check its prompt).
- **One entry is wrong:** `patch` it (changing a capture's `words`, `mustShow` or `page` sets it to `retake`), or `remove` it, or `add` a new one. Then run `check_plan.py`.
- **The whole plan needs another strategy:** only then ask the user whether to rebuild, and say that approved shots will be lost unless the entries are carried over.
- After any repair, the capture step does only what is not approved (section 3 of `screen-cap`) and the merge step is run again (it writes nothing if nothing changed).

## 4. Key reference frames (the first picture of every key subject)

The first picture that lists a name becomes its reference, so that picture **is the key frame**. Compose it as a clean introduction of the subject:

- the subject is large and clearly visible: whole figure (or the whole object or place), facing the viewer or three-quarter view, even light, plain neutral expression, nothing hiding it; it fills at least a third of the frame height;
- no extreme expression, action pose, crowd, partial view, silhouette, night shot or heavy mood in the first picture of a name;
- **Studio staging: the whole cast in the key frame.** Every cast person is in the first picture, together in the studio shot, so no actor is ever drawn alone and every later picture reuses that shot. Never a solo key frame in a different room;
- **Story staging: each character's key frame is a clean introduction in the scene where the character first enters or speaks.** Prefer the clip where the character first speaks (a voice is never introduced by an invisible character). The character is large and clear in that scene's own place, alone or with the others who are in that moment, each of them named; a character who is only a small figure in a wide shot is not introduced there: show the place without people on the scene's first clip and introduce each person on a closer picture;
- a **place** is named only when its first picture shows the place with the same people (or nobody) that the later pictures show; never name a backdrop that has a person standing in it. In story staging, give a place that scenes return to its own establishing picture with nobody in it;
- an exchange keeps its people in frame: the introduction picture of a character that answers someone also shows (and names) that person; the person's own reference already exists, so a small figure is fine;
- a name is also listed on its **own first picture**, and on every later picture that shows the subject (maximum 5 names per picture; if a shot shows more, leave out the least important);
- a subject that appears in only one picture gets no name; describe it in that prompt only.

Reference names: lowercase letters, digits and single hyphens (`bolt`, `verona-street`), one name per subject, spelled the same everywhere.

## 5. Writing each prompt

Build every prompt in this exact order, as plain sentences, self-contained (never "as before" or "the previous picture"):

1. **Canvas:** `<aspect token>, full-bleed, for <production type> <title>.` Aspect token: `16:9 landscape image (1920x1080)` or `9:16 portrait image (1080x1920)`. This is the first thing in the prompt.
2. `Cut <CUT-ID>: <short label>.`
3. `Shot:` the framing, pose, action and single focal moment. Describe what is seen, not the dialogue.
4. `Characters:` for each subject in the shot. **At the subject's first picture** give the full description (face, build, age, hair, clothing, colours, props), at most 300 characters each, and for a fully invented person add `not based on any real person`. **In later pictures** give a short tag of at most 100 characters (the name and its two or three most identifying features) and say `match the attached reference image`. For a cast person with a supplied photo, use the same sentence in every picture: `<Name>: <role>. Face, hair and build exactly as in the attached reference photo, drawn in this style with the same likeness; <attire and props>.` After the people, add the anti-drift clause from rule 5. A picture with no cast person says `Characters: none; icons and objects only. No person or body part appears.`
5. `Setting:` place, time of day, light (one or two sentences). In story staging every scene has its own place; write it in full in each prompt (self-contained), and use the same wording for the same place every time.
6. `One clear focal moment. Keep the bottom quarter of the frame calm for the captions.`
7. `Style: <style sentence>` identical in every prompt, at most 260 characters.
8. A blank line, then `Avoid:` the exclusions (at most 330 characters, the same in every prompt: modern objects or anachronisms for the setting, watermark, logos, invented signs or brands, `any person, hand, body part, face, crowd, silhouette, child or figure that is not a named character in this prompt`, and anything the project forbids), then the **fixed clause**: `Fill the whole frame edge to edge: no white bar, no black bar, no letterbox, no border and no panel along any edge. NO TEXT of any kind: no captions, no lettering, no readable signs, no interface.`

**Title and closing cards replace the "NO TEXT" sentence of the fixed clause** with lettering, because a title card is the title written on the picture, never the spoken line:

- **Title card** (first clip of the first scene, the INTRO scene when there is one; none when `cards` is `none`): `Lettering (required, must be clearly visible and the dominant element): exact baked-in lettering in <lettering style matching the production>, spelled exactly: "<TITLE>" (largest), "<SUBTITLE>" beneath it (smaller, same style), and along the bottom edge in small type "A Centerbeam AI production, built on VoiceTalker". No other text.` The picture shows the world of the production (an establishing view with the sky or a calm area left open for the lettering). Use the exact TITLE and SUBTITLE from Step 1, or, with `cards` = `first-last`, the ones given by the user or taken from the Scribe's title.
- **Closing card** (first clip of the last scene, the OUTRO scene when there is one; none when `cards` is `none`): the same, with the exact closing text from Step 1 (for example `The End` or `End of the excerpt`) as the largest line and the credit along the bottom edge. It shows the closing view of the same world.
- Every other picture keeps `NO TEXT of any kind`, unless the Scribe's story needs one specific piece of text on screen (for example clock digits): then name exactly which text and allow nothing else.

**Length budget.** The fixed parts (canvas 40 to 60, style up to 260, avoid up to 330, fixed clause about 190) take about 800 characters, so the shot, characters and setting must fit in **about 1,000 characters**. If a prompt is over 1,900, shorten the shot and the character tags (use tags instead of full descriptions), never the style, avoid or fixed clause, and never drop the Cut ID. Measure every prompt with the validation script and store its length.

**Cut IDs:** `<SLUG>-S<scene number, 2 digits>-ROOT` for the first clip of a scene and `<SLUG>-S<scene number>-C<clip ordinal, 2 digits>` for any other clip. `<SLUG>` is 2 to 6 capital letters from the title. Keep existing IDs verbatim if the user supplies a manifest.

**Consistency:** the same person, place or object is described the same way every time; the same style and avoid text everywhere. Honor brand, character and product images the user supplied; never invent logos, brands or real people.

## 6. Manifest file

Write `<scriptName>-image-manifest.md` next to the Scribe. Sections, in order:

1. **Header:** project, source Scribe (`scriptId`, `version`), staging (`studio`, `story` or mixed, and why), strategy (A, B, C, C+N or D with its rule), orientation and canvas, the style sentence, the avoid text, the cards choice (`scenes`, `first-last` or `none`) and, when there are cards, the title, subtitle, closing text and credit.
2. **Pictures by the numbers:** pictures, key references, the longest prompt in characters, runtime estimate (spoken words ÷ `defaultScrollWpm`) and pictures per minute.
3. **Key references table:** name, type, the cut that is its first picture (its key frame), how many pictures use it.
4. **Ordered cut ledger:** order, cut ID, scene, clip, role (`title`, `scene`, `key`, `impact`, `clip`, `closing`), reference names, characters.
5. **Production status:** a note that the pictures are made by VoiceTalker's Batch Media after Step 3 (or outside the app, section 9).
6. **The machine-readable block**, last, exactly once, as a JSON code fence:

```json
{
  "schema": "vt-image-manifest.v1",
  "project": "romeo-and-juliet-prologue-act1-sc1-excerpt",
  "sourceScribe": { "scriptId": "romeo-and-juliet-prologue-act1-sc1-excerpt", "version": "v1.00" },
  "staging": "story",
  "strategy": "C",
  "orientation": "16:9",
  "cards": "scenes",
  "aspectToken": "16:9 landscape image (1920x1080)",
  "title": "Romeo and Juliet",
  "subtitle": "Prologue and Act 1, Scene 1 (excerpt)",
  "closing": "End of the excerpt",
  "references": [
    { "name": "sampson", "type": "character", "firstCut": "RJ-S03-C02" }
  ],
  "cuts": [
    {
      "cutId": "RJ-S01-ROOT",
      "sceneId": "scene-001",
      "clipId": "clip-001-001",
      "role": "title",
      "referenceNames": [],
      "chars": 1712,
      "prompt": "16:9 landscape image (1920x1080), full-bleed, for the stage drama Romeo and Juliet. Cut RJ-S01-ROOT: …"
    }
  ]
}
```

`cards` is `scenes`, `first-last` or `none` (`scenes` when the field is missing); with `none` the manifest has no `title`, `subtitle` or `closing` and no cut has the role `title` or `closing`. `cuts` is in playback order, one entry per picture, `clipId` is the one clip that carries it, `chars` equals the length of `prompt`, and `references[].firstCut` is the first cut in the list that has the name in `referenceNames`.

**Schema `vt-image-manifest.v2` (the one this version writes).** It is the block above with `"schema": "vt-image-manifest.v2"`, `cuts` holding only the **generated** pictures (it may be empty), and two added keys: `plan` (every entry, section 3b) and `rules` (a record of the rules the user gave). Example:

```json
{
  "schema": "vt-image-manifest.v2",
  "cuts": [],
  "plan": [
    { "entryId": "M01", "scope": "clip", "clipId": "clip-002-003", "kind": "capture",
      "words": "Across the top is the toolbar. Load brings back a saved Scribe, Generate Image makes a picture, and Create and Play runs your Scribe.",
      "mustShow": ["toolbar", "Load", "Generate Image", "Create and Play"],
      "page": "http://localhost:5001/app", "frame": { "mode": "tight", "width": 1920, "height": 1080, "minCropWidth": 560 } },
    { "entryId": "M02", "scope": "clip", "clipId": "clip-004-001", "kind": "upload", "file": "media/intro.mp4", "mediaType": "video",
      "span": { "toClipId": "clip-004-004" } },
    { "entryId": "M03", "scope": "clip", "clipId": "clip-004-005", "kind": "none" },
    { "entryId": "M04", "scope": "scene", "sceneId": "scene-006", "kind": "placeholder", "wantKind": "generated" }
  ],
  "rules": [ { "rule": "every named button = capture", "scenes": ["scene-002"] } ]
}
```

A v1 manifest (no `plan`) is still valid input for the merge step. In v2, a scene is **not** required to have a picture on its first clip, and the title and closing cards are plan entries like any other (a `generated` entry with role `title` or `closing`, or an `upload`).

## 7. Validation (run it, show the result)

In the commands below, `<this-skill>` is this skill's folder: `~/.claude/skills/image-manifest` (or `~/.agents/skills/...` on Codex; inside the `voicetalker-skills` plugin, `skills/image-manifest/` in the plugin's folder). First run the plan check that sits beside this skill file: `python3 -I <this-skill>/check_plan.py <manifest.md> <scribe.json>` (a v2 manifest only; it checks every plan entry against the Scribe and must print `RESULT PASS`). Then save the script below to the scratchpad and run `python3 -I check_manifest.py <manifest.md> <scribe.json>` (the generated pictures and their prompts). Then run the drift check that sits beside this skill file: `python3 -I <this-skill>/check_drift.py <manifest.md> <cast.md> --scribe <scribe.json>` (rules R1 to R7, R10 and R11 in rule 5 above; R10 is every speaking cast character shown, R11 is the previous speaker kept in frame, and both need `--scribe` or the check fails; R3, whole cast together, applies only to `studio` staging and is skipped for `story`, which it reads from the manifest's `"staging"`; R8, the photo gate, runs later on the merged Scribe). With no cast file, say the drift check was not run and why; do not call the manifest fully checked. Do not report success until **both** print `RESULT PASS`.

```python
import json, re, sys, collections
FENCE = chr(96) * 3
md = open(sys.argv[1], encoding="utf-8").read(); sc = json.load(open(sys.argv[2]))
blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, md, re.S)
ok = True
def bad(m):
    global ok; ok = False; print("FAIL", m)
if not blocks: sys.exit("FAIL no json block")
m = json.loads(blocks[-1])
if m.get("schema") not in ("vt-image-manifest.v1", "vt-image-manifest.v2"): bad("schema")
V2 = m.get("schema") == "vt-image-manifest.v2"  # v2: media are optional; check_plan.py checks the plan
clips = {c["clipId"]: (s["sceneId"], i) for s in sc["scenes"] for i, c in enumerate(s["clips"])}
scenes = sc["scenes"]
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FIXED = "Fill the whole frame edge to edge: no white bar, no black bar, no letterbox, no border and no panel along any edge."
seen_cut, seen_clip, first, uses = set(), set(), {}, collections.Counter()
if m["aspectToken"] not in ("16:9 landscape image (1920x1080)", "9:16 portrait image (1080x1920)", "1:1 square image (1080x1080)"): print("NOTE custom aspect token:", m["aspectToken"])
for k in m["cuts"]:
    cid, cl = k["cutId"], k["clipId"]
    p = k["prompt"]
    if cid in seen_cut: bad("duplicate cut " + cid)
    seen_cut.add(cid)
    if cl not in clips: bad("clip not in Scribe: " + cl)
    elif clips[cl][0] != k["sceneId"]: bad("sceneId mismatch " + cid)
    if cl in seen_clip: bad("two cuts on one clip " + cl)
    seen_clip.add(cl)
    if len(p) != k["chars"]: bad("chars wrong %s: %d vs %d" % (cid, len(p), k["chars"]))
    if len(p) > 2000: bad("over 2000 characters: %s (%d)" % (cid, len(p)))
    if not p.startswith(m["aspectToken"]): bad("prompt must start with the aspect token: " + cid)
    if ("Cut " + cid + ":") not in p: bad("prompt lacks 'Cut %s:'" % cid)
    if FIXED not in p: bad("fixed clause missing " + cid)
    r = k.get("referenceNames", [])
    if len(r) > 5 or len(set(r)) != len(r): bad("referenceNames over 5 or repeated " + cid)
    for n in r:
        if not NAME.match(n): bad("bad name %r in %s" % (n, cid))
        uses[n] += 1; first.setdefault(n, cid)
    if k["role"] in ("title", "closing"):
        if "Lettering" not in p: bad("card has no Lettering instruction " + cid)
        if "NO TEXT of any kind" in p: bad("card forbids text " + cid)
        if "A Centerbeam AI production, built on VoiceTalker" not in p: bad("card lacks the credit " + cid)
        want = m["title"] + '"' if k["role"] == "title" else m["closing"]
        if want not in p: bad("card lacks its exact text %r in %s" % (want, cid))
        if k["role"] == "title" and m["subtitle"] not in p: bad("title card lacks the subtitle " + cid)
    elif "NO TEXT of any kind" not in p and "Lettering" not in p: bad("neither NO TEXT nor lettering " + cid)
by_clip = {k["clipId"]: k for k in m["cuts"]}
for s in scenes:
    if not V2 and s["clips"][0]["clipId"] not in by_clip: bad("first clip of scene has no picture: " + s["sceneId"])
cards = m.get("cards", "scenes")
if cards not in ("scenes", "first-last", "none"): bad("cards must be scenes, first-last or none")
if cards == "none":
    if any(k["role"] in ("title", "closing") for k in m["cuts"]): bad("cards is none but a cut has the role title or closing")
elif not V2:
    if by_clip.get(scenes[0]["clips"][0]["clipId"], {}).get("role") != "title": bad("the first clip of the first scene must carry the title card")
    if by_clip.get(scenes[-1]["clips"][0]["clipId"], {}).get("role") != "closing": bad("the first clip of the last scene must carry the closing card")
order = {c["clipId"]: n for n, c in enumerate(c for s in scenes for c in s["clips"])}
if [k["clipId"] for k in m["cuts"]] != sorted((k["clipId"] for k in m["cuts"]), key=order.get): bad("cuts are not in playback order")
ref = {r["name"]: r for r in m["references"]}
for n, cid in first.items():
    if n not in ref: bad("reference not in table: " + n)
    elif ref[n]["firstCut"] != cid: bad("firstCut of %s is %s but the first picture listing it is %s" % (n, ref[n]["firstCut"], cid))
    if uses[n] < 2: bad("name used on one picture only (give it no name): " + n)
for n in ref:
    if n not in first: bad("reference in table never used: " + n)
print("pictures", len(m["cuts"]), "references", len(ref), "longest prompt", max([k["chars"] for k in m["cuts"]] or [0]))
for n, cid in first.items(): print("  key frame of %-14s %s (used on %d)" % (n, cid, uses[n]))
words = sum(len(c["text"].split()) for s in scenes for c in s["clips"])
wpm = sc["settings"].get("defaultScrollWpm", 145)
print("estimated minutes %.1f, pictures per minute %.1f" % (words / wpm, len(m["cuts"]) / max(words / wpm, 0.1)))
print("RESULT", "PASS" if ok else "FAIL")
```

Also check by eye and say so in the report: each key frame is a clean, neutral introduction of its subject; every character is described the same way each time; the style and avoid text are identical; the title and closing cards show the exact words.

## 8. Report

Where the manifest is (full path); the staging (`studio`, `story` or mixed) and why; the strategy and orientation used and whether the user chose or you did; counts; the key references table; the validation result line by line; the style sentence; anything unresolved. The plan by the numbers (entries by kind, clips with no entry) and every rule used. Every part of this plan can be repaired singly or wholly (section 3c). Next step: run the capture step for the `capture` entries (and `screen-cap-video` for screen videos), then the merge step (`merge-media`) with this manifest and the Scribe.

## 9. Making the pictures (optional, outside the app)

Normally VoiceTalker's **Batch Media** makes the pictures after Step 3. If the user wants them made elsewhere (ChatGPT image generation, Google Nano Banana): make one cut at a time in ledger order, pass the prompt unchanged plus the key frame images of the names it lists, check the picture against the manifest (face, clothing, setting, exact lettering on cards), save it with the cut ID in the file name, and move on only when the user says next. Do not claim an integration or model exists that you have not verified.

## 10. Boundaries

Scribe words, voices and structure belong to Step 1; placing prompts in the Scribe belongs to Step 3. Do not generate audio, edit the Scribe, change the app, commit or publish.
