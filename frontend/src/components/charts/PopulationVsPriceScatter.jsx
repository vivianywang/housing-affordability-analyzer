import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { formatCurrency } from "../../utils/format";
import ChartTooltip from "./ChartTooltip";

// cities: array of records from GET /cities
// Each point is one city: x = median income, y = average house price.
export default function IncomeVsPriceScatter({ cities }) {
  const data = cities.filter((c) => c.median_income != null && c.average_house_price != null);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ScatterChart margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
        <XAxis
          type="number"
          dataKey="median_income"
          name="Median income"
          tickFormatter={(v) => formatCurrency(v)}
          tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
          axisLine={{ stroke: "var(--line)" }}
        />
        <YAxis
          type="number"
          dataKey="average_house_price"
          name="Average house price"
          tickFormatter={(v) => formatCurrency(v)}
          tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
          axisLine={{ stroke: "var(--line)" }}
          width={90}
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3", stroke: "var(--line)" }}
          content={
            <ChartTooltip
              formatValue={(v) => formatCurrency(v)}
              dataKey="average_house_price"
              seriesLabel="Average house price"
              extraLines={(point) => [{ label: "Median income", value: formatCurrency(point.median_income) }]}
            />
          }
        />
        <Scatter data={data} fill="var(--pine)" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}