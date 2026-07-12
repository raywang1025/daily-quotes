"""每日流程：抓新聞 → Gemini 整理 → 推播。

用法：
    python -m src.main            # 正常跑一次
    python -m src.main --dry-run  # 只抓取+整理，印出但不真的推播
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

import config
from src import notifier, summarizer
from src.scraper import Article, fetch_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("daily")

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sent_cache.json")
CACHE_LIMIT = 500


def _load_cache() -> set[str]:
    try:
        with open(CACHE_FILE, encoding="utf-8") as fh:
            return set(json.load(fh))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_cache(keys: list[str]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(keys[-CACHE_LIMIT:], fh, ensure_ascii=False)
    except OSError as exc:
        logger.warning("寫入快取失敗: %s", exc)


def _filter_new(articles: list[Article], cache: set[str]) -> list[Article]:
    return [a for a in articles if a.key not in cache]


def run(dry_run: bool = False) -> int:
    logger.info("開始抓取 AI 創業家新聞…")
    articles = fetch_articles()
    if not articles:
        logger.warning("沒有抓到任何新聞，結束")
        return 0

    cache = _load_cache()
    fresh = _filter_new(articles, cache)
    logger.info("去除已推播後剩下 %d 則新聞", len(fresh))
    if not fresh:
        logger.info("沒有新的新聞可推播，結束")
        return 0

    logger.info("用 Gemini 整理摘要…")
    digest = summarizer.summarize(fresh)

    if dry_run:
        logger.info("[dry-run] 只印出，不推播")
        print(notifier.format_message(digest))
        return 0

    ok = notifier.dispatch(digest)

    # 記錄本次涉及的新聞，避免明天重複推播
    pushed_keys = {a.key for a in fresh}
    _save_cache(list(cache | pushed_keys))

    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="AI 創業家每日新聞推播")
    parser.add_argument("--dry-run", action="store_true", help="只整理不推播")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
