from flask import Flask, jsonify
import sqlite3
import pandas as pd
from pathlib import Path

app = Flask(__name__)

# Absolute path to the project root
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "housing.db"

@app.route("/")
def home():
    return "Housing Affordability API is running!"

@app.route("/cities")
def cities():
    print(DB_PATH)
    print(DB_PATH.exists())

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("SELECT * FROM housing", conn)

    conn.close()

    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)