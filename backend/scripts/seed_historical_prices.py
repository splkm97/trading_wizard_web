#!/usr/bin/env python3
"""Seed historical prices from cache DB if main DB is empty."""

import os
import sqlite3


def get_db_path():
    """Get database path from DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    return None


def seed_historical_prices():
    """Import historical prices from cache if main DB table is empty."""
    db_path = get_db_path()
    if not db_path:
        print("Skipping historical prices seed: Not using SQLite")
        return

    cache_path = "/app/cache/historical_prices.db"
    if not os.path.exists(cache_path):
        print(f"Skipping historical prices seed: Cache file not found at {cache_path}")
        return

    # Connect to main DB
    main_conn = sqlite3.connect(db_path)
    main_cursor = main_conn.cursor()

    # Check if table exists and has data
    try:
        main_cursor.execute("SELECT COUNT(*) FROM historical_prices")
        count = main_cursor.fetchone()[0]
        if count > 0:
            print(f"Historical prices already populated ({count} records)")
            main_conn.close()
            return
    except sqlite3.OperationalError:
        # Table doesn't exist yet - migrations will create it
        print("Historical prices table not yet created - will be handled by migrations")
        main_conn.close()
        return

    # Import from cache
    print(f"Importing historical prices from {cache_path}...")
    cache_conn = sqlite3.connect(cache_path)
    cache_cursor = cache_conn.cursor()

    cache_cursor.execute("SELECT * FROM historical_prices")
    rows = cache_cursor.fetchall()

    if rows:
        main_cursor.executemany(
            "INSERT OR REPLACE INTO historical_prices VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        main_conn.commit()
        print(f"Imported {len(rows)} historical price records")
    else:
        print("No data in cache file")

    cache_conn.close()
    main_conn.close()


if __name__ == "__main__":
    seed_historical_prices()
