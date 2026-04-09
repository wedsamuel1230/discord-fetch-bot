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

## 2026-03-29 — v1.4.0

**Objective:** Start follow-builders hybrid migration implementation

**Actions:**

- Added migration toggles and config guards (`DIGEST_MODE`, follow-builders source mode, pinned ref requirement)
- Implemented follow-builders feed intake normalization (`feed-x`, `feed-podcasts`, `feed-blogs`)
- Implemented AI-builder summary renderer with identity + URL-preserving compact bullets
- Updated orchestrator to support `follow-builders-hybrid` and `follow-builders-only` execution paths
- Added regression tests for migration config validation, feed normalization/error surfacing, AI summary rendering, and hybrid mode orchestration
- Updated `.env.example`, `README.md`, Docker comments, and active context docs for migration settings
- Verified full regression suite (`python -m unittest tests.test_main -v`) and syntax compile checks

**Status:** ✅ Complete

## 2026-03-29 — v1.5.0

**Objective:** Remove legacy X path and Maker category; redistribute feeds and expand RSS coverage

**Actions:**

- Removed legacy X ingestion code from `main.py` (DuckDuckGo/X discovery + FxTwitter hydration helpers deleted)
- Removed support for `DIGEST_MODE=legacy`; valid modes are now follow-builders only (`follow-builders-hybrid`, `follow-builders-only`)
- Removed Maker topic from category configuration and redistributed Maker feeds to ESP32/RP2040/Arduino/3D categories
- Added extra RSS feeds: `reddit_localllama`, `reddit_singularity`, `reddit_microcontrollers`, `reddit_embedded`, `all3dp`, `reddit_additivemanufacturing`
- Removed obsolete dependency `duckduckgo-search` from `requirements.txt`
- Updated README + `.env.example` to reflect mode changes and category/feed updates
- Added/updated regression tests to enforce legacy-mode rejection, helper removal, feed redistribution, and new RSS keys
- Verified full regression suite (`python -m unittest tests.test_main -v`) passes with 13 tests green

**Status:** ✅ Complete

## 2026-03-29 — v1.5.1

**Objective:** Ensure full Traditional Chinese output for the AI builder section

**Actions:**

- Added follow-builders payload conversion into `ai_filter` input posts in `main.py`
- Updated orchestrator to summarize AI builder content via OpenRouter Traditional Chinese path
- Kept deterministic local fallback summary when model output is empty
- Updated hybrid orchestrator test to assert AI section goes through `ai_filter`
- Verified full regression suite remains green (`python -m unittest tests.test_main -v`, 13/13)

**Status:** ✅ Complete

## 2026-03-31 — v1.6.0

**Objective:** Enforce >=10 Xers per category and target 10 digest items per category

**Actions:**

- Added RED tests requiring:
  - every topic has at least 10 `x_handles`
  - AI topic includes requested handles (`Khazix0918`, `dotey`, `vista8`)
- Captured RED evidence with focused run in configured Python env:
  - `python -m unittest tests.test_main.TopicDistributionTests -v` failed before implementation
- Added `x_handles` catalogs to all categories in `main.py` (>=10 each)
- Added topic-X ingestion pipeline using RSS mirrors:
  - `TOPIC_X_ENABLED`, `TOPIC_X_LOOKBACK_HOURS`, `TOPIC_X_RSS_BASE_URLS`
  - per-handle fetch + per-topic merge path (`topic-X + RSS`)
- Updated non-AI hybrid orchestration to merge topic-X posts with RSS before summarization
- Updated `ai_filter` to target `fetch_limit` items (10 default) and adjusted char budget logic
- Captured GREEN evidence:
  - focused suite passes after implementation
  - full suite passes: `python -m unittest tests.test_main -v` (15/15)
- Updated operator docs:
  - `.env.example` with new topic-X env knobs
  - `README.md` with category-X and 10-item digest behavior

**Status:** ✅ Complete

## 2026-03-31 — v1.6.1

**Objective:** Fix init-webhook behavior and harden follow-builders sourcing for resilience/performance

**Actions:**

- Added RED tests for:
  - init message fallback to `DISCORD_WEBHOOK_URL` when init webhook is missing
  - env validation acceptance when `DISCORD_INIT_WEBHOOK_URL` is absent
  - follow-builders mirror failover across base URLs
  - follow-builders cache fallback when all upstream candidates fail
- Captured RED evidence:
  - focused test run failed before implementation (`InitWebhookTests`, `MigrationConfigTests`, `FollowBuildersFeedTests`)
- Implemented runtime behavior updates:
  - `DISCORD_INIT_WEBHOOK_URL` is no longer required at validation time
  - `send_init_message()` now falls back to main webhook when init webhook is empty
  - added `FOLLOW_BUILDERS_BASE_URLS` with candidate failover per feed
  - added local follow-builders cache controls (`FOLLOW_BUILDERS_CACHE_ENABLED`, `FOLLOW_BUILDERS_CACHE_TTL_HOURS`, `FOLLOW_BUILDERS_CACHE_PATH`)
  - AI path now falls back to AI RSS sources when follow-builders returns empty payload
  - added extra AI RSS fallback channels: `reddit_openai`, `reddit_chatgpt`
- Updated operator docs in `.env.example` and `README.md`
- Captured GREEN evidence:
  - focused suite passes (8/8)
  - full regression suite passes (`python -m unittest tests.test_main -v`, 19/19)

**Status:** ✅ Complete

## 2026-04-10 — v1.7.0

**Objective:** Start implementation of staged source expansion (X + YouTube) and Discord message refactor.

**Actions:**

- Added RED tests for rollout and Discord output behavior (`SourceRolloutTests`, new `DigestFormatTests` checks)
- Implemented source rollout controls:
  - `SOURCE_ROLLOUT_MODE` (`wave1`/`wave2`)
  - runtime overlay helpers for per-topic X and YouTube sources
- Implemented YouTube ingestion path for non-AI hybrid categories:
  - channel seed normalization and channel-id resolution
  - YouTube feed fetch + recency filtering
  - merged pipeline now: topic-X + YouTube + RSS
- Refactored Discord composition:
  - split compacting into helper stages
  - centralized render limits
  - deterministic topic ordering in embed assembly
  - visible bullet style updated to `body ｜ URL`
- Updated docs:
  - `.env.example` with rollout/YouTube controls
  - `README.md` with wave rollout and YouTube ingestion notes
- Verification:
  - focused RED observed before implementation
  - focused GREEN after changes
  - full regression GREEN: `python -m unittest tests.test_main -v` (26/26)

**Status:** ✅ Complete

---
