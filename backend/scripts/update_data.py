import os
from datetime import datetime, timezone

import pandas as pd

from sources import get_statscan_data, get_sample_data, normalize_cma_name
from cleaning import clean_data, merge_all
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITIES_PATH = os.path.join(BASE_DIR, "..", "data", "cities.csv")


def run_etl() -> pd.DataFrame:
    cities_df = pd.read_csv(CITIES_PATH)
    cities_df["cma_name"] = cities_df["cma_name"].apply(normalize_cma_name)
    metadata_values = {}

    try:
        statscan_df = get_statscan_data()
        metadata_values["statscan_release"] = statscan_df.attrs.get("release", "unknown")
        metadata_values["mortgage_rate_release"] = statscan_df.attrs.get("mortgage_release", "unknown")
    except Exception as exc:
        print(f"[warning] Statistics Canada download failed: {exc}")
        statscan_df = None
        metadata_values["statscan_release"] = f"failed: {exc}"

    if statscan_df is not None:
        our_names = set(cities_df["cma_name"])
        their_names = set(statscan_df["cma_name"].dropna())
        unmatched = our_names - their_names
        if unmatched:
            print(f"[update_data.py] WARNING: {len(unmatched)} cma_name(s) from cities.csv "
                  f"don't appear in the StatCan data at all: {sorted(unmatched)}")
            close_matches = {name: [t for t in their_names if name.split(" - ")[0].split(",")[0].strip().lower() in t.lower()]
                              for name in unmatched}
            for name, matches in close_matches.items():
                if matches:
                    print(f"    '{name}' -- possible match(es) in StatCan data: {matches}")

        merged = merge_all(cities_df, statscan_df)
        numeric_check_cols = [c for c in ["population", "median_income", "average_house_price", "cpi", "mortgage_rate"] if c in merged.columns]
        if numeric_check_cols:
            null_counts = merged[numeric_check_cols].isna().sum()
            if null_counts.sum() > 0:
                print(f"[update_data.py] null counts after merge (out of {len(merged)} cities):")
                print(null_counts.to_string())
    else:
        print("[warning] Falling back to sample data for this run.")
        merged = get_sample_data()

    df = clean_data(merged)
    df["last_updated"] = datetime.now(timezone.utc).isoformat()

    metadata_values["last_updated"] = datetime.now(timezone.utc).isoformat()

    conn = database.get_connection()
    database.init_schema(conn)
    database.write_housing(conn, df)
    database.write_metadata(conn, metadata_values)
    conn.close()

    return df


if __name__ == "__main__":
    result_df = run_etl()
    print(result_df)
    print("Database Updated")