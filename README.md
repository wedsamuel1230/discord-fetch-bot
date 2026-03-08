# Discord Daily Tech Bot

Automated daily digest of 6 tech topics posted to a Discord channel every afternoon at **13:30 HKT**.

**Version:** v1.3.0  
**Sources:** Public X discovery via DuckDuckGo + FxTwitter hydration, plus expanded RSS feeds  
**AI:** OpenRouter free-tier models (StepFun → Arcee → Llama fallback) → Traditional Chinese summaries  
**Delivery:** Digest webhook + separate init/status webhook  
**Deployment:** Docker container on Home Assistant OS  
**Notable:** No X API login required — public discovery eliminates twscrape/Nitter complexity

## Topics

| # | Topic | RSS Sources | X Query |
|---|-------|-------------|---------|
| 1 | 🤖 AI | OpenAI News, Hugging Face Blog, Google AI Blog, HN AI, Reddit AI feeds | ✅ |
| 2 | 🔌 ESP32 | r/esp32, Adafruit ESP32, Hackaday ESP32 | ✅ |
| 3 | 🔌 RP2040/RP2350 | r/RP2040, Raspberry Pi News, Hackaday RP2040 | ✅ |
| 4 | 🔌 Arduino | r/arduino, Arduino Blog, Adafruit | ✅ |
| 5 | 🛠️ Maker | Hackaday, Adafruit, Make:, r/maker, r/DIY | ✅ |
| 6 | 🖨️ 3D列印 | r/3Dprinting, Prusa Blog, 3D Printing Industry, VoxelMatters, 3Dnatives | ✅ |

\* Multi-topic feed — entries assigned by keyword matching  
† If a feed is unreachable, the bot logs and skips it gracefully

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

The X path no longer depends on logged-in scraping. The bot discovers recent `x.com/.../status/...` posts per topic with DuckDuckGo, then hydrates those posts through FxTwitter's public API.

## Environment Variables

| Variable | Description |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for 6-embed digest delivery |
| `DISCORD_INIT_WEBHOOK_URL` | Separate Discord webhook for boot init messages and daily self-update notices |
| `OPENROUTER_API_KEY` | OpenRouter API key — free tier at [openrouter.ai](https://openrouter.ai/) |
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

**Rate limits:** Free tier ~20 req/day (7 topics; one run fits). Purchase $5 credits for ~200/day buffer or production stability.

## Schedule & Notifications

**Daily Run:** 13:30 HKT (`Asia/Hong_Kong` timezone)

**Init Webhook:** On boot, the bot posts an init message to `DISCORD_INIT_WEBHOOK_URL` (separate channel recommended for ops visibility).

**Self-Update:** After each digest delivery, the bot checks the configured git remote (`SELF_UPDATE_REPO_PATH`, default `origin`). If `SELF_UPDATE_ENABLED=true` and the working tree is clean, it safely fast-forwards the local branch. If the working tree is dirty (uncommitted changes), the pull is skipped (fail-closed safety).

**Startup Mode:**
- `RUN_ON_STARTUP=true` — Runs immediately on boot, then again at 13:30 HKT
- `RUN_ON_STARTUP=false` — Silent boot; first run at 13:30 HKT (recommended)

## Notes

- **v1.3.0 architecture:** Removed `twscrape` and Nitter fallback entirely. Now uses public DuckDuckGo search for X status URLs + FxTwitter public API hydration. **No X API login required.**
- **Public discovery:** All X posts sourced through keyword discovery + public FxTwitter API. Eliminates account management and session complexity; improves reliability.
- **Self-update fail-closed:** If the working tree has uncommitted changes, the bot skips pulling rather than risking data loss or conflicts.
- **Separate init webhook:** Ops can route `DISCORD_INIT_WEBHOOK_URL` to a private channel for boot logs and self-update notices; digest goes to `DISCORD_WEBHOOK_URL`.
- **Broad feeds are keyword-routed:** Adafruit, Hackaday, Make:, and Raspberry Pi News span multiple topics (AI, embedded, maker) and are assigned by title/summary keyword matching.
- **Discord 6000-char limit:** Enforced at embed build time — longest descriptions are trimmed if total exceeds 5800 chars per Discord guidelines.
- **Single file:** All bot logic in `main.py` (~600 lines); async architecture with APScheduler 3.x for scheduling.

---

## Troubleshooting

**X posts not appearing?**
- Check DuckDuckGo search availability in your region (no VPN = simpler).
- Verify `OPENROUTER_API_KEY` is valid and has available quota.
- Check logs for `FxTwitter` or `DuckDuckGo` errors; if either is down, RSS feeds alone will still post.

**Discord webhook 429 (rate-limited)?**
- Retry is built in. Check log for backoff messages.
- If frequent, consider spacing topics or reducing feed sources.

**Self-update not working?**
- Ensure `SELF_UPDATE_ENABLED=true` and all three variables (`SELF_UPDATE_REPO_PATH`, `SELF_UPDATE_REMOTE`, `SELF_UPDATE_BRANCH`) are set correctly.
- Check that the bot's working tree is clean (no uncommitted changes).
- Verify git remote is accessible from the container.
