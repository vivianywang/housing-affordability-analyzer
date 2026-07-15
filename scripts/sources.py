"""
sources.py

Everything that talks to the OUTSIDE WORLD lives here.
Each function returns a pandas DataFrame. The rest of the pipeline
(cleaning.py, update_data.py) never needs to know where the data came from.

Statistics Canada is implemented for real using their public
Web Data Service (WDS): https://www.statcan.gc.ca/en/developers/wds
CREA / CMHC / Bank of Canada are still placeholders -- we'll wire them
up on later days, the same way we did StatCan here.
"""

import io
import zipfile
import requests
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Keep every source-specific detail (URLs, table/product IDs, column names)
# in one place. When a table gets renumbered or StatCan tweaks a column
# name, this is the only place that should need to change.

STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"

# Product IDs (a.k.a. table numbers with the dashes removed) for the
# StatCan tables we need. You can look these up / verify them at
# https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=<product_id>
STATCAN_TABLES = {
    # Population estimates, July 1, by census metropolitan area (CMA)
    "population": "17100135",
    # Economic family unit income statistics by CMA (median total income)
    "income": "98100075",
    # Consumer Price Index, monthly, not seasonally adjusted (by geography)
    "cpi": "18100004",
}

REQUEST_TIMEOUT = 60  # seconds

# A handful of sites (StatCan included) reject requests that don't look
# like they're coming from a browser. A normal-looking User-Agent avoids
# spurious 403s.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Low level helper: download + unzip a full StatCan table
# ---------------------------------------------------------------------------
def _download_statcan_table(product_id: str) -> pd.DataFrame:
    """
    Downloads a full StatCan data table as CSV using the WDS
    'getFullTableDownloadCSV' method and returns it as a DataFrame.

    Docs: https://www.statcan.gc.ca/en/developers/wds/user-guide
    """
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
        # The archive contains the data CSV plus a "...MetaData.csv" file.
        # We want the one that ISN'T metadata.
        csv_name = next(
            name for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        )
        with archive.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)

    return df


def _require_column(df: pd.DataFrame, expected: str, context: str) -> str:
    """
    Returns the actual column name matching `expected` (case-insensitive,
    since StatCan has changed VALUE/Value casing between releases before).
    Raises a RuntimeError listing every real column name if nothing matches,
    so a failure tells you exactly what StatCan sent instead of a bare
    KeyError.
    """
    for col in df.columns:
        if col.strip().lower() == expected.lower():
            return col
    raise RuntimeError(
        f"Expected a '{expected}' column in {context} but didn't find one. "
        f"Actual columns returned by StatCan: {list(df.columns)}"
    )


# ---------------------------------------------------------------------------
# Individual StatCan extracts
# ---------------------------------------------------------------------------
def _get_population_by_cma() -> pd.DataFrame:
    """Latest total population estimate for each Ontario CMA."""
    df = _download_statcan_table(STATCAN_TABLES["population"])

    ref_col = _require_column(df, "REF_DATE", "the population table")
    geo_col = _require_column(df, "GEO", "the population table")
    value_col = _require_column(df, "VALUE", "the population table")

    latest_ref_date = df[ref_col].max()
    df = df[df[ref_col] == latest_ref_date]

    # This table is broken down by age group and gender -- without
    # narrowing to the "all ages, both genders" total row, each CMA
    # appears dozens of times (one row per age/gender combo), which
    # both inflates row counts hugely and would pick an arbitrary
    # sub-total if left unfiltered.
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
    """
    This income table is wide-format: instead of one VALUE column, every
    statistic/year combo gets its own column, e.g.
    'Income statistics (16A):Median amount ($) (2020)[3]' and
    '...Median amount ($) (2015)[11]'. This finds every column containing
    `keyword` and returns the one for the most recent year in parentheses.
    """
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
    """Latest median total income for each Ontario CMA."""
    df = _download_statcan_table(STATCAN_TABLES["income"])

    geo_col = _require_column(df, "GEO", "the income table")
    median_col = _pick_latest_year_column(df, "Median amount ($)")

    family_col = next(
        (c for c in df.columns if "Economic family characteristics" in c), None
    )
    source_col = next(
        (c for c in df.columns if "Income sources and taxes" in c), None
    )

    # Narrow down to the "Total" / "Total income" rows -- this table has one
    # row per combination of family type x income source, and we want the
    # overall total for both, not a breakdown by family type or income type.
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
    """
    Latest all-items CPI value for Ontario.
    CPI is only published at the province level (and a few individual
    cities), so we apply one provincial value to every Ontario city
    rather than pretending there's a per-city figure.
    """
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

    return float(ontario.iloc[0][value_col])


# ---------------------------------------------------------------------------
# Public entry point used by update_data.py
# ---------------------------------------------------------------------------
def get_statscan_data() -> pd.DataFrame:
    """
    Connects to Statistics Canada, downloads the newest release for
    population, income and CPI, and returns one combined DataFrame
    keyed by cma_name:

        cma_name | population | median_income | cpi
    """
    population = _get_population_by_cma()
    income = _get_income_by_cma()
    cpi_value = _get_cpi_ontario()

    merged = pd.merge(population, income, on="cma_name", how="outer")
    merged["cpi"] = cpi_value

    return merged


# ---------------------------------------------------------------------------
# Placeholders -- implemented on later days
# ---------------------------------------------------------------------------
def get_crea_data():
    """Average resale house prices by city, from the Canadian Real Estate Association."""
    pass


def get_cmhc_data():
    """Average rent by city, from CMHC's Rental Market Survey."""
    pass


def get_bank_of_canada_data():
    """Current mortgage / policy interest rate, from the Bank of Canada Valet API."""
    pass


# ---------------------------------------------------------------------------
# Kept around for local testing / as a fallback if a live source is down
# ---------------------------------------------------------------------------
def get_sample_data() -> pd.DataFrame:
    data = {
        "city": ["Toronto", "Ottawa", "Thunder Bay"],
        "province": ["Ontario", "Ontario", "Ontario"],
        "region": ["GTA", "East", "North"],
        "average_house_price": [1030000, 650000, 430000],
        "average_rent": [2750, 2100, 1450],
        "median_income": [95000, 102000, 76000],
        "latitude": [43.6532, 45.4215, 48.3809],
        "longitude": [-79.3832, -75.6972, -89.2477],
    }
    return pd.DataFrame(data)