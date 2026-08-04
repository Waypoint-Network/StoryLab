# Adding the AI API key — StoryLab AI Summaries

This is the one thing left to turn the AI Summaries panel (`/summaries`)
from example content into real, generated output. Everything else —
the standing instructions box, the 5-star article gathering, the
fact-bounded source formatting, the database storage — is already built
and working. This document is the whole remaining step.

## Which provider

**Anthropic (Claude).** The rest of StoryLab is already built around
Claude's voice and its FACT BOUNDARY / no-fabrication rules (see the
existing ✍ Story Brief panel), so this feature follows the same
provider rather than introducing a second one.

## Where the key goes

1. Get a key from [console.anthropic.com](https://console.anthropic.com)
   (Account → API Keys).
2. In the repo root (same folder as this file), copy `.env.example` to
   a new file named exactly `.env`.
3. Open `.env` and replace the placeholder:
   ```
   ANTHROPIC_API_KEY=sk-ant-...your real key...
   ```
4. Restart the dashboard server (`python core/server.py --config
   fan_atlas_insiders`). It reads `.env` automatically on startup —
   nothing else to configure, no environment variables to set by hand
   in PowerShell.

**This file will never be pushed to GitHub.** `.env` is listed in
`.gitignore` (confirmed, not just assumed) — `git status` will never show
it as a change to commit, and `git add -A` won't pick it up. Only
`.env.example` (the placeholder template, no real key in it) is tracked.

## What actually changes when the key is added

Right now, `core/ai_summary.py`'s `generate_summary()` function checks
for the key first. With no key, it returns the "No API key configured
yet" message you see in the dashboard. With a key present but nothing
else changed, it goes one step further — it gathers that category's
5-star articles and builds them into the same fact-bounded source
format the Story Brief panel already uses — then stops at a clearly
marked `TODO` and tells you how many articles it found.

The one remaining piece is writing the actual outbound call to Anthropic
inside that `TODO` — a small, self-contained addition (roughly 30-50
lines): send the instructions + source articles, get a response back,
save it, done. I deliberately didn't write and leave that code dormant
now, since it's real external-service code with real cost — better to
write and test it for real once the key exists. When you're ready, just
say so and I'll wire it in; nothing else in the app needs to change.

## Cost, once it's wired up

Each press of "Generate Summaries" will make one real, billed API call
— small (fractions of a cent to a few cents depending on how many
5-star articles are in that category), but real, and **only** when you
press the button. Nothing runs automatically or on a schedule.
