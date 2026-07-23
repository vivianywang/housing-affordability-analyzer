import { useState } from "react";
import { api, BackendUnreachableError } from "../api";
import { formatCurrency, formatPercent } from "../utils/format";
import RatingGauge from "../components/RatingGauge";

const DEFAULT_TERM = 25;

function useNumberField(initial = "") {
  const [value, setValue] = useState(initial);
  const [touched, setTouched] = useState(false);
  return {
    value,
    onChange: (e) => setValue(e.target.value),
    onBlur: () => setTouched(true),
    touched,
    setTouched,
  };
}

export default function Calculator({ cities }) {
  const income = useNumberField("");
  const downPayment = useNumberField("");
  const interestRate = useNumberField("5.0");
  const [term, setTerm] = useState(DEFAULT_TERM);
  const [city, setCity] = useState(cities[0]?.city ?? "");

  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const fields = [income, downPayment, interestRate];
  const numericValues = fields.map((f) => Number(f.value));
  const isValid =
    city &&
    fields.every((f) => f.value !== "") &&
    numericValues.every((v) => Number.isFinite(v) && v >= 0) &&
    numericValues[0] > 0;

  function handleSubmit(e) {
    e.preventDefault();
    fields.forEach((f) => f.setTouched(true));
    if (!isValid) return;

    setStatus("loading");
    setErrorMessage("");

    api
      .calculate({
        city,
        income: Number(income.value),
        down_payment: Number(downPayment.value),
        interest_rate: Number(interestRate.value),
        term,
      })
      .then((data) => {
        setResult(data);
        setStatus("idle");
      })
      .catch((err) => {
        setStatus("error");
        setErrorMessage(
          err instanceof BackendUnreachableError
            ? "Unable to connect to backend. Please start the Flask server."
            : "Couldn't calculate affordability. Check your inputs and try again."
        );
      });
  }

  return (
    <div className="calculator-page">
      <section className="calculator-form-card">
        <h2 className="chart-card__title">Mortgage Calculator</h2>
        <p className="chart-card__caption">
          Enter your own numbers to see a personalized affordability result for any tracked city.
        </p>

        <form className="calculator-form" onSubmit={handleSubmit} noValidate>
          <label className="calculator-form__field">
            <span>Annual Income</span>
            <input
              type="number"
              min="0"
              step="1000"
              placeholder="e.g. 95000"
              value={income.value}
              onChange={income.onChange}
              onBlur={income.onBlur}
            />
            {income.touched && income.value === "" && (
              <span className="calculator-form__error">Required</span>
            )}
            {income.touched && income.value !== "" && Number(income.value) <= 0 && (
              <span className="calculator-form__error">Must be greater than 0</span>
            )}
          </label>

          <label className="calculator-form__field">
            <span>Down Payment</span>
            <input
              type="number"
              min="0"
              step="1000"
              placeholder="e.g. 100000"
              value={downPayment.value}
              onChange={downPayment.onChange}
              onBlur={downPayment.onBlur}
            />
            {downPayment.touched && downPayment.value === "" && (
              <span className="calculator-form__error">Required</span>
            )}
            {downPayment.touched && Number(downPayment.value) < 0 && (
              <span className="calculator-form__error">Can't be negative</span>
            )}
          </label>

          <label className="calculator-form__field">
            <span>Interest Rate (%)</span>
            <input
              type="number"
              min="0"
              step="0.1"
              value={interestRate.value}
              onChange={interestRate.onChange}
              onBlur={interestRate.onBlur}
            />
            {interestRate.touched && interestRate.value === "" && (
              <span className="calculator-form__error">Required</span>
            )}
          </label>

          <label className="calculator-form__field">
            <span>Mortgage Term</span>
            <select value={term} onChange={(e) => setTerm(Number(e.target.value))}>
              <option value={15}>15 years</option>
              <option value={20}>20 years</option>
              <option value={25}>25 years</option>
              <option value={30}>30 years</option>
            </select>
          </label>

          <label className="calculator-form__field">
            <span>City</span>
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              {cities.map((c) => (
                <option key={c.city} value={c.city}>
                  {c.city}
                </option>
              ))}
            </select>
          </label>

          <button className="calculator-form__submit" type="submit" disabled={status === "loading"}>
            {status === "loading" ? "Calculating…" : "Calculate"}
          </button>
        </form>
      </section>

      {status === "error" && <p className="affordability-card__error">{errorMessage}</p>}

      {status === "idle" && result && (
        <section className="affordability-card calculator-result" aria-label="Calculator result">
          <p className="affordability-card__eyebrow">Result for {result.city}</p>

          <RatingGauge rating={result.rating} />

          <div className="affordability-card__metrics">
            <div className="affordability-card__metric">
              <p className="affordability-card__metric-label">House Price</p>
              <p className="affordability-card__metric-value">{formatCurrency(result.house_price)}</p>
            </div>
            <div className="affordability-card__metric">
              <p className="affordability-card__metric-label">Loan Amount</p>
              <p className="affordability-card__metric-value">{formatCurrency(result.loan_amount)}</p>
            </div>
          </div>
          <div className="affordability-card__metrics">
            <div className="affordability-card__metric">
              <p className="affordability-card__metric-label">Monthly Mortgage</p>
              <p className="affordability-card__metric-value">{formatCurrency(result.monthly_payment)}</p>
            </div>
            <div className="affordability-card__metric">
              <p className="affordability-card__metric-label">Debt-to-Income</p>
              <p className="affordability-card__metric-value">{formatPercent(result.dti)}</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}