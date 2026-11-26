---
name: characters
version: 3.2.8
description: >-
  STEP 0 of 3 (optional, runs BEFORE scribe). Reads the same input file (text, Markdown, Word,
  PDF, PowerPoint or JSON), finds every speaker and every character that appears, asks the user a few
  short questions, and writes a reusable cast file: for each character the voice, the eight prosody
  fields, the emotion arc, the attire and attributes, and the exact picture description and short tag
  that Step 2 uses for image prompts. Step 1 reads the cast for voices and delivery; Step 2 reads it for
  looks. It also records the staging of the production (studio, story or mini-play), which Step 2 uses.
  The same cast file can be reused in later Scribes of the same series.
---

# VoiceTalker Characters, Step 0 of 3 (v3.2.8, optional)

> **Numbering (v3.0 pipeline):** the steps are 1 characters (optional), 2 scribe, 3 `image-manifest` (the media plan), 4 `screen-cap` and `screen-cap-video`, 5 `merge-media`, 6 load in VoiceTalker. Where this skill says "Step 2" for the image manifest or "Step 3" for the merge, read Step 3 and Step 5.


Pipeline: **Step 0 this skill (optional)** → Step 1 `scribe` → Step 2 `image-manifest` → Step 3 `merge-media`.

Without a cast file, Step 1 casts voices by default and Step 2 invents looks from the text. With one, the same character has the **same voice, the same delivery and the same look** in every clip and every picture, and in every later Scribe that reuses the file.

This skill owns: who the characters are, what they sound like, how their feeling changes, what they wear and look like. It does **not** write the Scribe, image prompts or manifest, generates no audio or images, and changes no source file.

## 1. Rules

1. **No unrequested changes.** Do not alter, summarize or reorder the input. Invent nothing the input contradicts. Original faces only: never describe a real person or a performer's likeness, and never copy a trademarked character's look unless the user supplies it. **When the user supplies a photo of a real person** (a host, a guest), do not describe the face in writing: record the photo's file name in the cast as `referenceImage` and write the character as drawn `exactly as in the attached reference photo`. That photo must be attached as the character's reference before any picture is made (Step 3 stops and says so).
2. **Ask, one question at a time, each with your proposal**, and wait for the answer (section 3). If the user says "defaults" or "you choose", use the proposals and say so in the report. Never ask about something the input already settles.
3. State the saved file's full path in the report and that the input was not changed.
4. **No character drift, no undefined actors.** The cast file is the complete list of people who may ever appear in a picture. Every on-screen character gets a complete written look (every field of section 6) or a `referenceImage` photo, never "not described here" without a photo. Nobody who is not in the cast (a hand, a child, staff, an audience, a crowd) is ever drawn. How people are staged depends on the **staging** (section 3, question 1), which Step 2 reads from the cast file. `studio` (a podcast, interview, panel or tutorial in one fixed set): actors are never alone, and Step 2 draws the whole cast together in one fixed studio shot and reuses it for every picture that shows a person. `story` (a play, drama, film, storyboard or comic: scenes are different places) and `mini-play` (a short staged comedy with a small cast): each picture shows only the people who are in that moment of that scene, each one named, and a speaking character is always on screen when they speak; no one is drawn who is not in the cast.

## 2. Read the input and find the cast

Read the whole input file with the same methods as Step 1 (`.txt`, `.md` directly; `.docx` with pandoc or python-docx; `.pdf` with pdftotext; `.pptx` with python-pptx or markitdown; a `.json` Scribe or other JSON by its text fields). Then list:

- **Speakers**: everyone who speaks (speaker labels, quoted speech, a named host or announcer). Add the **Narrator** (reads headings, directions and the INTRO and OUTRO); for a non-fiction input the Narrator or Announcer may be the only voice.
- **On-screen characters**: speakers who will be seen, plus people or creatures that are named but silent and recur. A Narrator who is never seen is `onScreen: false`.
- **Key places and objects** that recur and need a fixed look (a street, a ship, a ring). They are cast too (type `place` or `object`) with a look but no voice.
- For each: how many speeches or mentions, and where they first appear (scene heading and the first words of that line).

If a cast file is supplied (for a series, or from an earlier run), load it first: reuse every character whose `speaker` matches, **unchanged**, ask only about new characters and about anything the user wants changed, and keep the old file's other characters in the new file marked `reused`.

## 3. Questions (one at a time, in this order, skip what is settled)

1. **World and look.** "The input is set in <period and place>. Shall pictures be <painterly illustration / realistic film still / line drawing / the user's style>? One sentence of style:" (propose one). This sentence becomes `world` in the cast and the Step 2 style. Also say how you read the **staging** and why: `studio`, `story` or `mini-play` (a short staged comedy with a small cast, mostly dialogue). Propose one; the user may change it. It becomes `staging` in the cast.
2. **The cast list.** Show a short table of the speakers and on-screen characters you found (name, speeches, first appearance, on screen or not). "Is this the right cast? Anyone to add, merge or drop?"
3. **Voices.** Show the proposed voice for each character (section 4) with a reason. "Keep these voices, or name changes? (Give a custom voice ID if you have one.)"
4. **Delivery and feeling.** For each character: persona in one line, the voice's character, and a proposed **emotion arc** (section 5). "Anything to change in how any character speaks or feels?" Ask this once for the whole cast, not once per character.
5. **Attire and attributes** for each on-screen character and each key place or object (section 6). "Keep these looks, or change any?"
6. **Reuse.** "Save this cast to reuse for the rest of the series? File name:" (default `<project>-cast.md` next to the input).

Ask nothing else. If the answer to a question changes the cast, update it and move on; do not repeat the question.


## 3a. Option: casting from a source (replace or add a character)

Use this when the user asks to replace a character they dislike, or to cast a new one, from a source they name (the original work, an article, a study of the characters). It changes nothing until the user picks.

1. **Read the source** the user gives (a web page or a file) and the current Scribe or cast. Note the role the character plays in the story: the scenes they are in, what they do and say, and who they talk to.
2. **Extract personas.** From the source, take 4 to 6 figures or types that could fill that role. For each, note in one line what the source says about them (quote briefly and name the source).
3. **Modernise each one** for the story's world:
   - a **modern, ordinary name** that fits the setting (first name and surname), never an archaic or source name;
   - the **story role** they would play, keeping every scene and function the replaced character has, plus the personal stake the source suggests;
   - a **natural look**: age, build, skin, hair, clothes with wear, one telling detail; ordinary and specific, never glamorous, and clearly different from every other character in the cast;
   - a **voice** that no other speaker uses. In casting, any voice VoiceTalker supports may be proposed, and one cast may mix them:
     - a built-in **Gemini** voice (`google`, `gemini-3.8-flash-tts`), or a **programmed Gemini voice**: a built-in voice shaped by written direction in the eight prosody fields and `ttsInstructions` (accent, age, texture, register, pace, attitude), so it sounds like this character and no one else. State the base voice and the direction in one line. 
     - an **OpenAI** voice (`openai`, `gpt-4o-mini-tts`: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer, verse, marin, cedar), each character keeping one provider, model and voice that belong together;
     - a **custom voice** from My Voices: a designed voice (made from a description), a cloned voice (made from a recording) or a VoiceTalker voice preset. Use its real ID or preset name only; never invent one. If it does not exist yet, describe the voice to make, record it as `customVoiceNote`, and give the character a built-in voice until the user supplies the ID;
     - **Me**: the user reads the part themselves (a manual turn, no TTS).
4. **Present them as a numbered bullet list**, one number per candidate, with these lines under each: the name and its source figure, the role, the look, and the voice with its kind (Gemini, programmed Gemini, OpenAI, custom or Me). No tables unless the user asks for one. Keep it short enough to read on a phone.
5. **Ask one question**: which one should replace the character (or "none"). Wait for the answer. If the user rejects the list or a part of it (for example the names), fix only that part and show the list again.
6. **Only after the user picks**, update the cast file with the new character (name, voice, prosody, look, `imageDescription`, `imageTag`, `referenceName`) and report what still has to change elsewhere: the character's name in the Scribe text, their voice in the Scribe, and every picture that shows them, which needs a new reference image first. Do not edit the Scribe or any picture; those belong to Steps 1 and 3 and need the user's go-ahead.

## 4. Voices and prosody (the hard rules)

Same compatibility rules as Step 1: provider, model and voice never mix.

- Default provider `google`, model `gemini-3.8-flash-tts`, voice from the verified Gemini list: `Kore`, `Orus`, `Charon`, `Algenib`, `Iapetus`, `Puck`, `Fenrir`, `Alnilam`, `Aoede`, `Autonoe`, `Zephyr`, `Laomedeia`, `Despina`, `Vindemiatrix`, `Achird`, `Rasalgethi`, `Achernar`, `Sulafat`. Each speaker has **one voice, different from every other speaker**, chosen by apparent age, gender, temperament and status. An OpenAI voice (`coral`, `onyx`, `ballad`, and so on, with `gpt-4o-mini-tts`) only if the user asks. A custom voice only with its real ID (`voice_…`); a custom voice name without an ID is recorded as `customVoiceNote` and the character uses the default until the user supplies the ID.
- The **eight prosody fields** for each speaker, written once and used on every clip of that speaker: `voiceAffect`, `tone`, `pacing`, `emotion` (the baseline; the arc changes it clip by clip), `pronunciation`, `pauses`, `emphasis`, `delivery`.
  - `pacing`: a words-per-minute figure suited to the character, suggested between about 120 and 190 wpm (slower for a stately, elderly, hurt or halting character; faster for urgent or excited speech). These are suggestions, not requirements.
  - `pauses`: describe the pauses the owner wants for this speaker (none, natural breaks between sentences, a breath at each ellipsis, a beat before a reveal). Pauses may be added according to the owner's direction.
  - `pronunciation`: a pronunciation guide for every hard name in the input (`Westenra is wes-TEN-ruh`) and the accent, stated once and kept consistent. Never respell the spoken text.
  - Describe behaviour, not mood labels: register, tempo, attitude, who the speaker is talking to, which words carry the stress. Each speaker must sound different from the others.
  - Gemini inline tags are not part of the cast; Step 1 adds them only when the input asks.

## 5. Emotion arc

For each character who speaks more than a few times, list the points where the feeling changes. Each point is `at` (the first 3 to 8 words of the line where it starts, copied exactly from the input), `emotion` (a short behavioural description) and an optional `instruction` (one sentence of extra direction for that line). A point applies from that line until the character's next point. Step 1 writes the `emotion` into the `emotion` style field of those clips (and the `instruction` into `ttsInstructions`). Keep it clean: no pause, beat or slow wording. Characters who speak once or twice need only the baseline.

## 6. Attire and attributes (for pictures)

For every `onScreen` character: `age`, `build`, `face` (shape, eyes, brows, skin), `hair`, `attire` (garments with colours and materials, in the period and setting), `props` (what they carry), `bearing` (posture and expression at rest). Then write two strings that Step 2 copies word for word:

- `imageDescription`: the full description in **300 characters or fewer**, used the first time the character is drawn;
- `imageTag`: the identifying features in **100 characters or fewer**, used in every later picture.

For a `place` or `object`: `imageDescription` (300 or fewer) and `imageTag` (100 or fewer) of how it looks. Faces are original; a fully invented person is described as not based on any real person. A character who is never seen has no look and `onScreen: false`.

For a character with a supplied photo: `look.face` and `look.hair` say `from the reference photo`, `referenceImage` holds the photo's file name (a `.jpg` or `.png` in the project folder), and `imageDescription` and `imageTag` give the role, attire and props plus the words `face, hair and build exactly as in the attached reference photo`; no facial feature is written.

`referenceName`: the lowercase hyphenated name Step 2 lists in `referenceNames` (`sampson`, `verona-street`), one per subject. Step 2 only uses a name that appears on two or more pictures.

## 7. Output: `<project>-cast.md`

Markdown for people, ending in one machine-readable block. Sections: **Header** (project, source file, date, provider and model, world sentence, staging); **Cast table** (speaker, role, voice, on screen, reference name); then **one block per character** with persona, voice and why, the eight prosody fields as a table, the emotion arc as a list (`at` → emotion), and attire and attributes; then the machine-readable block, last, exactly once:

```json
{
  "schema": "vt-cast.v1",
  "project": "romeo-and-juliet-prologue-act1-sc1-excerpt",
  "world": "Painterly cinematic illustration of Renaissance-era Verona, sun-bleached stone and terracotta palette, long soft light, warm light against deep shadow.",
  "staging": "story",
  "provider": "google",
  "model": "gemini-3.8-flash-tts",
  "characters": [
    {
      "speaker": "Sampson",
      "type": "character",
      "role": "speaker",
      "onScreen": true,
      "referenceName": "sampson",
      "persona": "A swaggering young Capulet servingman whose bluster covers his nerves.",
      "voice": { "provider": "google", "voice": "Algenib" },
      "prosody": {
        "voiceAffect": "Swaggering young servingman, bright and forward",
        "tone": "Boastful, cocky",
        "pacing": "Brisk and continuous, about 180 wpm",
        "emotion": "Bluster covering nerves",
        "pronunciation": "Clear English; Montague is MON-tuh-gyoo",
        "pauses": "Natural breaks between sentences",
        "emphasis": "Stress the insults and 'bite my thumb'",
        "delivery": "Comic bravado"
      },
      "emotionArc": [
        { "at": "A dog of that house", "emotion": "Rising bravado", "instruction": "" },
        { "at": "No, sir, I do not bite", "emotion": "Cornered cunning, pretending innocence", "instruction": "" }
      ],
      "look": {
        "age": "about 20", "build": "broad-shouldered", "face": "round face, brown eyes, thick brows",
        "hair": "short black curls", "attire": "plain work clothes with a muted red-brown livery tabard",
        "props": "sword at the hip, small round buckler on the left forearm", "bearing": "chin raised, chest out"
      },
      "imageDescription": "Sampson: young Capulet servingman, about 20, broad-shouldered, round face, brown eyes, short black curls, muted red-brown livery tabard over plain work clothes, sword sheathed at the hip, small round buckler on his left forearm; swaggering.",
      "imageTag": "Sampson: broad young Capulet servingman, red-brown livery, buckler on left arm"
    }
  ]
}
```

A silent narrator is `{"speaker": "Narrator", "type": "character", "role": "narrator", "onScreen": false, …}` with a voice and prosody but no `look`, `imageDescription` or `imageTag`. A place or object has `type` `place` or `object`, no `voice` and no `prosody`.

## 8. Report

Where the cast file is (full path); the cast table; the world sentence; the staging and why; which answers came from the user and which are defaults; anything unresolved (custom voice IDs, a character with no description). Next step: run **scribe** with the input file and this cast file.

## 9. Boundaries

Words, scenes and clips belong to Step 1; prompts and pictures to Steps 2 and 3. Do not generate audio or images, edit the input, change the app, commit or publish.
