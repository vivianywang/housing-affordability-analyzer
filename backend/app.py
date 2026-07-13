from flask import Flask
from flask_cors import CORS
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "housing.db")

@app.route("/cities")
def cities():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM housing", conn)
    conn.close()
    return df.to_dict(orient="records")

if __name__ == "__main__":
    app.run(debug=True)