import pandas as pd

NUMERIC_COLUMNS = [
    "average_house_price",
    "median_income",
    "population",
    "cpi",
    "mortgage_rate",
    "latitude",
    "longitude",
    "affordability_score",
]

FINAL_COLUMNS = [
    "city",
    "province",
    "average_house_price",
    "median_income",
    "population",
    "cpi",
    "mortgage_rate",
    "latitude",
    "longitude",
    "affordability_score",
]


def merge_all(cities_df: pd.DataFrame, statscan_df: pd.DataFrame) -> pd.DataFrame:
    """
    Every field now comes from the same StatCan extract, keyed by
    cma_name, so this is a single merge -- no more separate CREA/CMHC/BoC
    matching steps.
    """
    return cities_df.merge(statscan_df, on="cma_name", how="left")


def compute_affordability_score(df: pd.DataFrame) -> pd.DataFrame:
    """Price-to-income ratio. Lower = more affordable."""
    df["affordability_score"] = (df["average_house_price"] / df["median_income"]).round(2)
    return df


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

    df = compute_affordability_score(df)

    df = df[FINAL_COLUMNS].reset_index(drop=True)
    return df