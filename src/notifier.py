"""推播管道：把摘要送到 Telegram（或印在 console）。

刻意抽象化，之後要新增 LINE / Email 只要多寫一個 send_* 並在 dispatch 掛上。
"""
from __future__ import annotations

import html
import logging
from datetime import datetime, timezone

import requests

import config

logger = logging.getLogger(__name__)


def _stars(rating) -> str:
    """把 1~5 的評分轉成星號；無效值回傳空字串。"""
    try:
        n = int(rating)
    except (TypeError, ValueError):
        return ""
    if not 1 <= n <= 5:
        return ""
    return "★" * n + "☆" * (5 - n)


def format_message(digest: dict) -> str:
    """組成 Telegram HTML 格式的訊息。"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headline = html.escape(digest.get("headline", "一人公司 × AI 每日摘要"))

    lines = [f"🤖 <b>一人公司 × AI 日報</b> · {today}", f"<i>{headline}</i>", ""]

    items = digest.get("items", [])
    if not items:
        lines.append("今日暫無值得推播的新聞。")
    else:
        for i, item in enumerate(items, 1):
            title = html.escape(item.get("title", "").strip())
            insight = html.escape(item.get("insight", "").strip())
            takeaway = html.escape(item.get("takeaway", "").strip())
            barrier = html.escape(item.get("barrier", "").strip())
            mvp = html.escape(item.get("mvp", "").strip())
            evidence = html.escape(item.get("evidence", "").strip())
            source = html.escape(item.get("source", "").strip())
            url = item.get("url", "").strip()

            head = f'{i}. <a href="{html.escape(url)}"><b>{title}</b></a>' if url else f"{i}. <b>{title}</b>"
            stars = _stars(item.get("rating"))
            if stars:
                head += f"  {stars}"
            lines.append(head)

            # 詳細內容放進可展開的引用區塊，預設摺疊、點箭頭展開
            detail_lines = []
            if insight:
                detail_lines.append(insight)
            if takeaway:
                detail_lines.append(f"💡 {takeaway}")
            if barrier:
                detail_lines.append(f"🚧 {barrier}")
            if mvp:
                detail_lines.append(f"🌱 {mvp}")
            if evidence:
                detail_lines.append(f"🧾 {evidence}")
            if source:
                detail_lines.append(f"<i>— {source}</i>")
            if detail_lines:
                lines.append(f"<blockquote expandable>{chr(10).join(detail_lines)}</blockquote>")
            lines.append("")

    return "\n".join(lines).strip()


def _send_telegram(text: str) -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.error("缺少 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code != 200:
            logger.error("Telegram 推播失敗 %s: %s", resp.status_code, resp.text)
            return False
        logger.info("Telegram 推播成功")
        return True
    except requests.RequestException as exc:
        logger.error("Telegram 推播例外: %s", exc)
        return False


def _send_console(text: str) -> bool:
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")
    return True


def dispatch(digest: dict) -> bool:
    """依 config.NOTIFIER 選擇管道送出。"""
    text = format_message(digest)

    if config.NOTIFIER == "telegram":
        ok = _send_telegram(text)
        if not ok:
            logger.warning("Telegram 失敗，改印在 console 以免遺失內容")
            _send_console(text)
        return ok

    return _send_console(text)
