export default function ChartTooltip({ active, payload, formatValue, dataKey, seriesLabel, extraLines }) {
    if (!active || !payload || !payload.length) return null;
  
    const point = payload[0].payload;
    const value = dataKey ? point[dataKey] : payload[0].value;
  
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip__title">{point.city}</p>
        {seriesLabel && (
          <p className="chart-tooltip__line">
            <span>{seriesLabel}</span>
            <span>{formatValue(value)}</span>
          </p>
        )}
        {extraLines?.(point).map((line) => (
          <p className="chart-tooltip__line" key={line.label}>
            <span>{line.label}</span>
            <span>{line.value}</span>
          </p>
        ))}
      </div>
    );
  }