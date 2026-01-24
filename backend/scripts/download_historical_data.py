#!/usr/bin/env python3
"""Download historical stock data and store in database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.models.historical_price import HistoricalPrice


def load_stock_codes() -> list[str]:
    """Load unique stock codes from kospi_top100.txt."""
    data_dir = Path(__file__).parent.parent / "data"
    stock_file = data_dir / "kospi_top100.txt"
    codes = stock_file.read_text().strip().splitlines()
    return list(dict.fromkeys(codes))


def download_stock_data(stock_code: str, start: str, end: str) -> list[dict]:
    """Download OHLCV data for a single stock."""
    records = []

    for suffix in [".KS", ".KQ"]:
        ticker = f"{stock_code}{suffix}"
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
            if not df.empty:
                break
        except Exception:
            continue
    else:
        print(f"  ⚠ No data for {stock_code}")
        return []

    if hasattr(df.columns, "get_level_values"):
        df.columns = df.columns.get_level_values(0)

    for date_idx, row in df.iterrows():
        records.append(
            {
                "stock_code": stock_code,
                "date": date_idx.date(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }
        )

    return records


def main():
    start_date = "2023-01-01"
    end_date = "2025-01-10"

    print(f"📊 Downloading historical data: {start_date} ~ {end_date}")

    db_path = Path(__file__).parent.parent / "data" / "trading_wizard.db"
    engine = create_engine(f"sqlite:///{db_path}")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.query(HistoricalPrice).delete()
    session.commit()
    print("🗑️  Cleared existing historical data")

    stock_codes = load_stock_codes()
    print(f"📋 Found {len(stock_codes)} stocks to download")

    all_records = []
    completed = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(download_stock_data, code, start_date, end_date): code
            for code in stock_codes
        }

        for future in as_completed(futures):
            code = futures[future]
            completed += 1
            try:
                records = future.result()
                all_records.extend(records)
                print(f"  [{completed}/{len(stock_codes)}] {code}: {len(records)} records")
            except Exception as e:
                print(f"  [{completed}/{len(stock_codes)}] {code}: ERROR - {e}")

    print(f"\n💾 Inserting {len(all_records)} records into database...")

    batch_size = 500
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i : i + batch_size]
        try:
            session.bulk_insert_mappings(HistoricalPrice, batch)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"  Batch error at {i}: {e}")
        if (i + batch_size) % 5000 == 0:
            print(f"  Inserted {min(i + batch_size, len(all_records))} / {len(all_records)}")

    session.close()

    print(f"\n✅ Done! Inserted {len(all_records)} historical price records")


if __name__ == "__main__":
    main()
