#!/usr/bin/env python3
"""Discord Daily Tech Bot.

Daily tech news digest from follow-builders upstream feeds and local RSS,
filtered and
summarised into Traditional Chinese via OpenRouter AI, then delivered as
5 themed Discord embeds every afternoon at 13:30 HKT.

Architecture : single-file async Python app
Data sources : follow-builders upstream feed JSON + RSS feeds via httpx/feedparser
AI           : OpenRouter free-tier models (OpenAI-compatible REST)
Delivery     : Discord webhooks for digest + init status
Scheduler    : APScheduler AsyncIOScheduler + CronTrigger at 13:30 HKT

AI model fallback chain (verify IDs at https://openrouter.ai/models):
    1. stepfun/step-3.5-flash:free            (StepFun Step 3.5 Flash — primary)
    2. arcee-ai/trinity-large-preview:free    (Arcee Trinity Large Preview — fallback)
    3. meta-llama/llama-3.2-3b-instruct:free  (extra free fallback)
"""
from __future__ import annotations

import asyncio
import calendar
import html
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import feedparser
import httpx
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ─── Constants ────────────────────────────────────────────────────────────────
HKT = pytz.timezone("Asia/Hong_Kong")
USER_AGENT = "DiscordTechBot/1.0"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REPO_PATH = os.environ.get("SELF_UPDATE_REPO_PATH", ".")
DIGEST_MODE_FB_HYBRID = "follow-builders-hybrid"
DIGEST_MODE_FB_ONLY = "follow-builders-only"
VALID_DIGEST_MODES = {
    DIGEST_MODE_FB_HYBRID,
    DIGEST_MODE_FB_ONLY,
}
SOURCE_ROLLOUT_WAVE1 = "wave1"
SOURCE_ROLLOUT_WAVE2 = "wave2"
VALID_SOURCE_ROLLOUT_MODES = {
    SOURCE_ROLLOUT_WAVE1,
    SOURCE_ROLLOUT_WAVE2,
}
VALID_FB_SOURCE_MODES = {"central", "pinned"}
DEFAULT_FB_BASE_URL = (
    "https://raw.githubusercontent.com/zarazhangrui/follow-builders/{ref}"
)
DEFAULT_FB_MIRROR_BASE_URLS: tuple[str, ...] = (
    "https://raw.githubusercontent.com/zarazhangrui/follow-builders/{ref}",
    "https://cdn.jsdelivr.net/gh/zarazhangrui/follow-builders@{ref}",
)
DEFAULT_FB_CACHE_PATH = "data/follow_builders_cache.json"
DEFAULT_TOPIC_X_RSS_BASE_URLS: tuple[str, ...] = (
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.rawbit.ninja",
    "https://nitter.1d4.us",
)
DISCORD_RENDER_LIMITS: dict[str, int] = {
    "compact_body_default": 56,
    "compact_body_ai_builder": 85,
    "embed_description_max": 4096,
    "total_payload_soft_max": 5800,
    "trim_step": 50,
}
DISCORD_LINK_SEPARATOR = " ｜ "

# AI model fallback cascade — update IDs if they differ on openrouter.ai/models
OPENROUTER_MODELS: list[str] = [
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

# ─── Environment Validation ───────────────────────────────────────────────────
_REQUIRED_ENV = [
    "DISCORD_WEBHOOK_URL",
    "OPENROUTER_API_KEY",
]


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse truthy/falsy env values safely."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Parse integer env values safely."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def validate_env() -> dict[str, str]:
    """Fail fast if any required env var is missing. Logs names only (no values)."""
    missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        log.error("❌ Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    digest_mode = os.environ.get("DIGEST_MODE", DIGEST_MODE_FB_HYBRID).strip().lower()
    if digest_mode not in VALID_DIGEST_MODES:
        log.error(
            "❌ DIGEST_MODE must be one of: %s",
            ", ".join(sorted(VALID_DIGEST_MODES)),
        )
        sys.exit(1)

    source_mode = (
        os.environ.get("FOLLOW_BUILDERS_SOURCE_MODE", "central").strip().lower()
    )
    if source_mode not in VALID_FB_SOURCE_MODES:
        log.error(
            "❌ FOLLOW_BUILDERS_SOURCE_MODE must be one of: %s",
            ", ".join(sorted(VALID_FB_SOURCE_MODES)),
        )
        sys.exit(1)

    pinned_ref = os.environ.get("FOLLOW_BUILDERS_PINNED_REF", "").strip()
    if source_mode == "pinned" and not pinned_ref:
        log.error(
            "❌ FOLLOW_BUILDERS_PINNED_REF is required when "
            "FOLLOW_BUILDERS_SOURCE_MODE=pinned"
        )
        sys.exit(1)

    fb_ref = pinned_ref if source_mode == "pinned" and pinned_ref else "main"
    source_rollout_mode = (
        os.environ.get("SOURCE_ROLLOUT_MODE", SOURCE_ROLLOUT_WAVE1).strip().lower()
    )
    if source_rollout_mode not in VALID_SOURCE_ROLLOUT_MODES:
        log.error(
            "❌ SOURCE_ROLLOUT_MODE must be one of: %s",
            ", ".join(sorted(VALID_SOURCE_ROLLOUT_MODES)),
        )
        sys.exit(1)

    default_fb_base_urls = [
        template.format(ref=fb_ref) for template in DEFAULT_FB_MIRROR_BASE_URLS
    ]
    raw_fb_base_urls = os.environ.get(
        "FOLLOW_BUILDERS_BASE_URLS",
        ",".join(default_fb_base_urls),
    )
    fb_base_urls = [
        part.strip().rstrip("/")
        for part in raw_fb_base_urls.split(",")
        if part.strip()
    ]
    if not fb_base_urls:
        fb_base_urls = default_fb_base_urls

    primary_fb_base_url = fb_base_urls[0]
    init_webhook_url = os.environ.get("DISCORD_INIT_WEBHOOK_URL", "").strip()

    cfg = {k: os.environ[k] for k in _REQUIRED_ENV}
    cfg.update(
        {
            "DISCORD_INIT_WEBHOOK_URL": init_webhook_url
            or cfg["DISCORD_WEBHOOK_URL"],
            "DIGEST_MODE": digest_mode,
            "FOLLOW_BUILDERS_SOURCE_MODE": source_mode,
            "FOLLOW_BUILDERS_PINNED_REF": pinned_ref,
            "SOURCE_ROLLOUT_MODE": source_rollout_mode,
            "FOLLOW_BUILDERS_BASE_URLS": ",".join(fb_base_urls),
            "FOLLOW_BUILDERS_FEED_X_URL": os.environ.get(
                "FOLLOW_BUILDERS_FEED_X_URL",
                f"{primary_fb_base_url}/feed-x.json",
            ),
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL": os.environ.get(
                "FOLLOW_BUILDERS_FEED_PODCASTS_URL",
                f"{primary_fb_base_url}/feed-podcasts.json",
            ),
            "FOLLOW_BUILDERS_FEED_BLOGS_URL": os.environ.get(
                "FOLLOW_BUILDERS_FEED_BLOGS_URL",
                f"{primary_fb_base_url}/feed-blogs.json",
            ),
            "FOLLOW_BUILDERS_CACHE_ENABLED": str(
                _env_bool("FOLLOW_BUILDERS_CACHE_ENABLED", default=True)
            ).lower(),
            "FOLLOW_BUILDERS_CACHE_TTL_HOURS": str(
                max(1, _env_int("FOLLOW_BUILDERS_CACHE_TTL_HOURS", default=48))
            ),
            "FOLLOW_BUILDERS_CACHE_PATH": os.environ.get(
                "FOLLOW_BUILDERS_CACHE_PATH",
                DEFAULT_FB_CACHE_PATH,
            ),
            "MAKER_RSS_ENABLED": str(_env_bool("MAKER_RSS_ENABLED", default=True)).lower(),
            "MAKER_RSS_TOPIC_SET": os.environ.get(
                "MAKER_RSS_TOPIC_SET",
                "ESP32,RP2040,Arduino,3D列印",
            ),
            "TOPIC_X_ENABLED": str(_env_bool("TOPIC_X_ENABLED", default=True)).lower(),
            "TOPIC_X_LOOKBACK_HOURS": str(
                max(1, _env_int("TOPIC_X_LOOKBACK_HOURS", default=24))
            ),
            "TOPIC_X_RSS_BASE_URLS": os.environ.get(
                "TOPIC_X_RSS_BASE_URLS",
                ",".join(DEFAULT_TOPIC_X_RSS_BASE_URLS),
            ),
            "TOPIC_YOUTUBE_ENABLED": str(
                _env_bool("TOPIC_YOUTUBE_ENABLED", default=True)
            ).lower(),
            "YOUTUBE_LOOKBACK_HOURS": str(
                max(1, _env_int("YOUTUBE_LOOKBACK_HOURS", default=48))
            ),
            "YOUTUBE_MAX_ITEMS_PER_CHANNEL": str(
                max(1, _env_int("YOUTUBE_MAX_ITEMS_PER_CHANNEL", default=2))
            ),
        }
    )

    log.info("✅ All env vars present: %s", ", ".join(_REQUIRED_ENV))
    return cfg


# ─── Topic Configuration ──────────────────────────────────────────────────────
TOPICS: list[dict[str, Any]] = [
    {
        "name": "AI",
        "emoji": "🤖",
        "color": 0x5865F2,
        "fetch_limit": 10,
        "discover_queries": [
            "AI agent open source model",
            "LLM release inference benchmark",
        ],
        "rss_feeds": [
            "openai_news",
            "huggingface_blog",
            "google_ai_blog",
            "hn_ai",
            "reddit_machinelearning",
            "reddit_artificial",
            "reddit_openai",
            "reddit_chatgpt",
            "reddit_localllama",
            "reddit_singularity",
        ],
        "x_handles": [
            "karpathy",
            "swyx",
            "joshwoodward",
            "petergyang",
            "_catwu",
            "amasad",
            "rauchg",
            "levie",
            "garrytan",
            "danshipper",
            "steipete",
            "dotey",
            "vista8",
            "Khazix0918",
        ],
    },
    {
        "name": "ESP32",
        "emoji": "🔌",
        "color": 0x57F287,
        "fetch_limit": 10,
        "discover_queries": [
            "ESP32 project esp-idf firmware",
            "ESP32 tutorial board library",
        ],
        "rss_feeds": [
            "reddit_esp32",
            "adafruit_esp32",
            "hackaday_esp32",
            "adafruit",
            "adafruit_learning",
            "hackaday",
            "makezine",
            "reddit_maker",
            "reddit_diy",
            "reddit_electronics",
            "reddit_microcontrollers",
            "reddit_embedded",
        ],
        "x_handles": [
            "EspressifSystem",
            "adafruit",
            "sparkfun",
            "pimoroni",
            "hackaday",
            "SeeedStudio",
            "unexpectedmaker",
            "cnxsoft",
            "Raspberry_Pi",
            "arduino",
        ],
    },
    {
        "name": "RP2040",
        "emoji": "🔌",
        "color": 0x2ECC71,
        "fetch_limit": 10,
        "discover_queries": [
            "RP2040 RP2350 Pico 2 project",
            "Raspberry Pi Pico firmware board",
        ],
        "rss_feeds": [
            "reddit_rp2040",
            "raspberry_pi_news",
            "hackaday_rp2040",
            "adafruit",
            "adafruit_learning",
            "hackaday",
            "makezine",
            "reddit_maker",
            "reddit_diy",
            "reddit_electronics",
            "reddit_microcontrollers",
            "reddit_embedded",
        ],
        "x_handles": [
            "Raspberry_Pi",
            "pimoroni",
            "adafruit",
            "sparkfun",
            "hackaday",
            "SeeedStudio",
            "ThePiHut",
            "JeffGeerling",
            "tomshardware",
            "cytrontech",
        ],
    },
    {
        "name": "Arduino",
        "emoji": "🔌",
        "color": 0x00979D,
        "fetch_limit": 10,
        "discover_queries": [
            "Arduino project tutorial shield library",
            "Arduino build release maker",
        ],
        "rss_feeds": [
            "reddit_arduino",
            "arduino_blog",
            "adafruit",
            "adafruit_learning",
            "hackaday",
            "makezine",
            "reddit_maker",
            "reddit_diy",
            "reddit_electronics",
            "reddit_microcontrollers",
            "reddit_embedded",
        ],
        "x_handles": [
            "arduino",
            "adafruit",
            "sparkfun",
            "hackaday",
            "make",
            "SeeedStudio",
            "dfrobotcn",
            "digikey",
            "MouserElec",
            "tindie",
        ],
    },
    {
        "name": "3D列印",
        "emoji": "🖨️",
        "color": 0xED4245,
        "fetch_limit": 10,
        "discover_queries": [
            "3D printing FDM resin print release",
            "3D printer model slicer filament",
        ],
        "rss_feeds": [
            "reddit_3dprinting",
            "prusa_blog",
            "3dprintingindustry",
            "voxelmatters",
            "3dnatives",
            "all3dp",
            "hackaday_3dprinting",
            "reddit_additivemanufacturing",
            "makezine",
            "reddit_diy",
        ],
        "x_handles": [
            "Prusa3D",
            "BambulabGlobal",
            "CNC_Kitchen",
            "makersmuse",
            "josefprusa",
            "all3dp",
            "3dprintindustry",
            "Formlabs",
            "Ultimaker",
            "eSUN3D",
        ],
    },
]


SOURCE_OVERLAYS: dict[str, dict[str, dict[str, list[str]]]] = {
    SOURCE_ROLLOUT_WAVE1: {
        "AI": {
            "x_handles": [
                "thdx",
                "mitchellh",
                "dhh",
                "jarredsumner",
                "jasonfried",
                "leerob",
                "ctatedev",
                "mattpocockuk",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@ThePrimeTimeagen",
                "https://www.youtube.com/@t3dotgg",
            ],
        },
        "ESP32": {
            "x_handles": [
                "sqfmi",
                "ladyada",
                "mbanzi",
                "dcuartielles",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@Dronebotworkshop",
                "https://www.youtube.com/@greatscottlab",
                "https://www.youtube.com/@HowToMechatronics",
            ],
        },
        "RP2040": {
            "x_handles": [
                "EbenUpton",
                "ben_nuttall",
                "pjrc",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@BenEater",
                "https://www.youtube.com/@PhilsLab",
            ],
        },
        "Arduino": {
            "x_handles": [
                "mbanzi",
                "dcuartielles",
                "TheArduinoGuy",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@Dronebotworkshop",
                "https://www.youtube.com/@greatscottlab",
                "https://www.youtube.com/@HowToMechatronics",
            ],
        },
        "3D列印": {
            "x_handles": [
                "josefprusa",
                "RealSexyCyborg",
                "CNC_Kitchen",
                "makersmuse",
                "joeltelling",
                "toms3dp",
                "CHEP",
                "SarahGoehrke",
                "ProfPearce",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@makersmuse",
                "https://www.youtube.com/@CNC_Kitchen",
                "https://www.youtube.com/@greatscottlab",
                "https://www.youtube.com/@Dronebotworkshop",
                "https://www.youtube.com/@HowToMechatronics",
            ],
        },
    },
    SOURCE_ROLLOUT_WAVE2: {
        "AI": {
            "x_handles": [
                "zeeg",
                "karrisaarinen",
                "kepano",
                "trq212",
                "bcherny",
                "lennysan",
                "shadcn",
                "emilkowalski",
                "jh3yy",
                "GergelyOrosz",
                "theo",
                "ThePrimeagen",
                "jamwt",
                "jamesacowling",
                "glcst",
                "samlambert",
                "zachlloydtweets",
                "captainsafia",
                "threepointone",
                "aarondfrancis",
                "clairevo",
                "schickling",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@atmoio",
                "https://www.youtube.com/@rasmic",
            ],
        },
        "ESP32": {
            "x_handles": [
                "beneater",
                "GreatScottLab",
                "mightyohm",
                "EEVblog",
                "Chris_Gammell",
                "BigClive",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@artfulbytes",
                "https://www.youtube.com/@PhilsLab",
            ],
        },
        "RP2040": {
            "x_handles": [
                "OpenBuilds",
                "bdring",
                "FarmBot",
                "echoshack",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@opensourcecnc",
            ],
        },
        "Arduino": {
            "x_handles": [
                "chr1sa",
                "gabriella_sneel",
                "HumansforRobots",
                "x2robotics",
                "zengirl2",
            ],
            "youtube_channels": [
                "https://www.youtube.com/@Jeremy_Fielding",
                "https://www.youtube.com/@Skyentific",
            ],
        },
        "3D列印": {
            "x_handles": [
                "OpenBuilds",
                "bdring",
                "FarmBot",
                "chr1sa",
                "mbanzi",
            ],
            "youtube_channels": [
                "https://www.youtube.com/user/jamesbruton",
                "https://www.youtube.com/@FireballTool",
                "https://www.youtube.com/@SienciLabs",
                "https://www.youtube.com/nyccnc",
            ],
        },
    },
}


def _dedupe_preserve(values: list[str], case_insensitive: bool = True) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower() if case_insensitive else value
        if not value or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _source_rollout_mode(cfg: dict[str, str]) -> str:
    mode = (cfg.get("SOURCE_ROLLOUT_MODE") or SOURCE_ROLLOUT_WAVE1).strip().lower()
    if mode not in VALID_SOURCE_ROLLOUT_MODES:
        return SOURCE_ROLLOUT_WAVE1
    return mode


def _normalize_x_handle(value: str) -> str:
    handle = str(value or "").strip().lstrip("@")
    if not handle:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "", handle)
    return cleaned


def _normalize_youtube_channel_seed(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("@"):  # already a handle
        return "@" + raw[1:].strip().lower()
    if raw.startswith("UC") and len(raw) >= 24:
        return raw

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.netloc.lower()
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        return ""

    path_parts = [p for p in parsed.path.split("/") if p]
    if not path_parts:
        return ""

    first = path_parts[0]
    if first.startswith("@"):
        return first.lower()

    if first == "channel" and len(path_parts) > 1 and path_parts[1].startswith("UC"):
        return path_parts[1]

    if first in {"c", "user"} and len(path_parts) > 1:
        return "@" + path_parts[1].strip().lower()

    return ""


def _topic_overlay_payload(topic_name: str, cfg: dict[str, str]) -> dict[str, list[str]]:
    wave = _source_rollout_mode(cfg)
    wave1_payload = SOURCE_OVERLAYS.get(SOURCE_ROLLOUT_WAVE1, {}).get(topic_name, {})
    if wave == SOURCE_ROLLOUT_WAVE1:
        return {
            "x_handles": list(wave1_payload.get("x_handles", [])),
            "youtube_channels": list(wave1_payload.get("youtube_channels", [])),
        }

    wave2_payload = SOURCE_OVERLAYS.get(SOURCE_ROLLOUT_WAVE2, {}).get(topic_name, {})
    return {
        "x_handles": list(wave1_payload.get("x_handles", []))
        + list(wave2_payload.get("x_handles", [])),
        "youtube_channels": list(wave1_payload.get("youtube_channels", []))
        + list(wave2_payload.get("youtube_channels", [])),
    }


def _topic_runtime_x_handles(topic: dict[str, Any], cfg: dict[str, str]) -> list[str]:
    base = [_normalize_x_handle(v) for v in (topic.get("x_handles") or [])]
    overlay = [
        _normalize_x_handle(v)
        for v in _topic_overlay_payload(str(topic.get("name") or ""), cfg).get(
            "x_handles", []
        )
    ]
    return _dedupe_preserve([v for v in base + overlay if v])


def _topic_runtime_youtube_channels(topic: dict[str, Any], cfg: dict[str, str]) -> list[str]:
    if cfg.get("TOPIC_YOUTUBE_ENABLED", "true") != "true":
        return []

    base = [
        _normalize_youtube_channel_seed(v)
        for v in (topic.get("youtube_channels") or [])
    ]
    overlay = [
        _normalize_youtube_channel_seed(v)
        for v in _topic_overlay_payload(str(topic.get("name") or ""), cfg).get(
            "youtube_channels", []
        )
    ]
    return _dedupe_preserve([v for v in base + overlay if v])


TOPIC_ORDER = {topic["name"]: index for index, topic in enumerate(TOPICS)}

# ─── RSS Feed Configuration ───────────────────────────────────────────────────
RSS_FEEDS: dict[str, str] = {
    "openai_news": "https://openai.com/news/rss.xml",
    "huggingface_blog": "https://huggingface.co/blog/feed.xml",
    "google_ai_blog": "https://blog.google/technology/ai/rss/",
    "hn_ai": "https://hnrss.org/newest?q=AI+LLM&points=10",
    "reddit_machinelearning": "https://www.reddit.com/r/MachineLearning/.rss",
    "reddit_artificial": "https://www.reddit.com/r/artificial/.rss",
    "reddit_openai": "https://www.reddit.com/r/OpenAI/.rss",
    "reddit_chatgpt": "https://www.reddit.com/r/ChatGPT/.rss",
    "reddit_localllama": "https://www.reddit.com/r/LocalLLaMA/.rss",
    "reddit_singularity": "https://www.reddit.com/r/singularity/.rss",
    "arduino_blog": "https://blog.arduino.cc/feed/",
    "raspberry_pi_news": "https://www.raspberrypi.com/news/feed/",
    "adafruit": "https://blog.adafruit.com/feed/",
    "adafruit_esp32": "https://blog.adafruit.com/category/esp32/feed/",
    "adafruit_learning": "https://learn.adafruit.com/feed",
    "hackaday": "https://hackaday.com/blog/feed/",
    "hackaday_esp32": "https://hackaday.com/tag/esp32/feed/",
    "hackaday_rp2040": "https://hackaday.com/tag/rp2040/feed/",
    "hackaday_3dprinting": "https://hackaday.com/tag/3d-printing/feed/",
    "makezine": "https://makezine.com/feed/",
    "reddit_esp32": "https://www.reddit.com/r/esp32/.rss",
    "reddit_arduino": "https://www.reddit.com/r/arduino/.rss",
    "reddit_rp2040": "https://www.reddit.com/r/RP2040/.rss",
    "reddit_maker": "https://www.reddit.com/r/maker/.rss",
    "reddit_diy": "https://www.reddit.com/r/DIY/.rss",
    "reddit_electronics": "https://www.reddit.com/r/electronics/.rss",
    "reddit_microcontrollers": "https://www.reddit.com/r/microcontrollers/.rss",
    "reddit_embedded": "https://www.reddit.com/r/embedded/.rss",
    "reddit_3dprinting": "https://www.reddit.com/r/3Dprinting/.rss",
    "reddit_additivemanufacturing": "https://www.reddit.com/r/AdditiveManufacturing/.rss",
    "prusa_blog": "https://blog.prusa3d.com/feed/",
    "3dprintingindustry": "https://3dprintingindustry.com/feed/",
    "voxelmatters": "https://www.voxelmatters.com/feed/",
    "3dnatives": "https://www.3dnatives.com/en/feed/",
    "all3dp": "https://all3dp.com/feed/",
}

RSS_FEED_FALLBACKS: dict[str, list[str]] = {
    "google_ai_blog": ["https://ai.googleblog.com/feeds/posts/default"],
}

# Broad feeds span multiple topics — keyword match determines assignment.
_MULTI_TOPIC_FEEDS: frozenset[str] = frozenset({
    "adafruit",
    "hackaday",
    "makezine",
    "raspberry_pi_news",
})

_MULTI_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "ESP32":  ["esp32", "esp-32", "esp-idf"],
    "RP2040": ["rp2040", "rp2350", "pico w", "pico 2", "raspberry pi pico", "circuitpython", "rp-series"],
    "Arduino": ["arduino"],
    "3D列印": ["3d print", "3dprint", "fdm", "resin", "filament", "sla"],
}

# ─── Utilities ────────────────────────────────────────────────────────────────

def strip_html(text: str, max_len: int = 300) -> str:
    """Unescape HTML entities, remove tags, collapse whitespace, truncate."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _entry_datetime(entry: Any) -> Optional[datetime]:
    """Return UTC-aware datetime from a feedparser entry (checks published then updated)."""
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val is not None:
            try:
                return datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
            except Exception:
                pass
    return None


# ─── T3b: RSS Feed Fetching ────────────────────────────────────────────────────

async def _fetch_one_feed(
    client: httpx.AsyncClient, key: str, url: str
) -> tuple[str, list[dict[str, Any]]]:
    """Fetch + parse one RSS/Atom feed. Never raises; logs warnings on failure."""
    candidate_urls = [url] + RSS_FEED_FALLBACKS.get(key, [])
    parsed = None
    selected_url = ""
    selected_status = None

    for candidate in candidate_urls:
        try:
            resp = await client.get(
                candidate,
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
                follow_redirects=True,
            )
            current_parsed = feedparser.parse(resp.text)
            entry_count = len(getattr(current_parsed, "entries", []))

            # Accept normal success, or Thingiverse's odd behavior where /rss may return 404 but still contain feed data.
            if (200 <= resp.status_code < 400 and entry_count > 0) or (
                key == "thingiverse" and entry_count > 0
            ):
                parsed = current_parsed
                selected_url = candidate
                selected_status = resp.status_code
                break

            log.warning(
                "RSS candidate unusable [%s] %s: status=%s entries=%d",
                key,
                candidate,
                resp.status_code,
                entry_count,
            )
        except Exception as exc:
            log.warning("RSS fetch failed [%s] %s: %s", key, candidate, exc)

    if parsed is None:
        return key, []

    if parsed.get("bozo"):
        log.warning(
            "RSS bozo flag [%s]: %s", key, parsed.get("bozo_exception", "unknown")
        )

    now_utc = datetime.now(tz=timezone.utc)
    cutoff = now_utc - timedelta(hours=24)
    all_entries = list(parsed.entries)[:20]

    # Prefer recent entries; fall back to latest 3 if none are within 24h
    recent = [
        e
        for e in all_entries
        if (dt := _entry_datetime(e)) is not None and dt >= cutoff
    ]
    if not recent:
        recent = all_entries[:3]
    recent = recent[:5]

    entries: list[dict[str, Any]] = []
    for entry in recent:
        title = strip_html(getattr(entry, "title", "") or "", 200)
        link = getattr(entry, "link", "") or ""
        raw_summary = (
            getattr(entry, "summary", "")
            or (getattr(entry, "content", None) or [{}])[0].get("value", "")
            or ""
        )
        summary = strip_html(raw_summary, 300)
        if title and link:
            entries.append(
                {"source": "rss", "title": title, "link": link, "summary": summary}
            )

    log.info(
        "RSS [%s]: %d entries (url=%s status=%s)",
        key,
        len(entries),
        selected_url,
        selected_status,
    )
    return key, entries


async def fetch_all_rss(
    client: httpx.AsyncClient,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch all configured RSS feeds concurrently."""
    tasks = [_fetch_one_feed(client, k, u) for k, u in RSS_FEEDS.items()]
    results = await asyncio.gather(*tasks)
    return dict(results)


def _multi_feed_match(entry: dict[str, Any], topic_name: str) -> bool:
    """Return True if entry keywords suggest it belongs to this topic."""
    keywords = _MULTI_TOPIC_KEYWORDS.get(topic_name, [])
    if not keywords:
        # No keyword restriction defined for this topic in multi-topic feeds
        return True
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw in text for kw in keywords)


def get_rss_for_topic(
    all_rss: dict[str, list[dict[str, Any]]],
    topic: dict[str, Any],
) -> list[dict[str, Any]]:
    """Collect RSS entries mapped to a topic, applying keyword filter for multi-topic feeds."""
    seen_links: set[str] = set()
    result: list[dict[str, Any]] = []
    for feed_key in topic["rss_feeds"]:
        for entry in all_rss.get(feed_key, []):
            if feed_key in _MULTI_TOPIC_FEEDS and not _multi_feed_match(
                entry, topic["name"]
            ):
                continue
            link = entry.get("link", "")
            if link and link in seen_links:
                continue
            seen_links.add(link)
            result.append(entry)
    return result


def _maker_topic_set(cfg: dict[str, str]) -> set[str]:
    raw = cfg.get("MAKER_RSS_TOPIC_SET", "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def _follow_builders_base_urls(cfg: dict[str, str]) -> list[str]:
    raw = cfg.get("FOLLOW_BUILDERS_BASE_URLS", "")
    urls = [part.strip().rstrip("/") for part in raw.split(",") if part.strip()]
    return urls


def _follow_builders_feed_candidates(
    cfg: dict[str, str],
    feed_filename: str,
    explicit_url_key: str,
) -> list[str]:
    candidates: list[str] = []
    explicit = (cfg.get(explicit_url_key) or "").strip()
    if explicit:
        candidates.append(explicit)

    for base in _follow_builders_base_urls(cfg):
        candidates.append(f"{base}/{feed_filename}")

    deduped: list[str] = []
    seen: set[str] = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def _read_follow_builders_cache(cfg: dict[str, str]) -> Optional[dict[str, Any]]:
    if cfg.get("FOLLOW_BUILDERS_CACHE_ENABLED", "true") != "true":
        return None

    cache_path = (cfg.get("FOLLOW_BUILDERS_CACHE_PATH") or DEFAULT_FB_CACHE_PATH).strip()
    try:
        ttl_hours = max(1, int(cfg.get("FOLLOW_BUILDERS_CACHE_TTL_HOURS", "48")))
    except ValueError:
        ttl_hours = 48

    if not cache_path or not os.path.exists(cache_path):
        return None

    age_seconds = time.time() - os.path.getmtime(cache_path)
    if age_seconds > ttl_hours * 3600:
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception as exc:
        log.warning("Failed reading follow-builders cache: %s", exc)
        return None


def _write_follow_builders_cache(cfg: dict[str, str], payload: dict[str, Any]) -> None:
    if cfg.get("FOLLOW_BUILDERS_CACHE_ENABLED", "true") != "true":
        return

    cache_path = (cfg.get("FOLLOW_BUILDERS_CACHE_PATH") or DEFAULT_FB_CACHE_PATH).strip()
    if not cache_path:
        return

    try:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
    except Exception as exc:
        log.warning("Failed writing follow-builders cache: %s", exc)


def _topic_x_enabled(cfg: dict[str, str]) -> bool:
    return cfg.get("TOPIC_X_ENABLED", "true") == "true"


def _topic_x_lookback_hours(cfg: dict[str, str]) -> int:
    raw = cfg.get("TOPIC_X_LOOKBACK_HOURS", "24")
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return 24


def _topic_x_rss_base_urls(cfg: dict[str, str]) -> list[str]:
    raw = cfg.get("TOPIC_X_RSS_BASE_URLS", "")
    urls = [part.strip().rstrip("/") for part in raw.split(",") if part.strip()]
    if not urls:
        return list(DEFAULT_TOPIC_X_RSS_BASE_URLS)
    return urls


def _topic_youtube_enabled(cfg: dict[str, str]) -> bool:
    return cfg.get("TOPIC_YOUTUBE_ENABLED", "true") == "true"


def _youtube_lookback_hours(cfg: dict[str, str]) -> int:
    raw = cfg.get("YOUTUBE_LOOKBACK_HOURS", "48")
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return 48


def _youtube_items_per_channel(cfg: dict[str, str]) -> int:
    raw = cfg.get("YOUTUBE_MAX_ITEMS_PER_CHANNEL", "2")
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return 2


_YOUTUBE_CHANNEL_ID_CACHE: dict[str, str] = {}


def _extract_youtube_channel_id_from_html(html_text: str) -> str:
    patterns = (
        r'itemprop="channelId"\s+content="(UC[\w-]{20,})"',
        r'"channelId"\s*:\s*"(UC[\w-]{20,})"',
    )
    for pattern in patterns:
        match = re.search(pattern, html_text)
        if match:
            return match.group(1)
    return ""


async def _resolve_youtube_channel_id(
    client: httpx.AsyncClient,
    channel_seed: str,
) -> str:
    if channel_seed.startswith("UC"):
        return channel_seed

    cached = _YOUTUBE_CHANNEL_ID_CACHE.get(channel_seed)
    if cached:
        return cached

    if not channel_seed.startswith("@"):
        return ""

    profile_url = f"https://www.youtube.com/{channel_seed}"
    try:
        resp = await client.get(
            profile_url,
            headers={"User-Agent": USER_AGENT},
            timeout=20.0,
            follow_redirects=True,
        )
        if not (200 <= resp.status_code < 400):
            return ""
        channel_id = _extract_youtube_channel_id_from_html(resp.text)
        if channel_id:
            _YOUTUBE_CHANNEL_ID_CACHE[channel_seed] = channel_id
        return channel_id
    except Exception:
        return ""


async def _fetch_topic_youtube_channel_posts(
    client: httpx.AsyncClient,
    channel_seed: str,
    cfg: dict[str, str],
) -> list[dict[str, Any]]:
    channel_id = await _resolve_youtube_channel_id(client, channel_seed)
    if not channel_id:
        return []

    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        resp = await client.get(
            feed_url,
            headers={"User-Agent": USER_AGENT},
            timeout=20.0,
            follow_redirects=True,
        )
        parsed = feedparser.parse(resp.text)
    except Exception:
        return []

    now_utc = datetime.now(tz=timezone.utc)
    cutoff = now_utc - timedelta(hours=_youtube_lookback_hours(cfg))
    all_entries = list(getattr(parsed, "entries", []))[:15]
    recent = [e for e in all_entries if (dt := _entry_datetime(e)) and dt >= cutoff]
    if not recent:
        recent = all_entries[: _youtube_items_per_channel(cfg)]
    recent = recent[: _youtube_items_per_channel(cfg)]

    posts: list[dict[str, Any]] = []
    label = channel_seed if channel_seed.startswith("@") else channel_id
    for entry in recent:
        title = strip_html(str(getattr(entry, "title", "") or ""), 200)
        summary = strip_html(str(getattr(entry, "summary", "") or title), 320)
        link = str(getattr(entry, "link", "") or "").strip()
        if not link:
            continue
        posts.append(
            {
                "source": "rss",
                "title": f"YouTube | {label}: {title}",
                "summary": summary,
                "link": link,
                "published": str(getattr(entry, "published", "") or ""),
            }
        )

    return posts


async def fetch_topic_youtube_posts(
    client: httpx.AsyncClient,
    topic: dict[str, Any],
    cfg: dict[str, str],
) -> list[dict[str, Any]]:
    if not _topic_youtube_enabled(cfg):
        return []

    channel_seeds = _topic_runtime_youtube_channels(topic, cfg)
    if not channel_seeds:
        return []

    tasks = [
        _fetch_topic_youtube_channel_posts(client, seed, cfg)
        for seed in channel_seeds
    ]
    buckets = await asyncio.gather(*tasks)

    merged: list[dict[str, Any]] = []
    seen_links: set[str] = set()
    for posts in buckets:
        for post in posts:
            link = str(post.get("link") or "").strip()
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            merged.append(post)

    target = topic.get("fetch_limit", 10)
    try:
        target_count = max(1, int(target))
    except (TypeError, ValueError):
        target_count = 10

    return merged[: max(target_count * 3, 15)]


async def _fetch_topic_x_handle_posts(
    client: httpx.AsyncClient,
    handle: str,
    cfg: dict[str, str],
) -> list[dict[str, Any]]:
    candidate_urls = [
        f"{base}/{handle.lstrip('@')}/rss" for base in _topic_x_rss_base_urls(cfg)
    ]

    parsed = None
    selected_url = ""
    selected_status = None

    for candidate in candidate_urls:
        try:
            resp = await client.get(
                candidate,
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
                follow_redirects=True,
            )
            current_parsed = feedparser.parse(resp.text)
            entry_count = len(getattr(current_parsed, "entries", []))
            if 200 <= resp.status_code < 400 and entry_count > 0:
                parsed = current_parsed
                selected_url = candidate
                selected_status = resp.status_code
                break
        except Exception as exc:
            log.warning("Topic-X fetch failed [%s] %s: %s", handle, candidate, exc)

    if parsed is None:
        return []

    now_utc = datetime.now(tz=timezone.utc)
    cutoff = now_utc - timedelta(hours=_topic_x_lookback_hours(cfg))
    all_entries = list(parsed.entries)[:20]

    recent = [
        e
        for e in all_entries
        if (dt := _entry_datetime(e)) is not None and dt >= cutoff
    ]
    if not recent:
        recent = all_entries[:3]
    recent = recent[:3]

    posts: list[dict[str, Any]] = []
    for entry in recent:
        title = strip_html(getattr(entry, "title", "") or "", 180)
        raw_summary = (
            getattr(entry, "summary", "")
            or (getattr(entry, "content", None) or [{}])[0].get("value", "")
            or ""
        )
        summary = strip_html(raw_summary, 320)
        content = summary or title
        if title and summary and title.lower() not in summary.lower():
            content = f"{title} — {summary}"

        url = str(getattr(entry, "link", "") or "").strip()
        if not content or not url:
            continue

        posts.append(
            {
                "source": "x",
                "author": handle.lstrip("@"),
                "content": content,
                "url": url,
                "like_count": 0,
            }
        )

    log.info(
        "Topic-X [%s]: %d posts (url=%s status=%s)",
        handle,
        len(posts),
        selected_url,
        selected_status,
    )
    return posts


async def fetch_topic_x_posts(
    client: httpx.AsyncClient,
    topic: dict[str, Any],
    cfg: dict[str, str],
) -> list[dict[str, Any]]:
    """Fetch topic-specific Xer posts via public RSS mirrors."""
    if not _topic_x_enabled(cfg):
        return []

    handles = _topic_runtime_x_handles(topic, cfg)
    if not handles:
        return []

    tasks = [_fetch_topic_x_handle_posts(client, handle, cfg) for handle in handles]
    buckets = await asyncio.gather(*tasks)

    merged: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for posts in buckets:
        for post in posts:
            url = post.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            merged.append(post)

    target = topic.get("fetch_limit", 10)
    try:
        target_count = max(1, int(target))
    except (TypeError, ValueError):
        target_count = 10

    return merged[: max(target_count * 4, 20)]


async def _fetch_json_payload(
    client: httpx.AsyncClient, urls: list[str], label: str
) -> tuple[dict[str, Any], Optional[str]]:
    errors: list[str] = []
    for url in urls:
        try:
            resp = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=30.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, dict):
                raise ValueError(f"{label} payload is not an object")
            log.info("follow-builders %s source: %s", label, url)
            return payload, None
        except Exception as exc:
            errors.append(f"{url}: {exc}")

    if not errors:
        return {}, f"{label} feed error: no candidate URLs configured"
    return {}, f"{label} feed error: {'; '.join(errors[:2])}"


async def fetch_follow_builders_feeds(
    client: httpx.AsyncClient, cfg: dict[str, str]
) -> dict[str, Any]:
    """Fetch and normalize follow-builders upstream feed JSON payloads."""
    x_payload, x_error = await _fetch_json_payload(
        client,
        _follow_builders_feed_candidates(cfg, "feed-x.json", "FOLLOW_BUILDERS_FEED_X_URL"),
        "x",
    )
    podcasts_payload, podcasts_error = await _fetch_json_payload(
        client,
        _follow_builders_feed_candidates(
            cfg,
            "feed-podcasts.json",
            "FOLLOW_BUILDERS_FEED_PODCASTS_URL",
        ),
        "podcasts",
    )
    blogs_payload, blogs_error = await _fetch_json_payload(
        client,
        _follow_builders_feed_candidates(
            cfg,
            "feed-blogs.json",
            "FOLLOW_BUILDERS_FEED_BLOGS_URL",
        ),
        "blogs",
    )

    errors = [e for e in (x_error, podcasts_error, blogs_error) if e]

    builders: list[dict[str, Any]] = []
    for raw_builder in x_payload.get("x") or []:
        if not isinstance(raw_builder, dict):
            continue
        handle = str(raw_builder.get("handle") or "").strip()
        name = str(raw_builder.get("name") or handle or "Unknown").strip()

        tweets: list[dict[str, str]] = []
        for raw_tweet in raw_builder.get("tweets") or []:
            if not isinstance(raw_tweet, dict):
                continue
            text = strip_html(str(raw_tweet.get("text") or ""), 280)
            url = str(raw_tweet.get("url") or "").strip()
            if not text or not url:
                continue
            tweets.append({"text": text, "url": url})

        if tweets:
            builders.append(
                {
                    "name": name,
                    "handle": handle,
                    "tweets": tweets,
                }
            )

    podcasts: list[dict[str, str]] = []
    for raw_podcast in podcasts_payload.get("podcasts") or []:
        if not isinstance(raw_podcast, dict):
            continue
        name = str(raw_podcast.get("name") or "Podcast").strip()
        title = strip_html(str(raw_podcast.get("title") or "Untitled"), 180)
        url = str(raw_podcast.get("url") or "").strip()
        transcript = strip_html(str(raw_podcast.get("transcript") or ""), 400)
        if not url:
            continue
        podcasts.append(
            {
                "name": name,
                "title": title,
                "url": url,
                "transcript": transcript,
            }
        )

    blogs: list[dict[str, str]] = []
    for raw_blog in blogs_payload.get("blogs") or []:
        if not isinstance(raw_blog, dict):
            continue
        name = str(raw_blog.get("name") or "Blog").strip()
        title = strip_html(str(raw_blog.get("title") or "Untitled"), 180)
        url = str(raw_blog.get("url") or "").strip()
        content = strip_html(str(raw_blog.get("content") or ""), 400)
        if not url:
            continue
        blogs.append(
            {
                "name": name,
                "title": title,
                "url": url,
                "content": content,
            }
        )

    normalized = {
        "generated_at": x_payload.get("generatedAt")
        or podcasts_payload.get("generatedAt")
        or blogs_payload.get("generatedAt")
        or "",
        "builders": builders,
        "podcasts": podcasts,
        "blogs": blogs,
        "stats": {
            "x_builders": len(builders),
            "total_tweets": sum(len(b["tweets"]) for b in builders),
            "podcast_items": len(podcasts),
            "blog_items": len(blogs),
        },
        "errors": errors,
    }

    if builders or podcasts or blogs:
        _write_follow_builders_cache(cfg, normalized)
        return normalized

    cached = _read_follow_builders_cache(cfg)
    if cached:
        cached_errors = [str(err) for err in (cached.get("errors") or [])]
        cached_errors.extend(errors)
        cached_errors.append("using cached follow-builders data")
        cached_payload = dict(cached)
        cached_payload["errors"] = cached_errors
        log.warning("Using cached follow-builders data due to upstream fetch failure")
        return cached_payload

    return normalized


def build_ai_builder_summary(fb_data: dict[str, Any], max_lines: int = 10) -> str:
    """Render a concise AI-builder section from normalized follow-builders feed data."""
    lines: list[str] = []
    seen_urls: set[str] = set()

    for builder in fb_data.get("builders") or []:
        handle = str(builder.get("handle") or "").strip()
        name = str(builder.get("name") or handle or "Builder").strip()
        label = f"@{handle}" if handle else name

        for tweet in builder.get("tweets") or []:
            text = strip_html(str(tweet.get("text") or ""), 110)
            url = str(tweet.get("url") or "").strip()
            if not text or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            lines.append(f"• {label}: {text} {url}")
            break
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines:
        for item in fb_data.get("podcasts") or []:
            title = strip_html(str(item.get("title") or "Podcast update"), 95)
            name = strip_html(str(item.get("name") or "Podcast"), 40)
            url = str(item.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            lines.append(f"• 🎙 {name}: {title} {url}")
            if len(lines) >= max_lines:
                break

    if len(lines) < max_lines:
        for item in fb_data.get("blogs") or []:
            title = strip_html(str(item.get("title") or "Blog update"), 95)
            name = strip_html(str(item.get("name") or "Blog"), 40)
            url = str(item.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            lines.append(f"• 📝 {name}: {title} {url}")
            if len(lines) >= max_lines:
                break

    if not lines:
        return "NO_CONTENT"

    return _compact_summary_for_discord(
        "\n".join(lines),
        max_body_len=DISCORD_RENDER_LIMITS["compact_body_ai_builder"],
    )


def _fb_data_to_posts(fb_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert follow-builders normalized payload into ai_filter-compatible posts."""
    posts: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for builder in fb_data.get("builders") or []:
        handle = str(builder.get("handle") or "").strip()
        author = handle or str(builder.get("name") or "builder").strip()
        for tweet in builder.get("tweets") or []:
            content = strip_html(str(tweet.get("text") or ""), 500)
            url = str(tweet.get("url") or "").strip()
            if not content or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            posts.append(
                {
                    "source": "x",
                    "author": author,
                    "content": content,
                    "url": url,
                    "like_count": 0,
                }
            )

    for podcast in fb_data.get("podcasts") or []:
        url = str(podcast.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        title = strip_html(str(podcast.get("title") or "Podcast"), 220)
        summary = strip_html(
            str(podcast.get("transcript") or title),
            320,
        )
        name = strip_html(str(podcast.get("name") or "Podcast"), 80)
        posts.append(
            {
                "source": "rss",
                "title": f"Podcast | {name}: {title}",
                "link": url,
                "summary": summary,
            }
        )

    for blog in fb_data.get("blogs") or []:
        url = str(blog.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        title = strip_html(str(blog.get("title") or "Blog"), 220)
        summary = strip_html(
            str(blog.get("content") or title),
            320,
        )
        name = strip_html(str(blog.get("name") or "Blog"), 80)
        posts.append(
            {
                "source": "rss",
                "title": f"Blog | {name}: {title}",
                "link": url,
                "summary": summary,
            }
        )

    return posts


# ─── T4: AI Filtering (OpenRouter) ────────────────────────────────────────────

def _format_for_prompt(posts: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, p in enumerate(posts, 1):
        if p["source"] == "x":
            lines.append(
                f"{i}. [X] @{p['author']}: {p['content'][:400]} | {p['url']}"
            )
        else:
            lines.append(
                f"{i}. [RSS] {p['title']}: {p['summary'][:300]} | {p['link']}"
            )
    return "\n".join(lines)


def _raw_fallback(posts: list[dict[str, Any]], max_items: int = 10) -> str:
    lines = ["⚠️ AI 摘要不可用（原始資料）"]
    for p in posts[:max_items]:
        if p["source"] == "x":
            snippet = p.get("content", "")[:150]
            lines.append(f"• @{p['author']}: {snippet}…\n  {p['url']}")
        else:
            snippet = p.get("summary", "")[:150]
            lines.append(f"• {p['title']}: {snippet}…\n  {p['link']}")
    return "\n".join(lines)


def _split_summary_bullets(summary: str) -> list[str]:
    raw_lines = [line.strip() for line in summary.splitlines() if line.strip()]
    bullets: list[str] = []
    current = ""

    for line in raw_lines:
        if line.startswith("•"):
            if current:
                bullets.append(current)
            current = line
        elif current:
            current += " " + line
        else:
            current = "• " + line

    if current:
        bullets.append(current)
    return bullets


def _compact_bullet_for_discord(raw_bullet: str, max_body_len: int) -> str:
    normalized = re.sub(r"\s+", " ", raw_bullet).strip()
    url_match = re.search(r"https?://\S+", normalized)

    body = normalized[1:].strip() if normalized.startswith("•") else normalized
    url = ""
    if url_match:
        url = url_match.group(0)
        body = normalized[: url_match.start()].lstrip("•").strip()

    if len(body) > max_body_len:
        body = body[: max_body_len - 1].rstrip(" ,;:，；：") + "…"

    if url:
        return f"• {body}{DISCORD_LINK_SEPARATOR}{url}"
    return f"• {body}"


def _compact_summary_for_discord(
    summary: str,
    max_body_len: int = DISCORD_RENDER_LIMITS["compact_body_default"],
) -> str:
    """Normalize AI output into compact one-line bullets for Discord embeds."""
    if not summary:
        return ""

    stripped = summary.strip()
    if stripped in {"NO_CONTENT", ""}:
        return stripped

    compacted = [
        _compact_bullet_for_discord(bullet, max_body_len)
        for bullet in _split_summary_bullets(stripped)
    ]

    return "\n".join(compacted)


async def ai_filter(
    client: httpx.AsyncClient,
    posts: list[dict[str, Any]],
    topic: dict[str, Any],
    cfg: dict[str, str],
) -> str:
    """Summarise posts in Traditional Chinese via OpenRouter with model fallback cascade."""
    if not posts:
        return "NO_CONTENT"

    target_items = topic.get("fetch_limit", 10)
    try:
        target_items = max(1, int(target_items))
    except (TypeError, ValueError):
        target_items = 10

    target_char_budget = min(1600, max(700, target_items * 95))

    chip_restriction = ""
    if topic["name"] in ("ESP32", "RP2040", "Arduino"):
        chip_restriction = (
            f"Only keep posts specifically about {topic['name']}. "
            "Remove posts about unrelated microcontrollers or SBCs. "
        )

    system_msg = (
        "You are a tech news curator. All output must be in Traditional Chinese "
        "(繁體中文). Be concise and informative."
    )
    user_msg = (
        f"Topic: {topic['emoji']} {topic['name']}\n\n"
        f"Posts:\n{_format_for_prompt(posts)}\n\n"
        "Instructions:\n"
        f"- {chip_restriction}"
        "- Remove ads, promotional content, reposts, and off-topic posts.\n"
        f"- Keep the best {target_items} posts.\n"
        f"- Output exactly {target_items} bullet lines when enough quality posts are available.\n"
        "- For each, write one short Traditional Chinese line in 'why it matters' style, followed by the URL on the same line.\n"
        "- Keep each line brief and skimmable; do not write full 2-sentence summaries.\n"
        "- Format: one post per line, each starting with • \n"
        "- If no posts are valuable, respond with exactly: NO_CONTENT\n"
        f"- Total response must be under {target_char_budget} characters."
    )

    for model in OPENROUTER_MODELS:
        try:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {cfg['OPENROUTER_API_KEY']}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/discord-tech-bot",
                    "X-Title": "Discord Tech Bot",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 900,
                    "temperature": 0.3,
                },
                timeout=60.0,  # free-tier models can be slow
            )

            if resp.status_code != 200:
                log.warning(
                    "OpenRouter [%s] HTTP %d for %s: %s",
                    model,
                    resp.status_code,
                    topic["name"],
                    resp.text[:200],
                )
                continue

            content = (
                resp.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if content is None:
                content = ""
            elif not isinstance(content, str):
                content = str(content)
            content = content.strip()
            if not content:
                log.warning(
                    "OpenRouter [%s] empty/null content for %s", model, topic["name"]
                )
                continue

            # Enforce per-topic char budget — trim at last complete bullet.
            if len(content) > target_char_budget:
                truncated = content[:target_char_budget].rsplit("\n•", 1)[0]
                content = (
                    truncated.rstrip() + "\n…"
                    if len(truncated) < len(content[:target_char_budget])
                    else content[: target_char_budget - 1] + "…"
                )
                log.warning(
                    "Truncated AI output for %s to fit %d-char budget",
                    topic["name"],
                    target_char_budget,
                )

            log.info("✅ AI [%s] → %s: %d chars", model, topic["name"], len(content))
            return content

        except Exception as exc:
            log.warning(
                "OpenRouter [%s] error for %s: %s", model, topic["name"], exc
            )
            continue

    log.error("All AI models exhausted for %s — raw fallback", topic["name"])
    return _raw_fallback(posts, max_items=target_items)


# ─── T5: Discord Embed Builder ────────────────────────────────────────────────

def _embed_for(topic: dict[str, Any], summary: str) -> dict[str, Any]:
    now_hkt = datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M")
    if not summary or summary.strip() in ("NO_CONTENT", ""):
        description = "⚠️ 今日暫無相關內容"
    else:
        description = _compact_summary_for_discord(summary)[
            : DISCORD_RENDER_LIMITS["embed_description_max"]
        ]
    return {
        "title": f"{topic['emoji']} {topic['name']} 每日精選",
        "description": description,
        "color": topic["color"],
        "footer": {"text": f"更新時間：{now_hkt} HKT"},
    }


def _error_embed(topic: dict[str, Any]) -> dict[str, Any]:
    now_hkt = datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M")
    return {
        "title": f"{topic['emoji']} {topic['name']} 每日精選",
        "description": "❌ 抓取失敗，請檢查 log",
        "color": topic["color"],
        "footer": {"text": f"更新時間：{now_hkt} HKT"},
    }


def _embed_char_len(embed: dict[str, Any]) -> int:
    return (
        len(embed.get("title", ""))
        + len(embed.get("description", ""))
        + len(embed.get("footer", {}).get("text", ""))
    )


def build_all_embeds(
    results: list[tuple[dict[str, Any], Optional[str]]],
) -> list[dict[str, Any]]:
    """Build embeds and trim descriptions if total exceeds Discord's 6000-char limit."""
    ordered_results = sorted(
        results,
        key=lambda item: TOPIC_ORDER.get(str(item[0].get("name") or ""), 999),
    )
    embeds = [
        _error_embed(topic) if summary is None else _embed_for(topic, summary)
        for topic, summary in ordered_results
    ]

    # Safety margin: keep total below soft cap (Discord hard limit is 6000)
    trim_step = DISCORD_RENDER_LIMITS["trim_step"]
    total_limit = DISCORD_RENDER_LIMITS["total_payload_soft_max"]
    total = sum(_embed_char_len(e) for e in embeds)
    while total > total_limit:
        longest_idx = max(
            range(len(embeds)), key=lambda i: len(embeds[i].get("description", ""))
        )
        desc = embeds[longest_idx].get("description", "")
        if len(desc) <= trim_step:
            break  # Nothing left to trim
        embeds[longest_idx]["description"] = desc[: len(desc) - trim_step] + "…"
        total = sum(_embed_char_len(e) for e in embeds)

    if total > total_limit:
        log.warning(
            "Total embed chars %d still above %d after trimming",
            total,
            total_limit,
        )

    return embeds


def _post_primary_url(post: dict[str, Any]) -> str:
    return str(post.get("url") or post.get("link") or "").strip()


# ─── T6: Discord Webhook Sender ───────────────────────────────────────────────

async def send_to_discord(
    client: httpx.AsyncClient,
    embeds: list[dict[str, Any]],
    cfg: dict[str, str],
) -> bool:
    """POST all embeds to Discord webhook; handles 429 with a single retry."""

    async def _post() -> httpx.Response:
        return await client.post(
            cfg["DISCORD_WEBHOOK_URL"],
            json={"embeds": embeds},
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    try:
        resp = await _post()
        if resp.status_code == 429:
            retry_after = float(resp.json().get("retry_after", 5))
            log.warning("Discord 429 — retrying after %.1fs", retry_after)
            await asyncio.sleep(retry_after)
            resp = await _post()

        if resp.status_code in (200, 204):
            log.info(
                "✅ Discord webhook delivered (%d embeds, HTTP %d)",
                len(embeds),
                resp.status_code,
            )
            return True

        log.error(
            "Discord webhook failed: HTTP %d — %s",
            resp.status_code,
            resp.text[:300],
        )
        return False

    except Exception as exc:
        log.error("Discord webhook exception: %s", exc)
        return False


async def send_init_message(
    client: httpx.AsyncClient,
    cfg: dict[str, str],
    branch: str,
    remote: str,
    rss_feed_count: int,
) -> bool:
    """Send a startup/init status message to a separate Discord webhook."""
    content = (
        f"Bot init | branch={branch or 'unknown'} remote={remote or 'origin'} "
        f"rss_feeds={rss_feed_count} topics={len(TOPICS)} "
        f"startup_run={str(_env_bool('RUN_ON_STARTUP', False)).lower()}"
    )

    try:
        target_url = (cfg.get("DISCORD_INIT_WEBHOOK_URL") or "").strip()
        if not target_url:
            target_url = cfg["DISCORD_WEBHOOK_URL"]
            log.info(
                "DISCORD_INIT_WEBHOOK_URL is empty; falling back to DISCORD_WEBHOOK_URL"
            )

        resp = await client.post(
            target_url,
            json={"content": content},
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )
        if resp.status_code in (200, 204):
            log.info("✅ Init webhook delivered")
            return True
        log.warning("Init webhook failed: HTTP %d", resp.status_code)
        return False
    except Exception as exc:
        log.warning("Init webhook exception: %s", exc)
        return False


def _git(repo_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", repo_path, *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # git not installed; return a failed CompletedProcess
        return subprocess.CompletedProcess(
            args=["git", *args], returncode=127, stdout="", stderr="git not found in PATH"
        )


def get_repo_tracking(repo_path: str = REPO_PATH) -> tuple[str, str]:
    """Get current branch and remote for repo, with graceful fallback if git unavailable."""
    try:
        branch_result = _git(repo_path, "branch", "--show-current")
        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()
        else:
            log.warning("Failed to get current git branch: %s", branch_result.stderr)
            branch = os.environ.get("SELF_UPDATE_BRANCH", "main")
    except Exception as exc:
        log.warning("Error querying git: %s; using fallback branch", exc)
        branch = os.environ.get("SELF_UPDATE_BRANCH", "main")
    
    remote = os.environ.get("SELF_UPDATE_REMOTE", "origin")
    return branch, remote


def check_and_apply_repo_update(repo_path: str = REPO_PATH) -> dict[str, Any]:
    """Fast-forward local repo to the configured remote branch when safe.
    
    Gracefully handles git unavailability (returns skipped status).
    """
    try:
        branch, remote = get_repo_tracking(repo_path)
        dirty_result = _git(repo_path, "status", "--short")
        
        # Check if git is available
        if dirty_result.returncode == 127:  # "command not found"
            log.warning("Git not available; skipping self-update")
            return {
                "status": "skipped",
                "reason": "git not installed",
                "branch": branch,
                "remote": remote,
            }
        
        dirty = dirty_result.stdout.strip()
        if dirty:
            return {
                "status": "skipped",
                "reason": "working tree is dirty",
                "branch": branch,
                "remote": remote,
            }

        fetch_result = _git(repo_path, "fetch", remote, branch)
        if fetch_result.returncode != 0:
            return {
                "status": "error",
                "reason": fetch_result.stderr.strip() or "git fetch failed",
                "branch": branch,
                "remote": remote,
            }

        before = _git(repo_path, "rev-parse", "HEAD").stdout.strip()
        after = _git(repo_path, "rev-parse", f"{remote}/{branch}").stdout.strip()
        if not before or not after:
            return {
                "status": "error",
                "reason": "unable to resolve git revisions",
                "branch": branch,
                "remote": remote,
            }
        if before == after:
            return {
                "status": "up-to-date",
                "branch": branch,
                "remote": remote,
                "before": before,
                "after": after,
            }

        pull_result = _git(repo_path, "pull", "--ff-only", remote, branch)
        if pull_result.returncode != 0:
            return {
                "status": "error",
                "reason": pull_result.stderr.strip() or "git pull failed",
                "branch": branch,
                "remote": remote,
                "before": before,
                "after": after,
            }

        return {
            "status": "updated",
            "branch": branch,
            "remote": remote,
            "before": before,
            "after": after,
        }
    except Exception as exc:
        log.warning("Unexpected error during repo update: %s; skipping", exc)
        return {
            "status": "skipped",
            "reason": f"exception: {exc}",
        }


def restart_current_process() -> None:
    """Restart the current Python process after a successful self-update."""
    log.info("Restarting process to load updated code")
    os.execv(sys.executable, [sys.executable, *sys.argv])


async def maybe_apply_repo_update(
    client: httpx.AsyncClient, cfg: dict[str, str]
) -> dict[str, Any]:
    if not _env_bool("SELF_UPDATE_ENABLED", default=True):
        return {"status": "skipped", "reason": "self-update disabled"}

    result = await asyncio.to_thread(check_and_apply_repo_update, REPO_PATH)
    status = result.get("status")
    if status == "updated":
        await client.post(
            cfg["DISCORD_INIT_WEBHOOK_URL"],
            json={
                "content": (
                    f"Bot update applied | branch={result['branch']} "
                    f"{result['before'][:7]}->{result['after'][:7]}"
                )
            },
            headers={"Content-Type": "application/json"},
            timeout=15.0,
        )
        restart_current_process()
    return result


# ─── T7: Orchestrator ─────────────────────────────────────────────────────────

async def run_daily_job(cfg: dict[str, str]) -> None:
    """
    Full daily pipeline:
      1. Fetch all RSS feeds concurrently (single batch).
            2. Build AI category from follow-builders feed.
            3. For non-AI categories (hybrid mode): RSS + AI filter.
            4. Build embeds and POST to Discord.

    Each topic is error-isolated — individual failures produce an error embed,
    not a crash of the whole job.
    """
    start = time.monotonic()
    log.info(
        "═══ Daily job started at %s HKT ═══",
        datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M:%S"),
    )

    digest_mode = cfg.get("DIGEST_MODE", DIGEST_MODE_FB_HYBRID)
    maker_enabled = cfg.get("MAKER_RSS_ENABLED", "true") == "true"
    maker_topics = _maker_topic_set(cfg)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        results: list[tuple[dict[str, Any], Optional[str]]] = []
        all_rss: dict[str, list[dict[str, Any]]] = {}

        if digest_mode == DIGEST_MODE_FB_HYBRID and maker_enabled:
            log.info("Fetching %d RSS feeds concurrently…", len(RSS_FEEDS))
            all_rss = await fetch_all_rss(client)

        ai_topic = next((topic for topic in TOPICS if topic["name"] == "AI"), TOPICS[0])
        fb_data = await fetch_follow_builders_feeds(client, cfg)
        if fb_data["errors"]:
            log.warning(
                "follow-builders feed warnings: %s",
                "; ".join(fb_data["errors"]),
            )
        fb_posts = _fb_data_to_posts(fb_data)

        ai_input_posts = list(fb_posts)
        if not ai_input_posts:
            log.warning(
                "follow-builders returned no AI posts; falling back to AI RSS sources"
            )
            if not all_rss:
                log.info("Fetching RSS feeds for AI fallback…")
                all_rss = await fetch_all_rss(client)
            ai_input_posts = get_rss_for_topic(all_rss, ai_topic)

        if ai_input_posts:
            ai_summary = await ai_filter(client, ai_input_posts, ai_topic, cfg)
        else:
            ai_summary = "NO_CONTENT"

        # Keep deterministic local fallback summary when model response is empty.
        if ai_summary in {"NO_CONTENT", ""}:
            if fb_posts:
                ai_summary = build_ai_builder_summary(
                    fb_data,
                    max_lines=ai_topic.get("fetch_limit", 10),
                )
            elif ai_input_posts:
                ai_summary = _raw_fallback(
                    ai_input_posts,
                    max_items=ai_topic.get("fetch_limit", 10),
                )

        results.append((ai_topic, ai_summary))

        if digest_mode == DIGEST_MODE_FB_HYBRID and maker_enabled:
            run_topics = [
                topic
                for topic in TOPICS
                if topic["name"] != "AI"
                and (not maker_topics or topic["name"] in maker_topics)
            ]
        else:
            run_topics = []

        for topic in run_topics:
            try:
                rss_posts = get_rss_for_topic(all_rss, topic)
                x_posts = await fetch_topic_x_posts(client, topic, cfg)
                youtube_posts = await fetch_topic_youtube_posts(client, topic, cfg)

                # Hybrid path for non-AI categories: topic-X + YouTube + RSS merged.
                seen_urls: set[str] = set()
                merged: list[dict[str, Any]] = []

                for post in x_posts:
                    url = _post_primary_url(post)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                for post in youtube_posts:
                    url = _post_primary_url(post)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                for post in rss_posts:
                    url = _post_primary_url(post)
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                log.info(
                    "%s: %d X + %d YouTube + %d RSS merged=%d",
                    topic["name"],
                    len(x_posts),
                    len(youtube_posts),
                    len(rss_posts),
                    len(merged),
                )
                if len(merged) < int(topic.get("fetch_limit", 10)):
                    log.warning(
                        "%s: fewer than %d posts available",
                        topic["name"],
                        int(topic.get("fetch_limit", 10)),
                    )

                summary = await ai_filter(client, merged, topic, cfg)
                results.append((topic, summary))

            except Exception as exc:
                log.error(
                    "Topic %s pipeline error: %s",
                    topic["name"],
                    exc,
                    exc_info=True,
                )
                results.append((topic, None))  # None → error embed

            # Brief pause between topics (reduces burst API pressure)
            await asyncio.sleep(2)

        # Phase 3 — deliver
        embeds = build_all_embeds(results)
        await send_to_discord(client, embeds, cfg)
        update_result = await maybe_apply_repo_update(client, cfg)
        if update_result.get("status") not in {"up-to-date", "skipped"}:
            log.info("Self-update result: %s", update_result)

    elapsed = time.monotonic() - start
    log.info("═══ Daily job complete in %.1fs ═══", elapsed)


# ─── T8: Scheduler & Main Loop ────────────────────────────────────────────────

async def main() -> None:
    """Entry point: validate env → run once → schedule daily at 13:30 HKT."""
    log.info("Discord Daily Tech Bot — starting up")

    # T10: startup validation (fail fast if env vars missing)
    cfg = validate_env()

    branch, remote = get_repo_tracking(REPO_PATH)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        await send_init_message(
            client,
            cfg,
            branch=branch,
            remote=remote,
            rss_feed_count=len(RSS_FEEDS),
        )

    async def _job() -> None:
        await run_daily_job(cfg)

    run_on_startup = _env_bool("RUN_ON_STARTUP", default=False)
    if run_on_startup:
        log.info("RUN_ON_STARTUP=true -> executing immediate startup run")
        await _job()
    else:
        log.info("RUN_ON_STARTUP=false -> skip immediate run; waiting for schedule")

    # Schedule daily at 13:30 HKT
    scheduler = AsyncIOScheduler(timezone=HKT)
    scheduler.add_job(_job, CronTrigger(hour=13, minute=30, timezone=HKT))
    scheduler.start()

    jobs = scheduler.get_jobs()
    if jobs:
        log.info("⏰ Next scheduled run: %s", jobs[0].next_run_time)

    try:
        # Keep event loop alive
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutdown signal — stopping scheduler")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
