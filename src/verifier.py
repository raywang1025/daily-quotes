"""官網收費驗證：抓貼文裡的產品連結，檢查有沒有定價／收費訊號。

只驗「他有沒有在收費」——定價頁是鐵證。
「有沒有人買單」「數字是不是吹的」外部驗不了，
所以摘要裡自稱的數字一律標「作者自稱」，把責任還給原作者。
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DailyAIDigestBot/1.0; +https://github.com/raywang1025/daily-quotes)"
    )
}

# 這些網域不是產品官網，不用驗
_SKIP_DOMAINS = (
    "reddit.com", "redd.it", "redditmedia.com", "redditstatic.com",
    "ycombinator.com", "imgur.com", "github.com", "twitter.com", "x.com",
    "youtube.com", "youtu.be", "linkedin.com", "google.com", "apple.com",
    "play.google.com", "discord.gg", "discord.com", "medium.com",
)

_TAG_RE = re.compile(r"<[^>]+>")

# 否定片語要先刪掉再比對，不然「no in-app purchases」（免費）會被誤判成有收費
_NEGATION_RE = re.compile(
    r"\b(?:no|without|free of|zero)\s+(?:\w+[- ]){0,2}?"
    r"(?:purchases?|subscriptions?|paywalls?|pricing|fees?|charges?|credit card)",
    re.I,
)

# 收費訊號：命中任何一個就視為「官網有收費」
_PRICE_RE = re.compile(
    r"\$\s?\d|€\s?\d|per month|/month|/mo\b|/year|/yr\b|free trial|paid plan|upgrade to pro|premium plan",
    re.I,
)
_PRICE_WORDS = ("pricing", "subscribe now", "checkout", "buy now")


def _is_product_link(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    if not host:
        return False
    return not any(host == d or host.endswith("." + d) for d in _SKIP_DOMAINS)


def _fetch_text(url: str) -> str:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=8)
        if resp.status_code != 200:
            return ""
        return _TAG_RE.sub(" ", resp.text[:200_000]).lower()
    except requests.RequestException:
        return ""


def _signals(text: str) -> list[str]:
    text = _NEGATION_RE.sub(" ", text)
    found: list[str] = []
    match = _PRICE_RE.search(text)
    if match:
        found.append(match.group(0).strip())
    for word in _PRICE_WORDS:
        if word in text:
            found.append(word)
            break
    return found


def check_pricing(links: list[str]) -> str:
    """回傳收費證據描述；查不到（或沒有官網連結）就回空字串。"""
    candidates = [u for u in links if _is_product_link(u)][:2]
    for url in candidates:
        text = _fetch_text(url)
        sig = _signals(text) if text else []
        if sig:
            return f"官網 {url} 有收費訊號：{'、'.join(sig[:3])}"
        # 首頁沒有 → 試 /pricing 頁
        try:
            parsed = urlparse(url)
            pricing_url = f"{parsed.scheme}://{parsed.hostname}/pricing"
        except ValueError:
            continue
        text = _fetch_text(pricing_url)
        sig = _signals(text) if text else []
        if sig:
            return f"官網 {pricing_url} 有收費訊號：{'、'.join(sig[:3])}"
    return ""
