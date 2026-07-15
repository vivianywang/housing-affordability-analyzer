import os
from datetime import datetime, timezone

import pandas as pd

from sources import (
    get_statscan_data,
    get_crea_data,
    get_cmhc_data,
    get_bank_of_canada_data,
    get_sample_data,
)
from cleaning import clean_data, merge_all
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITIES_PATH = os.path.join(BASE_DIR, "..", "data", "cities.csv")


def run_etl() -> pd.DataFrame:
    cities_df = pd.read_csv(CITIES_PATH)
    metadata_values = {}

    try:
        statscan_df = get_statscan_data()
        metadata_values["statscan_release"] = statscan_df.attrs.get("release", "unknown")
    except Exception as exc:
        print(f"[warning] Statistics Canada download failed: {exc}")
        statscan_df = None
        metadata_values["statscan_release"] = f"failed: {exc}"

    try:
        crea_df = get_crea_data()
        metadata_values["crea_release"] = "local file" if crea_df is not None else "not available"
    except Exception as exc:
        print(f"[warning] CREA data load failed: {exc}")
        crea_df = None
        metadata_values["crea_release"] = f"failed: {exc}"

    try:
        cmhc_df = get_cmhc_data()
        metadata_values["cmhc_release"] = "local file" if cmhc_df is not None else "not available"
    except Exception as exc:
        print(f"[warning] CMHC data load failed: {exc}")
        cmhc_df = None
        metadata_values["cmhc_release"] = f"failed: {exc}"

    try:
        boc_df = get_bank_of_canada_data()
        metadata_values["boc_rate"] = boc_df.iloc[0]["mortgage_rate"]
        metadata_values["boc_release"] = boc_df.attrs.get("release", "unknown")
    except Exception as exc:
        print(f"[warning] Bank of Canada download failed: {exc}")
        boc_df = None
        metadata_values["boc_rate"] = "unavailable"

    if statscan_df is not None:
        merged = merge_all(cities_df, statscan_df, crea_df, cmhc_df, boc_df)
    else:
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