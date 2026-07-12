"""集中管理設定與新聞來源。"""
import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# ===== Gemini =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

# ===== 推播 =====
NOTIFIER = os.getenv("NOTIFIER", "telegram").strip().lower()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ===== 抓取 =====
MAX_ITEMS_PER_FEED = _int("MAX_ITEMS_PER_FEED", 8)
MAX_DIGEST_ITEMS = _int("MAX_DIGEST_ITEMS", 6)
LOOKBACK_HOURS = _int("LOOKBACK_HOURS", 36)

# AI / 創業家相關新聞來源（RSS，比直接爬 HTML 穩定）
NEWS_FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "TechCrunch Startups", "url": "https://techcrunch.com/category/startups/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
    {"name": "Hacker News (AI)", "url": "https://hnrss.org/newest?q=AI+OR+startup+OR+founder&count=25"},
]

# 讓標題含這些關鍵字的新聞優先（與 AI 創業家/募資高度相關）
PRIORITY_KEYWORDS = [
    "founder", "startup", "funding", "raises", "raised", "seed", "series a",
    "series b", "venture", "vc", "ai", "openai", "anthropic", "acqui", "ipo",
    "launch", "valuation", "investor",
]
