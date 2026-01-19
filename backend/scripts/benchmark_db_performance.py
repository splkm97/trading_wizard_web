#!/usr/bin/env python3
"""
Database Performance Benchmark Script.

Compares ORM vs Raw SQL query performance for historical price data.

Expected Results:
- ORM Approach: ~100-300ms average
- Raw SQL Approach: ~20-60ms average
- Improvement: 70-85%

Usage:
    cd backend
    python scripts/benchmark_db_performance.py
"""

import os
import statistics
import sys
import time
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    """Get database URL from environment."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

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

    return "postgresql://user:password@localhost:5432/trading_wizard"


def get_test_stock_code(engine) -> str:
    """Get a stock code with data for testing."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT stock_code, COUNT(*) as cnt
            FROM historical_prices
            GROUP BY stock_code
            ORDER BY cnt DESC
            LIMIT 1
        """
            )
        )
        row = result.fetchone()
        if row:
            return row[0]
    return "005930"  # Samsung Electronics as fallback


def benchmark_orm_approach(engine, stock_code: str, iterations: int = 50) -> list[float]:
    """Benchmark ORM-based query approach (current implementation)."""
    from src.models.historical_price import HistoricalPrice

    Session = sessionmaker(bind=engine)
    session = Session()

    end_date = date.today()
    start_date = end_date - timedelta(days=120)
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    times = []
    for _ in range(iterations):
        start = time.time()

        records = (
            session.query(HistoricalPrice)
            .filter(
                HistoricalPrice.stock_code == stock_code,
                HistoricalPrice.date >= start_str,
                HistoricalPrice.date <= end_str,
            )
            .order_by(HistoricalPrice.date)
            .all()
        )

        # Convert to DataFrame (current pattern)
        data = {
            "Open": [r.open for r in records],
            "High": [r.high for r in records],
            "Low": [r.low for r in records],
            "Close": [r.close for r in records],
            "Volume": [r.volume for r in records],
        }
        _ = pd.DataFrame(data, index=[r.date for r in records])

        times.append(time.time() - start)

    session.close()
    return times


def benchmark_raw_sql_approach(engine, stock_code: str, iterations: int = 50) -> list[float]:
    """Benchmark Raw SQL + pandas approach (optimized implementation)."""
    end_date = date.today()
    start_date = end_date - timedelta(days=120)

    query = text(
        """
        SELECT date, open, high, low, close, volume
        FROM historical_prices
        WHERE stock_code = :code
          AND date >= :start_date
          AND date <= :end_date
        ORDER BY date ASC
    """
    )

    times = []
    for _ in range(iterations):
        start = time.time()

        with engine.connect() as conn:
            df = pd.read_sql_query(
                query,
                conn,
                params={
                    "code": stock_code,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                index_col="date",
            )
            # Rename columns to match expected format
            df.columns = ["Open", "High", "Low", "Close", "Volume"]

        times.append(time.time() - start)

    return times


def print_stats(name: str, times: list[float]) -> dict:
    """Print and return statistics for timing results."""
    avg = statistics.mean(times) * 1000
    med = statistics.median(times) * 1000
    min_t = min(times) * 1000
    max_t = max(times) * 1000
    std = statistics.stdev(times) * 1000 if len(times) > 1 else 0

    print(f"\n{name}:")
    print(f"  Average: {avg:.2f}ms")
    print(f"  Median:  {med:.2f}ms")
    print(f"  Min:     {min_t:.2f}ms")
    print(f"  Max:     {max_t:.2f}ms")
    print(f"  StdDev:  {std:.2f}ms")

    return {"avg": avg, "med": med, "min": min_t, "max": max_t, "std": std}


def main():
    print("=" * 60)
    print(" Database Performance Benchmark")
    print("=" * 60)

    database_url = get_database_url()
    print(f"\n Database: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")

    engine = create_engine(database_url, pool_pre_ping=True)

    # Check for data
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM historical_prices"))
            count = result.fetchone()[0]
            print(f" Total records: {count:,}")

            if count == 0:
                print("\n No data in database. Run bulk_load_historical_prices_postgres.py first.")
                sys.exit(1)
    except Exception as e:
        print(f"\n Database error: {e}")
        sys.exit(1)

    stock_code = get_test_stock_code(engine)
    print(f" Test stock: {stock_code}")

    iterations = 50
    print(f"\n Running {iterations} iterations per approach...")

    # Warm up
    print("\n Warming up...")
    benchmark_raw_sql_approach(engine, stock_code, 5)
    benchmark_orm_approach(engine, stock_code, 5)

    # Actual benchmarks
    print("\n Running benchmarks...")

    orm_times = benchmark_orm_approach(engine, stock_code, iterations)
    orm_stats = print_stats("ORM Approach (Current)", orm_times)

    sql_times = benchmark_raw_sql_approach(engine, stock_code, iterations)
    sql_stats = print_stats("Raw SQL Approach (Optimized)", sql_times)

    # Calculate improvement
    improvement = (1 - sql_stats["avg"] / orm_stats["avg"]) * 100
    speedup = orm_stats["avg"] / sql_stats["avg"]

    print("\n" + "=" * 60)
    print(f" Improvement: {improvement:.1f}%")
    print(f" Speedup:     {speedup:.1f}x faster")
    print("=" * 60)

    # Summary table
    print("\n Summary:")
    print("  " + "-" * 40)
    print(f"  {'Metric':<20} {'ORM':>10} {'Raw SQL':>10}")
    print("  " + "-" * 40)
    print(f"  {'Average (ms)':<20} {orm_stats['avg']:>10.2f} {sql_stats['avg']:>10.2f}")
    print(f"  {'Median (ms)':<20} {orm_stats['med']:>10.2f} {sql_stats['med']:>10.2f}")
    print(f"  {'Min (ms)':<20} {orm_stats['min']:>10.2f} {sql_stats['min']:>10.2f}")
    print(f"  {'Max (ms)':<20} {orm_stats['max']:>10.2f} {sql_stats['max']:>10.2f}")
    print("  " + "-" * 40)

    return 0 if improvement > 50 else 1  # Pass if >50% improvement


if __name__ == "__main__":
    sys.exit(main())
