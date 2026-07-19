import { formatCurrency, formatNumber, formatPercent } from "../utils/format";

const CARD_DEFS = [
  { key: "average_house_price", label: "Average House Price", format: formatCurrency },
  { key: "median_income", label: "Median Income", format: formatCurrency },
  { key: "population", label: "Population", format: formatNumber },
  { key: "mortgage_rate", label: "Mortgage Rate", format: (v) => formatPercent(v) },
];

export default function SummaryCards({ cityData, loading }) {
  return (
    <section className="summary-cards" aria-label="City summary">
      {CARD_DEFS.map(({ key, label, format }) => (
        <div className="stat-card" key={key}>
          <p className="stat-card__label">{label}</p>
          <p className="stat-card__value">
            {loading ? <span className="stat-card__loading">Loading…</span> : format(cityData?.[key])}
          </p>
        </div>
      ))}
    </section>
  );
}