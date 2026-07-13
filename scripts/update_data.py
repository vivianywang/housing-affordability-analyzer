import sqlite3
import os

from sources import get_sample_data
from cleaning import clean_data

df = get_sample_data()
df = clean_data(df)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "housing.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)

df.to_sql(
    "housing",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(df)
print("Database Updated")