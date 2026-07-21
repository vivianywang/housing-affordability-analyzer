import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import ChartTooltip from "./ChartTooltip";

export default function AffordabilityRankingChart({ ranking }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart
        data={ranking}
        layout="vertical"
        margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
          axisLine={{ stroke: "var(--line)" }}
        />
        <YAxis
          type="category"
          dataKey="city"
          tick={{ fill: "var(--ink-soft)", fontSize: 12 }}
          axisLine={{ stroke: "var(--line)" }}
          width={90}
        />
        <Tooltip
          cursor={{ fill: "var(--pine-dim)" }}
          content={
            <ChartTooltip
              formatValue={(v) => `${v.toFixed(2)}x income`}
              dataKey="affordability_score"
              seriesLabel="Price-to-income ratio"
            />
          }
        />
        <Bar dataKey="affordability_score" fill="var(--pine)" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}