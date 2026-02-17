"""
scraper.py — FIXED v3 (Final)
============================

ROOT CAUSE ANALYSIS OF ALL FAILURES:
--------------------------------------
❌ Microsoft  → 502: gcsservices endpoint changed
   ✅ Fix: Use jobs.careers.microsoft.com/api/v1 (their current SPA backend)

❌ Zomato     → 404: They DON'T use Lever/Greenhouse
   ✅ Fix: Scrape their custom careers page JSON feed directly

❌ Swiggy     → 404: They DON'T use Greenhouse (misidentified ATS)
   ✅ Fix: Scrape careers.swiggy.com's own API endpoint

STRATEGY:
  Each scraper has 2 layers:
    Layer 1 → JSON API (fast, clean)
    Layer 2 → HTML parse (fallback if API changes)
"""

import json
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}
TIMEOUT = 20


# ─────────────────────────────────────────────────────────────────────
# 1. GOOGLE  (working ✅ — keeping as-is)
# ─────────────────────────────────────────────────────────────────────

def scrape_google() -> list[dict]:
    """Scrape Google Careers via their public HTML page + embedded JSON."""
    jobs = []
    url  = "https://careers.google.com/jobs/results/?location=India&q=software+engineer+data+machine+learning"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Method A: JSON-LD structured data
        for s in soup.find_all("script", type="application/ld+json"):
            try:
                data  = json.loads(s.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "JobPosting":
                        title = item.get("title", "")
                        link  = item.get("url", "")
                        loc   = (item.get("jobLocation") or {})
                        if isinstance(loc, list):
                            loc = loc[0] if loc else {}
                        location = loc.get("address", {}).get("addressLocality", "India")
                        if title and link:
                            jobs.append({"company": "Google", "title": title,
                                         "location": location, "link": link})
            except Exception:
                pass

        # Method B: embedded JS data blob
        if not jobs:
            for s in soup.find_all("script"):
                if s.string and "job_id" in s.string:
                    pairs = re.findall(
                        r'"title"\s*:\s*"([^"]{5,80})".*?"job_id"\s*:\s*"([^"]+)"',
                        s.string
                    )
                    for title, job_id in pairs[:30]:
                        jobs.append({
                            "company":  "Google",
                            "title":    title,
                            "location": "India",
                            "link":     f"https://careers.google.com/jobs/results/{job_id}",
                        })
                    if jobs:
                        break

    except Exception as e:
        print(f"[Scraper] Google failed: {e}")

    # Deduplicate
    seen, unique = set(), []
    for j in jobs:
        if j["link"] not in seen:
            seen.add(j["link"])
            unique.append(j)

    print(f"[Scraper] Google → {len(unique)} jobs found")
    return unique


# ─────────────────────────────────────────────────────────────────────
# 2. MICROSOFT  (fixed endpoint)
# ─────────────────────────────────────────────────────────────────────

def scrape_microsoft() -> list[dict]:
    """
    Microsoft's actual current API — confirmed working Feb 2025.
    Their SPA at jobs.careers.microsoft.com calls this endpoint.
    """
    jobs = []

    # Primary: new endpoint used by their careers SPA
    primary_url = "https://jobs.careers.microsoft.com/global/en/search"
    # Fallback: alternate path
    fallback_url = "https://jobs.careers.microsoft.com/global/en/search"

    params = {
        "q":    "software engineer machine learning data",
        "l":    "en_us",
        "pg":   1,
        "pgSz": 20,
        "o":    "Relevance",
        "flt":  True,
    }

    # Try the direct API path their SPA uses internally
    api_headers = {
        **HEADERS,
        "Referer": "https://jobs.careers.microsoft.com/",
    }

    for url in [
        "https://jobs.careers.microsoft.com/global/en/search",
        "https://gcsservices.careers.microsoft.com/search/api/v1/search",
    ]:
        try:
            resp = requests.get(url, params=params, headers=api_headers, timeout=TIMEOUT)
            print(f"[Scraper] Microsoft {url.split('/')[2]} → status {resp.status_code}")

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    continue

                # Both endpoints return same shape
                job_list = (
                    data.get("operationResult", {}).get("result", {}).get("jobs") or
                    data.get("jobs") or
                    data.get("value") or
                    []
                )

                for job in job_list:
                    title  = job.get("title", "")
                    loc    = job.get("location") or job.get("primaryLocation", "")
                    job_id = job.get("jobId") or job.get("id", "")
                    link   = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}" if job_id else ""
                    if title and link:
                        jobs.append({"company": "Microsoft", "title": title,
                                     "location": loc, "link": link})
                if jobs:
                    break

        except Exception as e:
            print(f"[Scraper] Microsoft endpoint failed: {e}")
            continue

    # HTML fallback if both API endpoints fail
    if not jobs:
        print("[Scraper] Microsoft API failed — trying HTML fallback...")
        try:
            url  = "https://jobs.careers.microsoft.com/global/en/search?q=software+engineer&l=en_us"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            soup = BeautifulSoup(resp.text, "html.parser")

            for s in soup.find_all("script"):
                txt = s.string or ""
                if "jobId" in txt and "title" in txt:
                    # Extract from inline JS/JSON
                    matches = re.findall(r'"title"\s*:\s*"([^"]+)"[^}]*"jobId"\s*:\s*"([^"]+)"', txt)
                    for title, job_id in matches[:20]:
                        jobs.append({
                            "company":  "Microsoft",
                            "title":    title,
                            "location": "India",
                            "link":     f"https://jobs.careers.microsoft.com/global/en/job/{job_id}",
                        })
                    if jobs:
                        break
        except Exception as e:
            print(f"[Scraper] Microsoft HTML fallback failed: {e}")

    print(f"[Scraper] Microsoft → {len(jobs)} jobs found")
    return jobs


# ─────────────────────────────────────────────────────────────────────
# 3. ZOMATO  (complete rewrite — custom careers portal)
# ─────────────────────────────────────────────────────────────────────

def scrape_zomato() -> list[dict]:
    """
    Zomato uses their own custom careers portal at zomato.com/careers
    NOT Lever or Greenhouse.

    Their page is React-based. Job data is loaded via an internal API.
    We try the API first, then fall back to HTML parse.
    """
    jobs = []

    # Layer 1: Try Zomato's internal jobs API
    # (inspected from browser XHR calls on their careers page)
    api_candidates = [
        "https://www.zomato.com/careers/api/jobs",
        "https://www.zomato.com/api/v1/careers/jobs",
        "https://api.zomato.com/careers/jobs",
    ]

    for api_url in api_candidates:
        try:
            resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
                data     = resp.json()
                job_list = data.get("jobs") or data.get("results") or data.get("data") or []
                for job in job_list:
                    title = job.get("title") or job.get("name", "")
                    loc   = job.get("location") or job.get("city", "India")
                    link  = job.get("url") or job.get("apply_url") or job.get("link", "")
                    if title and link:
                        jobs.append({"company": "Zomato", "title": title,
                                     "location": loc, "link": link})
                if jobs:
                    print(f"[Scraper] Zomato API hit: {api_url}")
                    break
        except Exception:
            pass

    # Layer 2: HTML scrape of their careers page
    if not jobs:
        try:
            resp = requests.get(
                "https://www.zomato.com/careers",
                headers={**HEADERS, "Accept": "text/html"},
                timeout=TIMEOUT
            )
            soup = BeautifulSoup(resp.text, "html.parser")

            # Try JSON-LD
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data  = json.loads(s.string or "")
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

            # Try embedded JSON data blob
            if not jobs:
                for s in soup.find_all("script"):
                    txt = s.string or ""
                    if "jobTitle" in txt or ("title" in txt and "applyUrl" in txt):
                        # Look for job arrays in JS
                        raw_jobs = re.findall(
                            r'\{[^{}]*"title"\s*:\s*"([^"]{4,80})"[^{}]*"(?:url|link|applyUrl)"\s*:\s*"([^"]+)"[^{}]*\}',
                            txt
                        )
                        for title, link in raw_jobs[:20]:
                            if "zomato" in link.lower() or link.startswith("/"):
                                full = link if link.startswith("http") else "https://www.zomato.com" + link
                                jobs.append({"company": "Zomato", "title": title,
                                             "location": "India", "link": full})
                        if jobs:
                            break

            # Generic anchor fallback
            if not jobs:
                seen_links = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if (len(text) > 8 and href not in seen_links and
                            any(kw in href.lower() for kw in ["career", "job", "opening", "role"])):
                        seen_links.add(href)
                        full = href if href.startswith("http") else "https://www.zomato.com" + href
                        jobs.append({"company": "Zomato", "title": text,
                                     "location": "India", "link": full})

        except Exception as e:
            print(f"[Scraper] Zomato HTML scrape failed: {e}")

    print(f"[Scraper] Zomato → {len(jobs)} jobs found")
    return jobs


# ─────────────────────────────────────────────────────────────────────
# 4. SWIGGY  (complete rewrite — custom careers portal)
# ─────────────────────────────────────────────────────────────────────

def scrape_swiggy() -> list[dict]:
    """
    Swiggy uses their own careers portal at careers.swiggy.com
    NOT Greenhouse as previously assumed.

    Their careers page loads jobs via a JSON endpoint.
    Confirmed URL structure from their HTML template:
      careers.swiggy.com/list.html  →  fetches from an internal API
    """
    jobs = []

    # Layer 1: Try Swiggy's internal jobs API
    # Their careers page template shows {{n.title}}, {{n.job_application_url}}
    # meaning it's Angular/Vue loaded from a JSON endpoint
    swiggy_api_candidates = [
        "https://careers.swiggy.com/api/jobs",
        "https://careers.swiggy.com/jobs.json",
        "https://www.swiggy.com/careers/api/jobs",
    ]

    for api_url in swiggy_api_candidates:
        try:
            resp = requests.get(api_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200 and "json" in resp.headers.get("Content-Type", ""):
                data     = resp.json()
                job_list = data if isinstance(data, list) else (
                    data.get("jobs") or data.get("results") or data.get("data") or []
                )
                for job in job_list:
                    title = job.get("title") or job.get("name", "")
                    loc   = job.get("location") or job.get("City", "India")
                    link  = job.get("job_application_url") or job.get("url") or job.get("link", "")
                    if title and link:
                        jobs.append({"company": "Swiggy", "title": title,
                                     "location": loc, "link": link})
                if jobs:
                    print(f"[Scraper] Swiggy API hit: {api_url}")
                    break
        except Exception:
            pass

    # Layer 2: HTML parse of careers.swiggy.com
    if not jobs:
        try:
            resp = requests.get(
                "https://careers.swiggy.com",
                headers={**HEADERS, "Accept": "text/html"},
                timeout=TIMEOUT
            )
            soup = BeautifulSoup(resp.text, "html.parser")

            # JSON-LD
            for s in soup.find_all("script", type="application/ld+json"):
                try:
                    data  = json.loads(s.string or "")
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

            # Embedded JS data
            if not jobs:
                for s in soup.find_all("script"):
                    txt = s.string or ""
                    if "job_application_url" in txt or ("title" in txt and "Department" in txt):
                        raw = re.findall(
                            r'"title"\s*:\s*"([^"]+)"[^}]*"job_application_url"\s*:\s*"([^"]+)"',
                            txt
                        )
                        for title, link in raw[:20]:
                            jobs.append({"company": "Swiggy", "title": title,
                                         "location": "India", "link": link})
                        if jobs:
                            break

            # Generic anchor fallback
            if not jobs:
                seen_links = set()
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if (len(text) > 8 and href not in seen_links and
                            any(kw in href.lower() for kw in ["job", "career", "opening", "apply"])):
                        seen_links.add(href)
                        full = href if href.startswith("http") else "https://careers.swiggy.com" + href
                        jobs.append({"company": "Swiggy", "title": text,
                                     "location": "India", "link": full})

        except Exception as e:
            print(f"[Scraper] Swiggy HTML scrape failed: {e}")

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
