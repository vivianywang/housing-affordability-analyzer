export function formatCurrency(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return new Intl.NumberFormat("en-CA", {
      style: "currency",
      currency: "CAD",
      maximumFractionDigits: 0,
    }).format(value);
  }
  
  export function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return new Intl.NumberFormat("en-CA").format(Math.round(value));
  }
  
  export function formatPercent(value, decimals = 1) {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return `${value.toFixed(decimals)}%`;
  }
  
  // "2026-07-17T22:05:01.872854+00:00" -> "July 2026"
  export function formatMonthYear(isoString) {
    if (!isoString) return "—";
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat("en-CA", { month: "long", year: "numeric" }).format(date);
  }