import io
import re
import zipfile
import requests
import pandas as pd


STATCAN_BASE_URL = "https://www150.statcan.gc.ca/t1/wds/rest"

STATCAN_TABLES = {
    "population": "17100135",
    "income": "98100075",
    "cpi": "18100004",
    "house_price": "98100256",
    "mortgage_rate": "34100145",
}

REQUEST_TIMEOUT = 60

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

def _download_statcan_table(product_id: str, max_download_seconds: int = 45) -> pd.DataFrame:
    import time

    start = time.time()
    print(f"  [sources] requesting table {product_id}...")

    lookup_url = f"{STATCAN_BASE_URL}/getFullTableDownloadCSV/{product_id}/en"

    response = requests.get(lookup_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "SUCCESS":
        raise RuntimeError(f"StatCan WDS returned an error for table {product_id}: {payload}")

    zip_url = payload["object"]

    print(f"  [sources] downloading table {product_id} zip (hard limit {max_download_seconds}s)...")
    download_start = time.time()
    chunks = []
    downloaded_bytes = 0

    with requests.get(zip_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT, stream=True) as zip_response:
        zip_response.raise_for_status()
        for chunk in zip_response.iter_content(chunk_size=1_000_000):
            if chunk:
                chunks.append(chunk)
                downloaded_bytes += len(chunk)
            elapsed_download = time.time() - download_start
            if elapsed_download > max_download_seconds:
                raise RuntimeError(
                    f"Table {product_id} download exceeded {max_download_seconds}s "
                    f"({downloaded_bytes / 1_000_000:.1f}MB downloaded so far) -- "
                    f"this table is likely too large to download in full; it needs a "
                    f"narrower StatCan API call instead of getFullTableDownloadCSV."
                )

    content = b"".join(chunks)
    size_mb = len(content) / 1_000_000

    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        csv_name = next(
            name for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        )
        with archive.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)

    elapsed = time.time() - start
    print(f"  [sources] table {product_id} done: {size_mb:.1f}MB, {len(df):,} rows, {elapsed:.1f}s")

    return df


def normalize_cma_name(name):
    if not isinstance(name, str):
        return None

    lname = name.lower()

    if "gatineau" in lname:
        if "quebec part" in lname:
            return None
        if "ontario" not in lname and (
            re.search(r",\s*que\.?\s*$", lname) or lname.rstrip().endswith("quebec")
        ):
            return None

    name = re.sub(r"\s*\((?:CMA|CA)\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\((?:Ontario|Quebec) part\)", "", name, flags=re.IGNORECASE)
    name = re.sub(r",\s*Ontario part,?\s*Ontario\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r",\s*Ont\.?/Que\.?\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r",\s*Ontario/Quebec\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r",\s*(Ont\.|Ontario)\s*$", "", name, flags=re.IGNORECASE)

    return name.strip().strip(",").strip().lower()


def _clean_cma_join_key(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes df['cma_name'], drops unmatchable rows, and dedupes."""
    df = df.copy()
    raw = df["cma_name"].astype(str)
    df["cma_name"] = raw.apply(normalize_cma_name)
    df["_raw_cma_name"] = raw
    df = df.dropna(subset=["cma_name"])
    is_ontario_part = df["_raw_cma_name"].str.lower().str.contains("ontario part", na=False)
    df = df.assign(_prefer=is_ontario_part).sort_values("_prefer", ascending=False)
    df = df.drop_duplicates(subset=["cma_name"], keep="first")

    combined_ottawa = (
        df["cma_name"].eq("ottawa - gatineau")
        & ~df["_raw_cma_name"].str.lower().str.contains("ontario part", na=False)
    )
    if combined_ottawa.any():
        print(
            "  [sources] note: this table only reports Ottawa - Gatineau as one "
            "combined Ontario/Quebec CMA (no Ontario-only breakdown available), "
            "so Ottawa's figure here includes the Quebec (Gatineau) side."
        )

    return df.drop(columns=["_raw_cma_name", "_prefer"])


def _require_column(df: pd.DataFrame, expected: str, context: str) -> str:
    for col in df.columns:
        if col.strip().lower() == expected.lower():
            return col
    raise RuntimeError(
        f"Expected a '{expected}' column in {context} but didn't find one. "
        f"Actual columns returned by StatCan: {list(df.columns)}"
    )


def _find_value_column(df: pd.DataFrame):
    for col in df.columns:
        if col.strip().lower() == "value":
            return col
    return None


def _pick_latest_year_column(df: pd.DataFrame, keyword: str) -> str:
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


def _apply_dimension_filters(df: pd.DataFrame, dimension_filters):
    for entry in dimension_filters:
        keyword, must_contain = entry[0], entry[1]
        exact = entry[2] if len(entry) > 2 else False
        col = next((c for c in df.columns if keyword.lower() in c.lower()), None)
        if col is None:
            print(
                f"  [sources] WARNING: no column matching dimension keyword "
                f"{keyword!r} was found -- this filter was skipped entirely, "
                f"so unwanted categories may leak through. Actual columns: "
                f"{list(df.columns)}"
            )
            continue
        if exact:
            df = df[df[col].astype(str).str.strip().str.lower() == must_contain.strip().lower()]
        else:
            df = df[df[col].astype(str).str.contains(must_contain, case=False, na=False)]
    return df


def _select_dimension(df: pd.DataFrame, dimension_keyword: str, desired_category: str):
    wide_matches = [
        c for c in df.columns
        if c.lower().startswith(dimension_keyword.lower()) and "):" in c
    ]
    if wide_matches:
        selected = [c for c in wide_matches if desired_category.lower() in c.lower()]
        if not selected:
            raise RuntimeError(
                f"No wide column for '{dimension_keyword}' matching '{desired_category}'. "
                f"Options: {wide_matches}"
            )
        selected.sort(key=len)
        return df, selected[0]

    row_col = next((c for c in df.columns if dimension_keyword.lower() in c.lower()), None)
    if row_col:
        df = df[df[row_col].astype(str).str.contains(desired_category, case=False, na=False)]
    return df, None


def _extract_statcan_metric(
    df: pd.DataFrame,
    metric_name: str,
    wide_format_keyword: str,
    dimension_filters=None,
    context: str = "",
) -> pd.DataFrame:
    geo_col = _require_column(df, "GEO", context or metric_name)
    value_col = _find_value_column(df)

    if value_col:
        ref_col = next((c for c in df.columns if c.strip().upper() == "REF_DATE"), None)
        if ref_col:
            latest_ref_date = df[ref_col].max()
            df = df[df[ref_col] == latest_ref_date]
        if dimension_filters:
            df = _apply_dimension_filters(df, dimension_filters)
        metric_col = value_col
    else:
        metric_col = _pick_latest_year_column(df, wide_format_keyword)
        if dimension_filters:
            df = _apply_dimension_filters(df, dimension_filters)

    out = df[[geo_col, metric_col]].rename(columns={geo_col: "cma_name", metric_col: metric_name})
    out[metric_name] = out[metric_name].astype(str).str.replace(",", "", regex=False)
    out[metric_name] = pd.to_numeric(out[metric_name], errors="coerce")
    out = out.dropna(subset=[metric_name])

    dup_geo = sorted(out["cma_name"][out["cma_name"].duplicated(keep=False)].unique())
    if dup_geo:
        print(
            f"  [sources] WARNING: {context or metric_name} has more than one row "
            f"for the same GEO value after dimension filtering -- the filters "
            f"aren't narrowing down to a single category, so an arbitrary row "
            f"will be kept per city. Affected GEO values: {dup_geo}"
        )

    return _clean_cma_join_key(out)

def _get_population_by_cma() -> pd.DataFrame:
    """Latest total population estimate for each Ontario CMA."""
    df = _download_statcan_table(STATCAN_TABLES["population"])

    ref_col = _require_column(df, "REF_DATE", "the population table")
    latest_ref_date = df[ref_col].max()
    df = df[df[ref_col] == latest_ref_date]

    return _extract_statcan_metric(
        df,
        "population",
        wide_format_keyword="Population",
        dimension_filters=[("age group", "all ages"), ("sex", "Both sexes", True)],
        context="the population table",
    )


def _get_income_by_cma() -> pd.DataFrame:
    """Latest median total income for each Ontario CMA."""
    df = _download_statcan_table(STATCAN_TABLES["income"])
    return _extract_statcan_metric(
        df,
        "median_income",
        wide_format_keyword="Median amount ($)",
        dimension_filters=[
            ("Economic family characteristics", "Total - Persons by selected economic family characteristics", True),
            ("Income sources and taxes", "Total income", True),
        ],
        context="the income table",
    )


def _get_cpi_ontario():
    """Latest all-items CPI value for Ontario (applied province-wide)."""
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


def _get_house_price_by_cma() -> pd.DataFrame:
    df = _download_statcan_table(STATCAN_TABLES["house_price"])
    geo_col = _require_column(df, "GEO", "the house value table")

    bucket_col = next(
        (c for c in df.columns if "value" in c.lower() and "dwelling" in c.lower() and "):" not in c),
        None,
    )
    if bucket_col is None:
        raise RuntimeError(
            f"No 'Value (owner-estimated) of dwelling' column found. Columns: {list(df.columns)}"
        )

    before = len(df)
    df = df[df[bucket_col].astype(str).str.contains("Average value of dwellings", case=False, na=False)]
    if df.empty and before > 0:
        raise RuntimeError(
            f"Filtering '{bucket_col}' to 'Average value of dwellings' zeroed out all rows."
        )

    stats_col = next((c for c in df.columns if c.lower().startswith("statistics")), None)
    if stats_col:
        df = df[df[stats_col].astype(str).str.strip() == "Number of private households"]

    value_col = None
    for dimension, category in [
        ("Age of primary household maintainer", "Total"),
        ("Presence of mortgage payments", "Total"),
        ("Number of bedrooms", "Total"),
        ("Condominium status", "Total"),
        ("Structural type of dwelling", "Total"),
    ]:
        row_col = next((c for c in df.columns if dimension.lower() in c.lower() and "):" not in c), None)
        before = len(df)

        df, wide_col = _select_dimension(df, dimension, category)
        if wide_col:
            value_col = wide_col
            continue

        if row_col and len(df) == 0 and before > 0:
            raise RuntimeError(
                f"Filtering house value table on '{dimension}' contains '{category}' "
                f"zeroed out all rows (had {before} before). Inspect it directly, e.g.: "
                f"pd.read_csv(...)['{row_col}'].unique()"
            )

    if value_col is None:
        raise RuntimeError("Could not find the 'Structural type of dwelling' wide column for the total.")

    if df.empty:
        raise RuntimeError("House value table filtered down to zero rows before a wide column could be selected.")

    out = df[[geo_col, value_col]].rename(columns={geo_col: "cma_name", value_col: "average_house_price"})
    out["average_house_price"] = out["average_house_price"].astype(str).str.replace(",", "", regex=False)
    out["average_house_price"] = pd.to_numeric(out["average_house_price"], errors="coerce")
    out = out.dropna(subset=["average_house_price"])
    result = _clean_cma_join_key(out)

    if result.empty:
        raise RuntimeError(
            f"House value table produced 0 usable rows after selecting column '{value_col}' -- "
            f"the column exists but every value was non-numeric or missing."
        )

    return result


def _get_mortgage_rate():
    """Latest conventional 5-year mortgage lending rate, national (table 34-10-0145-01)."""
    df = _download_statcan_table(STATCAN_TABLES["mortgage_rate"])

    ref_col = _require_column(df, "REF_DATE", "the mortgage rate table")
    value_col = _require_column(df, "VALUE", "the mortgage rate table")

    latest_ref_date = df[ref_col].max()
    latest = df[df[ref_col] == latest_ref_date]

    if latest.empty:
        raise RuntimeError("No rows found in table 34-10-0145-01")

    return float(latest.iloc[0][value_col]), str(latest_ref_date)

def get_statscan_data() -> pd.DataFrame:
    """
    Downloads every field from Statistics Canada and returns one combined
    DataFrame keyed by cma_name. Each metric is fetched independently --
    if one table is too large or times out, the others still make it
    into the result instead of the whole thing being discarded.
    """
    release_info = {}
    merged = None

    def _add(df_new, label):
        nonlocal merged
        if merged is None:
            merged = df_new
        else:
            merged = pd.merge(merged, df_new, on="cma_name", how="outer")

    print("[sources] fetching population...")
    try:
        _add(_get_population_by_cma(), "population")
    except Exception as exc:
        print(f"  [sources] population failed, skipping: {exc}")

    print("[sources] fetching income...")
    try:
        _add(_get_income_by_cma(), "income")
    except Exception as exc:
        print(f"  [sources] income failed, skipping: {exc}")

    print("[sources] fetching CPI (this table is large, can take a while)...")
    try:
        cpi_value, cpi_ref_date = _get_cpi_ontario()
        release_info["release"] = cpi_ref_date
    except Exception as exc:
        print(f"  [sources] CPI failed, skipping: {exc}")
        cpi_value = None

    print("[sources] fetching house price...")
    try:
        _add(_get_house_price_by_cma(), "house_price")
    except Exception as exc:
        print(f"  [sources] house price failed, skipping: {exc}")

    print("[sources] fetching mortgage rate...")
    try:
        mortgage_rate, mortgage_ref_date = _get_mortgage_rate()
        release_info["mortgage_release"] = mortgage_ref_date
    except Exception as exc:
        print(f"  [sources] mortgage rate failed, skipping: {exc}")
        mortgage_rate = None

    if merged is None:
        raise RuntimeError("Every StatCan source failed -- nothing to merge.")

    if cpi_value is not None:
        merged["cpi"] = cpi_value
    if mortgage_rate is not None:
        merged["mortgage_rate"] = mortgage_rate

    merged.attrs.update(release_info)
    return merged

def get_sample_data() -> pd.DataFrame:
    data = {
        "city": ["Toronto", "Ottawa", "Thunder Bay"],
        "province": ["Ontario", "Ontario", "Ontario"],
        "average_house_price": [1030000, 650000, 430000],
        "median_income": [95000, 102000, 76000],
        "population": [6250000, 1050000, 110000],
        "cpi": [162.3, 162.3, 162.3],
        "mortgage_rate": [6.44, 6.44, 6.44],
        "latitude": [43.6532, 45.4215, 48.3809],
        "longitude": [-79.3832, -75.6972, -89.2477],
    }
    return pd.DataFrame(data)