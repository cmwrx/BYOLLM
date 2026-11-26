---
name: menu
version: 3.2.8
description: >-
  Shows an ASCII menu of every VoiceTalker skill in two sections: Basic (no Python) and Advanced (Python 3.8 or later required). The person picks a number; the menu asks for that skill's
  parameters one at a time (each with numbered options and a proposed answer), then runs the skill. Works in
  any order, can be used again and again in a session (it remembers the files already named), and never reads or
  changes a file the person did not name. Works the same whether the skills are installed as separate folders or as
  the VoiceTalker plugin. Use when the person types /menu (in the plugin /voicetalker-skills:menu), or asks for the menu, the
  list of VoiceTalker skills, or "what can I run".
---

# VoiceTalker Menu (v3.2.8)

A launcher. It does no work itself: it shows the menu, collects the parameters for the skill the person picks, and runs that skill.

## 1. Rules

1. **Show the menu first**, in the layout that fits the screen (section 2b): in colour where the host can draw it (section 2a), else the wide block of section 2 or the compact block of section 2b (a fenced code block, nothing added inside it). Then ask one question, as plain text: `Choose a number (or S for scenarios, ? for usage, 0 to exit):`
1a. **Usage patterns (section 3b).** On `?`, show the whole usage view of section 3b in the layout that fits the screen, then ask the menu question again. After the person picks a number, first show that skill's row and pattern lines from the same layout, with the legend's first line above them, then ask the first missing parameter.
2. **One question at a time.** Each question lists numbered options (1, 2, 3) with the proposed answer first, so the person can reply with a number, `yes` or `defaults`. Never ask two things in one message.
3. **Never assume.** Ask for every required parameter in the table in section 3 that the person has not already given. Do not search for files; ask for the path. Read only files the person names.
4. **Remember within the session.** Keep the last Scribe, cast file, manifest, image folder, app address and output folder the person named, and offer them as the proposed answer ("Use `my-story-scribe-v1.00.json` again? 1 yes, 2 another file").
5. **Confirm, then run.** Before running, show one line: `Run <skill> on <inputs>?` with `1 Run`, `2 Change something`, `3 Back to the menu`. On 1, call the skill the way the host calls skills (the Skill tool in Claude Code, `$name` in Codex, `/name` in Grok Build, `@name` in ChatGPT), by the name the host lists it under, passing the parameters as its argument line. When the skills come from the VoiceTalker plugin, the host may list each name with the plugin's prefix (for example `<plugin>:scribe`): use the name exactly as listed. Skills that need a sign-in, a browser or a paid batch say so themselves; do not skip their questions.
6. **After the skill finishes**, say in one line what it saved (full path) and what the usual next step is (section 4), then show the menu again. Do not run the next step unasked.
7. **If a skill is not installed**, say so, give the install steps from the README, section 2: `README.md` at the top of the plugin's folder (it comes with the plugin), or `docs/VOICETALKERS/SKILLS/README.md` in the VoiceTalker project; then return to the menu.
8. **Python check for Advanced.** The first time in a session the person picks an Advanced number (7 to 14), and has not said they have Python 3.8 or later, ask once: `Advanced skills need Python 3.8 or later. Check with: python3 --version`, with `1 I have it`, `2 I do not (show how to install it)`, `3 Back to the menu`. On 2, give the install steps from the README section "Before you start: Python 3 is required" and return to the menu. Basic numbers (1 to 6), 15 `soundscape`, 16 and 16B `film-critic`, and 17 `codeumentation` (they need no Python) are never asked this. For 16 and 16B on a recorded video, ffmpeg is needed to take stills and read the sound (or give a transcript and stills instead). For 12 and 13 add: Google Chrome and Pillow are also needed (13 also needs ffmpeg). Pillow is the Python picture library the screen-capture scripts use to crop and save shots; check with `python3 -c "import PIL; print(PIL.__version__)"`, install with `python3 -m pip install Pillow` (README, "Only for the screen-capture skills"). If the host cannot run commands (a plain chat), say once that the Advanced skills will write their files but every `RESULT` line is unverified, and let the person choose.
9. No emojis. Plain text only, except the coloured menu of section 2a.
10. **The same menu as a page.** `app/index.html` (the VoiceTalker Agent Skills app, in the plugin's `app/` folder) shows this menu as a tree, builds each skill's prompt for the person's own agent, and keeps a run order. Its data is `app/agent-skills.json`; when a skill, number or scenario changes here, change that file too.

## 2. The menu (print this block verbatim)

Two sections. **Basic** skills need no Python. **Advanced** skills run Python 3.8 or later on the person's computer (the writing steps still save their files without it, but nothing is checked).

```
+==============================================================================+
|                     V O I C E T A L K E R   S K I L L S                      |
|                Centerbeam AI  -  skill set v3.2.8  -  VT 1.08                |
+==============================================================================+
|                                                                              |
|  BASIC  (no Python needed)                                                   |
|   1  scribe-wizard     short brief, 1 to 3 speakers  ->  Scribe JSON         |
|   2  comic-strip       panel script  ->  comic Scribe JSON                   |
|   3  existing-images   place pictures you already own                        |
|   4  characters        cast: voices, delivery, looks            (optional)   |
|   5  scribe            document or story  ->  Scribe JSON                    |
|   6  scribe-reviewer   review a Scribe: ranked defects, read-only            |
|                                                                              |
|  ADVANCED  (Python 3.8 or later required: python3 --version)                 |
|   ADD PICTURES AND MEDIA                                                     |
|   7  image-manifest    plan the MEDIA for every scene and clip, any mix      |
|   8  merge-media       ONE merge: plan -> pictures, shots, videos, none      |
|   9  gen-svg           animated SVG pictures                                 |
|  10  gen-gpt-images    ChatGPT prompt set (JPG) from the media plan          |
|  11  gen-frames        timed flipbook frames and single-frame holds          |
|   CAPTURE A REAL APP  (also needs Google Chrome and Pillow)                  |
|  12  screen-cap        screen shots of the plan, checked shot by shot        |
|  13  screen-cap-video  screen video + the media cut sheet (also ffmpeg)      |
|   VIDEO INTO A SCRIBE                                                        |
|  14  videotalker-import   VideoTalker scene list  ->  media cut sheet        |
|   SOUND AND MUSIC                                                            |
|  15  soundscape        subagent sound design: Scribe or brief -> plan        |
|   CRITIQUE AND REPAIR                                                        |
|  16  film-critic       subagent video critique: Scribe, video or brief       |
|  16B   balcony review  Siskel & Ebert style: thumbs + edit score             |
|   MAINTAIN                                                                   |
|  17  codeumentation    code + every doc a change touches, one pass           |
|                                                                              |
|   S  scenarios (step-by-step recipes)                0  exit                 |
|                                                                              |
+------------------------------------------------------------------------------+
|  Any order. Any number of times. Every skill saves a NEW file.               |
+==============================================================================+
```

## 2a. The menu in colour (only where the host can draw it)

If the host has a tool that draws an inline visual or widget (for example `show_widget` in the Claude app and on claude.ai), draw the menu with it instead of the plain block: the same lines, the same text and the same spacing as section 2, in a monospace font on a dark terminal-style panel (`#1b1b1b`), with these colours:

| Part | Colour |
|---|---|
| Box lines (the plus, equals, dash and bar characters) | teal `#5DCAA5` |
| `V O I C E T A L K E R   S K I L L S` | amber `#FAC775`, bold |
| `Centerbeam AI ... VT 1.08` | purple `#AFA9EC` |
| `BASIC (no Python needed)` | green `#97C459`, bold |
| `ADVANCED (Python 3.8 ...)` | pink `#ED93B1`, bold |
| Group headers (`ADD PICTURES AND MEDIA`, `CAPTURE A REAL APP ...`, `VIDEO INTO A SCRIBE`, `SOUND AND MUSIC`, `CRITIQUE AND REPAIR`, `MAINTAIN`) | blue `#85B7EB` |
| Numbers and `S` | amber `#FAC775` |
| Skill names | white `#ffffff` |
| Descriptions | gray `#B4B2A9` |
| `(optional)` and the footer line | dark gray `#888780` |
| `0  exit` | red `#F09595` |

**Fit the screen.** Make the widget responsive with a CSS container or media query: from about 600 px wide, draw the 80-column box exactly as in section 2; below that (a phone), draw a stacked list instead, with no box lines and nothing scrolling sideways: the section headers (`BASIC`, `ADVANCED`, the six group headers) in their colours, then one row per skill with the number and the skill name on the first line and the description on a second, smaller line, then `S scenarios` and `0 exit`. Same text and colours in both, except that on a phone no word is letter-spaced: write `VOICETALKER SKILLS` and `USAGE`, not `V O I C E T A L K E R   S K I L L S` or `U S A G E`, with normal letter spacing.

**Tap to choose.** Where the widget can send a message to the chat (for example `sendPrompt` in the Claude app), make every row, `S` and `0` tappable, and add a `? usage` button beside them: a tap sends just the number or character (`7`, `16B`, `S`, `?`, `0`), exactly as if the person had typed it. Typing still works. Rows need a tap target of at least 44 px high on a phone.

The picture only shows the menu, so ask the question as plain text after it. If the host has no such tool (a terminal, Codex, Grok Build, ChatGPT or another plain chat), or the drawing fails, print the plain block of section 2. Never print colour escape codes (ANSI) as text.

## 2b. Picking the layout, and the compact text menu

| Host | Layout |
|---|---|
| Can draw a widget (Claude app, claude.ai) | Section 2a: the box on desktop, the stacked list on a phone, both tappable |
| A terminal, an IDE, or a desktop chat without widgets | Section 2: the wide 80-column box |
| A phone chat without widgets, or the host says the screen is narrow | The compact block below |

The person can always choose: `menu wide` prints section 2, `menu compact` prints the block below, and the choice holds for the rest of the session. The compact block is at most 40 characters wide, so it does not wrap on a phone. Print it verbatim in a fenced code block:

```
VOICETALKER SKILLS  v3.2.8  VT 1.08
Centerbeam AI

BASIC  (no Python)
 1 scribe-wizard   brief -> Scribe
 2 comic-strip     panels -> Scribe
 3 existing-images your own pictures
 4 characters      cast (optional)
 5 scribe          story -> Scribe
 6 scribe-reviewer review a Scribe

ADVANCED  (Python 3.8+)
 Pictures and media
 7 image-manifest  plan the media
 8 merge-media     one merge
 9 gen-svg         animated SVG
10 gen-gpt-images  ChatGPT prompts
11 gen-frames      timed frames + holds
 Capture a real app (Chrome, Pillow)
12 screen-cap      screen shots
13 screen-cap-video screen video
 Video into a Scribe
14 videotalker-import cut sheet
 Sound and music
15 soundscape      sound plan (subagent)
 Critique and repair
16 film-critic     video critique
16B balcony review Siskel & Ebert style
 Maintain
17 codeumentation  code + docs, one pass

 S scenarios        0 exit
```

## 3. Parameters to ask, by number

Ask only what is missing. `R` = required, `O` = optional. The skill itself asks its own detailed questions afterwards (voices, picture rule, camera, and so on); the menu asks only what it needs to start.

| # | Skill to run | Parameters, in the order to ask them |
|---|---|---|
| 1 | `scribe-wizard` | R brief or goals file (or "I will describe it now"); O output folder |
| 2 | `comic-strip` | R panel script or idea; O cast file |
| 3 | `existing-images` | R Scribe `.json`; R folder or list of the pictures; O orientation (16:9 or 9:16) |
| 4 | `characters` | R input file (text, Markdown, Word, PDF, PowerPoint or JSON); O an earlier cast file to reuse |
| 5 | `scribe` | R input file; O cast file; (the skill asks INTRO/OUTRO: both, one, neither) |
| 6 | `scribe-reviewer` | R Scribe `.json`; O the source file it was made from; O an earlier version of the Scribe (for a diff review); O effort level: low, medium, high or max (default medium). It only reports, unless you ask for fixes. Run it in a fresh session, not the one that wrote the Scribe |
| 7 | `image-manifest` | R Scribe `.json`; O cast file; O your own media files; (the skill asks the picture rule, orientation and which media, one question at a time) |
| 8 | `merge-media` | R Scribe `.json`; R image manifest (the media plan) or media cut sheet `.md` or `.json` (the files must sit under the Scribe's folder); run after the screen shots are approved |
| 9 | `gen-svg` | R at least one of: cast file, Scribe, image manifest, your pictures, or a written description; O output folder |
| 10 | `gen-gpt-images` | R image manifest `.md` (the media plan); O which pictures (default all); O JPG or PNG (default JPG); O cast file; (the skill asks them one at a time, then saves the JSON prompt set) |
| 11 | `gen-frames-manifest` | R Scribe `.json` (or an existing frames manifest); O your images; O aspect ratio 16:9, 9:16 or 1:1 (default 16:9); O frame plan (three matched frames by default, or selective holds and cuts); O companion manifest or native Scribe handoff; O speech-bubble planning. The skill asks the rest; then `n` handles the next clip |
| 12 | `screen-cap` | R image manifest (the media plan) `.md`; R the Scribe it was made for; R address of the page to capture (any web app; macOS: port 5000 is AirPlay and answers 403, ask for the real one); O output folder. It asks you about every shot as it is taken |
| 13 | `screen-cap-video` | R Scribe `.json`; R app address and port; O video plan or shot list to follow; O completed run (`…-completed.json` or transcript) for real lengths; (the skill asks files, orientation, camera, effects, colour, frame rate; then writes the cut sheet) |
| 14 | `videotalker-import` | R VideoTalker scene list `.json`; R Scribe `.json` built from the same narration; O final or draft files |
| 15 | `soundscape` | R source: `file` (Scribe `.json`, or a sound brief `.md`, `.txt`, `.docx` or `.pdf`), `url`, `paste`, or `current session` (default: the Scribe or brief already in this conversation); O run timings (`.txt` or `.srt` from a completed run); O audio folder (default `audio` next to the Scribe); O apply: `no` (default, the plan only) or `yes` (a Scribe only: a new versioned Scribe with the added sounds). It runs as a subagent and never changes a sound that is already there |
| 16 | `film-critic` | R source: `file` (Scribe `.json`, recorded video `.mp4`, `.mov` or `.webm`, screenplay, or a video brief `.md`, `.txt`, `.docx` or `.pdf`), `url`, `paste`, or `current session` (default); O mode: `critique` (default) or `loop` (review and repair until you are satisfied; see scenario 15); O run timings; O an earlier version or critique; O your own change notes; O repair by: `agent 2` (default) or `subagent` (asks you to approve each change). It runs as a subagent; read-only unless you approve changes |
| 16B | `film-critic`, mode `balcony` | The same source as 16. The Siskel & Ebert style review: two invented critics, thumbs up or down, and the final edit score (0 to 100) with its history across loops |
| 17 | `codeumentation` | O the change: `current session` (default: the changes made in this conversation), a file (notes, a diff, a spec), a URL, or pasted text; O project root (default: the project open in this session); O mode: `apply` (default) or `list` (show every file that would change, change nothing); O version: keep (default) or a new number. It ends with an independent subagent gap check |

Questions to open with when the person is unsure which file is current: "Have you edited this Scribe by hand in VoiceTalker since the file on disk was saved? 1 No, 2 Yes (save it from VoiceTalker first and give me that file)."

## 3a. What each skill accepts

When the person asks what a skill accepts (or `?` and a number), show its row. `no` means the skill does not say it reads that kind of input: ask for a file instead.

| # | Skill | File | URL | Pasted text | Current conversation |
|---|---|---|---|---|---|
| 1 | `scribe-wizard` | brief or goals `.md` | no | the brief or goals | yes: describe it in answers to its questions |
| 2 | `comic-strip` | panel script; cast file | no | the panel script or a comic idea | no |
| 3 | `existing-images` | Scribe `.json`; the pictures (a folder or a picture list) | no | the list of picture paths | no |
| 4 | `characters` | text, Markdown, Word, PDF, PowerPoint or JSON; an earlier cast file | no | no | no |
| 5 | `scribe` | text, Markdown, Word, PDF, PowerPoint or JSON; cast file | no | no | no |
| 6 | `scribe-reviewer` | Scribe `.json`; source; an earlier version | no | the Scribe JSON | no |
| 7 | `image-manifest` | Scribe `.json`; cast file; your own media files | no | no | no |
| 8 | `merge-media` | Scribe `.json`; media plan or media cut sheet | no | no | no |
| 9 | `gen-svg` | cast file, Scribe, image manifest or your pictures | no | a written description | no |
| 10 | `gen-gpt-images` | image manifest `.md`; cast file | no | no | no |
| 11 | `gen-frames-manifest` | Scribe `.json` or a frames manifest; your images | no | no | no |
| 12 | `screen-cap` | image manifest `.md`; the Scribe | the page to capture | no | no |
| 13 | `screen-cap-video` | Scribe `.json`; video plan or shot list; a completed run | the app address and port | no | no |
| 14 | `videotalker-import` | VideoTalker scene list `.json`; Scribe `.json`; the scene videos | no | no | no |
| 15 | `soundscape` | Scribe `.json` or a sound brief (`.md`, `.txt`, `.docx`, `.pdf`); run timings | a Scribe JSON or a brief | the Scribe JSON or the brief | yes (the default): the Scribe or brief already in this chat |
| 16, 16B | `film-critic` | Scribe `.json`, recorded video, screenplay or video brief; run timings; an earlier version | a Scribe, a brief or a page (a video link only if the host can download it) | the Scribe JSON, a script or the brief | yes (the default): the Scribe, video or brief already in this chat |
| 17 | `codeumentation` | notes, a diff or a spec of the change; the project folder | a spec or an issue page | a description of the change | yes (the default): the changes made in this chat |

## 3b. Usage patterns

The parameters of section 3 and the inputs of section 3a, written the way command-line usage is written, inside the full menu: header, sections, group headers, every skill with its description, the `S ? 0` line and the footer. Never drop any of these.

**Layout.** Pick it as in section 2b:

- **Widget, wide (about 600 px or more):** the wide block below, drawn in colour on the dark panel of section 2a, with the colours of section 2a plus these for the patterns: `<required>` teal `#5DCAA5`, `[optional]` blue `#85B7EB`, the `|` and `...` signs dark gray `#888780`, `url`, `"text"`, `"idea"`, `"paths"`, `"json"` and `chat` pink `#ED93B1`, the `U S A G E` title and legend gray.
- **Widget, phone:** the stacked list of section 2a with the same header (plus `USAGE`; no letter-spaced words on a phone) and the legend, then, under each skill's name and description, its pattern on a third line (wrapped, never scrolling sideways), coloured as above; then `S`, `? usage` and `0 exit` as tappable buttons and the footer.
- **No widget:** the wide block below in a terminal or on a desktop, the compact block on a phone (`menu wide` and `menu compact` switch). Print it verbatim in a fenced code block.

Wide:

```
+==============================================================================+
|                     V O I C E T A L K E R   S K I L L S                      |
|                Centerbeam AI  -  skill set v3.2.8  -  VT 1.08                |
|                                  U S A G E                                   |
+==============================================================================+
|                                                                              |
|  <x> required   [x] optional   a|b one of   x... one or more                 |
|  file.json a file   url a web address   "text" pasted   chat this chat       |
|  source = .txt .md .docx .pdf .pptx .json                                    |
|                                                                              |
|  BASIC  (no Python needed)                                                   |
|   1  scribe-wizard     short brief, 1 to 3 speakers  ->  Scribe JSON         |
|        <brief.md|"text"|chat> [out/]                                         |
|   2  comic-strip       panel script  ->  comic Scribe JSON                   |
|        <script.md|"idea"> [cast.md]                                          |
|   3  existing-images   place pictures you already own                        |
|        <scribe.json> <pics/|"paths"> [16:9|9:16]                             |
|   4  characters        cast: voices, delivery, looks (optional)              |
|        <source> [cast.md]                                                    |
|   5  scribe            document or story  ->  Scribe JSON                    |
|        <source> [cast.md]                                                    |
|   6  scribe-reviewer   review a Scribe: ranked defects, read-only            |
|        <scribe.json|"json"> [source] [old.json] [low|medium|high|max]        |
|                                                                              |
|  ADVANCED  (Python 3.8 or later required: python3 --version)                 |
|   ADD PICTURES AND MEDIA                                                     |
|   7  image-manifest    plan the MEDIA for every scene and clip, any mix      |
|        <scribe.json> [cast.md] [media...]                                    |
|   8  merge-media       ONE merge: plan -> pictures, shots, videos, none      |
|        <scribe.json> <plan.md|cuts.json>                                     |
|   9  gen-svg           animated SVG pictures                                 |
|        <cast|scribe|plan|pics|"text">... [out/]                              |
|  10  gen-gpt-images    ChatGPT prompt set (JPG) from the media plan          |
|        <plan.md> [pics...] [jpg|png] [cast.md]                               |
|  11  gen-frames        timed flipbook frames and single-frame holds          |
|        <scribe.json|frames.json> [pics...] [16:9|9:16|1:1]                   |
|        [frames=3] [bubbles=on|off]                                           |
|   CAPTURE A REAL APP  (also needs Google Chrome and Pillow)                  |
|  12  screen-cap        screen shots of the plan, checked shot by shot        |
|        <plan.md> <scribe.json> <url> [out/]                                  |
|  13  screen-cap-video  screen video + the media cut sheet (also ffmpeg)      |
|        <scribe.json> <url:port> [shots.md] [run.json]                        |
|   VIDEO INTO A SCRIBE                                                        |
|  14  videotalker-import  VideoTalker scene list  ->  media cut sheet         |
|        <scenes.json> <scribe.json> [videos/]                                 |
|   SOUND AND MUSIC                                                            |
|  15  soundscape        subagent sound design: Scribe or brief -> plan        |
|        [scribe.json|brief.md|url|"text"|chat] [run.txt] [audio/] [apply]     |
|   CRITIQUE AND REPAIR                                                        |
|  16  film-critic       subagent video critique: Scribe, video or brief       |
|        [scribe.json|video.mp4|brief.md|url|"text"|chat] [critique|loop]      |
|        [run.txt] [old] [notes] [agent2|subagent]                             |
|  16B   balcony review  Siskel & Ebert style: thumbs + edit score             |
|        same source as 16, mode balcony                                       |
|   MAINTAIN                                                                   |
|  17  codeumentation    code + every doc a change touches, one pass           |
|        [change.md|url|"text"|chat] [root/] [apply|list] [version]            |
|                                                                              |
|   S  scenarios   ?  usage   0  exit                                          |
|                                                                              |
+------------------------------------------------------------------------------+
|  Any order. Any number of times. Every skill saves a NEW file.               |
+==============================================================================+
```

Compact (at most 40 characters wide):

```
VOICETALKER SKILLS  v3.2.8  VT 1.08
Centerbeam AI                USAGE

<x> required  [x] optional
a|b one of    x... one or more
url  "text" pasted  chat this chat
source = txt md docx pdf pptx json

BASIC  (no Python)
 1 scribe-wizard   brief -> Scribe
   <brief.md|"text"|chat> [out/]
 2 comic-strip     panels -> Scribe
   <script.md|"idea"> [cast.md]
 3 existing-images your own pictures
   <scribe.json> <pics/|"paths">
   [16:9|9:16]
 4 characters      cast (optional)
   <source> [cast.md]
 5 scribe          story -> Scribe
   <source> [cast.md]
 6 scribe-reviewer review a Scribe
   <scribe.json|"json"> [source]
   [old.json] [low|medium|high|max]

ADVANCED  (Python 3.8+)
 Pictures and media
 7 image-manifest  plan the media
   <scribe.json> [cast.md] [media...]
 8 merge-media     one merge
   <scribe.json> <plan.md|cuts.json>
 9 gen-svg         animated SVG
   <cast|scribe|plan|pics|"text">...
   [out/]
10 gen-gpt-images  ChatGPT prompts
   <plan.md> [pics...] [jpg|png]
   [cast.md]
11 gen-frames      timed frames + holds
   <scribe.json|frames.json> [pics...]
   [16:9|9:16|1:1] [frames=3]
   [bubbles=on|off]
 Capture a real app (Chrome, Pillow)
12 screen-cap      screen shots
   <plan.md> <scribe.json> <url>
   [out/]
13 screen-cap-video screen video
   <scribe.json> <url:port>
   [shots.md] [run.json]
 Video into a Scribe
14 videotalker-import cut sheet
   <scenes.json> <scribe.json>
   [videos/]
 Sound and music
15 soundscape      sound plan (subagent)
   [scribe.json|brief|url|"text"|chat]
   [run.txt] [audio/] [apply]
 Critique and repair
16 film-critic     video critique
   [scribe|video|brief|url|"text"|chat]
   [critique|loop] [run.txt] [old]
   [notes] [agent2|subagent]
16B balcony review Siskel & Ebert style
   same source as 16, mode balcony
 Maintain
17 codeumentation  code + docs, one pass
   [change|url|"text"|chat] [root/]
   [apply|list] [version]

 S scenarios  ? usage  0 exit
Any order. Any number of times.
Every skill saves a NEW file.
```

## 4. Usual next step (say it after a run, do not run it)

| After | Next |
|---|---|
| 4 characters | 5 scribe (give it the cast file) |
| 1, 2 or 5 a Scribe | 6 scribe-reviewer (in a fresh session), then 7 image-manifest, or 12/13 if the Scribe narrates an app, or 9 gen-svg |
| 7 image-manifest | 10 gen-gpt-images (to make the pictures in ChatGPT), or 11 gen-frames (timed frames and holds), or 12 screen-cap (for the capture entries), 13 screen-cap-video (for screen videos), then 8 merge-media |
| 3 existing-images | In VoiceTalker: import the pictures and attach them |
| 12 screen-cap | 8 merge-media |
| 13 screen-cap-video | 8 merge-media (give it the cut sheet) |
| 14 videotalker-import | 8 merge-media (give it the cut sheet) |
| 15 soundscape | Make the new sounds from its generation list, save them in the audio folder, then run 15 again with apply `yes` (or place them in VoiceTalker's Sounds view); then Batch Media, Sounds Upload tab |
| 1, 2 or 5 a Scribe, or after a VoiceTalker run | 15 soundscape, when the episode needs fuller sound |
| 16 film-critic | Approve the recommended changes you want; 16 in mode `loop` makes them (agent 2 or the subagent) and runs 16B; repeat until you are satisfied (scenario 15) |
| 16B balcony review | Fix what would change the critics' minds (16, mode `loop`), record again, and run 16B again to compare the edit score |
| Any change to code or docs | 17 codeumentation, so every file that describes the change says the same thing |
| 17 codeumentation | Read its report; start a new session so agents load the updated skills; reinstall the plugin where it lists installed copies it could not reach |
| 8 merge-media | In VoiceTalker: open the merged Scribe, Load picture or video, then Batch Media for generated pictures; save; play it |
| 10 gen-gpt-images | In ChatGPT: key frames first, then the rest, in one conversation; then load the pictures in VoiceTalker as your own pictures (or 8 merge-media with an upload plan) |
| 6 scribe-reviewer | NEEDS FIXES: ask 6 for a fix pass (or fix it in VoiceTalker), then run 6 again. READY: 7 image-manifest, or open it in VoiceTalker |
| 11 gen-frames | On a compatible VoiceTalker build, open the versioned Scribe with timed `frames[]`, load its pictures, and record a short MP4 proof. Scenario 14 in the README covers companion-manifest handoff for older builds. |

## 5. S: scenarios

When the person picks S, read section 6 (typical scenarios, step by step) of the README: `README.md` at the top of the plugin's folder (it comes with the plugin), or `docs/VOICETALKERS/SKILLS/README.md` in the VoiceTalker project; if neither file can be read, say so and return to the menu. List the scenario titles as numbered options, and on a choice walk through its steps one at a time, offering the matching menu number at each step.

## 6. Boundaries

This skill shows a menu and gathers parameters. It does not read files the person did not name, create or change files itself, run a skill without the person's "Run", commit, or publish.
