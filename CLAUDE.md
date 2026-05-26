# StoryLab — Claude Code Project Brief
*Save as `CLAUDE.md` in the root of `roots-vs/storylab`. Paste as your first message when starting a new Claude Code session.*

---

## What StoryLab Is

**StoryLab** is a story intelligence platform. Its job is to sense, source, curate, and help craft stories that matter to specific people in their day-to-day roles — the athletic department marketing director trying to justify a new revenue program, the season-ticket holder planning an away-game trip, the real estate agent trying to close a relationship, the buyer deciding where to plant roots.

This is people-centric storytelling, not content marketing. The distinction matters:
- Content marketing asks: *what should we publish?*
- StoryLab asks: *what stories matter to this person right now, and what is the best way to carry them?*

StoryLab is the shared story intelligence engine across two companies:

**Waypoint** — turns college fan loyalty into revenue for university athletic departments. School-branded travel booking portals (GoCougsTravel.com, Mountaineer.Travel). Primary audiences: AD marketing directors and CMOs at P4 universities, and the fans themselves. Story intelligence brand: **Crowd Commerce**.

**Longitude** — real estate marketing for the Wasatch Back (Summit and Wasatch Counties, Utah). Audience: agents, brokers, buyers, and the business owner networks those agents serve. Story intelligence runs through the Longitude brand.

StoryLab serves both. Each company has its own feed registry, relevance rubric, editorial voice, and person-role definitions — but they share the same sensing, scoring, curation, and story-briefing engine.

---

## Related Repositories

| Repo | What it is | Relationship to StoryLab |
|------|-----------|--------------------------|
| `roots-vs/Waypoint-fan-graph` | Fan graph / Fan Atlas — PageRank analysis of WVU fan social networks | Will send audience signals TO StoryLab (Layer 4) |
| `roots-vs/Agent-Intelligencer` | Longitude's market intelligence tool — agent directory, movement tracking, PostgreSQL sync to Longitude Network | Parallel instance; shares architectural pattern with StoryLab |
| `roots-vs/longitude-network` | Longitude Network PostgreSQL database (3,669 agents) | Agent-Intelligencer reads from this; StoryLab may query it for Longitude person-role definitions |

Do not merge StoryLab into any of these repos. StoryLab is its own layer. The graph repos send signals in; they do not own the content logic.

---

## Operators

**Waypoint side:**
- **Matt Sanders** — CEO. Primary curator. Sets editorial direction and story priorities.
- **Scott Stevens** — CMO. Creative and campaign oversight. Reviews story briefs before execution.
- **Jake Welch** — Operations. Runs the daily fetch and brief generation workflow.

**Longitude side:**
- **Spencer Sanders** — Tech. Runs platform, connects Longitude network signals.
- **Erik Mikkelsen** — Runs Longitude editorial and agent-facing content.
- **Jake Hancock** — Operations. Daily workflow on the Longitude side.

This is a **human-assisted platform**. Operators curate, score, and approve. The platform senses, surfaces, and recommends. Automation supports human judgment; it does not replace it. Build accordingly — do not over-automate before the editorial logic is validated by real operator decisions.

---

## Repository Structure

```
roots-vs/storylab/
  core/
    aggregator.py          # Feed fetch, parse, deduplicate — shared engine
    scorer.py              # Scoring pipeline — shared logic, pluggable rules
    brief_generator.py     # Weekly brief output — shared format
    server.py              # Local HTTP server — shared
    dashboard.html         # Dashboard UI shell — shared

  configs/
    waypoint/
      feeds.py             # Waypoint feed registry (travel, sports-biz, athletics, marketing, ad-revenue, fan-loyalty)
      scoring_rules.py     # AD audience relevance rubric
      voice.md             # Crowd Commerce editorial standards
      person_roles.py      # Role definitions: AD marketing director, fan, etc.
    longitude/
      feeds.py             # Longitude feed registry (national-brokerage, local-market, agent-intel, etc.)
      scoring_rules.py     # Agent/owner/buyer relevance rubric
      voice.md             # Longitude editorial standards
      person_roles.py      # Role definitions: agent, broker, buyer, business owner

  integrations/
    fan_graph_connector.py     # Reads cluster signals from Waypoint-fan-graph (Phase 2)
    longitude_sync.py          # Reads from Longitude Network PostgreSQL (Phase 2)

  output/
    briefs/                # Generated weekly story briefs (gitignored)

  run_mac.sh               # One-click launcher
  requirements.txt
  .gitignore               # curation.db, output/briefs/, __pycache__/
```

**Config selection at runtime:** Pass `--config waypoint` or `--config longitude` to aggregator.py, server.py, and brief_generator.py. Each config loads its own feeds, scoring rules, and voice. One codebase, two editorial contexts.

---

## Database Schema

SQLite. Database file: `curation.db` (gitignored, lives alongside scripts at runtime).

### `articles` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY | |
| `url_hash` | TEXT UNIQUE | SHA256 of URL — deduplication key |
| `title` | TEXT | |
| `summary` | TEXT | |
| `url` | TEXT | |
| `source` | TEXT | Publication name |
| `category` | TEXT | Feed category (e.g. `travel`, `ad-revenue`, `agent-intel`) |
| `published_date` | TEXT | ISO format |
| `fetched_date` | TEXT | ISO format |
| `status` | TEXT | `new` → `saved` → `in_queue` → `archived` \| `skipped` |
| `relevance_score` | INTEGER | 1–5. Scored on ingest. |
| `story_type` | TEXT | `trend-signal` \| `case-study` \| `tool-or-data` \| `interview` \| `opinion` |
| `config` | TEXT | `waypoint` or `longitude` — which company context this article belongs to |

### `fetch_log` table

| Column | Type |
|--------|------|
| `id` | INTEGER PRIMARY KEY |
| `fetch_date` | TEXT |
| `feeds_attempted` | INTEGER |
| `feeds_succeeded` | INTEGER |
| `articles_added` | INTEGER |
| `config` | TEXT |

---

## Article Status Workflow

```
new → saved (save for later) → in_queue (queued for a story brief) → archived (used)
                                                                    ↓
                                                                 skipped
```

---

## Three Core Layers

### Layer 1 — Sensing & Sourcing
RSS ingestion, feed management, deduplication. Runs daily (cron or manual). Outputs raw articles into the database with initial scoring.

### Layer 2 — Story Recognition & Scoring
Every article is scored on two dimensions at ingest:

**Relevance score (1–5):** How directly does this serve the intended person-role? Scoring criteria live in `configs/{company}/scoring_rules.py`. High-scoring articles (4–5) surface first and receive an audience badge in the dashboard.

**Story type:** What kind of story is this?
- `trend-signal` — a data point, shift, or pattern worth tracking
- `case-study` — a real program, real result, real operational detail
- `tool-or-data` — a product, platform, dataset, or methodology
- `interview` — a named person with a perspective or insight
- `opinion` — analysis, argument, or reframe

Story type matters because it drives format recommendation.

### Layer 3 — Story Brief & Format Recommendation
When an operator queues articles for a story, the system generates a **Story Brief** — not a GPT prompt for a written article, but a format-agnostic brief that routes to the right execution path.

**Story Brief fields:**
- Story type
- Intended person-role (from `person_roles.py`)
- Recommended format(s), ranked: text / meme / infographic / tool or database / audio / podcast / short video / long video / game
- Calendar moment / trigger
- Source capsules (title, URL, key facts — no fabrication beyond source material)
- Suggested angle / hook
- Revenue chain close (Waypoint) or relationship chain close (Longitude)

The format recommendation logic starts as a human-assisted suggestion layer. Operators review and override. Over time, their decisions become the training signal for automation.

---

## Feed Categories

### Waypoint (`configs/waypoint/feeds.py`)

| Category | What it covers |
|----------|---------------|
| `travel` | Travel & hospitality trade media |
| `sports-biz` | Sports Business Journal, SportTechie, Sportico, Front Office Sports |
| `athletics` | College athletics, NACMA Podcast, On3, conference news |
| `marketing` | Marketing & growth trade media — with college sports angle required |
| `ad-revenue` | Athletic department revenue and business strategy — NACDA, NACMA, Learfield |
| `fan-loyalty` | Fan engagement and loyalty technology — Loyalty360, venue tech, experience media |

### Longitude (`configs/longitude/feeds.py`)

| Category | What it covers |
|----------|---------------|
| `national-brokerage` | Compass, Sotheby's, BHHS, Coldwell Banker, RE/MAX, eXp, etc. |
| `local-market` | Wasatch Back listing activity, development, resort real estate |
| `agent-intel` | Agent movements, team formations, production rankings |
| `industry-practice` | Buyer/seller rep best practices, marketing, tech tools |
| `market-data` | Median prices, days on market, inventory, YoY comparisons |
| `comp-market` | Aspen, Jackson Hole, Sun Valley, Steamboat — benchmark markets |

---

## Relevance Scoring — Waypoint AD Audience Rubric

Scoring criteria for `configs/waypoint/scoring_rules.py`. Score 1–5:

| Score | Signal |
|-------|--------|
| 5 | Fan revenue programs with real numbers; travel behavior data; peer AD case studies; NIL commerce; loyalty technology adoption in college sports |
| 4 | Athletic department revenue strategy; fan engagement tech; conference or school-specific data; NACDA/NACMA sourced |
| 3 | General hospitality or travel industry news; sports business without specific AD angle; marketing technology without college sports application |
| 2 | Adjacent industry with loose relevance; interesting but no clear AD implication |
| 1 | Generic marketing, general business, or travel content with no college sports angle |

---

## Editorial Voice — Waypoint (Crowd Commerce)

Full voice spec lives in `configs/waypoint/voice.md`. Summary:

- Audience: AD marketing directors, CMOs, and marketing staff at P4 universities
- They are busy, skeptical of vendors, and have seen every pitch
- They trust content that names real programs, real numbers, and real operational detail
- They distrust anything that sounds like vendor marketing
- Voice: credible, current, efficient — the best B2B trade desk
- Never: "in the ever-evolving landscape of..." / "game-changing" / "synergy" / "disruptive" without a concrete example
- Every piece closes by connecting back to the revenue chain: fan loyalty → behavior shift → travel booking → new revenue for the AD

---

## Technical Constraints

- Python 3.14 on Mac (Matt's environment)
- No virtual environment required — core engine uses Python standard library only
- `dashboard.html` is fully self-contained — no build step, no npm, no dependencies
- SQLite for the database — no cloud, no external DB required to run locally
- `requirements.txt` exists for optional enhancements (beautifulsoup4 for HTML parsing, psycopg2-binary for PostgreSQL sync in Phase 2)
- Google Drive sync can be slow — if files seem stale, verify Drive is fully synced before running

### Known fixes — do not revert:
1. **SSL cert expiry fallback** — retries with unverified context when cert has expired. Uses `_SSL_UNVERIFIED` context in aggregator.py.
2. **XML sanitization** — strips invalid XML 1.0 control characters before parsing. Uses `sanitize_xml()` function. Fixes CMI and Sprout Social malformed feeds.
3. **Dead feeds commented out** — Hospitality Net (404) and On3 NIL (404) are in `NO_RSS_SOURCES` with workaround notes, not in the active FEEDS list.
4. **NACMA Podcast** — Spotify/Anchor RSS: `https://anchor.fm/s/36cd0a60/podcast/rss`

---

## Phase 2 — Fan Graph Signal Integration (do not build yet)

When ready, `integrations/fan_graph_connector.py` will read from `roots-vs/Waypoint-fan-graph` cluster outputs and feed trending topic signals into the StoryLab scoring layer. Output: "What are WVU bridge nodes engaging with this week" → content hook recommendations tied to specific fan atlas segments.

Do not build this until the core scoring and brief generation layers are working and validated by real operator use.

---

## What NOT to Do

- Do not fabricate statistics or assert facts not present in source material — FACT BOUNDARY rule applies to all brief outputs
- Do not generate story briefs from general knowledge — only from curated source capsules
- Do not pitch Waypoint or Longitude explicitly in story outputs — persuasion is implicit through credibility
- Do not add content with no relevance to the intended person-role — it dilutes the signal
- Do not revert the SSL fallback or XML sanitization fixes
- Do not over-automate — this is a human-assisted platform; build surfaces for operator judgment, not around it
- Do not merge this repo into fan-graph, Agent-Intelligencer, or longitude-network

---

## Immediate Next Actions — Start Here

When you open this project in Claude Code:

1. **Read existing curation-tool files first** — `feeds.py`, `aggregator.py`, `dashboard.html` from the local Crowd Commerce curation-tool — understand current state before making changes.

2. **Set up the repo structure** — create `core/`, `configs/waypoint/`, `configs/longitude/`, `integrations/`, `output/briefs/` directories. Move curation-tool files into `core/` with updated import paths.

3. **Add `relevance_score` and `story_type` columns** to the articles table schema in `aggregator.py` and the initial INSERT statement.

4. **Write `score_article()` in `scorer.py`** — takes title + summary + category + config, returns `relevance_score` (1–5) and `story_type` using keyword matching against the config-specific scoring rules.

5. **Update `dashboard.html`** — display relevance score badges, add "AD Leaders" filter tab (scores 4–5), add story type label on each card, sort high-relevance articles to top within each category.

6. **Expand `configs/waypoint/feeds.py`** — add `ad-revenue` and `fan-loyalty` categories with initial sources from the list above. Verify RSS URLs before adding.

7. **Write `brief_generator.py`** — queries top 10 high-relevance articles from the past 7 days, outputs a structured markdown Story Brief with: story type, person-role, ranked format recommendations, source capsules, suggested hook, and revenue chain close. Format-agnostic by design.

---

*Brief prepared May 2026. StoryLab v1.0 — Waypoint + Longitude story intelligence platform.*
