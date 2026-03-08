#!/usr/bin/env python3
"""Discord Daily Tech Bot.

Daily tech news digest from X (Twitter) and RSS feeds, filtered and
summarised into Traditional Chinese via OpenRouter AI, then delivered as
6 themed Discord embeds every afternoon at 13:30 HKT.

Architecture : single-file async Python app
Data sources : x-tweet-fetcher-style X discovery + RSS feeds via httpx/feedparser
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
import logging
import os
import re
import subprocess
import sys
import time
import warnings
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote, urlparse

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
SEARCH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FXTWITTER_API_BASE = "https://api.fxtwitter.com"
DUCKDUCKGO_HTML_SEARCH = "https://html.duckduckgo.com/html/"
STATUS_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/(\d+)"
)
REPO_PATH = os.environ.get("SELF_UPDATE_REPO_PATH", ".")

# AI model fallback cascade — update IDs if they differ on openrouter.ai/models
OPENROUTER_MODELS: list[str] = [
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

# ─── Environment Validation ───────────────────────────────────────────────────
_REQUIRED_ENV = [
    "DISCORD_WEBHOOK_URL",
    "DISCORD_INIT_WEBHOOK_URL",
    "OPENROUTER_API_KEY",
]


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse truthy/falsy env values safely."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def validate_env() -> dict[str, str]:
    """Fail fast if any required env var is missing. Logs names only (no values)."""
    missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        log.error("❌ Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)
    cfg = {k: os.environ[k] for k in _REQUIRED_ENV}
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
        ],
    },
    {
        "name": "Maker",
        "emoji": "🛠️",
        "color": 0xFEE75C,
        "fetch_limit": 10,
        "discover_queries": [
            "maker project diy electronics build",
            "hackaday makerspace fabrication tutorial",
        ],
        "rss_feeds": [
            "hackaday",
            "adafruit",
            "adafruit_learning",
            "makezine",
            "reddit_maker",
            "reddit_diy",
            "reddit_electronics",
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
            "hackaday_3dprinting",
        ],
    },
]

# ─── RSS Feed Configuration ───────────────────────────────────────────────────
RSS_FEEDS: dict[str, str] = {
    "openai_news": "https://openai.com/news/rss.xml",
    "huggingface_blog": "https://huggingface.co/blog/feed.xml",
    "google_ai_blog": "https://blog.google/technology/ai/rss/",
    "hn_ai": "https://hnrss.org/newest?q=AI+LLM&points=10",
    "reddit_machinelearning": "https://www.reddit.com/r/MachineLearning/.rss",
    "reddit_artificial": "https://www.reddit.com/r/artificial/.rss",
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
    "reddit_3dprinting": "https://www.reddit.com/r/3Dprinting/.rss",
    "prusa_blog": "https://blog.prusa3d.com/feed/",
    "3dprintingindustry": "https://3dprintingindustry.com/feed/",
    "voxelmatters": "https://www.voxelmatters.com/feed/",
    "3dnatives": "https://www.3dnatives.com/en/feed/",
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
    "Maker":  ["maker", "diy", "hack", "makerspace", "electronics", "project"],
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


# ─── T2/T3: X Discovery + FxTwitter Hydration ────────────────────────────────

def _normalize_x_status_url(url: str) -> Optional[str]:
    match = STATUS_URL_RE.search((url or "").strip())
    if not match:
        return None
    return f"https://x.com/{match.group(1)}/status/{match.group(2)}"


def _normalize_public_x_url(url: str) -> Optional[str]:
    candidate = html.unescape((url or "").strip()).rstrip(").,/")
    status_url = _normalize_x_status_url(candidate)
    if status_url:
        return status_url

    try:
        parsed = urlparse(candidate)
    except Exception:
        return None

    if parsed.netloc not in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        return None

    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) != 1:
        return None
    handle = segments[0]
    if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
        return None
    return f"https://x.com/{handle}"


def _discover_query_strings(topic: dict[str, Any]) -> list[str]:
    queries = topic.get("discover_queries") or []
    return queries if queries else [topic.get("name", "technology")]


def _discover_via_duckduckgo_html(query: str, limit: int) -> list[dict[str, str]]:
    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as client:
            resp = client.post(
                DUCKDUCKGO_HTML_SEARCH,
                data={"q": query},
                headers={"User-Agent": SEARCH_USER_AGENT},
            )
            resp.raise_for_status()
    except Exception as exc:
        log.warning("DuckDuckGo HTML discovery failed [%s]: %s", query, exc)
        return []

    matches = re.findall(
        r'https?://(?:www\.)?(?:x|twitter)\.com/[^"\'&<> ]+',
        resp.text,
    )
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_url in matches:
        normalized = _normalize_public_x_url(raw_url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        results.append({"url": normalized, "title": query, "snippet": query})
        if len(results) >= limit:
            break
    return results


def _discover_via_ddgs(query: str, limit: int) -> list[dict[str, str]]:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    results: list[dict[str, str]] = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=max(limit, 1)):
                    normalized = _normalize_public_x_url(
                        result.get("url") or result.get("href") or ""
                    )
                    if not normalized:
                        continue
                    results.append(
                        {
                            "url": normalized,
                            "title": (result.get("title") or "").strip(),
                            "snippet": (result.get("body") or result.get("snippet") or "").strip(),
                        }
                    )
        except Exception as exc:
            log.warning("DDGS discovery failed [%s]: %s", query, exc)
    return results


def _discover_via_google_news_rss(query: str, limit: int) -> list[dict[str, str]]:
    search_url = (
        "https://news.google.com/rss/search?q="
        f"{quote(f'site:x.com {query}')}&hl=en-US&gl=US&ceid=US:en"
    )
    try:
        parsed = feedparser.parse(search_url)
    except Exception as exc:
        log.warning("Google News RSS discovery failed [%s]: %s", query, exc)
        return []

    results: list[dict[str, str]] = []
    for entry in parsed.entries:
        source = getattr(entry, "source", {}) or {}
        source_title = str(source.get("title") or "")
        if source_title.lower() != "x.com":
            continue

        raw_title = strip_html(getattr(entry, "title", "") or "", 280)
        title = raw_title.removesuffix(" - x.com").strip()
        if not title:
            continue

        handle_match = re.search(r"\(@([A-Za-z0-9_]{1,15})\)", title)
        if handle_match:
            url = f"https://x.com/{handle_match.group(1)}"
        else:
            url = getattr(entry, "link", "") or ""

        results.append({"url": url, "title": title, "snippet": title})
        if len(results) >= limit:
            break

    return results


def discover_x_urls(topic: dict[str, Any], limit: int = 10) -> list[dict[str, str]]:
    """Discover X status URLs using the same search-first strategy as x-tweet-fetcher."""
    seen: set[str] = set()
    discovered: list[dict[str, str]] = []
    per_query_limit = max(limit, 1)

    for query in _discover_query_strings(topic):
        query_variants = [
            f"site:x.com {query}",
            f"site:twitter.com {query}",
            f"{query} x.com",
        ]
        for search_query in query_variants:
            for result in _discover_via_duckduckgo_html(search_query, per_query_limit):
                if result["url"] in seen:
                    continue
                seen.add(result["url"])
                discovered.append(result)
                if len(discovered) >= limit:
                    return discovered
            if len(discovered) >= limit:
                return discovered

        for result in _discover_via_google_news_rss(query, per_query_limit):
            if result["url"] in seen:
                continue
            seen.add(result["url"])
            discovered.append(result)
            if len(discovered) >= limit:
                return discovered

        for search_query in query_variants:
            for result in _discover_via_ddgs(search_query, per_query_limit):
                if result["url"] in seen:
                    continue
                seen.add(result["url"])
                discovered.append(result)
                if len(discovered) >= limit:
                    return discovered

    return discovered


async def fetch_fxtwitter_tweet(
    client: httpx.AsyncClient, url: str
) -> Optional[dict[str, Any]]:
    """Hydrate a discovered X status URL using FxTwitter's public API."""
    normalized = _normalize_x_status_url(url)
    if not normalized:
        return None

    match = STATUS_URL_RE.search(normalized)
    if not match:
        return None

    username, tweet_id = match.groups()
    api_url = f"{FXTWITTER_API_BASE}/{username}/status/{tweet_id}"

    try:
        resp = await client.get(
            api_url,
            headers={"User-Agent": USER_AGENT},
            timeout=30.0,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        log.warning("FxTwitter fetch failed [%s]: %s", normalized, exc)
        return None

    if payload.get("code") != 200:
        log.warning(
            "FxTwitter returned code %s for %s",
            payload.get("code"),
            normalized,
        )
        return None

    tweet = payload.get("tweet") or {}
    author = (tweet.get("author") or {}).get("screen_name") or username
    content = strip_html(tweet.get("text") or "", 500)
    if not content:
        return None

    return {
        "source": "x",
        "author": author,
        "content": content,
        "url": normalized,
        "like_count": int(tweet.get("likes") or 0),
        "retweet_count": int(tweet.get("retweets") or 0),
        "view_count": int(tweet.get("views") or 0),
        "created_at": tweet.get("created_at") or "",
    }


def _fallback_discovered_post(result: dict[str, str]) -> Optional[dict[str, Any]]:
    raw_url = result.get("url", "")
    normalized = _normalize_public_x_url(raw_url)
    final_url = normalized or raw_url
    if not final_url:
        return None

    author = "x"
    if normalized:
        parsed = urlparse(normalized)
        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments:
            author = segments[0]

    title = result.get("title") or ""
    handle_match = re.search(r"\(@([A-Za-z0-9_]{1,15})\)", title)
    if author == "x" and handle_match:
        author = handle_match.group(1)

    content = strip_html(result.get("snippet") or title, 280)
    if not content:
        return None

    return {
        "source": "x",
        "author": author,
        "content": content,
        "url": final_url,
        "like_count": 0,
    }


async def fetch_tweets(
    _unused_api: Any, topic: dict[str, Any], client: Optional[httpx.AsyncClient] = None
) -> list[dict[str, Any]]:
    """Discover public X posts and hydrate them via FxTwitter."""
    if client is None:
        return []

    discovered = discover_x_urls(topic, limit=topic["fetch_limit"])
    posts: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for result in discovered:
        post = await fetch_fxtwitter_tweet(client, result["url"])
        if post is None:
            post = _fallback_discovered_post(result)
        if not post:
            continue
        if post["url"] in seen_urls:
            continue
        posts.append(post)
        seen_urls.add(post["url"])

    log.info(
        "%s: %d discovered X posts (queries=%d)",
        topic["name"],
        len(posts),
        len(_discover_query_strings(topic)),
    )
    return posts


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
    """Fetch all 11 RSS feeds concurrently."""
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


def _raw_fallback(posts: list[dict[str, Any]]) -> str:
    lines = ["⚠️ AI 摘要不可用（原始資料）"]
    for p in posts[:5]:
        if p["source"] == "x":
            snippet = p.get("content", "")[:150]
            lines.append(f"• @{p['author']}: {snippet}…\n  {p['url']}")
        else:
            snippet = p.get("summary", "")[:150]
            lines.append(f"• {p['title']}: {snippet}…\n  {p['link']}")
    return "\n".join(lines)


async def ai_filter(
    client: httpx.AsyncClient,
    posts: list[dict[str, Any]],
    topic: dict[str, Any],
    cfg: dict[str, str],
) -> str:
    """Summarise posts in Traditional Chinese via OpenRouter with model fallback cascade."""
    if not posts:
        return "NO_CONTENT"

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
        "- Keep the best 3–5 posts.\n"
        "- For each, write 1–2 sentence Traditional Chinese summary followed by URL on the same line.\n"
        "- Format: one post per line, each starting with • \n"
        "- If no posts are valuable, respond with exactly: NO_CONTENT\n"
        "- Total response must be under 650 characters."
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
                    "max_tokens": 600,
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

            # Enforce 700-char budget — trim at last complete bullet
            if len(content) > 700:
                truncated = content[:700].rsplit("\n•", 1)[0]
                content = (
                    truncated.rstrip() + "\n…"
                    if len(truncated) < len(content[:700])
                    else content[:697] + "…"
                )
                log.warning(
                    "Truncated AI output for %s to fit 700-char budget", topic["name"]
                )

            log.info("✅ AI [%s] → %s: %d chars", model, topic["name"], len(content))
            return content

        except Exception as exc:
            log.warning(
                "OpenRouter [%s] error for %s: %s", model, topic["name"], exc
            )
            continue

    log.error("All AI models exhausted for %s — raw fallback", topic["name"])
    return _raw_fallback(posts)


# ─── T5: Discord Embed Builder ────────────────────────────────────────────────

def _embed_for(topic: dict[str, Any], summary: str) -> dict[str, Any]:
    now_hkt = datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M")
    if not summary or summary.strip() in ("NO_CONTENT", ""):
        description = "⚠️ 今日暫無相關內容"
    else:
        description = summary[:4096]  # hard Discord per-embed limit
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
    """Build 7 embeds and trim descriptions if total exceeds Discord's 6000-char limit."""
    embeds = [
        _error_embed(topic) if summary is None else _embed_for(topic, summary)
        for topic, summary in results
    ]

    # Safety margin: keep total below 5800 (Discord hard limit is 6000)
    total = sum(_embed_char_len(e) for e in embeds)
    while total > 5800:
        longest_idx = max(
            range(len(embeds)), key=lambda i: len(embeds[i].get("description", ""))
        )
        desc = embeds[longest_idx].get("description", "")
        if len(desc) <= 50:
            break  # Nothing left to trim
        embeds[longest_idx]["description"] = desc[: len(desc) - 50] + "…"
        total = sum(_embed_char_len(e) for e in embeds)

    if total > 5800:
        log.warning("Total embed chars %d still above 5800 after trimming", total)

    return embeds


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
        resp = await client.post(
            cfg["DISCORD_INIT_WEBHOOK_URL"],
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
    return subprocess.run(
        ["git", "-C", repo_path, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def get_repo_tracking(repo_path: str = REPO_PATH) -> tuple[str, str]:
    branch_result = _git(repo_path, "branch", "--show-current")
    branch = branch_result.stdout.strip() or os.environ.get("SELF_UPDATE_BRANCH", "main")
    remote = os.environ.get("SELF_UPDATE_REMOTE", "origin")
    return branch, remote


def check_and_apply_repo_update(repo_path: str = REPO_PATH) -> dict[str, Any]:
    """Fast-forward local repo to the configured remote branch when safe."""
    branch, remote = get_repo_tracking(repo_path)
    dirty_result = _git(repo_path, "status", "--short")
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
    2. For each topic: fetch X tweets + merge RSS + AI filter.
      3. Build all 7 embeds and POST to Discord.

    Each topic is error-isolated — individual failures produce an error embed,
    not a crash of the whole job.
    """
    start = time.monotonic()
    log.info(
        "═══ Daily job started at %s HKT ═══",
        datetime.now(tz=HKT).strftime("%Y-%m-%d %H:%M:%S"),
    )

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Phase 1 — RSS (concurrent, single batch)
        log.info("Fetching %d RSS feeds concurrently…", len(RSS_FEEDS))
        all_rss = await fetch_all_rss(client)

        # Phase 2 — per-topic pipeline
        results: list[tuple[dict[str, Any], Optional[str]]] = []

        for topic in TOPICS:
            try:
                rss_posts = get_rss_for_topic(all_rss, topic)
                tweets = await fetch_tweets(None, topic, client)

                # Merge: RSS first (higher quality), X after; deduplicate by URL
                seen_urls: set[str] = set()
                merged: list[dict[str, Any]] = []

                for post in rss_posts:
                    url = post.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                for post in tweets:
                    url = post.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(post)

                log.info(
                    "%s: %d RSS + %d X → %d merged",
                    topic["name"],
                    len(rss_posts),
                    len(tweets),
                    len(merged),
                )
                if len(merged) < 3:
                    log.warning(
                        "%s: fewer than 3 posts available", topic["name"]
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

            # Brief pause between topics (reduces X rate-limit risk)
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
