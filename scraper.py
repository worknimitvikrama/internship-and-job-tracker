"""
scraper.py  —  FIXED v2
Job scrapers for Google, Microsoft, Zomato, and Swiggy.

ROOT CAUSES OF PREVIOUS FAILURES (and fixes):
  ❌ Google  → /api/v3/search/ deprecated → 404
     ✅ Fix: Try updated URL params + BeautifulSoup HTML fallback

  ❌ Microsoft → gcsservices.careers.microsoft.com → 502
     ✅ Fix: Use new endpoint jobs.careers.microsoft.com

  ❌ Zomato  → slug "zomato" not on Lever → 404
     ✅ Fix: Try multiple known ATS slugs + HTML scrape fallback

  ❌ Swiggy  → slug "swiggy" not on Greenhouse → 404
     ✅ Fix: Swiggy uses Lever (not Greenhouse) + try correct slugs

HOW TO RE-FIND SLUGS WHEN THEY BREAK:
  Open careers page → DevTools → Network → XHR
  Look for requests to api.lever.co or boards-api.greenhouse.io
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────

def _try_lever(slug: str, company: str) -> list[dict]:
    """Attempt Lever public JSON API for a given slug."""
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            postings = resp.json()
            if isinstance(postings, list) and postings:
                jobs = []
                for post in postings:
                    title    = post.get("text", "")
                    location = post.get("categories", {}).get("location", "India")
                    link     = post.get("hostedUrl", "")
                    if title and link:
                        jobs.append({"company": company, "title": title,
                                     "location": location, "link": link})
                return jobs
    except Exception:
        pass
    return []


def _try_greenhouse(slug: str, company: str) -> list[dict]:
    """Attempt Greenhouse public JSON API for a given slug."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            jobs = []
            for job in data.get("jobs", []):
                title    = job.get("title", "")
                location = job.get("location", {}).get("name", "India")
                link     = job.get("absolute_url", "")
                if title and link:
                    jobs.append({"company": company, "title": title,
                                 "location": location, "link": link})
            return jobs
    except Exception:
        pass
    return []


# ─────────────────────────────────────────────────────────────────────
# 1. GOOGLE
# ─────────────────────────────────────────────────────────────────────

def scrape_google() -> list[dict]:
    """
    Scrape Google Careers for India tech roles.
    Google does not expose a stable public JSON API, so we parse HTML.
    """
    jobs = []

    # Their SPA embeds job data in a JSON blob inside a <script> tag
    url = "https://careers.google.com/jobs/results/?location=India&q=software+engineer+data+machine+learning"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Method A: look for JSON-LD structured data
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            try:
                import json
                data = json.loads(s.string)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            title = item.get("title", "")
                            loc   = item.get("jobLocation", {}).get("address", {}).get("addressLocality", "India")
                            link  = item.get("url", "")
                            if title and link:
                                jobs.append({"company": "Google", "title": title,
                                             "location": loc, "link": link})
            except Exception:
                pass

        # Method B: look for embedded job data in window.__data or similar
        if not jobs:
            all_scripts = soup.find_all("script")
            for s in all_scripts:
                if s.string and "job_id" in s.string and "title" in s.string:
                    # Try to pull title + job_id pairs from JS blob
                    pairs = re.findall(
                        r'"title"\s*:\s*"([^"]{5,80})".*?"job_id"\s*:\s*"([^"]+)"',
                        s.string
                    )
                    for title, job_id in pairs[:30]:
                        link = f"https://careers.google.com/jobs/results/{job_id}"
                        jobs.append({"company": "Google", "title": title,
                                     "location": "India", "link": link})
                    if jobs:
                        break

        # Method C: job card HTML elements
        if not jobs:
            cards = soup.select("[data-job-id], [class*='job-card'], li[class*='lLd3Je']")
            for card in cards:
                title_el = card.select_one("h3, h2, [class*='title']")
                link_el  = card.select_one("a[href]")
                if title_el and link_el:
                    href = link_el["href"]
                    jobs.append({
                        "company":  "Google",
                        "title":    title_el.get_text(strip=True),
                        "location": "India",
                        "link":     "https://careers.google.com" + href if href.startswith("/") else href,
                    })

    except Exception as e:
        print(f"[Scraper] Google scrape failed: {e}")

    # Deduplicate by link
    seen = set()
    unique = []
    for j in jobs:
        if j["link"] not in seen:
            seen.add(j["link"])
            unique.append(j)

    print(f"[Scraper] Google → {len(unique)} jobs found")
    return unique


# ─────────────────────────────────────────────────────────────────────
# 2. MICROSOFT
# ─────────────────────────────────────────────────────────────────────

def scrape_microsoft() -> list[dict]:
    """
    Microsoft's new careers API endpoint (updated 2024).
    Replaced the old gcsservices.careers.microsoft.com endpoint.
    """
    jobs = []

    endpoints = [
        # New primary endpoint
        "https://jobs.careers.microsoft.com/global/en/search",
        # Fallback: old endpoint (may still work intermittently)
        "https://gcsservices.careers.microsoft.com/search/api/v1/search",
    ]

    params = {
        "q":    "software engineer machine learning data",
        "l":    "en_us",
        "pg":   1,
        "pgSz": 20,
        "o":    "Relevance",
        "flt":  True,
    }

    for endpoint in endpoints:
        try:
            resp = requests.get(endpoint, params=params, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    continue

                # Handle both API response shapes
                job_list = (
                    data.get("operationResult", {}).get("result", {}).get("jobs", [])
                    or data.get("jobs", [])
                    or data.get("value", [])
                )

                for job in job_list:
                    title  = job.get("title", "")
                    loc    = job.get("location", "") or job.get("primaryLocation", "")
                    job_id = job.get("jobId", "") or job.get("id", "")
                    link   = (
                        f"https://jobs.careers.microsoft.com/global/en/job/{job_id}"
                        if job_id else ""
                    )
                    if title and link:
                        jobs.append({"company": "Microsoft", "title": title,
                                     "location": loc, "link": link})

                if jobs:
                    break  # stop trying if we got results

        except Exception as e:
            print(f"[Scraper] Microsoft endpoint {endpoint} failed: {e}")
            continue

    print(f"[Scraper] Microsoft → {len(jobs)} jobs found")
    return jobs


# ─────────────────────────────────────────────────────────────────────
# 3. ZOMATO
# ─────────────────────────────────────────────────────────────────────

def scrape_zomato() -> list[dict]:
    """
    Zomato careers — tries multiple ATS endpoints + HTML fallback.

    TO UPDATE: Visit https://www.zomato.com/careers in DevTools → Network
    Look for XHR to api.lever.co or boards-api.greenhouse.io to find slug.
    """
    jobs = []

    # Try Lever slugs (most likely for Indian startups)
    for slug in ["zomato", "zomatocareers", "zomato-india"]:
        jobs = _try_lever(slug, "Zomato")
        if jobs:
            print(f"[Scraper] Zomato → Lever slug '{slug}' worked!")
            break

    # Try Greenhouse slugs
    if not jobs:
        for slug in ["zomato", "zomatocareers"]:
            jobs = _try_greenhouse(slug, "Zomato")
            if jobs:
                print(f"[Scraper] Zomato → Greenhouse slug '{slug}' worked!")
                break

    # HTML fallback: scrape their careers page directly
    if not jobs:
        try:
            resp = requests.get(
                "https://www.zomato.com/careers",
                headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
                timeout=TIMEOUT
            )
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try JSON-LD first
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(s.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") == "JobPosting":
                            jobs.append({
                                "company":  "Zomato",
                                "title":    item.get("title", ""),
                                "location": "India",
                                "link":     item.get("url", ""),
                            })
                except Exception:
                    pass

            # Generic anchor scrape
            if not jobs:
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if len(text) > 8 and any(
                        kw in href.lower() for kw in ["career", "job", "opening", "role", "apply"]
                    ):
                        full = href if href.startswith("http") else "https://www.zomato.com" + href
                        jobs.append({"company": "Zomato", "title": text,
                                     "location": "India", "link": full})

        except Exception as e:
            print(f"[Scraper] Zomato HTML fallback failed: {e}")

    print(f"[Scraper] Zomato → {len(jobs)} jobs found")
    return jobs


# ─────────────────────────────────────────────────────────────────────
# 4. SWIGGY
# ─────────────────────────────────────────────────────────────────────

def scrape_swiggy() -> list[dict]:
    """
    Swiggy careers — tries Lever (their actual ATS), then Greenhouse, then HTML.

    NOTE: Swiggy's registered company is "Bundl Technologies Pvt Ltd"
    so Lever/Greenhouse slug may be 'bundl-technologies' or similar.

    TO UPDATE: Visit https://careers.swiggy.com in DevTools → Network
    Look for XHR to api.lever.co or boards-api.greenhouse.io to find slug.
    """
    jobs = []

    # Try Lever first (Swiggy uses Lever per multiple sources)
    for slug in ["swiggy", "bundl-technologies", "bundltechnologies", "swiggytech"]:
        jobs = _try_lever(slug, "Swiggy")
        if jobs:
            print(f"[Scraper] Swiggy → Lever slug '{slug}' worked!")
            break

    # Try Greenhouse as backup
    if not jobs:
        for slug in ["swiggy", "bundltechnologies", "swiggyindia"]:
            jobs = _try_greenhouse(slug, "Swiggy")
            if jobs:
                print(f"[Scraper] Swiggy → Greenhouse slug '{slug}' worked!")
                break

    # HTML fallback
    if not jobs:
        for url in ["https://careers.swiggy.com", "https://www.swiggy.com/careers"]:
            try:
                resp = requests.get(
                    url,
                    headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
                    timeout=TIMEOUT
                )
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")

                # JSON-LD
                for s in soup.find_all("script", type="application/ld+json"):
                    try:
                        import json
                        data = json.loads(s.string)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if item.get("@type") == "JobPosting":
                                jobs.append({
                                    "company":  "Swiggy",
                                    "title":    item.get("title", ""),
                                    "location": "India",
                                    "link":     item.get("url", ""),
                                })
                    except Exception:
                        pass

                # Generic anchors
                if not jobs:
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        text = a.get_text(strip=True)
                        if len(text) > 8 and any(
                            kw in href.lower() for kw in ["job", "opening", "role", "apply", "position"]
                        ):
                            full = href if href.startswith("http") else url + href
                            jobs.append({"company": "Swiggy", "title": text,
                                         "location": "India", "link": full})

                if jobs:
                    break

            except Exception as e:
                print(f"[Scraper] Swiggy HTML fallback ({url}) failed: {e}")

    print(f"[Scraper] Swiggy → {len(jobs)} jobs found")
    return jobs


# ─────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def scrape_all() -> list[dict]:
    """Run all scrapers and return combined list."""
    all_jobs = []
    all_jobs.extend(scrape_google())
    all_jobs.extend(scrape_microsoft())
    all_jobs.extend(scrape_zomato())
    all_jobs.extend(scrape_swiggy())
    print(f"\n[Scraper] Total raw jobs fetched: {len(all_jobs)}")
    return all_jobs
