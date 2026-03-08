# Discord Daily Tech Bot — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python bot that fetches daily tech posts from X and RSS feeds, filters/summarizes them via OpenRouter free-tier models, and delivers 7 themed Discord embeds daily at 08:00 HKT.

**Architecture:** Single-file async Python application (`main.py`). Dual data sources: tweet fetching via `twscrape` (async) and RSS feeds via `feedparser` (sync parse, async fetch). AI filtering via OpenRouter free-tier models (OpenAI-compatible REST). Delivery via Discord webhook POST. Scheduled with `APScheduler` AsyncScheduler (recommended) or `schedule` in a thread. Dockerized for Home Assistant OS deployment.

**Tech Stack:** Python 3.11, twscrape, feedparser, httpx, APScheduler (or schedule+pytz), Docker

**Plan Location:** `memory-bank/plans/2026-03-04-discord-daily-tech-bot.md`

**Memory Bank Context:** Greenfield project. No prior code. See `memory-bank/projectbrief.md` for goals and constraints.

---

## Executive Summary

A single-file Python bot that runs 24/7 in a Docker container on Home Assistant OS. Each day at 08:00 HKT (and once on startup), it:

1. Fetches posts from two sources per topic: RSS feeds via `feedparser` and tweets from X via `twscrape`
2. Merges and deduplicates results (RSS first, then X posts)
3. Filters and summarizes each topic's posts into Traditional Chinese via OpenRouter free-tier AI models
4. Sends all 7 topic embeds in a single Discord webhook POST

Key design decisions informed by research:
- **Dual data sources** — RSS feeds provide reliable baseline content; X tweets supplement with real-time community posts
- **OpenRouter free tier** — zero-cost AI filtering using Llama 3.2 3B (primary) with Gemma 3 4B fallback; ~20 req/day limit fits 7 topics
- **APScheduler over schedule** — native async + timezone support eliminates threading complexity (R7)
- **Character budget enforcement** — Discord's 6000-char total embed limit requires concise summaries (R2)
- **Per-topic error isolation** — each topic wrapped in try/except; never crashes the bot (spec requirement)
- **Cookie-based twscrape login preferred** — more stable than password-based (R1)
- **Async RSS fetching** — feedparser is sync; fetch feed content with `httpx` first, then parse with `feedparser.parse(body)` to avoid blocking

---

## Problem Statement

| Element | Detail |
|---|---|
| **Goal** | Daily automated tech news digest from X + RSS feeds to Discord, covering 7 topics (AI, ESP32, RP2040, RP2350, Arduino, Maker, 3D Printing) |
| **Context** | Greenfield. Deploy as Docker container on Home Assistant OS. |
| **Success Criteria** | Bot fetches from RSS + X, filters via AI, summarizes, and delivers 7 embeds daily without crashing. |
| **Constraints** | Single `main.py`. Env-var secrets. Python 3.11. twscrape + feedparser + httpx + scheduler. |
| **Out of Scope** | Discord gateway bot, slash commands, multi-channel, web UI, CI/CD, monitoring. |
| **Assumptions** | X account active and not rate-limited. OpenRouter API key valid (free tier). RSS feeds are accessible. HA OS supports Docker. Schedule: **13:30 HKT** (user confirmed). |

---

## Research Summary

| # | Finding | Impact |
|---|---|---|
| 1 | `twscrape` is fully async (asyncio/httpx), supports `min_faves:N` search operator | Spec feasible as written |
| 2 | `twscrape` session in SQLite `accounts.db` — persistent | Docker volume mount required for `data/` |
| 3 | OpenRouter API is OpenAI-compatible (`POST /chat/completions`, Bearer auth) | Can use `httpx` directly, same as OpenAI SDK |
| 4 | OpenRouter free tier: `llama-3.2-3b-instruct:free` (131k ctx) and `gemma-3-4b-it:free` (32k ctx) confirmed active at $0 | Two reliable free models available |
| 5 | OpenRouter free tier rate limit: ~20 req/day without credits, ~200 req/day with $5+ credits | 7 topics/day fits within free limit; purchasing $5 credits adds large safety margin |
| 6 | `mistralai/mistral-7b-instruct:free` may no longer exist as a free variant | Use only confirmed models; drop mistral from fallback chain or verify at runtime |
| 7 | OpenRouter free models are deprioritized; latency spikes possible, "not suitable for production" per docs | Accept latency; add generous timeout (60s); this is a daily batch job, not real-time |
| 8 | Discord webhooks: max 10 embeds/POST (7 topics fits) | Single POST confirmed |
| 9 | **Discord 6000-char total limit** across all embeds in one message | Must enforce per-embed budget ~800 chars |
| 10 | `schedule` has no async support; `APScheduler` has native `AsyncScheduler` + timezone | Recommend APScheduler |
| 11 | Cookie-based twscrape login is more stable than username/password | Document both paths |
| 12 | Webhook rate limit: ~5 req/2s; single POST avoids issues | Architecture confirmed |
| 13 | `feedparser` v6.0.12: synchronous only, returns result dict (never raises exceptions) | Fetch feed body with `httpx` async, then parse with `feedparser.parse(body)` |
| 14 | `feedparser` needs custom User-Agent for Reddit RSS (returns 429/403 with default) | Set `agent='DiscordTechBot/1.0'` or fetch via `httpx` with User-Agent header |
| 15 | Reddit RSS returns valid Atom 1.0 with `<updated>` on entries; parseable by feedparser | Reddit feeds confirmed reliable |
| 16 | Printables RSS and Thingiverse RSS are **unverified/unreliable** | Mark as optional; test before committing; use fallback if broken |
| 17 | feedparser `published_parsed` may be `None` on some entries; Atom feeds use `updated_parsed` more reliably | Check both attributes defensively |
| 18 | 11 sequential sync RSS fetches = 10–30 seconds wall time | Use `httpx` async concurrent fetch for all feeds, then parse each body synchronously |

---

## Topic Configuration Reference

| # | Topic | Emoji | Color | Query (primary) | min_faves | Fallback min_faves |
|---|---|---|---|---|---|---|
| 1 | AI | 🤖 | 0x5865F2 | `(new AI model OR AI project OR AI tool OR AI release OR AI paper) -is:retweet -is:reply` | 20 | 5 |
| 2 | ESP32 | 🔌 | 0x57F287 | `ESP32 (project OR tutorial OR build OR release OR firmware OR library) -is:retweet -is:reply` | 5 | 1 |
| 3 | RP2040 | 🔌 | 0x2ECC71 | `RP2040 (project OR tutorial OR build OR release OR firmware OR library) -is:retweet -is:reply` | 5 | 1 |
| 4 | RP2350 | 🔌 | 0x1ABC9C | `RP2350 (project OR tutorial OR build OR release OR firmware OR library) -is:retweet -is:reply` | 3 | 1 |
| 5 | Arduino | 🔌 | 0x00979D | `Arduino (project OR tutorial OR build OR shield OR library OR new) -is:retweet -is:reply` | 10 | 1 |
| 6 | Maker | 🛠 | 0xFEE75C | `(maker project OR DIY build OR hackaday OR hackspace OR makerspace) -is:retweet -is:reply` | 10 | 1 |
| 7 | 3D列印 | 🖨 | 0xED4245 | `(3Dprinting OR 3Dprint OR FDM OR resin print) (project OR model OR build OR release) -is:retweet -is:reply` | 10 | 1 |

---

## RSS Feed Configuration Reference

| Feed Key | URL | Topic Mapping |
|---|---|---|
| 🛠 Hackaday | `https://hackaday.com/blog/feed/` | Maker |
| 🔌 Hackster | `https://www.hackster.io/feed` | ESP32, RP2040, RP2350, Arduino (filter by content) |
| 🔌 Adafruit | `https://blog.adafruit.com/feed/` | ESP32, RP2040, Arduino, Maker |
| 🖨 Printables | `https://www.printables.com/rss.xml` | 3D列印 (**unverified — test before relying**) |
| 🖨 Thingiverse | `https://www.thingiverse.com/rss` | 3D列印 (**unverified — test before relying**) |
| 🤖 HN (AI) | `https://hnrss.org/newest?q=AI+LLM&points=10` | AI |
| 🔌 r/esp32 | `https://www.reddit.com/r/esp32/.rss` | ESP32 |
| 🔌 r/arduino | `https://www.reddit.com/r/arduino/.rss` | Arduino |
| 🔌 r/RP2040 | `https://www.reddit.com/r/RP2040/.rss` | RP2040 |
| 🖨 r/3Dprinting | `https://www.reddit.com/r/3Dprinting/.rss` | 3D列印 |
| 🛠 r/maker | `https://www.reddit.com/r/maker/.rss` | Maker |

### Feed-to-Topic Mapping

| Topic | RSS Feeds | X Query |
|---|---|---|
| AI | HN (AI) | ✅ (per spec) |
| ESP32 | r/esp32, Hackster*, Adafruit* | ✅ (per spec) |
| RP2040 | r/RP2040, Hackster*, Adafruit* | ✅ (per spec) |
| RP2350 | Hackster* | ✅ (per spec) |
| Arduino | r/arduino, Hackster*, Adafruit* | ✅ (per spec) |
| Maker | r/maker, Hackaday, Adafruit* | ✅ (per spec) |
| 3D列印 | r/3Dprinting, Printables†, Thingiverse† | ✅ (per spec) |

\* = multi-topic feed; AI filter determines which topic each entry belongs to  
† = unverified feed; may be broken; graceful fallback if unavailable

### RSS Fetch Rules
- Fetch latest **5 entries per feed** per run
- Skip entries older than **24 hours** (check `published_parsed` or `updated_parsed`)
- If no entries within 24h → include the latest 3 regardless of date
- Extract: `title`, `link`, `summary` (max 300 chars, strip HTML)

### Merging RSS + X Posts per Topic
- RSS entries listed first (higher quality / curated sources)
- X posts listed after
- Deduplicate by URL if same link appears in both
- Minimum **3 posts total** per topic (RSS + X combined)

---

## OpenRouter AI Configuration Reference

### Models (Ordered by Preference)
| Priority | Model | Context | Status |
|---|---|---|---|
| 1 (Primary) | `stepfun-ai/step-3.5-flash` | — | StepFun Step 3.5 Flash |
| 2 (Fallback) | `arcee-ai/arcee-trinity-large-preview` | — | Arcee Trinity Large Preview |

### Rate Limits
- **Without credits:** ~20 requests/day (shared across all free models)
- **With $5+ credits:** ~200 requests/day
- 7 topics/day = 7 requests minimum (fits within free limit)
- Budget 1 retry per topic = 14 requests max (still fits)

### Endpoint & Auth
- Endpoint: `POST https://openrouter.ai/api/v1/chat/completions`
- Auth: `Authorization: Bearer {OPENROUTER_API_KEY}`
- Optional headers: `HTTP-Referer`, `X-OpenRouter-Title` (for attribution, not required)

### Fallback Logic
1. Try primary model (`stepfun-ai/step-3.5-flash`)
2. If fails → retry with fallback model (`arcee-ai/arcee-trinity-large-preview`)
3. If all models fail → skip AI filtering, send raw posts with "⚠️ AI 摘要不可用" prefix

---

## Task Phases

### Phase A: Foundation (T1, T9) — Parallelizable

#### Task 1: Project Scaffold & Configuration

**Files:**
- Create: `main.py` (empty entry point)
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `data/.gitkeep`
- Create: `.env.example`

**Step 1:** Create `requirements.txt` with pinned dependencies:
- `twscrape>=0.17.0`
- `feedparser>=6.0.12`
- `httpx>=0.27.0`
- `apscheduler>=4.0.0a5` (or `schedule>=1.2.0` + `pytz`)

**Step 2:** Create `Dockerfile` per spec (Python 3.11-slim, WORKDIR /app, install deps, CMD python main.py)

**Step 3:** Create `.env.example` documenting all 6 env vars (DISCORD_WEBHOOK_URL, OPENROUTER_API_KEY, X_USERNAME, X_PASSWORD, X_EMAIL, X_EMAIL_PW)

**Step 4:** Create `data/` directory with `.gitkeep` for twscrape DB persistence

**Step 5:** Create minimal `main.py` with entry point structure (imports, `async def main()`, `if __name__`)

**Acceptance Criteria:**
- [ ] All files exist
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `docker build .` succeeds
- [ ] Env vars documented

**Memory Bank Updates:**
- Update: `memory-bank/activeContext.md` — "T1 scaffold complete"
- Append: `memory-bank/SESSION.md` — session entry

---

#### Task 9: Dockerfile & Deployment Config

**Files:**
- Modify: `Dockerfile` (add volume, healthcheck if desired)
- Create: `docker-compose.yml` (optional but recommended for HA OS)

**Step 1:** Finalize Dockerfile:
- Base: `python:3.11-slim`
- Working dir: `/app`
- Copy and install requirements
- Copy source
- Volume: `/app/data` for persistent `accounts.db`
- CMD: `python main.py`

**Step 2:** Create `docker-compose.yml` for easy deployment on HA OS:
- Service: `discord-bot`
- Environment: pass-through all 6 env vars
- Volume: `./data:/app/data`
- Restart: `unless-stopped`

**Acceptance Criteria:**
- [ ] `docker build -t discord-tech-bot .` succeeds
- [ ] `docker-compose up` runs with env vars
- [ ] `data/` is persisted across container restarts

---

### Phase B: Data Ingestion (T2, T3, T3b) — Sequential

#### Task 2: twscrape Account Setup Module

**Files:**
- Modify: `main.py` — add `setup_twscrape()` function

**Step 1:** Write function `async def setup_twscrape() -> API`:
- Initialize `twscrape.API("data/accounts.db")`
- Check if accounts exist in pool
- If not: add account using env vars, call `login_all()`
- If yes: skip login, return API instance
- Log outcome

**Step 2:** Add error handling for login failure (log + raise)

**Step 3:** Test manually: run setup, verify `data/accounts.db` created

**Acceptance Criteria:**
- [ ] First run creates `accounts.db` and logs in
- [ ] Subsequent runs skip login and reuse session
- [ ] Login failure is logged with clear error message

---

#### Task 3: Tweet Fetching with Fallback

**Files:**
- Modify: `main.py` — add `fetch_tweets()` function

**Step 1:** Define topic config as a list of dicts (name, emoji, color, query, min_faves, fallback_min_faves, fetch_limit=10, rss_feeds=[], ai_filter_instruction)

**Step 2:** Write `async def fetch_tweets(api, topic) -> list[dict]`:
- Build query string with `min_faves:{topic.min_faves}`
- Call `api.search(query, limit=topic.fetch_limit)`
- Collect results via `gather()`
- If len(results) < 3: retry with `min_faves:{topic.fallback_min_faves}`
- Return list of dicts: `{source: "x", author, content, url, like_count}`
- Log fetch count per topic

**Step 3:** Add per-topic delay (2-3 seconds) between fetches to reduce suspension risk (R1)

**Acceptance Criteria:**
- [ ] Primary query returns tweets with all required fields including `source: "x"`
- [ ] Fallback triggers when results < 3
- [ ] Returns empty list gracefully (never raises)
- [ ] Delay between fetches present

---

#### Task 3b: RSS Feed Fetching

**Files:**
- Modify: `main.py` — add `fetch_rss_feeds()` function

**Step 1:** Define RSS feed config: dict mapping feed key to URL (11 feeds total, see RSS Feed Configuration Reference)

**Step 2:** Define feed-to-topic mapping: which feeds contribute to which topics

**Step 3:** Write `async def fetch_all_rss(client: httpx.AsyncClient) -> dict[str, list[dict]]`:
- Fetch all 11 feed URLs concurrently using `httpx` (with User-Agent header `DiscordTechBot/1.0` for Reddit compatibility)
- Set per-request timeout: 15 seconds
- For each response: parse body with `feedparser.parse(body)`
- Check `result.bozo` — log warning if True but still use partial data
- Extract up to 5 entries per feed: `{source: "rss", title, link, summary (max 300 chars, HTML stripped)}`
- Filter by age: skip entries older than 24h (check `published_parsed` or `updated_parsed`, whichever exists)
- If no entries within 24h: include latest 3 regardless of date
- Return dict keyed by feed name

**Step 4:** Write `def get_rss_for_topic(all_rss: dict, topic) -> list[dict]`:
- Look up which feeds map to this topic
- Collect and return all matching entries

**Step 5:** Handle Printables/Thingiverse gracefully — if feed returns error or empty, log warning and continue

**Acceptance Criteria:**
- [ ] All 11 feeds fetched concurrently (not sequentially)
- [ ] Reddit feeds succeed with custom User-Agent
- [ ] Entries have `source: "rss"`, `title`, `link`, `summary`
- [ ] 24h age filter works; fallback to latest 3 if none recent
- [ ] Broken feeds logged as warning, not crash
- [ ] Printables/Thingiverse failures handled gracefully

---

### Phase C: AI Processing (T4) — Independent

#### Task 4: OpenRouter AI Filtering & Summarization

**Files:**
- Modify: `main.py` — add `ai_filter()` function

**Step 1:** Write `async def ai_filter(posts: list[dict], topic) -> str`:
- Build prompt:
  - System: "You are a tech news curator. Output in Traditional Chinese."
  - User: Include topic name, filter instructions (per spec), raw post data (source, title/author, content/summary, URL)
  - Instruct: "Remove ads, reposts, irrelevant. For MCU topics only keep posts about {chip}. Keep minimum 3 posts. For each, write 1-2 sentence Traditional Chinese summary followed by URL. If nothing valuable, return exactly NO_CONTENT."
- POST to `https://openrouter.ai/api/v1/chat/completions` with `httpx`
- Headers: `Authorization: Bearer {OPENROUTER_API_KEY}`
- Model: `meta-llama/llama-3.2-3b-instruct:free` (primary)
- Parse `choices[0].message.content`
- Return content string (or `"NO_CONTENT"`)

**Step 2:** Implement model fallback:
- If primary model fails (timeout, HTTP error, empty response) → retry with `arcee-ai/arcee-trinity-large-preview`
- If fallback also fails → return raw posts formatted as plain text with "⚠️ AI 摘要不可用" prefix
- Log which model was used and any fallback transitions

**Step 3:** Enforce character budget:
- If response > 700 chars, truncate intelligently (cut last post, add "…")
- Log warning when truncation occurs

**Step 4:** Handle API errors with generous timeout (60s — free models are deprioritized, latency spikes expected)

**Acceptance Criteria:**
- [ ] Returns Traditional Chinese summaries with URLs
- [ ] Handles empty post list (returns NO_CONTENT)
- [ ] Primary model tried first, fallback on failure
- [ ] If all models fail, returns raw posts with warning prefix
- [ ] Respects ~700 char budget per topic
- [ ] Timeout set to 60s (free tier latency)
- [ ] Model name logged for each call

---

### Phase D: Discord Output (T5, T6) — Sequential

#### Task 5: Discord Embed Builder

**Files:**
- Modify: `main.py` — add `build_embed()` function

**Step 1:** Write `def build_embed(topic, summary_text) -> dict`:
- Build embed dict:
  - `title`: `"{emoji} {topic_name} 每日精選"`
  - `description`: summary_text (or "⚠️ 內容不足" if NO_CONTENT or empty)
  - `color`: topic color (int)
  - `footer`: `{"text": "更新時間：{YYYY-MM-DD HH:MM} HKT"}`
- If error state: `description` = "❌ 抓取失敗，請檢查 log"

**Step 2:** Add validation:
- Title ≤ 256 chars
- Description ≤ 4096 chars
- Truncate description if over limit

**Step 3:** Write `def build_all_embeds(results) -> list[dict]`:
- Iterate 7 topics, call `build_embed()` for each
- Calculate total chars across all embeds
- If total > 5800 (safety margin below 6000): trim longest descriptions
- Return list of 7 embed dicts

**Acceptance Criteria:**
- [ ] Each embed has title, description, color, footer
- [ ] Error embeds use error text
- [ ] Total character count across all embeds ≤ 6000
- [ ] Always returns exactly 7 embeds

---

#### Task 6: Discord Webhook Sender

**Files:**
- Modify: `main.py` — add `send_to_discord()` function

**Step 1:** Write `async def send_to_discord(embeds: list[dict]) -> bool`:
- POST to `DISCORD_WEBHOOK_URL` with `httpx`
- Payload: `{"embeds": embeds}`
- Content-Type: `application/json`
- Handle response:
  - 204/200: success, log
  - 429: parse `Retry-After`, wait, retry once
  - Other errors: log and return False

**Acceptance Criteria:**
- [ ] Sends all 7 embeds in single POST
- [ ] Handles 429 with retry
- [ ] Logs success with timestamp
- [ ] Returns boolean success indicator

---

### Phase E: Integration (T7, T8, T10) — Sequential

#### Task 7: Orchestrator (Per-Topic Pipeline)

**Files:**
- Modify: `main.py` — add `run_daily_job()` function

**Step 1:** Write `async def run_daily_job()`:
- Call `setup_twscrape()` to get API instance
- Fetch all RSS feeds concurrently via `fetch_all_rss()` (single batch)
- For each of 7 topics (sequential to reduce X rate-limit risk):
  - `try:`
    - `rss_posts = get_rss_for_topic(all_rss, topic)`
    - `tweets = await fetch_tweets(api, topic)`
    - Merge: RSS posts first, then X posts; deduplicate by URL
    - If total < 3 posts, log warning
    - `summary = await ai_filter(merged_posts, topic)`
    - Store `(topic, summary)` pair
    - `await asyncio.sleep(2)` — inter-topic delay
  - `except Exception as e:`
    - Log error with topic name + traceback
    - Store `(topic, ERROR_MARKER)` pair
- Build all embeds from results
- Send to Discord
- Log completion timestamp

**Acceptance Criteria:**
- [ ] RSS feeds fetched once (not per-topic)
- [ ] RSS and X posts merged with RSS first
- [ ] URL deduplication works
- [ ] All 7 topics processed regardless of individual failures
- [ ] Failed topics get error embed, not crash
- [ ] Results sent in single webhook POST
- [ ] Total execution logged

---

#### Task 8: Scheduler & Main Loop

**Files:**
- Modify: `main.py` — complete the `main()` function

**Option A (Recommended): APScheduler**

**Step 1:** Write `async def main()`:
- Log startup
- Run `run_daily_job()` once immediately
- Create `AsyncScheduler`
- Add job: `CronTrigger(hour=8, minute=0, timezone="Asia/Hong_Kong")` → `run_daily_job`
- `await scheduler.run_until_stopped()`

**Option B: schedule library**

**Step 1:** Write `def main()`:
- Log startup
- `asyncio.run(run_daily_job())` — immediate run
- `schedule.every().day.at("08:00", "Asia/Hong_Kong").do(lambda: asyncio.run(run_daily_job()))`
- `while True: schedule.run_pending(); time.sleep(30)`

**Step 2:** Add `if __name__ == "__main__"` guard

**Acceptance Criteria:**
- [ ] Runs once immediately on startup
- [ ] Scheduled to run daily at 08:00 HKT
- [ ] Runs indefinitely without exiting
- [ ] Clean shutdown on SIGTERM (for Docker)

---

#### Task 10: Error Handling & Logging

**Files:**
- Modify: `main.py` — add logging config, wrap all entry points

**Step 1:** Configure `logging` at module level:
- Format: `%(asctime)s [%(levelname)s] %(message)s`
- Level: INFO
- Stream: stdout (Docker captures)

**Step 2:** Ensure all functions log:
- Startup: env var presence check (not values!)
- Per-topic: fetch count, filter result length, errors
- Webhook: status code, success/failure
- Schedule: next run time

**Step 3:** Add startup validation:
- Check all 6 env vars are set (DISCORD_WEBHOOK_URL, OPENROUTER_API_KEY, X_USERNAME, X_PASSWORD, X_EMAIL, X_EMAIL_PW)
- Fail fast with clear error if any missing

**Acceptance Criteria:**
- [ ] All output to stdout with timestamps
- [ ] Missing env vars cause immediate clear error
- [ ] Per-topic errors logged with topic name
- [ ] No secrets logged

---

### Phase F: Validation (T11)

#### Task 11: Integration Testing & Validation

**Step 1:** Manual dry-run checklist:
- [ ] `docker build -t discord-tech-bot .` succeeds
- [ ] Container starts with all env vars
- [ ] twscrape login succeeds (or reuses session)
- [ ] RSS feeds fetched concurrently (check logs for 11 feeds)
- [ ] Reddit feeds succeed with custom User-Agent
- [ ] All 7 topics fetch posts from both RSS + X (check logs)
- [ ] Merged posts show RSS first, then X, no duplicates
- [ ] OpenRouter AI summaries return Traditional Chinese text
- [ ] Model fallback works if primary model fails
- [ ] If all AI models fail, raw posts shown with warning
- [ ] All 7 embeds appear in Discord channel
- [ ] Embeds have correct colors, titles, footer timestamps
- [ ] Total embed character count under 6000
- [ ] Error in one topic doesn't crash others
- [ ] Container survives restart (accounts.db persisted)
- [ ] Scheduled run fires at 08:00 HKT next day

**Step 2:** Edge case validation:
- [ ] Simulate OpenRouter API failure → fallback model tried → raw posts if all fail
- [ ] Simulate empty tweet results + empty RSS → "⚠️ 內容不足" shown
- [ ] Simulate missing env var → clear startup error
- [ ] Simulate broken RSS feed (Printables/Thingiverse) → warning logged, other feeds unaffected
- [ ] Simulate Reddit 429 → logged, topic still has X data

---

## Risk Register

| # | Risk | Prob | Impact | Mitigation | Contingency |
|---|---|---|---|---|---|
| R1 | X account suspension | High | Critical | Cookie-based login; low volume (70 tweets/day); inter-topic delay | Backup account in pool; RSS feeds provide baseline content even if X is down |
| R2 | 6000-char embed limit exceeded | Medium | High | Per-embed budget ~800 chars; truncation in embed builder | Split into 2 webhook POSTs |
| R3 | Zero tweet results | Medium | Medium | Fallback query with lower min_faves; RSS feeds supplement | "⚠️ 內容不足" embed; RSS-only content |
| R4 | OpenRouter free tier exhausted or down | Medium | Medium | 7 req/day fits within ~20 daily limit; model fallback chain (Llama → Gemma) | Skip AI filtering; send raw posts with "⚠️ AI 摘要不可用" |
| R5 | Docker volume not mounted | Medium | Medium | Document volume mount; auto-detect missing DB | Re-run login flow |
| R6 | Schedule drift on restart | Low | Low | Run on startup; restart policy | Dedup check (last-run timestamp) |
| R7 | `schedule` async conflict | High | Medium | Use APScheduler AsyncScheduler | Thread-based schedule fallback |
| R8 | RSS feed unavailable (Printables/Thingiverse) | High | Low | Mark as optional; log warning; other feeds + X provide content | Drop broken feed; rely on remaining sources |
| R9 | Reddit RSS returns 429/403 | Medium | Low | Custom User-Agent header (`DiscordTechBot/1.0`); single fetch per run | Log warning; topic still has X data |
| R10 | OpenRouter free model latency spikes (30-120s) | Medium | Low | Generous 60s timeout; daily batch job tolerates delay | Skip to fallback model after timeout |

---

## Open Questions

1. **Schedule time:** ~~Spec says "13:30 HKT" in overview, "08:00 HKT" in Scheduling section.~~ **Resolved: 13:30 HKT (user confirmed).**
2. **APScheduler vs schedule:** Research strongly recommends APScheduler for async compatibility. Spec lists `schedule` in requirements.txt. Plan documents both options — implementer should confirm.
3. **twscrape account count:** Single account for ~70 tweets/day should be safe, but account suspension risk is reduced by RSS providing baseline content.
4. **OpenRouter daily limit:** ~20 req/day without credits. Consider purchasing $5 credits for ~200 req/day safety margin if bot is critical.
5. **`mistralai/mistral-7b-instruct:free`:** Research indicates this variant may no longer exist. Removed from fallback chain. If user wants a third fallback, verify availability at runtime.
6. **Printables + Thingiverse RSS:** Research indicates these feeds are unverified/unreliable. Plan handles gracefully but these may produce zero content.
7. **Multi-topic RSS feeds (Hackster, Adafruit):** These cover multiple topics. AI filter must assign entries to the correct topic. Alternative: assign all entries from these feeds to their most-likely topic only.

---

## Out of Scope (Explicit)

- Discord gateway bot functionality (slash commands, presence, reactions)
- Multi-channel or multi-server posting
- Web dashboard or admin UI
- CI/CD pipeline
- Automated testing framework
- Monitoring/alerting/health checks beyond basic logging
- Tweet caching or deduplication across days
- User-configurable topics at runtime
- Paid AI model usage (staying on free tier)
- RSS feed discovery or auto-configuration

---

## Next Steps

1. **Review** this plan for completeness and correctness
2. **Confirm** open questions (schedule time, APScheduler vs schedule)
3. **Implement** via `superpowers:executing-plans` — task-by-task with TDD
4. **Validate** per Task 11 checklist
