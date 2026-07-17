from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "housing.db")


def read_housing() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM housing", conn)
    conn.close()
    return df


def monthly_payment(principal, annual_rate, years):
    r = annual_rate / 100 / 12
    n = years * 12

    if r == 0:
        return principal / n

    payment = (
        principal *
        (r * (1 + r) ** n)
        /
        ((1 + r) ** n - 1)
    )

    return payment


@app.route("/cities")
def cities():
    return read_housing().to_dict(orient="records")


@app.route("/city/<city_name>")
def city(city_name):
    df = read_housing()
    row = df[df["city"].str.lower() == city_name.lower()]

    if row.empty:
        return jsonify({"error": "City not found"}), 404

    return jsonify(row.iloc[0].to_dict())


@app.route("/summary")
def summary():
    df = read_housing()

    return jsonify({
        "average_house_price": round(df["average_house_price"].mean(), 2),
        "average_income": round(df["median_income"].mean(), 2),
        "city_count": int(df["city"].nunique()),
    })


@app.route("/ranking")
def ranking():
    df = read_housing()
    df = df.dropna(subset=["affordability_score"]).sort_values("affordability_score")

    return df[["city", "average_house_price", "median_income", "affordability_score"]].to_dict(
        orient="records"
    )


@app.route("/metadata")
def metadata():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM metadata", conn)
    conn.close()

    return jsonify(dict(zip(df["key"], df["value"])))


@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()

    income = float(data["income"])
    down_payment = float(data["down_payment"])
    interest_rate = float(data["interest_rate"])
    term = int(data["term"])
    city = data["city"]

    df = read_housing()
    city_data = df[df["city"] == city]

    if city_data.empty:
        return jsonify({"error": "City not found"}), 404

    house_price = float(city_data.iloc[0]["average_house_price"])

    loan = max(0, house_price - down_payment)

    payment = monthly_payment(
        loan,
        interest_rate,
        term
    )

    monthly_income = income / 12
    dti = payment / monthly_income

    if dti < 0.30:
        rating = "Excellent"
    elif dti < 0.40:
        rating = "Good"
    elif dti < 0.50:
        rating = "Moderate"
    else:
        rating = "Poor"

    return jsonify({
        "city": city,
        "house_price": round(house_price, 2),
        "loan_amount": round(loan, 2),
        "monthly_payment": round(payment, 2),
        "dti": round(dti * 100, 1),
        "rating": rating
    })


if __name__ == "__main__":
    app.run(debug=True)