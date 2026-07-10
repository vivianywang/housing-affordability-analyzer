import sqlite3

conn = sqlite3.connect("./database/housing.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS housing(
    city TEXT PRIMARY KEY,
    region TEXT,
    average_house_price REAL,
    average_rent REAL,
    median_income REAL,
    latitude REAL,
    longitude REAL,
    last_updated TEXT
)
""")

cities = [
    ("Toronto","GTA",1030000,2750,95000,43.65,-79.38,"2026-07-09"),
    ("Ottawa","East",650000,2100,102000,45.42,-75.69,"2026-07-09"),
    ("Thunder Bay","North",430000,1450,76000,48.38,-89.25,"2026-07-09")
]

cursor.executemany("""
INSERT OR REPLACE INTO housing
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", cities)

conn.commit()
conn.close()

print("Database updated!")
