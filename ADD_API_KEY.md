# OpenAI API key — StoryLab AI Summaries

Strategy Lab's Helm publishing workflow does not use an AI API key. It sends
operator-approved, source-backed signals directly to The Helm.

`OPENAI_API_KEY` is reserved only for the separate AI Summaries feature. That
feature is not connected to OpenAI yet, so adding a key now does not make any
call, create any charge, or change the source-only brief workflow.

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

## What happens next

When we intentionally wire the AI Summaries feature to OpenAI, it will use
this local key only when an operator explicitly asks it to generate a summary.
Until then, Strategy Lab remains source-backed and local, and Helm publishing
uses only its own endpoint and key.
