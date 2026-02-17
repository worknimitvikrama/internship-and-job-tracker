"""
database.py
SQLite handler — stores scraped jobs, checks for duplicates.
"""

import sqlite3
from datetime import datetime

DB_PATH = "jobs.db"


def init_db():
    """Create the jobs table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company     TEXT NOT NULL,
            title       TEXT NOT NULL,
            location    TEXT,
            link        TEXT UNIQUE,
            date_scraped TEXT
        )
    """)
    conn.commit()
    conn.close()


def is_new_job(link: str) -> bool:
    """Return True if this link has NOT been seen before."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE link = ?", (link,))
    exists = cursor.fetchone()
    conn.close()
    return exists is None


def save_job(company: str, title: str, location: str, link: str):
    """Insert a new job record into the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO jobs (company, title, location, link, date_scraped)
            VALUES (?, ?, ?, ?, ?)
            """,
            (company, title, location, link, datetime.now().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already exists (UNIQUE constraint) — silently skip
    finally:
        conn.close()


def get_all_jobs():
    """Fetch all stored jobs (useful for debugging / testing)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company, title, location, link, date_scraped FROM jobs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
