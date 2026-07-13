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

# AI 創業家相關新聞來源（RSS，比直接爬 HTML 穩定）。
# startup_focused=True 的來源本身就是創業內容，不用再靠關鍵字過濾。
NEWS_FEEDS = [
    {"name": "TechCrunch Startups", "url": "https://techcrunch.com/category/startups/feed/", "startup_focused": True},
    {"name": "TechCrunch Venture", "url": "https://techcrunch.com/category/venture/feed/", "startup_focused": True},
    {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/", "startup_focused": True},
    {"name": "Y Combinator Blog", "url": "https://www.ycombinator.com/blog/rss", "startup_focused": True},
    {"name": "a16z", "url": "https://a16z.com/feed/", "startup_focused": True},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "Hacker News (AI 創業)", "url": "https://hnrss.org/newest?q=founder+OR+funding+OR+%22AI+startup%22&count=25"},
]

# 創業相關關鍵字：非 startup_focused 來源的文章必須命中至少一個才保留，
# 確保推播的是「AI 創業家」內容，而不是單純的 AI 資訊。
ENTREPRENEUR_KEYWORDS = [
    "founder", "co-founder", "startup", "startups", "funding", "raises",
    "raised", "seed", "series a", "series b", "series c", "venture", "vc",
    "acquisition", "acquires", "acquired", "ipo", "valuation", "investor",
    "investors", "accelerator", "y combinator", "unicorn", "exit", "pivot",
    "bootstrapped", "entrepreneur", "business model", "monetization",
    "revenue", "pitch", "term sheet",
]

# AI 相關關鍵字：用來加分排序，讓「AI 新創」比一般新創排更前面。
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "genai", "generative",
    "machine learning", "openai", "anthropic", "gpt", "claude", "gemini",
    "agent", "agents", "foundation model",
]
