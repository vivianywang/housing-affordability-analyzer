import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { formatCurrency } from "../../utils/format";
import ChartTooltip from "./ChartTooltip";

// cities: array of records from GET /cities
export default function HousePriceBarChart({ cities }) {
  const data = [...cities]
    .filter((c) => c.average_house_price != null)
    .sort((a, b) => b.average_house_price - a.average_house_price);

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
        <XAxis dataKey="city" tick={{ fill: "var(--ink-soft)", fontSize: 12 }} axisLine={{ stroke: "var(--line)" }} />
        <YAxis
          tickFormatter={(v) => formatCurrency(v)}
          tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
          axisLine={{ stroke: "var(--line)" }}
          width={90}
        />
        <Tooltip
          content={
            <ChartTooltip
              formatValue={(v) => formatCurrency(v)}
              seriesLabel="Average house price"
              dataKey="average_house_price"
            />
          }
        />
        <Bar dataKey="average_house_price" fill="var(--pine)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}