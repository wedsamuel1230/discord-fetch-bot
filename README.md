# Discord Daily Tech Bot

Automated daily digest of 6 tech topics posted to a Discord channel every afternoon at **13:30 HKT**.

**Sources:** X (Twitter) via `twscrape` + 11 RSS feeds  
**AI:** OpenRouter free-tier models → Traditional Chinese summaries  
**Delivery:** Single Discord webhook POST (6 themed embeds)  
**Deployment:** Docker container on Home Assistant OS

## Topics

| # | Topic | RSS Sources | X Query |
|---|-------|-------------|---------|
| 1 | 🤖 AI | Hacker News (AI/LLM) | ✅ |
| 2 | 🔌 ESP32 | r/esp32, Hackster\*, Adafruit\* | ✅ |
| 3 | 🔌 RP2040/RP2350 | r/RP2040, Hackster\*, Adafruit\* | ✅ |
| 4 | 🔌 Arduino | r/arduino, Hackster\*, Adafruit\* | ✅ |
| 5 | 🛠️ Maker | Hackaday, Adafruit\*, r/maker | ✅ |
| 6 | 🖨️ 3D列印 | r/3Dprinting, Printables, Thingiverse | ✅ |

\* Multi-topic feed — entries assigned by keyword matching  
† Unverified feed — may be unreachable; bot gracefully skips if broken

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

If `twscrape` login is blocked by Cloudflare/IP reputation, the bot now automatically falls back to Nitter search RSS for X-topic coverage.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |
| `OPENROUTER_API_KEY` | OpenRouter API key — free tier at [openrouter.ai](https://openrouter.ai/) |
| `X_USERNAME` | X (Twitter) username |
| `X_PASSWORD` | X (Twitter) password |
| `X_EMAIL` | Email address for X account |
| `X_EMAIL_PW` | Email password (used by twscrape for login verification) |
| `NITTER_BASE_URLS` | Optional comma-separated fallback mirrors for X search RSS |
| `RUN_ON_STARTUP` | `true` to run immediately on boot; default `false` (silent boot) |

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

## Persistence

`data/accounts.db` stores twscrape session cookies. The volume mount `./data:/app/data` ensures logins survive container restarts.

## Schedule

Runs daily at **13:30 HKT** (`Asia/Hong_Kong` timezone). Startup run is optional via `RUN_ON_STARTUP`.

To avoid sending anything while booting, set:

```env
RUN_ON_STARTUP=false
```

## Notes

- **X account risk:** twscrape uses cookie-based login (preferred). Bot fetches ~70 tweets/day — well within safe limits. A second backup account can be added to the pool.
- **Cloudflare block handling:** if twscrape has no active account, topic-level X retrieval falls back to Nitter search RSS mirrors.
- **Mirror override:** set `NITTER_BASE_URLS` in `.env` if default mirrors are blocked from your network.
- **Hackster / Adafruit feeds** cover multiple topics; entries are assigned via keyword matching in the title/summary. The AI filter refines further.
- **Printables / Thingiverse RSS** use primary URLs plus built-in fallback URLs, so feed collection still works when primary URLs return 404.
- **Discord 6000-char limit:** Enforced at build time — longest descriptions are trimmed if total exceeds 5800 chars.
