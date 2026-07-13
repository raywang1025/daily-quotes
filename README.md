# 一人公司 × AI 日報 (Daily Solo Founder × AI Digest)

每天自動從 **Hacker News 與 Reddit 獨立創業社群**抓「一人公司 / 超小團隊用 AI 做出高營收」的實戰案例，用 **Google Gemini** 整理成繁體中文摘要並**推播到 Telegram**。每則案例包含：

- **做什麼、怎麼做到**：產品、客群、營收數字、關鍵做法
- 💡 **啟發**：這個案例可以怎麼借鏡
- 🚧 **門檻與天花板**：複製需要什麼能力、規模上限與風險在哪

大公司動態、VC 募資新聞、純 AI 模型資訊會被關鍵字過濾與 Gemini 提示詞雙重排除。

排程靠 **GitHub Actions cron**，不需要自己養伺服器。

## 運作流程

```
RSS 新聞來源 ──► scraper（抓取、去重、依相關度排序）
                     │
                     ▼
              summarizer（Gemini 整理成每日摘要）
                     │
                     ▼
              notifier（推播到 Telegram）
```

- `config.py` — 設定與新聞來源清單
- `src/scraper.py` — 從 RSS 抓一人創業 × AI 案例
- `src/summarizer.py` — 呼叫 Gemini 整理摘要（失敗時退回原始新聞）
- `src/notifier.py` — 推播（Telegram / console，可擴充 LINE/Email）
- `src/main.py` — 串起整個流程，含已推播去重快取
- `.github/workflows/daily.yml` — 每日定時觸發

## 本機測試

```bash
pip install -r requirements.txt
cp .env.example .env      # 填入你的 key

# 只抓取＋整理，印出但不推播
python -m src.main --dry-run

# 實際跑一次（會依 NOTIFIER 推播）
python -m src.main
```

沒設定 `GEMINI_API_KEY` 也能跑，會退回未經 AI 整理的原始新聞。
把 `NOTIFIER=console` 就會直接印在終端機，方便測試。

## 取得金鑰

| 項目 | 取得方式 |
|------|----------|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `TELEGRAM_BOT_TOKEN` | Telegram 找 [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TELEGRAM_CHAT_ID` | 先跟你的 bot 說一句話，再找 [@userinfobot](https://t.me/userinfobot) 查你的 chat id |

## 部署（GitHub Actions）

到 repo 的 **Settings → Secrets and variables → Actions** 加入：

- Secret：`GEMINI_API_KEY`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`
- （選用）Variable：`GEMINI_MODEL`

預設每天 UTC 00:00（台灣早上 08:00）推播，可在 `daily.yml` 調整 cron，或在 Actions 頁面按 **Run workflow** 手動測試。

## 客製化

- **改內容來源**：編輯 `config.py` 的 `NEWS_FEEDS`（`solo_focused: True` 的來源不經關鍵字過濾）
- **調整過濾嚴格度**：編輯 `config.py` 的 `SOLO_KEYWORDS` / `AI_KEYWORDS`
- **改推播則數 / 抓取範圍**：`.env` 裡的 `MAX_DIGEST_ITEMS`、`LOOKBACK_HOURS` 等
- **換推播管道**：在 `src/notifier.py` 新增 `_send_line()` / `_send_email()`，並在 `dispatch()` 掛上
