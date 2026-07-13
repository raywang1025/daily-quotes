"""用 Gemini 把抓到的新聞整理成一份「一人公司 × AI 每日案例摘要」。"""
from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

import config
from src.scraper import Article

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """你是一位專門研究「一人公司如何用 AI 做出高營收」的創業教練。
讀者是想靠 AI 一個人創業的人。他要的不是 AI 新聞，也不是大公司或 VC 募資消息，
而是一人（或兩三人）公司的實戰案例：他們做什麼、怎麼做到、我能不能複製。

請從我提供的內容清單中挑出最有價值的案例與討論，整理成繁體中文每日摘要。

挑選標準（依優先序）：
1. 一人或超小團隊做出可觀營收（有具體 MRR/ARR/收入數字最好）的真實案例，
   尤其是靠 AI 工具（ChatGPT/Claude/自動化/AI 產品）達成的。
2. 一人創業的實戰方法：怎麼找到利基、怎麼獲客、怎麼定價、怎麼用 AI 自動化到一個人能扛。
3. 適合一個人切入的 AI 商機、市場缺口或新玩法。
絕對不要挑：大公司動態、VC 募資新聞、單純的 AI 模型/產品資訊、沒有實質內容的自我推廣文。

每則的寫法（都用繁體中文，語氣像在跟朋友分析案例）：
1. insight：這個人/公司在做什麼、賣給誰、營收或成果多少、關鍵是怎麼做到的（2~3 句）。
2. takeaway：對讀者的啟發——這個案例可以怎麼借鏡、哪個環節最值得學（1 句）。
3. barrier：門檻與天花板——複製這件事需要什麼能力或資源、規模上限或最大風險在哪（1~2 句）。
4. rating：1~5 的整數，代表「對想用 AI 一人創業的讀者」的幫助程度。
   5 = 有具體營收數字＋可複製做法的一人 AI 案例；3 = 有參考價值但資訊不完整；
   1 = 只是沾邊。請誠實給分，不要每則都給高分。
5. 最多輸出 {max_items} 則，依 rating 由高到低排序。
6. 嚴格只回傳 JSON，不要有 markdown 圍欄或多餘文字。

輸出格式：
{{
  "headline": "今日案例一句話總覽",
  "items": [
    {{"title": "精簡標題（含營收數字更好）", "rating": 4, "insight": "案例做什麼、成果、怎麼做到", "takeaway": "對讀者的一句話啟發", "barrier": "門檻與天花板", "source": "來源", "url": "原文連結"}}
  ]
}}
"""


def _rating(item: dict) -> int:
    """回傳案例評分；缺漏或無效時當 0 分。"""
    try:
        return int(item.get("rating", 0))
    except (TypeError, ValueError):
        return 0


def _build_input(articles: list[Article]) -> str:
    payload = [
        {
            "title": a.title,
            "source": a.source,
            "url": a.url,
            "summary": a.summary,
        }
        for a in articles
    ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


def _fallback_digest(articles: list[Article]) -> dict:
    """Gemini 不可用時，直接用抓到的新聞組一份摘要，確保仍能推播。"""
    items = [
        {
            "title": a.title,
            "insight": a.summary[:120] if a.summary else "",
            "takeaway": "",
            "barrier": "",
            "source": a.source,
            "url": a.url,
        }
        for a in articles[: config.MAX_DIGEST_ITEMS]
    ]
    return {"headline": "今日一人公司 × AI 案例", "items": items}


def summarize(articles: list[Article]) -> dict:
    """回傳 {'headline': str, 'items': [...]}。"""
    if not articles:
        return {"headline": "今日暫無新的一人公司案例", "items": []}

    if not config.GEMINI_API_KEY:
        logger.warning("未設定 GEMINI_API_KEY，改用原始新聞（不經 AI 整理）")
        return _fallback_digest(articles)

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=_build_input(
                articles[: config.MAX_ITEMS_PER_FEED * len(config.NEWS_FEEDS)]
            ),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT.format(max_items=config.MAX_DIGEST_ITEMS),
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
        data = json.loads(_strip_fences(response.text))
        items = data.get("items", [])
        if not items:
            raise ValueError("Gemini 回傳空清單")

        if all(_rating(i) == 0 for i in items):
            # Gemini 沒照格式給評分時不過濾，避免整份被誤砍
            logger.warning("所有案例都沒有有效評分，跳過星等過濾")
            kept = items
        else:
            kept = [i for i in items if _rating(i) >= config.MIN_RATING]
        dropped = len(items) - len(kept)
        if dropped:
            logger.info("過濾掉 %d 則低於 %d 星的案例", dropped, config.MIN_RATING)
        if not kept:
            logger.info("今日沒有達 %d 星的案例，不推播", config.MIN_RATING)
            return {"headline": f"今日沒有達 {config.MIN_RATING} 星的案例", "items": []}

        kept = kept[: config.MAX_DIGEST_ITEMS]
        return {"headline": data.get("headline", "今日一人公司 × AI 案例"), "items": kept}
    except Exception as exc:  # noqa: BLE001 — 任何失敗都退回原始摘要，保證推播
        logger.error("Gemini 整理失敗，改用原始新聞: %s", exc)
        return _fallback_digest(articles)
