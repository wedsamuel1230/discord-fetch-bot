# Project Brief — Discord Daily Tech Bot

## Goal
Build a Python bot that fetches daily tech posts from X (Twitter) and RSS, filters/summarizes them via OpenRouter in Traditional Chinese, and delivers 6 themed embeds to Discord via webhook daily at 13:30 HKT.

## Constraints
- Platform: Python 3.11, Docker on Home Assistant OS
- X sourcing: public DuckDuckGo discovery + FxTwitter hydration, no authenticated scraping
- RSS: feedparser (sync parse, async fetch via httpx) — expanded catalog across 6 topics
- AI: OpenRouter models (StepFun Step 3.5 Flash primary, Arcee Trinity Large Preview fallback)
- Delivery: Discord digest webhook + separate init/status webhook
- Scheduling: APScheduler AsyncScheduler (recommended) or schedule+pytz
- Secrets: All via environment variables
- Architecture: Single `main.py` file

## Stakeholders
- Owner: User (local developer / self-hosted)

## Definition of Done

- [ ] Bot starts and sends an init message to the separate Discord init webhook
- [ ] Fetches RSS feeds and public X posts for all 6 topics
- [ ] OpenRouter AI filters/summarizes into Traditional Chinese (with model fallback)
- [ ] 6 embeds sent in single Discord webhook POST
- [ ] Runs daily at 13:30 HKT + once on startup if configured
- [ ] Checks git remote daily and fast-forwards safely when local repo is clean
- [ ] Per-topic error isolation (never crashes)
- [ ] Dockerized and deployable on HA OS

## Key Risks

- DuckDuckGo or FxTwitter availability changes (mitigate: graceful logging, RSS provides baseline even if X is thin)
- Discord 6000-char total embed limit (mitigate: per-embed char budget, truncation)
- OpenRouter free tier daily limit ~20 req/day (mitigate: 7 topics fits; $5 credits expands to ~200/day)
- Broad public feeds can surface cross-topic noise (mitigate: keyword routing + AI filtering)

Created: 2026-03-04 | Last Updated: 2026-03-04
