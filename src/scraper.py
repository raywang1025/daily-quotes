"""從多個網路平台（RSS）抓取 AI / 創業家相關新聞。"""
from __future__ import annotations

import html
import logging
import re
import time
from calendar import timegm
from dataclasses import dataclass, field
from datetime import datetime, timezone

import feedparser
import requests

import config

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DailyAIDigestBot/1.0; +https://github.com/raywang1025/daily-quotes)"
    )
}


@dataclass
class Article:
    title: str
    url: str
    source: str
    summary: str = ""
    published: datetime | None = None
    score: int = 0
    _key: str = field(default="", repr=False)

    @property
    def key(self) -> str:
        """去重用的穩定鍵。"""
        return self._key or self.url


def _clean(text: str) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _parse_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            return datetime.fromtimestamp(timegm(value), tz=timezone.utc)
    return None


def _count_keywords(text: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", text))


def _relevance(title: str, summary: str) -> tuple[int, int]:
    """回傳 (創業相關命中數, AI 相關命中數)。"""
    text = f"{title} {summary}".lower()
    return (
        _count_keywords(text, config.ENTREPRENEUR_KEYWORDS),
        _count_keywords(text, config.AI_KEYWORDS),
    )


def _fetch_feed(url: str) -> feedparser.FeedParserDict | None:
    """先用 requests 抓（帶 UA / timeout），再交給 feedparser 解析。"""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except requests.RequestException as exc:
        logger.warning("抓取失敗 %s: %s", url, exc)
        return None


def fetch_articles() -> list[Article]:
    """回傳去重、依相關度與時間排序後的新聞清單。"""
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - config.LOOKBACK_HOURS * 3600

    seen: set[str] = set()
    articles: list[Article] = []

    for feed in config.NEWS_FEEDS:
        parsed = _fetch_feed(feed["url"])
        if not parsed or not getattr(parsed, "entries", None):
            continue

        count = 0
        for entry in parsed.entries:
            if count >= config.MAX_ITEMS_PER_FEED:
                break

            url = (getattr(entry, "link", "") or "").strip()
            title = _clean(getattr(entry, "title", ""))
            if not url or not title:
                continue

            key = url.split("?")[0].rstrip("/").lower()
            if key in seen:
                continue

            published = _parse_time(entry)
            if published and published.timestamp() < cutoff:
                continue

            summary = _clean(getattr(entry, "summary", ""))[:500]

            ent_hits, ai_hits = _relevance(title, summary)
            # 一般 AI 新聞來源：沒有任何創業相關字眼就略過，
            # 只留「AI 創業家」內容，不推單純的 AI 資訊。
            if not feed.get("startup_focused") and ent_hits == 0:
                continue

            seen.add(key)
            articles.append(
                Article(
                    title=title,
                    url=url,
                    source=feed["name"],
                    summary=summary,
                    published=published,
                    score=ent_hits * 2 + ai_hits,
                    _key=key,
                )
            )
            count += 1

        # 對來源禮貌，稍微間隔
        time.sleep(0.3)

    # 相關度高的、以及較新的排前面
    articles.sort(
        key=lambda a: (a.score, a.published or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )
    logger.info("共抓到 %d 則新聞", len(articles))
    return articles
