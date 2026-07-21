import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { formatCurrency } from "../../utils/format";

// data: array of { city, monthlyMortgage, monthlyIncome }
export default function MortgageVsIncomeChart({ data }) {
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
          cursor={{ fill: "var(--pine-dim)" }}
          formatter={(value, name) => [formatCurrency(value), name]}
          contentStyle={{
            background: "var(--paper-card)",
            border: "1px solid var(--line)",
            borderRadius: 4,
            fontFamily: "var(--font-body)",
            fontSize: 13,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 13, fontFamily: "var(--font-body)" }} />
        <Bar dataKey="monthlyIncome" name="Monthly income" fill="var(--line)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="monthlyMortgage" name="Monthly mortgage" fill="var(--ochre)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}