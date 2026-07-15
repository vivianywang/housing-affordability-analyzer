import pandas as pd

NUMERIC_COLUMNS = [
    "average_house_price",
    "average_rent",
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
    "average_rent",
    "median_income",
    "population",
    "cpi",
    "mortgage_rate",
    "latitude",
    "longitude",
    "affordability_score",
]


def merge_all(cities_df, statscan_df, crea_df=None, cmhc_df=None, boc_df=None) -> pd.DataFrame:
    merged = cities_df.merge(statscan_df, on="cma_name", how="left")

    if crea_df is not None and not crea_df.empty:
        merged = merged.merge(crea_df, on="city", how="left")
    else:
        merged["average_house_price"] = None

    if cmhc_df is not None and not cmhc_df.empty:
        merged = merged.merge(cmhc_df, on="city", how="left")
    else:
        merged["average_rent"] = None

    if boc_df is not None and not boc_df.empty:
        merged["mortgage_rate"] = boc_df.iloc[0]["mortgage_rate"]
    else:
        merged["mortgage_rate"] = None

    return merged


def compute_affordability_score(df: pd.DataFrame) -> pd.DataFrame:
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