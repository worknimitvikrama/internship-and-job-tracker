# 🔧 Troubleshooting Guide

## ❌ "Scraper failed: 404 / 502 / 0 jobs found"

This is the most common issue. Company career APIs change URLs frequently.

---

## How to Find the Correct API Endpoint (5 minutes)

1. **Open** the company's careers page in Chrome
   - Google: https://careers.google.com/jobs/results/
   - Microsoft: https://jobs.careers.microsoft.com
   - Zomato: https://www.zomato.com/careers
   - Swiggy: https://careers.swiggy.com

2. **Open DevTools** → Press `F12` or right-click → Inspect

3. **Go to Network tab** → Filter by `XHR` or `Fetch`

4. **Reload the page** and look for requests to:
   - `api.lever.co/v0/postings/...`
   - `boards-api.greenhouse.io/v1/boards/.../jobs`
   - Any JSON API returning job data

5. **Copy the URL** — the slug is the company identifier in the path
   - Example: `api.lever.co/v0/postings/SLUG_IS_HERE?mode=json`

6. **Update `scraper.py`** — add the new slug to the list:
   ```python
   for slug in ["new-slug-here", "old-slug"]:
       jobs = _try_lever(slug, "Zomato")
   ```

---

## Quick Slug Test in Terminal

```bash
# Test a Lever slug
curl "https://api.lever.co/v0/postings/SLUG_HERE?mode=json" | python3 -m json.tool | head -20

# Test a Greenhouse slug
curl "https://boards-api.greenhouse.io/v1/boards/SLUG_HERE/jobs" | python3 -m json.tool | head -20
```

If you get a JSON array of jobs → slug is correct ✅
If you get `{"code":"...", "message":"..."}` → wrong slug ❌

---

## Known Working Slugs (last verified Feb 2026)

| Company   | ATS        | Slug to try          |
|-----------|------------|----------------------|
| Zomato    | Lever?     | zomato / zomato-india |
| Swiggy    | Lever?     | swiggy / bundl-technologies |
| Microsoft | Own API    | jobs.careers.microsoft.com |
| Google    | Own API    | HTML scrape          |

---

## Error Reference

| Error | Meaning | Fix |
|-------|---------|-----|
| 404 Not Found | Wrong API URL or slug | Find new slug using DevTools |
| 502 Bad Gateway | Server changed / overloaded | Try alternate endpoint in scraper.py |
| 0 jobs found | API changed response format | Check JSON structure, update parsing |
| SSL Error | Certificate issue | Add `verify=False` to requests.get() (temporary) |
| Timeout | Server slow | Increase `TIMEOUT` in scraper.py |

---

## If Everything Breaks: Nuclear Option

If all APIs fail, use **Indeed RSS feeds** as guaranteed fallback:

```python
import feedparser

def scrape_indeed_rss(company: str) -> list[dict]:
    url = f"https://in.indeed.com/rss?q={company}+software+engineer&l=India"
    feed = feedparser.parse(url)
    return [{
        "company": company,
        "title": entry.title,
        "location": "India",
        "link": entry.link,
    } for entry in feed.entries[:20]]
```

Add `feedparser` to requirements.txt and call this as a fallback.
