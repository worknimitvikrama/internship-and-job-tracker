# 🚀 India Tech Job Tracker — MVP

> Daily AI/ML/Data/SDE job alerts from **Google, Microsoft, Zomato & Swiggy** — straight to Telegram. Runs free on GitHub Actions.

---

## 📁 Project Structure

```
job-tracker/
├── main.py                      # Entry point — orchestrates everything
├── scraper.py                   # Scrapers for all 4 companies
├── filter.py                    # Keyword filter (AI / ML / Data / SDE)
├── database.py                  # SQLite — tracks seen jobs, avoids re-alerts
├── notifier.py                  # Sends Telegram alerts
├── requirements.txt             # Only needs `requests`
├── .github/
│   └── workflows/
│       └── cron.yml             # GitHub Actions daily cron
└── .gitignore
```

---

## ⚙️ How It Works

```
[GitHub Actions] → runs daily at 9 AM UTC (2:30 PM IST)
       ↓
[scraper.py]    → hits public career APIs (Google, Microsoft, Zomato, Swiggy)
       ↓
[filter.py]     → keeps only AI/ML/Data/SDE/Backend/Frontend roles
       ↓
[database.py]   → checks SQLite if job link was seen before
       ↓
[notifier.py]   → sends Telegram alert ONLY for NEW jobs
```

---

## 💬 Telegram Alert Format

```
🚀 New AI/SDE Job Alert!

🏢 Company: Google
💼 Role: Software Engineer, ML
📍 Location: Bangalore, India
🔗 Apply Here → https://careers.google.com/...
```

---

## 🛠️ Setup Guide

### Step 1 — Clone & Test Locally

```bash
git clone https://github.com/YOUR_USERNAME/job-tracker.git
cd job-tracker
pip install -r requirements.txt
```

Run it locally (no Telegram needed for first test):
```bash
python main.py
```

---

### Step 2 — Create Your Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → copy your **bot token**
3. Start a chat with your new bot
4. Get your **chat ID**:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"chat": {"id": 123456789}` in the response

---

### Step 3 — Add GitHub Secrets

In your GitHub repo:
1. Go to **Settings → Secrets and variables → Actions**
2. Add two secrets:

| Secret Name           | Value                  |
|-----------------------|------------------------|
| `TELEGRAM_BOT_TOKEN`  | Your bot token         |
| `TELEGRAM_CHAT_ID`    | Your chat ID (number)  |

---

### Step 4 — Push to GitHub

```bash
git add .
git commit -m "feat: India tech job tracker MVP"
git push origin main
```

GitHub Actions will automatically run daily at **9 AM UTC (2:30 PM IST)**.

To trigger it manually: **Actions → Daily Job Tracker → Run workflow**

---

## 🔑 Keyword Filter

Edit `filter.py` → `KEYWORDS` list to customize what roles you track:

```python
KEYWORDS = [
    "AI", "Machine Learning", "ML", "Data",
    "SDE", "Software Engineer", "Backend", "Frontend",
    "NLP", "Computer Vision", "GenAI", "LLM",
    ...
]
```

---

## 💰 Cost Breakdown

| Component       | Cost      |
|-----------------|-----------|
| GitHub Actions  | ✅ Free (2,000 min/month for public repos) |
| SQLite DB       | ✅ Free (file stored in Actions cache)      |
| Telegram Bot    | ✅ Free forever                             |
| Hosting / VPS   | ✅ Not needed                               |
| **Total**       | **₹0 / month** |

---

## 🧠 Tech Stack

- **Python 3.11** — clean, no magic
- **requests** — HTTP calls to career APIs
- **SQLite** — zero-config local database
- **Telegram Bot API** — free push notifications
- **GitHub Actions** — free cron scheduler

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| No Telegram alert | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets are set correctly |
| Scraper returns 0 jobs | The company may have changed their API URL — check `scraper.py` and update the URL |
| Same jobs re-alerted | The Actions cache was cleared — first run after cache clear will re-alert all known jobs |
| `jobs.db` grows too large | Run `python -c "from database import *; init_db()"` to reset, or manually delete the cache |

---

## 📈 Resume / Portfolio Description

> **India Tech Job Tracker** — A Python automation tool that daily scrapes AI/ML/SDE job postings from Google, Microsoft, Zomato, and Swiggy using public career APIs. Filters roles by keyword, deduplicates using SQLite, and delivers real-time Telegram alerts for new positions. Deployed serverlessly via GitHub Actions with zero infrastructure cost.

**Skills demonstrated:** Python · REST APIs · SQLite · Telegram Bot API · GitHub Actions · CI/CD · Web Scraping · Automation

---

## 📌 Companies & Data Sources

| Company   | Source              | Method |
|-----------|---------------------|--------|
| Google    | careers.google.com  | Public JSON API |
| Microsoft | careers.microsoft.com | Public talent API |
| Zomato    | Lever ATS           | Public JSON feed |
| Swiggy    | Greenhouse ATS      | Public JSON feed |

> All endpoints are publicly accessible — no login, no API keys, no scraping of HTML pages.
