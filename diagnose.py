"""
diagnose.py
===========
Run this to test each scraper one at a time and see exactly
what's working, what's failing, and why.

Usage:
  python diagnose.py           # tests all 4
  python diagnose.py microsoft # tests only Microsoft
  python diagnose.py zomato    # tests only Zomato
"""

import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def check_url(label, url, expect_json=True):
    """Quick check: hit a URL and report status + content type."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        ct = r.headers.get("Content-Type", "")
        size = len(r.content)
        is_json = "json" in ct or (r.text.strip().startswith("{") or r.text.strip().startswith("["))
        status = "✅" if r.status_code == 200 else "❌"
        json_ok = "JSON✅" if (expect_json and is_json) else ("JSON❌" if expect_json else "")
        print(f"  {status} [{r.status_code}] {json_ok} {size}B  {label}")
        print(f"       URL: {url}")
        if r.status_code == 200 and is_json:
            try:
                import json
                data = r.json()
                if isinstance(data, list):
                    print(f"       → List with {len(data)} items")
                elif isinstance(data, dict):
                    print(f"       → Dict keys: {list(data.keys())[:5]}")
            except Exception:
                pass
        return r.status_code == 200
    except Exception as e:
        print(f"  ❌ ERROR  {label}: {e}")
        return False

def diagnose_microsoft():
    print("\n━━━ MICROSOFT ━━━")
    check_url("Primary API", "https://jobs.careers.microsoft.com/global/en/search?q=software+engineer&l=en_us&pg=1&pgSz=5&o=Relevance&flt=True")
    check_url("Old API", "https://gcsservices.careers.microsoft.com/search/api/v1/search?q=engineer&l=en_us&pg=1&pgSz=5&o=Relevance&flt=True")
    check_url("Careers Page HTML", "https://jobs.careers.microsoft.com/global/en/search", expect_json=False)

def diagnose_zomato():
    print("\n━━━ ZOMATO ━━━")
    check_url("Careers Page", "https://www.zomato.com/careers", expect_json=False)
    check_url("API guess 1", "https://www.zomato.com/careers/api/jobs")
    check_url("API guess 2", "https://www.zomato.com/api/v1/careers/jobs")
    # Show what's in the HTML
    try:
        r = requests.get("https://www.zomato.com/careers", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        scripts = [s for s in soup.find_all("script") if s.get("src") or (s.string and len(s.string or "") > 50)]
        print(f"  ℹ️  Page has {len(scripts)} scripts, {len(soup.find_all('a'))} links")
        # Check for any API URLs in the page
        import re
        api_urls = re.findall(r'https?://[^\s"\'<>]+(?:api|json|jobs)[^\s"\'<>]*', r.text)
        if api_urls:
            print("  ℹ️  API-like URLs found in page:")
            for u in set(api_urls[:5]):
                print(f"       {u}")
    except Exception as e:
        print(f"  ❌ HTML fetch failed: {e}")

def diagnose_swiggy():
    print("\n━━━ SWIGGY ━━━")
    check_url("Main Careers Page", "https://careers.swiggy.com", expect_json=False)
    check_url("List Page", "https://careers.swiggy.com/list.html?dept=Engineering&loc=1", expect_json=False)
    check_url("API guess 1", "https://careers.swiggy.com/api/jobs")
    check_url("API guess 2", "https://careers.swiggy.com/jobs.json")
    # Show what's in the HTML
    try:
        r = requests.get("https://careers.swiggy.com/list.html?dept=Engineering&loc=1", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        import re
        api_urls = re.findall(r'https?://[^\s"\'<>]+(?:api|json|jobs)[^\s"\'<>]*', r.text)
        ng_urls  = re.findall(r'(?:http|/)[^\s"\'<>]*\.json[^\s"\'<>]*', r.text)
        if api_urls or ng_urls:
            print("  ℹ️  API-like URLs found in page source:")
            for u in set((api_urls + ng_urls)[:8]):
                print(f"       {u}")
        # Check script src
        for s in soup.find_all("script", src=True)[:5]:
            print(f"  ℹ️  Script: {s['src']}")
    except Exception as e:
        print(f"  ❌ HTML fetch failed: {e}")

def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    print("=" * 50)
    print("  Job Tracker — Scraper Diagnosis Tool")
    print("=" * 50)

    if target in ("all", "microsoft"):
        diagnose_microsoft()
    if target in ("all", "zomato"):
        diagnose_zomato()
    if target in ("all", "swiggy"):
        diagnose_swiggy()

    print("\n" + "=" * 50)
    print("  Tip: If you see API URLs in the page source,")
    print("  add them to scraper.py's api_candidates list.")
    print("=" * 50)

if __name__ == "__main__":
    main()
