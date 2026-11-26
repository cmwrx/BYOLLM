# Contributing

Thank you for helping improve VoiceTalker Agent Skills.

## How this repository is made

This repository is published from Centerbeam AI's source. Every release replaces `plugins/` and `docs/` with a fresh export, so a change made only here would be lost at the next release. Pull requests are welcome: we review them, apply the accepted change to the source, and it arrives here in the next release with credit to you.

## Issues

1. **Bug:** use the bug report form. Name the skill, the agent (Claude, ChatGPT, Codex, Gemini, Grok, Copilot or another), the skill set version, what you ran, and what you saw. Attach the smallest Scribe or brief that shows it; remove anything private first.
2. **Idea:** use the feature request form and say what it would let you do.
3. **Security:** never in a public issue; see [SECURITY.md](SECURITY.md).

## Pull requests

1. One change per pull request.
2. Keep each skill's rules: a skill saves a new file and never overwrites the user's; it asks one question at a time; it never runs without the user's go-ahead.
3. All skills share one version (the `version` line in every `SKILL.md` and the three plugin manifests); leave it as it is, we set it at release.
4. Update the codeumentation: every doc, menu and table your change touches (the plugin's `README.md`, `menu/SKILL.md`, `app/agent-skills.json`).
5. Run `python3 tools/check.py`; it must print `RESULT PASS`.
6. By opening a pull request you agree that your contribution is released under [LICENSE.txt](LICENSE.txt).
