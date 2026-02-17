"""
main.py
Entry point — ties together scraping, filtering, DB, and Telegram alerts.

Run locally:
  TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python main.py

GitHub Actions runs this on a daily cron schedule.
"""

from scraper  import scrape_all
from filter   import is_relevant
from database import init_db, is_new_job, save_job
from notifier import send_alert


def main():
    print("=" * 55)
    print("  India Tech Job Tracker — MVP")
    print("=" * 55)

    # 1. Boot up the database
    init_db()

    # 2. Scrape all companies
    all_jobs = scrape_all()

    # 3. Filter → only AI / ML / Data / SDE roles
    relevant = [j for j in all_jobs if is_relevant(j["title"])]
    print(f"\n[Filter] Relevant jobs after keyword filter: {len(relevant)}")

    # 4. For each relevant job — check if NEW, then save + alert
    new_count = 0
    for job in relevant:
        link = job.get("link", "")
        if not link:
            continue  # skip jobs with no link

        if is_new_job(link):
            save_job(
                company  = job["company"],
                title    = job["title"],
                location = job.get("location", ""),
                link     = link,
            )
            send_alert(
                company  = job["company"],
                title    = job["title"],
                location = job.get("location", ""),
                link     = link,
            )
            new_count += 1

    # 5. Summary
    print("\n" + "=" * 55)
    print(f"  ✅ Done!  New jobs found & alerted: {new_count}")
    print("=" * 55)


if __name__ == "__main__":
    main()
