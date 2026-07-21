import { useEffect, useState } from "react";
import { api } from "../api";
import { formatCurrency, formatPercent } from "../utils/format";
import { ASSUMED_DOWN_PAYMENT_PCT, ASSUMED_TERM_YEARS, buildCalculatePayload } from "../utils/affordability";

const RATING_ORDER = ["Excellent", "Good", "Moderate", "Poor"];

export default function AffordabilityCard({ cityData }) {
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle"); 
  useEffect(() => {
    if (!cityData) return;

    let cancelled = false;
    setStatus("loading");

    api
      .calculate(buildCalculatePayload(cityData))
      .then((data) => {
        if (!cancelled) {
          setResult(data);
          setStatus("idle");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [cityData]);

  const ratingIndex = result ? RATING_ORDER.indexOf(result.rating) : -1;

  return (
    <section className="affordability-card" aria-label="Affordability">
      <p className="affordability-card__eyebrow">Affordability</p>

      {status === "loading" && <p className="affordability-card__loading">Loading…</p>}
      {status === "error" && (
        <p className="affordability-card__error">Couldn't calculate affordability for this city.</p>
      )}

      {status === "idle" && result && (
        <>
          <div className="affordability-card__rating" data-rating={result.rating}>
            {result.rating}
          </div>

          <div className="affordability-card__gauge" role="img" aria-label={`Affordability rating: ${result.rating}`}>
            {RATING_ORDER.map((tier, i) => (
              <span
                key={tier}
                className="affordability-card__gauge-segment"
                data-active={i === ratingIndex}
                data-tier={tier}
              />
            ))}
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

          <p className="affordability-card__assumptions">
            Based on median income, {Math.round(ASSUMED_DOWN_PAYMENT_PCT * 100)}% down,{" "}
            {ASSUMED_TERM_YEARS}-year term
          </p>
        </>
      )}
    </section>
  );
}