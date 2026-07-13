"""用 Gemini 把抓到的新聞整理成一份「AI 創業家每日摘要」。"""
from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

import config
from src.scraper import Article

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """你是一位服務「AI 創業家」的創業顧問兼科技財經編輯。
讀者是正在經營或準備創辦 AI 公司的創業者，他們要的不是 AI 新知，而是能幫助自己創業的情報。
請從我提供的新聞清單中挑出對他們最有價值的內容，整理成一份繁體中文的每日摘要。

挑選標準（依優先序）：
1. AI 新創的募資、併購、估值、商業模式與成長動態。
2. 知名 AI 創業家、投資人的觀點、策略與經驗談。
3. 對 AI 創業有直接影響的平台、政策或市場變化。
絕對不要挑：單純的模型發布、學術研究、產品評測等與創業無關的純 AI 技術新聞。

寫法要求：
1. insight 用 1~2 句講清楚「發生什麼事、為什麼重要」，語氣專業精簡。
2. takeaway 用一句話點出「對 AI 創業者的啟示」：這代表什麼機會、風險或可借鏡之處。
3. 最多輸出 {max_items} 則，依對創業者的價值排序。
4. 嚴格只回傳 JSON，不要有 markdown 圍欄或多餘文字。

輸出格式：
{{
  "headline": "今日一句話總覽（創業者視角）",
  "items": [
    {{"title": "精簡標題", "insight": "1~2 句重點與影響", "takeaway": "對創業者的一句話啟示", "source": "來源", "url": "原文連結"}}
  ]
}}
"""


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
            "source": a.source,
            "url": a.url,
        }
        for a in articles[: config.MAX_DIGEST_ITEMS]
    ]
    return {"headline": "今日 AI 創業家新聞摘要", "items": items}


def summarize(articles: list[Article]) -> dict:
    """回傳 {'headline': str, 'items': [...]}。"""
    if not articles:
        return {"headline": "今日暫無新的 AI 創業家新聞", "items": []}

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
        items = data.get("items", [])[: config.MAX_DIGEST_ITEMS]
        if not items:
            raise ValueError("Gemini 回傳空清單")
        return {"headline": data.get("headline", "今日 AI 創業家新聞摘要"), "items": items}
    except Exception as exc:  # noqa: BLE001 — 任何失敗都退回原始摘要，保證推播
        logger.error("Gemini 整理失敗，改用原始新聞: %s", exc)
        return _fallback_digest(articles)
