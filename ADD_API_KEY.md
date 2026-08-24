# OpenAI API key — StoryLab AI Summaries

Strategy Lab's Helm publishing workflow does not use an AI API key. It sends
operator-approved, source-backed signals directly to The Helm.

`OPENAI_API_KEY` is reserved only for the separate AI Summaries feature. It is
used only after an operator explicitly presses Generate on a Daily or Weekly
summary. It never runs during feed fetching or source-only brief generation.

## Where the key goes

1. In the repository root, create a file named `.env` if it does not already
   exist.
2. Add this line, replacing the value with your private API key:

   ```env
   OPENAI_API_KEY=
   ```

3. Keep the Helm settings in the same file when their real values are ready:

   ```env
   HELM_STRATEGY_ENDPOINT=
   HELM_STRATEGY_API_KEY=
   ```

`.env` is ignored by Git, so do not put the key in `.env.example`, source
code, or a chat message.

## How daily and weekly summaries work

- A **Daily** summary uses only five-star sources that have not appeared in an
  earlier Daily summary for that flywheel group.
- A **Weekly** summary has its own source history. It includes every source
  that is new since the prior Weekly summary, even if that source already
  appeared in a Daily summary.
- When there is no new source material for a cadence, its Generate button is
  disabled. Existing summaries are never silently rewritten.

The integration sends only the saved source capsules to OpenAI and requests a
structured, fact-bounded response. API response storage is disabled; StoryLab
stores the generated text locally with the exact article IDs used.

## What happens next

Open the relevant Flywheel Brief, review its current source articles, and use
the Daily or Weekly Generate button. A new summary uses `gpt-5-mini`, then
appears on that same brief with the existing source evidence still visible.
Strategy Lab remains source-backed and local, and Helm publishing uses only
its own endpoint and key.
