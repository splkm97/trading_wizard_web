#!/usr/bin/env python3
"""
Bulk load historical stock prices into SQLite from yfinance.

This script downloads KOSPI Top 100 stock historical data and bulk inserts
into SQLite using optimized batch processing for maximum performance.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
BATCH_SIZE = 500  # Records per batch
MAX_WORKERS = 10  # Parallel download threads
DATE_RANGE_DAYS = 365 * 2  # 2 years of data


def load_stock_codes() -> list[str]:
    """Load KOSPI Top 100 stock codes."""
    data_dir = Path(__file__).parent.parent / "data"
    stock_file = data_dir / "kospi_top100.txt"

    if not stock_file.exists():
        print(f"  Stock list not found: {stock_file}")
        sys.exit(1)

    codes = stock_file.read_text().strip().splitlines()
    return list(dict.fromkeys(codes))  # Remove duplicates


def download_stock_data(stock_code: str, start_date: str, end_date: str) -> list[dict]:
    """Download single stock OHLCV data from yfinance."""
    records = []
    df = pd.DataFrame()

    # Try KOSPI (.KS) then KOSDAQ (.KQ)
    for suffix in [".KS", ".KQ"]:
        ticker = f"{stock_code}{suffix}"
        try:
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
                threads=True,
            )
            if not df.empty:
                break
        except Exception:
            continue

    if df.empty:
        return []

    # Handle MultiIndex columns (yfinance returns MultiIndex for single ticker too)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Reset index to make date a column
    df = df.reset_index()

    # Rename 'Date' or 'index' column if necessary
    if "Date" in df.columns:
        df = df.rename(columns={"Date": "date"})
    elif "index" in df.columns:
        df = df.rename(columns={"index": "date"})

    # Convert date to date type
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Select and clean columns
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in df.columns for col in required_cols):
        return []

    df = df[["date", "Open", "High", "Low", "Close", "Volume"]].dropna()

    # Build records using iloc for safe access
    for i in range(len(df)):
        row = df.iloc[i]
        try:
            records.append(
                {
                    "stock_code": stock_code,
                    "date": row["date"],
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )
        except (ValueError, TypeError):
            # Skip rows with invalid data
            continue

    return records


def bulk_insert_sqlite(engine, records: list[dict]) -> int:
    """
    Bulk insert using SQLite INSERT OR REPLACE (upsert).
    """
    if not records:
        print("  No records to insert")
        return 0

    start_time = time.time()
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]

            # Build values for INSERT
            values_list = []
            params = {}
            for j, record in enumerate(batch):
                param_prefix = f"p{j}_"
                values_list.append(
                    f"(:{param_prefix}stock_code, :{param_prefix}date, "
                    f":{param_prefix}open, :{param_prefix}high, "
                    f":{param_prefix}low, :{param_prefix}close, :{param_prefix}volume)"
                )
                params[f"{param_prefix}stock_code"] = record["stock_code"]
                params[f"{param_prefix}date"] = (
                    record["date"].isoformat()
                    if hasattr(record["date"], "isoformat")
                    else str(record["date"])
                )
                params[f"{param_prefix}open"] = record["open"]
                params[f"{param_prefix}high"] = record["high"]
                params[f"{param_prefix}low"] = record["low"]
                params[f"{param_prefix}close"] = record["close"]
                params[f"{param_prefix}volume"] = record["volume"]

            # SQLite INSERT OR REPLACE
            sql = f"""
                INSERT OR REPLACE INTO historical_prices
                    (stock_code, date, open, high, low, close, volume)
                VALUES {', '.join(values_list)}
            """

            conn.execute(text(sql), params)
            inserted += len(batch)

            if (i + BATCH_SIZE) % 5000 == 0:
                elapsed = time.time() - start_time
                rate = inserted / elapsed if elapsed > 0 else 0
                print(f"    Inserted {inserted:,} records ({rate:.0f} records/s)")

    elapsed = time.time() - start_time
    print(
        f"  Inserted {inserted:,} records in {elapsed:.2f}s "
        f"({inserted/elapsed:.0f} records/s)"
    )
    return inserted


def get_database_url() -> str:
    """Get database URL from environment or .env file."""
    # Try environment variable first
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    # Try loading from .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
            db_url = os.environ.get("DATABASE_URL")
            if db_url:
                return db_url
        except ImportError:
            pass

    # Default SQLite URL
    return "sqlite:///./data/trading_wizard.db"


def main():
    """Main execution logic."""
    print("=" * 70)
    print(" SQLite Historical Data Bulk Loader")
    print("=" * 70)

    # Get database connection
    database_url = get_database_url()
    print(f"\n Database: {database_url}")

    engine = create_engine(database_url, echo=False)

    # Verify table exists
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM historical_prices"))
            count = result.fetchone()[0]
            print(f" Current records in DB: {count:,}")
    except Exception as e:
        print(f"  Database connection error: {e}")
        print("  Make sure the database exists and tables are migrated.")
        sys.exit(1)

    # Load stock codes
    stock_codes = load_stock_codes()
    print(f" Loading {len(stock_codes)} stock codes...")

    # Set date range
    end_date = date.today()
    start_date = end_date - timedelta(days=DATE_RANGE_DAYS)
    print(f" Date range: {start_date} ~ {end_date}")

    # Parallel download
    print(f"\n Downloading data (max_workers={MAX_WORKERS})...")
    download_start = time.time()

    all_records = []
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                download_stock_data, code, start_date.isoformat(), end_date.isoformat()
            ): code
            for code in stock_codes
        }

        for future in as_completed(futures):
            code = futures[future]
            completed += 1

            try:
                records = future.result()
                all_records.extend(records)

                if completed % 10 == 0 or completed == len(stock_codes):
                    print(f"  [{completed}/{len(stock_codes)}] {code}: {len(records)} records")

            except Exception as e:
                print(f"  [{completed}/{len(stock_codes)}] {code}: ERROR - {e}")

    download_elapsed = time.time() - download_start
    print(f"\n Downloaded {len(all_records):,} records in {download_elapsed:.1f}s")
    print(f"   Average: {len(all_records)/len(stock_codes):.1f} records/stock")

    if not all_records:
        print("\n No data downloaded. Exiting.")
        sys.exit(1)

    # Bulk Insert
    print(f"\n Inserting {len(all_records):,} records into SQLite...")
    insert_start = time.time()

    inserted = bulk_insert_sqlite(engine, all_records)

    insert_elapsed = time.time() - insert_start
    total_elapsed = download_elapsed + insert_elapsed

    print(f" Inserted {inserted:,} records in {insert_elapsed:.1f}s")
    print(f"   Total time: {total_elapsed:.1f}s")

    # Final statistics
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM historical_prices"))
            count = result.fetchone()[0]
            print(f"\n Final record count: {count:,}")

            # Top stocks by record count
            result = conn.execute(
                text(
                    """
                SELECT stock_code, COUNT(*) as count
                FROM historical_prices
                GROUP BY stock_code
                ORDER BY count DESC
                LIMIT 5
            """
                )
            )

            print("\n Top 5 stocks by record count:")
            print("   Stock Code | Record Count")
            print("   " + "-" * 25)
            for row in result:
                print(f"   {row[0]:<10} | {row[1]:>10,}")

    except Exception as e:
        print(f"  Could not fetch final statistics: {e}")

    print("\n" + "=" * 70)
    print(" Bulk load completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
