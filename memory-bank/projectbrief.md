# Project Brief — Discord Daily Tech Bot

## Goal

Build a Python bot that consumes follow-builders centralized AI feeds plus local RSS for non-AI categories, summarizes content in Traditional Chinese via OpenRouter, and delivers a daily Discord digest at 13:30 HKT.

## Constraints

- Platform: Python 3.11, Docker on Home Assistant OS
- AI sourcing: follow-builders centralized feeds (`feed-x.json`, `feed-podcasts.json`, `feed-blogs.json`)
- AI sourcing robustness: mirror failover (`FOLLOW_BUILDERS_BASE_URLS`) + optional local cache fallback
- AI fallback sources: OpenAI/HuggingFace/Google AI/HN AI + Reddit AI channels (`r/OpenAI`, `r/ChatGPT`, `r/LocalLLaMA`, `r/singularity`)
- Philosophy: track AI builders (researchers, founders, PMs, engineers), not influencer noise
- Non-AI sourcing: feedparser (sync parse, async fetch via httpx) + topic-X RSS mirror ingestion
- Category policy: each category must define at least 10 Xers (`x_handles`)
- Digest target: 10 digest items per category when enough quality sources exist
- AI: OpenRouter models (StepFun Step 3.5 Flash primary, Arcee Trinity Large Preview fallback)
- Delivery: Discord digest webhook + separate init/status webhook
- Init delivery fallback: when `DISCORD_INIT_WEBHOOK_URL` is empty, send init post to `DISCORD_WEBHOOK_URL`
- Scheduling: APScheduler AsyncIOScheduler + CronTrigger at 13:30 HKT
- Secrets: All via environment variables
- Architecture: Single `main.py` file

## Stakeholders

- Owner: User (local developer / self-hosted)

## Definition of Done

- [ ] Bot starts and sends an init message (to init webhook when configured, else main webhook fallback)
- [ ] AI section is sourced from follow-builders feeds (builders + podcasts + official blogs)
- [ ] Non-AI categories merge topic-X posts with local RSS before summarization
- [ ] Every category defines at least 10 Xers in runtime config
- [ ] Digest targets 10 news lines per category (AI + non-AI)
- [ ] OpenRouter summaries are in Traditional Chinese with fallback model chain
- [ ] Digest embeds sent in one Discord webhook POST
- [ ] Runs daily at 13:30 HKT with optional startup run
- [ ] Checks git remote daily and fast-forwards safely when local repo is clean
- [ ] Per-topic error isolation (never crashes)
- [ ] Dockerized and deployable on HA OS

## Key Risks

- follow-builders upstream feed schema/availability changes (mitigate: tolerant parser + warnings + source pin mode)
- centralized source drift versus expected builder quality (mitigate: pinned source mode in production)
- topic-X mirror instability (mitigate: multiple mirror fallbacks + configurable mirror order)
- follow-builders origin instability (mitigate: mirror candidates + cache fallback window)
- Discord 6000-char total embed limit (mitigate: per-embed char budget, truncation)
- OpenRouter free tier daily limit ~20 req/day (mitigate: hybrid mode call volume management + optional credits)
- Broad public RSS/X feeds can surface cross-topic noise (mitigate: keyword routing + AI filtering)

Created: 2026-03-04 | Last Updated: 2026-03-31
