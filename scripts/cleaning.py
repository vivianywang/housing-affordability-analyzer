import pandas as pd

NUMERIC_COLUMNS = [
    "average_house_price",
    "average_rent",
    "median_income",
    "population",
    "interest_rate",
    "cpi",
    "latitude",
    "longitude",
]

FINAL_COLUMNS = [
    "city",
    "province",
    "average_house_price",
    "average_rent",
    "median_income",
    "population",
    "interest_rate",
    "cpi",
    "latitude",
    "longitude",
]


def merge_with_cities(statscan_df: pd.DataFrame, cities_df: pd.DataFrame) -> pd.DataFrame:
    merged = cities_df.merge(statscan_df, on="cma_name", how="left")
    return merged


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = None

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "province" in df.columns:
        df = df[df["province"] == "Ontario"]

    df = df.drop(columns=["cma_name"], errors="ignore")

    df = df.dropna(subset=["city", "latitude", "longitude"])

    df = df[FINAL_COLUMNS].reset_index(drop=True)
    return df