# Discord Daily Tech Bot

Automated daily digest of 6 tech topics posted to a Discord channel every afternoon at **13:30 HKT**.

**Sources:** X discovery via DuckDuckGo + FxTwitter hydration, plus expanded RSS feeds  
**AI:** OpenRouter free-tier models → Traditional Chinese summaries  
**Delivery:** Digest webhook + separate init/status webhook  
**Deployment:** Docker container on Home Assistant OS

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
|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |
| `DISCORD_INIT_WEBHOOK_URL` | Separate Discord webhook for boot/init and self-update notices |
| `OPENROUTER_API_KEY` | OpenRouter API key — free tier at [openrouter.ai](https://openrouter.ai/) |
| `RUN_ON_STARTUP` | `true` to run immediately on boot; default `false` (silent boot) |
| `SELF_UPDATE_ENABLED` | `true` to let the bot fetch/pull daily when the local repo is clean |
| `SELF_UPDATE_REPO_PATH` | Local git repo path used for self-update checks |
| `SELF_UPDATE_REMOTE` | Remote name for self-update, default `origin` |
| `SELF_UPDATE_BRANCH` | Branch to fast-forward, default current branch or `main` |

## AI Model Cascade

Models are tried in order; if one fails the next is attempted:

| Priority | Model ID | Notes |
|----------|----------|-------|
| 1 Primary | `stepfun/step-3.5-flash:free` | StepFun Step 3.5 Flash (free) |
| 2 Fallback | `arcee-ai/trinity-large-preview:free` | Arcee Trinity Large Preview (free) |
| 3 Fallback | `meta-llama/llama-3.2-3b-instruct:free` | Extra free model |
| 4 Emergency | *(raw posts)* | Returned with ⚠️ prefix if all models fail |

> **Important:** Verify model IDs at [openrouter.ai/models](https://openrouter.ai/models) before deployment. Update `OPENROUTER_MODELS` in `main.py` if the IDs differ.

**Free-tier rate limit:** ~20 req/day without credits (7 topics/day fits). Purchase $5 credits for ~200/day buffer.

## Schedule

Runs daily at **13:30 HKT** (`Asia/Hong_Kong` timezone). Startup run is optional via `RUN_ON_STARTUP`. On boot, the bot sends an init message to `DISCORD_INIT_WEBHOOK_URL`. After each daily digest, it checks the configured git remote and fast-forwards the local checkout if the working tree is clean.

To avoid sending anything while booting, set:

```env
RUN_ON_STARTUP=false
```

## Notes

- **No X login required:** public discovery + hydration avoids the old twscrape/Nitter reliability problems.
- **Self-update is fail-closed:** if the local repo has uncommitted changes, the bot skips updating rather than risking a destructive pull.
- **Broad feeds are keyword-routed:** Adafruit, Hackaday, Make:, and Raspberry Pi News can land in multiple topics depending on title/summary matches.
- **Discord 6000-char limit:** Enforced at build time — longest descriptions are trimmed if total exceeds 5800 chars.
