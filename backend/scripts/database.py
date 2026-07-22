import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR,'..','database','housing.db')}"
)

engine = create_engine(DATABASE_URL)
HOUSING_SCHEMA = """
CREATE TABLE IF NOT EXISTS housing (
    city TEXT PRIMARY KEY,
    province TEXT,
    average_house_price REAL,
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


def get_connection():
    return engine


def init_schema(engine):
    with engine.begin() as conn:
        conn.execute(text(HOUSING_SCHEMA))
        conn.execute(text(METADATA_SCHEMA))


def write_housing(engine, df):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS housing"))
        conn.execute(text(HOUSING_SCHEMA))
        df.to_sql(
            "housing",
            conn,
            if_exists="append",
            index=False
        )


def write_metadata(engine, values):
    with engine.begin() as conn:
        conn.execute(text(METADATA_SCHEMA))
        for key, value in values.items():
            conn.execute(
                text("""
                INSERT INTO metadata(key,value)
                VALUES (:key,:value)
                ON CONFLICT(key)
                DO UPDATE
                SET value=EXCLUDED.value
                """),
                {
                    "key": key,
                    "value": str(value)
                }
            )


def read_housing():
    return pd.read_sql(
        "SELECT * FROM housing",
        engine
    )


def read_metadata():
    df = pd.read_sql(
        "SELECT * FROM metadata",
        engine
    )
    return dict(zip(df.key, df.value))