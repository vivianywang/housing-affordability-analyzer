import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "housing.db")

HOUSING_SCHEMA = """
CREATE TABLE IF NOT EXISTS housing (
    city TEXT PRIMARY KEY,
    province TEXT,
    average_house_price REAL,
    average_rent REAL,
    median_income REAL,
    population REAL,
    cpi REAL,
    mortgage_rate REAL,
    latitude REAL,
    longitude REAL,
    affordability_score REAL,
    last_updated TEXT
)
"""

METADATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
)
"""


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(HOUSING_SCHEMA)
    cur.execute(METADATA_SCHEMA)
    conn.commit()


def write_housing(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS housing")
    cur.execute(HOUSING_SCHEMA)
    df.to_sql("housing", conn, if_exists="append", index=False)
    conn.commit()


def write_metadata(conn: sqlite3.Connection, values: dict) -> None:
    cur = conn.cursor()
    cur.execute(METADATA_SCHEMA)
    for key, value in values.items():
        cur.execute(
            """
            INSERT INTO metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, str(value)),
        )
    conn.commit()


def read_housing() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM housing", conn)
    conn.close()
    return df


def read_metadata() -> dict:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM metadata", conn)
    conn.close()
    return dict(zip(df["key"], df["value"]))