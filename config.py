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

# 只推播評分達此星數的案例（1~5，設 1 等於不過濾）
MIN_RATING = _int("MIN_RATING", 3)

# 一人公司 / 獨立開發者相關內容來源（RSS）。這類實戰案例主要在
# Hacker News 與 Reddit 的獨立創業社群，而不是 TechCrunch 這種 VC 媒體。
# solo_focused=True 的來源本身就是一人創業內容，不用再靠關鍵字過濾。
NEWS_FEEDS = [
    {
        "name": "HN 一人創業",
        "url": "https://hnrss.org/newest?q=%22solo+founder%22+OR+solopreneur+OR+%22indie+hacker%22+OR+%22one-person%22&count=30",
        "solo_focused": True,
    },
    {
        "name": "HN 營收實戰",
        "url": "https://hnrss.org/newest?q=MRR+OR+bootstrapped+OR+%22side+project%22+OR+%22micro+saas%22&count=30",
        "solo_focused": True,
    },
    {"name": "r/indiehackers", "url": "https://www.reddit.com/r/indiehackers/top/.rss?t=day", "solo_focused": True},
    {"name": "r/SoloFounders", "url": "https://www.reddit.com/r/SoloFounders/top/.rss?t=day", "solo_focused": True},
    {"name": "r/EntrepreneurRideAlong", "url": "https://www.reddit.com/r/EntrepreneurRideAlong/top/.rss?t=day", "solo_focused": True},
    {"name": "r/SaaS", "url": "https://www.reddit.com/r/SaaS/top/.rss?t=day"},
    {"name": "r/SideProject", "url": "https://www.reddit.com/r/SideProject/top/.rss?t=day"},
]

# 一人創業相關關鍵字：非 solo_focused 來源的文章必須命中至少一個才保留，
# 確保推播的是「一人公司怎麼做到」的內容，而不是大公司或 VC 新聞。
SOLO_KEYWORDS = [
    "solo founder", "solo", "solopreneur", "one-person", "one person",
    "single founder", "indie hacker", "indie", "bootstrapped",
    "bootstrapping", "self-funded", "no employees", "built alone",
    "side project", "micro saas", "micro-saas", "mrr", "arr", "revenue",
    "profitable", "passive income", "first customer", "first sale",
    "launched", "grew", "automation", "no-code",
]

# AI 相關關鍵字：用來加分排序，讓「用 AI 做到」的案例排最前面。
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "genai", "generative",
    "machine learning", "openai", "anthropic", "chatgpt", "gpt", "claude",
    "gemini", "agent", "agents", "automation", "wrapper", "prompt",
]
