# Project Brief — Discord Daily Tech Bot

## Goal
Build a Python bot that fetches daily tech posts from X (Twitter) and RSS, filters/summarizes them via OpenRouter in Traditional Chinese, and delivers 7 themed embeds to Discord via webhook daily at 13:30 HKT.

## Constraints
- Platform: Python 3.11, Docker on Home Assistant OS
- Scraping: twscrape (async, SQLite session persistence) with Nitter RSS fallback for X when login is blocked
- RSS: feedparser (sync parse, async fetch via httpx) — 11 feeds across 7 topics
- AI: OpenRouter models (StepFun Step 3.5 Flash primary, Arcee Trinity Large Preview fallback)
- Delivery: Discord Webhook (max 10 embeds/POST, 6000 char total limit)
- Scheduling: APScheduler AsyncScheduler (recommended) or schedule+pytz
- Secrets: All via environment variables (6 vars)
- Architecture: Single `main.py` file

## Stakeholders
- Owner: User (local developer / self-hosted)

## Definition of Done
- [ ] Bot starts and attempts X via twscrape; if blocked, uses Nitter fallback
- [ ] Fetches RSS feeds (11 sources) and tweets for all 7 topics with fallback logic
- [ ] OpenRouter AI filters/summarizes into Traditional Chinese (with model fallback)
- [ ] 7 embeds sent in single Discord webhook POST
- [ ] Runs daily at 13:30 HKT + once on startup
- [ ] Per-topic error isolation (never crashes)
- [ ] Dockerized and deployable on HA OS

## Key Risks
- X account suspension from scraping (mitigate: cookie login, low volume, delays; RSS provides baseline even if X fails)
- Discord 6000-char total embed limit (mitigate: per-embed char budget, truncation)
- OpenRouter free tier daily limit ~20 req/day (mitigate: 7 topics fits; $5 credits expands to ~200/day)
- Printables/Thingiverse RSS feeds unverified (mitigate: treat as optional, graceful fallback)

---
*Created: 2026-03-04 | Last Updated: 2026-03-04*
