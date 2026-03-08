# Session Log

## 2026-03-04 — v0.1.0
**Objective:** Create implementation plan for Discord Daily Tech Bot

**Actions:**
- Scoped problem: 7-topic daily tech digest from X to Discord
- Researched twscrape, Perplexity Sonar API, Discord webhooks, schedule vs APScheduler
- Discovered critical constraint: Discord 6000-char total embed limit
- Recommended APScheduler over schedule for async compatibility
- Decomposed into 11 tasks across 6 phases
- Identified 7 risks with mitigations
- Saved plan to `memory-bank/plans/2026-03-04-discord-daily-tech-bot.md`

**Status:** ✅ Complete

## 2026-03-04 — v0.2.0
**Objective:** Update plan: replace Perplexity with OpenRouter free-tier, add RSS feeds as primary data source

**Actions:**
- Researched OpenRouter free tier API: confirmed Llama 3.2 3B and Gemma 3 4B as free models; mistral-7b-instruct:free unverified
- Researched feedparser: sync-only, needs async fetch via httpx; Reddit requires custom User-Agent; Printables/Thingiverse unverified
- Replaced Perplexity Sonar with OpenRouter in plan (T4 rewritten, env var changed to OPENROUTER_API_KEY)
- Added Task 3b: RSS Feed Fetching with concurrent async fetch + feedparser parse
- Added RSS Feed Configuration Reference (11 feeds) and Feed-to-Topic Mapping
- Added OpenRouter AI Configuration Reference (models, rate limits, fallback logic)
- Updated orchestrator (T7) for dual-source merge (RSS first, X second, URL dedup)
- Updated risk register: added R8 (RSS unavailable), R9 (Reddit 429), R10 (OpenRouter latency)
- Updated validation checklist (T11) for RSS + OpenRouter edge cases

**Status:** ✅ Complete

## 2026-03-04 — v1.0.0
**Objective:** Full implementation — all T1–T11 in a single-file Python bot

**Actions:**
- Updated AI fallback chain: Llama 3.2 3B → StepFun Step 3.5 Flash → Arcee Trinity Large Preview (per user spec)
- Created `main.py`: all tasks T2–T11 in one async file (600 lines)
- Created `requirements.txt` (twscrape, feedparser, httpx, apscheduler 3.x, pytz)
- Created `Dockerfile` (python:3.11-slim, VOLUME /app/data)
- Created `docker-compose.yml` (restart: unless-stopped, env_file, data volume)
- Created `.env.example` (6 env vars documented)
- Created `.gitignore` (.env, accounts.db)
- Created `README.md` (setup, topic table, AI cascade, notes)
- Created `data/.gitkeep`

**Status:** ✅ Complete

## 2026-03-04 — v1.1.0
**Objective:** Fix missing X posts in runtime logs and harden deployment behavior

## 2026-03-08 — v1.3.1
**Objective:** Fix HAOS startup crash caused by stale image and missing git binary

**Actions:**
- Added `git` installation to Dockerfile for self-update support in containerized deployments
- Hardened git helper calls in `main.py` so missing git degrades to a logged skip instead of a startup crash
- Identified HAOS deployment root cause: files were uploaded, but the `discord-bot` image was not rebuilt before `docker run`
- Updated `upload.md` to require remote `docker build --pull -t discord-bot .` before container restart

**Status:** ✅ Complete

## 2026-03-08 — v1.3.2
**Objective:** Shorten Discord digest items into one-line "why it matters" bullets

**Actions:**
- Added a focused regression test to require verbose multi-line AI bullets to collapse into single-line Discord bullets
- Updated the OpenRouter prompt to request short Traditional Chinese "why it matters" lines instead of 1-2 sentence summaries
- Added Discord-side normalization so wrapped or overly verbose AI output is compacted while preserving source URLs
- Verified the focused test, full regression suite, and Python syntax check all pass

**Status:** ✅ Complete

**Actions:**
- Analyzed production logs: twscrape login blocked by Cloudflare (`403`) resulting in 0 active X accounts
- Added active-account validation in `setup_twscrape()` with explicit warning when account pool is inactive
- Added Nitter search RSS fallback in `fetch_tweets()` for X-topic ingestion when twscrape returns insufficient posts
- Made OpenRouter response parsing null-safe to avoid `'NoneType' object has no attribute 'strip'` on StepFun responses
- Updated README notes to document Cloudflare block handling and fallback behavior

**Status:** ✅ Complete

## 2026-03-04 — v1.1.1
**Objective:** Improve Nitter fallback reliability across network environments

**Actions:**
- Added simplified topic-specific Nitter search queries to improve fallback hit rate
- Added `NITTER_BASE_URLS` env override for configurable mirror routing
- Updated `.env.example` and `README.md` with mirror override instructions
- Rebuilt container and verified patched code path loaded in runtime logs

**Status:** ✅ Complete

## 2026-03-04 — v1.2.0
**Objective:** Apply user-specified fix list and verify RSS behavior

**Actions:**
- Updated RSS key URLs to requested values (`thingiverse/newest/rss`, `printables/feed.xml`)
- Merged RP2350 stream into RP2040 topic and matching logic
- Updated OpenRouter model order and added extra free fallback model (`meta-llama/llama-3.2-3b-instruct:free`)
- Suppressed noisy httpx URL logs by setting logger level to WARNING
- Rebuilt runtime image and verified feed handling path:
	- printables key now resolves through fallback with entries
	- thingiverse key resolves through fallback parse with entries

**Status:** ✅ Complete

---
