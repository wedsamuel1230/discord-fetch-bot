# Discord Daily Tech Bot

Automated daily digest of 5 tech topics posted to a Discord channel every afternoon at **13:30 HKT**.

**Version:** v1.7.0  
**Sources:** follow-builders upstream feeds for AI builders + per-category Xer lists (public X RSS mirrors) + per-category YouTube channel feeds + distributed local RSS feeds  
**AI:** OpenRouter free-tier models (StepFun → Arcee → Llama fallback) → Traditional Chinese summaries  
**Delivery:** Digest webhook + separate init/status webhook  
**Deployment:** Docker container on Home Assistant OS  
**Notable:** Legacy ad-hoc X scraping remains removed. Modes now: `follow-builders-hybrid` and `follow-builders-only`.

## Topics

| # | Topic | Sources |
| --- | --- | --- |
| 1 | 🤖 AI | follow-builders curated feed (`feed-x`, `feed-podcasts`, `feed-blogs`) primary + AI RSS fallback (`OpenAI`, `Hugging Face`, `Google AI`, `HN AI`, `r/OpenAI`, `r/ChatGPT`, `r/LocalLLaMA`, `r/singularity`) |
| 2 | 🔌 ESP32 | ESP32 Xer list (>=10) + curated YouTube channels + r/esp32 + Adafruit ESP32 + Hackaday ESP32 + redistributed maker feeds |
| 3 | 🔌 RP2040/RP2350 | RP2040 Xer list (>=10) + curated YouTube channels + r/RP2040 + Raspberry Pi News + Hackaday RP2040 + redistributed maker feeds |
| 4 | 🔌 Arduino | Arduino Xer list (>=10) + curated YouTube channels + r/arduino + Arduino Blog + Adafruit + redistributed maker feeds |
| 5 | 🖨️ 3D列印 | 3D Xer list (>=10) + curated YouTube channels + r/3Dprinting + Prusa Blog + 3D Printing Industry + VoxelMatters + 3Dnatives + All3DP |

\* Multi-topic feed — entries assigned by keyword matching  
† If a feed is unreachable, the bot logs and skips it gracefully

## Category Xer Baseline

Each category now defines at least 10 Xers in code. Example requested handles are included in AI: `Khazix0918`, `dotey`, `vista8`.

Each non-AI category can also ingest curated YouTube channels (resolved to channel feeds at runtime) and merges them with topic-X and RSS sources.

AI runtime priority is follow-builders first; AI RSS feeds are used as fallback only when follow-builders inputs are empty/unavailable.

Digest target is set to 10 items per category (`fetch_limit=10`), and summarization prompts now request 10 bullet lines when enough quality inputs exist.

## Source Rollout Waves

The bot supports staged source expansion to reduce noise and runtime risk.

| Mode | Behavior |
| --- | --- |
| `wave1` | High-signal curated additions (default) |
| `wave2` | Full expanded source overlay from reference curation |

## Quick Start

```bash
# 1. Copy and fill env vars
cp .env.example .env
$EDITOR .env

# 2. Build and run
docker-compose up -d

# 3. Tail logs
docker-compose logs -f
```

In `follow-builders-hybrid` mode, the AI section is sourced from follow-builders upstream feed files (`feed-x.json`, `feed-podcasts.json`, `feed-blogs.json`) and remixed by OpenRouter into Traditional Chinese, while non-AI categories continue using local RSS.

## Digest Modes

| Mode | AI Source | Non-AI Source | Notes |
| --- | --- | --- | --- |
| `follow-builders-hybrid` | follow-builders upstream feeds | Local RSS | Recommended migration mode |
| `follow-builders-only` | follow-builders upstream feeds | Disabled | AI-builders-only digest |

## Environment Variables

| Variable | Description |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for digest delivery |
| `DISCORD_INIT_WEBHOOK_URL` | Optional separate webhook for boot init messages; falls back to `DISCORD_WEBHOOK_URL` when empty |
| `OPENROUTER_API_KEY` | OpenRouter API key — free tier at [openrouter.ai](https://openrouter.ai/) |
| `DIGEST_MODE` | `follow-builders-hybrid` or `follow-builders-only` |
| `FOLLOW_BUILDERS_SOURCE_MODE` | `central` (default) or `pinned` |
| `FOLLOW_BUILDERS_PINNED_REF` | Required when source mode is `pinned` |
| `SOURCE_ROLLOUT_MODE` | `wave1` (default) or `wave2` for staged source expansion |
| `FOLLOW_BUILDERS_BASE_URLS` | Comma-separated follow-builders base URLs tried in order (mirror failover) |
| `FOLLOW_BUILDERS_FEED_X_URL` | Optional override for upstream `feed-x.json` URL |
| `FOLLOW_BUILDERS_FEED_PODCASTS_URL` | Optional override for upstream `feed-podcasts.json` URL |
| `FOLLOW_BUILDERS_FEED_BLOGS_URL` | Optional override for upstream `feed-blogs.json` URL |
| `FOLLOW_BUILDERS_CACHE_ENABLED` | `true`/`false` local cache fallback for follow-builders feeds |
| `FOLLOW_BUILDERS_CACHE_TTL_HOURS` | Cache freshness window in hours, default `48` |
| `FOLLOW_BUILDERS_CACHE_PATH` | Cache file path, default `data/follow_builders_cache.json` |
| `MAKER_RSS_ENABLED` | `true`/`false` to control non-AI RSS categories in hybrid mode |
| `MAKER_RSS_TOPIC_SET` | Comma-separated non-AI categories (default `ESP32,RP2040,Arduino,3D列印`) |
| `TOPIC_X_ENABLED` | `true`/`false` to include per-category Xer ingestion |
| `TOPIC_X_LOOKBACK_HOURS` | Time window for topic-X recency filter, default `24` |
| `TOPIC_X_RSS_BASE_URLS` | Comma-separated RSS mirror base URLs used for handle timelines |
| `TOPIC_YOUTUBE_ENABLED` | `true`/`false` to include per-category YouTube channel ingestion |
| `YOUTUBE_LOOKBACK_HOURS` | Time window for YouTube recency filter, default `48` |
| `YOUTUBE_MAX_ITEMS_PER_CHANNEL` | Max items per YouTube channel per run, default `2` |
| `RUN_ON_STARTUP` | `true` to run immediately on boot; default `false` (silent boot, first run at 13:30 HKT) |
| `SELF_UPDATE_ENABLED` | `true` to check git remote daily and fast-forward pull when working tree is clean |
| `SELF_UPDATE_REPO_PATH` | Local git repo path used for self-update checks |
| `SELF_UPDATE_REMOTE` | Remote name for self-update pulls, default `origin` |
| `SELF_UPDATE_BRANCH` | Branch to fast-forward to, default current branch or `main` |

## AI Model Cascade

Models are tried in order; if one fails the next is attempted:

| Priority | Model ID | Notes |
| --- | --- | --- |
| 1 Primary | `stepfun-ai/step-3.5-flash` | StepFun Step 3.5 Flash (recommended) |
| 2 Fallback | `arcee-ai/arcee-trinity-large-preview` | Arcee Trinity Large Preview |
| 3 Fallback | `meta-llama/llama-3.2-3b-instruct` | Llama 3.2 3B extra capacity |
| 4 Emergency | *(raw posts)* | Returned with ⚠️ prefix if all models fail |

**Important:** Verify model IDs and free-tier status at [openrouter.ai/models](https://openrouter.ai/models). Update `OPENROUTER_MODELS` in `main.py` if IDs or availability change.

**Rate limits:** Free tier ~20 req/day (current hybrid mode typically uses 4 non-AI topic summarization calls per run). Purchase $5 credits for ~200/day buffer or production stability.

## Schedule & Notifications

**Daily Run:** 13:30 HKT (`Asia/Hong_Kong` timezone)

**Init Webhook:** On boot, the bot posts an init message to `DISCORD_INIT_WEBHOOK_URL`. If it is unset/empty, it falls back to `DISCORD_WEBHOOK_URL`.

**Self-Update:** After each digest delivery, the bot checks the configured git remote (`SELF_UPDATE_REPO_PATH`, default `origin`). If `SELF_UPDATE_ENABLED=true` and the working tree is clean, it safely fast-forwards the local branch. If the working tree is dirty (uncommitted changes), the pull is skipped (fail-closed safety).

**Startup Mode:**

- `RUN_ON_STARTUP=true` — Runs immediately on boot, then again at 13:30 HKT
- `RUN_ON_STARTUP=false` — Silent boot; first run at 13:30 HKT (recommended)

## Notes

- **v1.6.0 category-X mode:** Each category includes at least 10 Xers. Non-AI categories merge topic-X RSS posts with topic RSS before AI summarization.
- **v1.7.0 staged expansion:** Source overlays support `wave1`/`wave2` rollout with curated X + YouTube additions from reference lists.
- **v1.7.0 message refactor:** Discord bullet compaction now uses deterministic topic ordering and `body ｜ URL` formatting for higher scanability.
- **v1.5.0 migration mode:** Legacy ad-hoc X scraping is fully removed. AI content is sourced from follow-builders feeds; former Maker feeds are redistributed into ESP32/RP2040/Arduino/3D categories.
- **Builder-first philosophy:** The AI section follows follow-builders' intent to track top AI builders (researchers, founders, PMs, engineers) instead of generic influencer content.
- **Source control tradeoff:** `central` source mode tracks upstream curated source updates automatically; `pinned` mode gives deterministic behavior by locking to a specific follow-builders commit/tag.
- **Upstream API-key caveat:** This bot consumes published follow-builders feed JSON files and does not require `X_BEARER_TOKEN` / `SUPADATA_API_KEY` locally unless you choose to self-generate those feed files.
- **Self-update fail-closed:** If the working tree has uncommitted changes, the bot skips pulling rather than risking data loss or conflicts.
- **Separate init webhook:** Ops can route `DISCORD_INIT_WEBHOOK_URL` to a private channel for boot logs and self-update notices; digest goes to `DISCORD_WEBHOOK_URL`.
- **Follow-builders failover:** The bot tries configured `FOLLOW_BUILDERS_BASE_URLS` in order for each feed and can use local cache fallback when all upstream candidates fail temporarily.
- **Broad feeds are keyword-routed:** Adafruit, Hackaday, Make:, and Raspberry Pi News span multiple topics and are assigned by title/summary keyword matching.
- **Discord 6000-char limit:** Enforced at embed build time — longest descriptions are trimmed if total exceeds 5800 chars per Discord guidelines.
- **Single file:** All bot logic remains centralized in `main.py` (~2200+ lines); async architecture with APScheduler 3.x for scheduling.
- **Curation references:** New long-form source curation lists are kept in `memory-bank/ref/youtuber-to-add.md`, `memory-bank/ref/youtuber-to-add-grok.md`, and `memory-bank/ref/xer-to-add.md`; recent implementation notes are archived under `memory-bank/logs/`.

---

## Troubleshooting

**AI builder section empty?**

- Check accessibility of follow-builders feed URLs (`feed-x.json`, `feed-podcasts.json`, `feed-blogs.json`).
- If one origin is unstable, set `FOLLOW_BUILDERS_BASE_URLS` with multiple mirrors in priority order.
- Keep `FOLLOW_BUILDERS_CACHE_ENABLED=true` so short upstream outages can still serve recent data.
- If using pinned mode, confirm `FOLLOW_BUILDERS_PINNED_REF` points to an existing commit/tag.
- Verify `OPENROUTER_API_KEY` is valid and has available quota.
- Check logs for `follow-builders feed warnings` to identify malformed or unreachable upstream payloads.

**Discord webhook 429 (rate-limited)?**

- Retry is built in. Check log for backoff messages.
- If frequent, consider spacing topics or reducing feed sources.

**Self-update not working?**

- Ensure `SELF_UPDATE_ENABLED=true` and all three variables (`SELF_UPDATE_REPO_PATH`, `SELF_UPDATE_REMOTE`, `SELF_UPDATE_BRANCH`) are set correctly.
- Check that the bot's working tree is clean (no uncommitted changes).
- Verify git remote is accessible from the container.
