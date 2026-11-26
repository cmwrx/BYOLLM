---
name: codeumentation
version: 3.2.8
description: OPTIONAL (any time a change is finished). Codeumentation(tm) is code plus documentation delivered as one thing. When the owner says "update the codeumentation", this skill finds every code and document file a change touches and brings all of them up to date in one pass - code, READMEs, workflow docs, version lines, counts and tables, menus, install notes, in-app Help, the changelog, plugin manifests, rebuilt packages and installed copies, slides and images - fixes the related gaps the change exposes, and reports what it changed and what it could not. It changes only what the change touches, keeps a copy of every file first, and ends with an independent subagent check for gaps.
---

# Codeumentation(tm)

**Definition.** Codeumentation is code and documentation treated as one deliverable. A change is not finished until every place that describes it says the same thing as the code: the code itself, every guide and help page that explains it, every version line and count that names it, every menu that lists it, and every package that ships it. "Update the codeumentation" is the owner's one-line command for that whole pass.

## What it touches

For the change in hand, check each of these and update the ones the change affects:

1. **Code:** the source files, their types and schemas, and the comments that explain the changed behaviour.
2. **READMEs and workflow docs:** every README, workflow document and guide that describes the change.
3. **Version lines:** every place the version is written (file headers, `version:` lines, manifests, menu headers), all saying the same number. Raise the version only for a release-sized change, and say so.
4. **Counts and tables:** "N skills", lists, tables, usage blocks, menus and their numbering (numbered in order, with nothing deprecated left in).
5. **Install notes:** install steps, requirements (Python, ffmpeg, browsers), and "check that it worked" lines.
6. **In-app Help:** the Help sections that describe the change, stating the app's current, actual behaviour and values, never planned ones.
7. **Changelog:** one dated header per release at the top; roll today's changes into the current release's entry instead of adding a second header for it; summarise, point to the release's docs folder, and list what was not changed and what was checked.
8. **Packages:** plugin manifests (every one, same name, version and description), rebuilt zips and plugin files, with the previous version's packages copied to the archive.
9. **Installed copies:** the copies the owner's agents load, where they can be reached; otherwise say how to reinstall.
10. **Slides, decks and images:** the ones that show the change; images that cannot be redrawn here are listed as not updated.
11. **Related gaps:** anything the change exposes as out of date or undocumented (a folder no guide mentions, a skill out of step with the version it depends on, a stale count elsewhere).

## Rules

1. **Only what the change touches.** Never change anything else, never rename or move the owner's files, never alter naming patterns. If the change conflicts with something existing, ask first.
2. **Copy before changing.** Keep a copy of every file before its first edit.
3. **Current truth only.** Docs and Help describe what the code does now.
4. **No tables in replies** unless the owner asks; numbered lists.

## Parameters

Ask only what is missing, one question at a time, with numbered options and the proposed answer first.

1. **The change** (required): `current session` (default: the changes made in this conversation since the last codeumentation pass), a file (notes, a diff, a spec), a URL, or pasted text.
2. **Project root** (default: the project open in this session).
3. **Mode:** `apply` (default) or `list` (show every file that would change, change nothing).
4. **Version:** keep, or raise to a named number (default: keep, unless the change adds or removes a feature or skill).

## Steps

1. **Inventory the change:** what was added, changed or removed, in one numbered list.
2. **Map it:** search the project for every file that names or describes each item (names, version numbers, counts, menu numbers, help ids). List them under the eleven headings above.
3. **Update** each file, keeping each file's own style and format.
4. **Rebuild** the packages and test that each one opens.
5. **Check:** run the project's type check or tests; search again for the old values (old version, old counts, old names) and fix any left.
6. **Independent gap check (subagent):** give a fresh subagent the inventory and the list of changed files, and ask it to find any place still out of date, any over-reach (a change nobody asked for), and any drift from the owner's intent. Fix what it confirms. Where the host has no subagent, do the check yourself and say it was not independent.
7. **Report:** what changed (by area), what was checked, and what was not updated and why (for example images that cannot be redrawn here, a website download, installed copies out of reach).
