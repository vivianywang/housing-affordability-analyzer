export const ASSUMED_DOWN_PAYMENT_PCT = 0.2;
export const ASSUMED_TERM_YEARS = 25;

export function buildCalculatePayload(cityData) {
  return {
    city: cityData.city,
    income: cityData.median_income,
    down_payment: cityData.average_house_price * ASSUMED_DOWN_PAYMENT_PCT,
    interest_rate: cityData.mortgage_rate,
    term: ASSUMED_TERM_YEARS,
  };
}