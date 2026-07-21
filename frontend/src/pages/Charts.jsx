import { useEffect } from "react";
import HousePriceBarChart from "../components/charts/HousePriceBarChart";
import IncomeVsPriceScatter from "../components/charts/IncomeVsPriceScatter";
import MortgageVsIncomeChart from "../components/charts/MortgageVsIncomeChart";
import PopulationVsPriceScatter from "../components/charts/PopulationVsPriceScatter";
import AffordabilityRankingChart from "../components/charts/AffordabilityRankingChart";
import ComingSoonChart from "../components/charts/ComingSoonChart";

function ChartCard({ title, caption, children }) {
  return (
    <section className="chart-card">
      <h2 className="chart-card__title">{title}</h2>
      {caption && <p className="chart-card__caption">{caption}</p>}
      {children}
    </section>
  );
}

// cities / ranking / paymentByCity are owned by App (see ensureChartsData
// there) so switching between Dashboard and Charts doesn't re-fetch
// everything each time -- this page just triggers the initial load.
export default function Charts({ cities, ranking, rankingLoading, paymentByCity, onEnterPage }) {
  useEffect(() => {
    onEnterPage();
  }, [onEnterPage]);

  const mortgageVsIncomeData = cities
    .filter((c) => paymentByCity[c.city])
    .map((c) => ({
      city: c.city,
      monthlyMortgage: paymentByCity[c.city].monthly_payment,
      monthlyIncome: c.median_income / 12,
    }));

  return (
    <div className="charts-page">
      <div className="charts-grid">
        <ChartCard title="House Price Comparison" caption="Average house price across all tracked cities.">
          <HousePriceBarChart cities={cities} />
        </ChartCard>

        <ChartCard
          title="Income vs House Price"
          caption="Each point is one city. Shows whether higher-income cities necessarily have higher housing prices."
        >
          <IncomeVsPriceScatter cities={cities} />
        </ChartCard>

        <ChartCard
          title="Monthly Mortgage vs Monthly Income"
          caption="A typical resident's mortgage payment against their monthly income, assuming median income, 20% down, 25-year term. (Substituted for a rent comparison -- rent data isn't in the database yet.)"
        >
          {mortgageVsIncomeData.length > 0 ? (
            <MortgageVsIncomeChart data={mortgageVsIncomeData} />
          ) : (
            <p className="chart-card__loading">Loading…</p>
          )}
        </ChartCard>

        <ChartCard
          title="Population vs House Price"
          caption="Each point is one city. Useful for discussing urbanization and housing costs."
        >
          <PopulationVsPriceScatter cities={cities} />
        </ChartCard>

        <ChartCard
          title="Affordability Ranking"
          caption="Price-to-income ratio by city, most affordable first."
        >
          {rankingLoading || !ranking ? (
            <p className="chart-card__loading">Loading…</p>
          ) : (
            <AffordabilityRankingChart ranking={ranking} />
          )}
        </ChartCard>

        <ChartCard title="Inflation Timeline">
          <ComingSoonChart
            title="CPI over time"
            reason="The database only stores the latest CPI snapshot right now, not a historical series. Plotting a real timeline means having update_data.py retain every year from the StatCan CPI table instead of collapsing to the most recent one."
          />
        </ChartCard>

        <ChartCard title="Mortgage Rate Timeline">
          <ComingSoonChart
            title="Mortgage rate over time"
            reason="Same limitation as the CPI chart -- only the current mortgage rate is stored. A historical view would need the Bank of Canada series retained across runs rather than overwritten each time."
          />
        </ChartCard>
      </div>
    </div>
  );
}