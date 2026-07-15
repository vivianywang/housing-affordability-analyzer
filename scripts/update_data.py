"""
update_data.py

The ETL entry point. Run this with:

    python scripts/update_data.py

Flow:

    Statistics Canada
        |
        v
    Download data
        |
        v
    Merge with data/cities.csv
        |
        v
    Clean (pandas)
        |
        v
    Write to SQLite (housing + metadata tables)

CREA, CMHC and Bank of Canada are still placeholders (see sources.py) --
their columns exist in the schema but will be empty / null until those
are implemented on later days.
"""

import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from sources import (
    get_statscan_data,
    get_crea_data,
    get_cmhc_data,
    get_bank_of_canada_data,
    get_sample_data,
)
from cleaning import clean_data, merge_with_cities

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "housing.db")
CITIES_PATH = os.path.join(BASE_DIR, "..", "data", "cities.csv")
print(f"[update_data.py] script location: {BASE_DIR}")
print(f"[update_data.py] writing database to: {os.path.abspath(DB_PATH)}")

HOUSING_SCHEMA = """
CREATE TABLE IF NOT EXISTS housing (
    city TEXT PRIMARY KEY,
    province TEXT,
    average_house_price REAL,
    average_rent REAL,
    median_income REAL,
    population REAL,
    interest_rate REAL,
    cpi REAL,
    latitude REAL,
    longitude REAL,
    last_updated TEXT
)
"""

METADATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    source TEXT PRIMARY KEY,
    last_updated TEXT,
    dataset_version TEXT,
    status TEXT
)
"""


def run_etl() -> pd.DataFrame:
    cities_df = pd.read_csv(CITIES_PATH)

    sources_used = []  # (source_name, status) tuples for the metadata table

    # --- Statistics Canada -------------------------------------------------
    try:
        statscan_df = get_statscan_data()
        sources_used.append(("Statistics Canada", "ok"))
        print(f"Downloaded StatCan data for {len(statscan_df)} CMAs")
    except Exception as exc:
        print(f"[warning] Statistics Canada download failed: {exc}")
        print("[warning] Falling back to sample data for this run.")
        statscan_df = None
        sources_used.append(("Statistics Canada", f"failed: {exc}"))

    if statscan_df is not None:
        merged = merge_with_cities(statscan_df, cities_df)
    else:
        # Fall back so the pipeline still produces *something* usable
        # instead of crashing (e.g. no internet access, StatCan is down,
        # or a column name changed upstream).
        merged = get_sample_data()

    # --- CREA / CMHC / Bank of Canada (placeholders for now) ---------------
    for name, fn in [
        ("CREA", get_crea_data),
        ("CMHC", get_cmhc_data),
        ("Bank of Canada", get_bank_of_canada_data),
    ]:
        result = fn()
        if result is None:
            sources_used.append((name, "not yet implemented"))
        else:
            sources_used.append((name, "ok"))
            # once these return real DataFrames, merge them in here the
            # same way statscan_df was merged above.

    df = clean_data(merged)
    df["last_updated"] = datetime.now(timezone.utc).isoformat()

    write_to_database(df, sources_used)
    return df


def write_to_database(df: pd.DataFrame, sources_used) -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS housing")
    cur.execute(HOUSING_SCHEMA)
    cur.execute(METADATA_SCHEMA)

    # Refresh housing data: table was just recreated fresh, insert the newest release.
    df.to_sql("housing", conn, if_exists="append", index=False)

    # Refresh metadata: one row per source, so the frontend can show
    # exactly what's live vs. still pending.
    now = datetime.now(timezone.utc).isoformat()
    for source_name, status in sources_used:
        cur.execute(
            """
            INSERT INTO metadata (source, last_updated, dataset_version, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source) DO UPDATE SET
                last_updated=excluded.last_updated,
                dataset_version=excluded.dataset_version,
                status=excluded.status
            """,
            (source_name, now, "latest release", status),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    result_df = run_etl()
    print(result_df)
    print("Database Updated")