import io
import os
import zipfile
import requests
import pandas as pd

STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
BOC_BASE_URL = "https://www.bankofcanada.ca/valet"

STATCAN_TABLES = {
    "population": "17100135",
    "income": "98100075",
    "cpi": "18100004",
}

BOC_SERIES = {
    "mortgage_rate_5yr": "V80691335",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREA_PRICES_PATH = os.path.join(BASE_DIR, "..", "data", "crea_avg_prices.csv")
CMHC_RENT_PATH = os.path.join(BASE_DIR, "..", "data", "cmhc_avg_rent.csv")

REQUEST_TIMEOUT = 60

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def _download_statcan_table(product_id: str) -> pd.DataFrame:
    lookup_url = f"{STATCAN_BASE_URL}/getFullTableDownloadCSV/{product_id}/en"

    response = requests.get(lookup_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"StatCan WDS returned an error for table {product_id}: {payload}")

    zip_url = payload["object"]

    zip_response = requests.get(zip_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT * 3)
    zip_response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as archive:
        csv_name = next(
            name for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        )
        with archive.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)

    return df


def _require_column(df: pd.DataFrame, expected: str, context: str) -> str:
    for col in df.columns:
        if col.strip().lower() == expected.lower():
            return col
    raise RuntimeError(
        f"Expected a '{expected}' column in {context} but didn't find one. "
        f"Actual columns returned by StatCan: {list(df.columns)}"
    )


def _get_population_by_cma() -> pd.DataFrame:
    df = _download_statcan_table(STATCAN_TABLES["population"])

    ref_col = _require_column(df, "REF_DATE", "the population table")
    geo_col = _require_column(df, "GEO", "the population table")
    value_col = _require_column(df, "VALUE", "the population table")

    latest_ref_date = df[ref_col].max()
    df = df[df[ref_col] == latest_ref_date]

    age_col = next((c for c in df.columns if "age group" in c.lower()), None)
    gender_col = next((c for c in df.columns if c.lower() in ("gender", "sex")), None)

    if age_col:
        df = df[df[age_col].astype(str).str.contains("all ages", case=False, na=False)]
    if gender_col:
        df = df[df[gender_col].astype(str).str.contains("total|both", case=False, na=False, regex=True)]

    df = df[[geo_col, value_col]].rename(columns={geo_col: "cma_name", value_col: "population"})
    df["population"] = pd.to_numeric(df["population"], errors="coerce")
    return df.dropna(subset=["population"])


def _pick_latest_year_column(df: pd.DataFrame, keyword: str) -> str:
    import re

    candidates = []
    for col in df.columns:
        if keyword.lower() in col.lower():
            match = re.search(r"\((\d{4})\)", col)
            if match:
                candidates.append((int(match.group(1)), col))

    if not candidates:
        raise RuntimeError(
            f"No column containing '{keyword}' with a year found. "
            f"Actual columns: {list(df.columns)}"
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _get_income_by_cma() -> pd.DataFrame:
    df = _download_statcan_table(STATCAN_TABLES["income"])

    geo_col = _require_column(df, "GEO", "the income table")
    median_col = _pick_latest_year_column(df, "Median amount ($)")

    family_col = next(
        (c for c in df.columns if "Economic family characteristics" in c), None
    )
    source_col = next(
        (c for c in df.columns if "Income sources and taxes" in c), None
    )

    if family_col:
        df = df[df[family_col].astype(str).str.contains("Total", case=False, na=False)]
    if source_col:
        df = df[df[source_col].astype(str).str.contains("Total income", case=False, na=False)]

    df["median_income"] = (
        df[median_col].astype(str).str.replace(",", "", regex=False)
    )
    df["median_income"] = pd.to_numeric(df["median_income"], errors="coerce")

    df = df[[geo_col, "median_income"]].rename(columns={geo_col: "cma_name"})
    return df.dropna(subset=["median_income"])


def _get_cpi_ontario() -> float:
    df = _download_statcan_table(STATCAN_TABLES["cpi"])

    ref_col = _require_column(df, "REF_DATE", "the CPI table")
    geo_col = _require_column(df, "GEO", "the CPI table")
    value_col = _require_column(df, "VALUE", "the CPI table")

    ontario = df[df[geo_col].astype(str).str.contains("Ontario", na=False)]

    products_col = next((c for c in ontario.columns if "Products" in c), None)
    if products_col:
        ontario = ontario[ontario[products_col].astype(str).str.contains("All-items", case=False, na=False)]

    latest_ref_date = ontario[ref_col].max()
    ontario = ontario[ontario[ref_col] == latest_ref_date]

    if ontario.empty:
        raise RuntimeError("Could not find an Ontario all-items CPI row in table 18-10-0004-01")

    return float(ontario.iloc[0][value_col]), str(latest_ref_date)


def get_statscan_data() -> pd.DataFrame:
    population = _get_population_by_cma()
    income = _get_income_by_cma()
    cpi_value, cpi_ref_date = _get_cpi_ontario()

    merged = pd.merge(population, income, on="cma_name", how="outer")
    merged["cpi"] = cpi_value
    merged.attrs["release"] = cpi_ref_date
    return merged


def _get_boc_series_latest(series_id: str):
    url = f"{BOC_BASE_URL}/observations/{series_id}/json"
    response = requests.get(
        url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, params={"recent": 1}
    )
    response.raise_for_status()
    payload = response.json()

    observations = payload.get("observations", [])
    if not observations:
        raise RuntimeError(f"Bank of Canada Valet API returned no observations for {series_id}")

    latest = observations[-1]
    value = float(latest[series_id]["v"])
    ref_date = latest["d"]
    return value, ref_date


def get_bank_of_canada_data() -> pd.DataFrame:
    rate, ref_date = _get_boc_series_latest(BOC_SERIES["mortgage_rate_5yr"])
    df = pd.DataFrame({"mortgage_rate": [rate]})
    df.attrs["release"] = ref_date
    return df


def get_crea_data():
    if not os.path.exists(CREA_PRICES_PATH):
        return None

    df = pd.read_csv(CREA_PRICES_PATH)
    if "city" not in df.columns or "average_house_price" not in df.columns:
        raise RuntimeError(
            f"{CREA_PRICES_PATH} must have 'city' and 'average_house_price' columns"
        )
    df["average_house_price"] = pd.to_numeric(df["average_house_price"], errors="coerce")
    return df[["city", "average_house_price"]].dropna()


def get_cmhc_data():
    if not os.path.exists(CMHC_RENT_PATH):
        return None

    df = pd.read_csv(CMHC_RENT_PATH)
    if "city" not in df.columns or "average_rent" not in df.columns:
        raise RuntimeError(
            f"{CMHC_RENT_PATH} must have 'city' and 'average_rent' columns"
        )
    df["average_rent"] = pd.to_numeric(df["average_rent"], errors="coerce")
    return df[["city", "average_rent"]].dropna()


def get_sample_data() -> pd.DataFrame:
    data = {
        "city": ["Toronto", "Ottawa", "Thunder Bay"],
        "province": ["Ontario", "Ontario", "Ontario"],
        "average_house_price": [1030000, 650000, 430000],
        "average_rent": [2750, 2100, 1450],
        "median_income": [95000, 102000, 76000],
        "population": [6250000, 1050000, 110000],
        "cpi": [162.3, 162.3, 162.3],
        "mortgage_rate": [6.44, 6.44, 6.44],
        "latitude": [43.6532, 45.4215, 48.3809],
        "longitude": [-79.3832, -75.6972, -89.2477],
    }
    return pd.DataFrame(data)