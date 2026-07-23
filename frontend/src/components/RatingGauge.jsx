const RATING_ORDER = ["Excellent", "Good", "Moderate", "Poor"];

export default function RatingGauge({ rating }) {
  const activeIndex = RATING_ORDER.indexOf(rating);

  return (
    <>
      <div className="affordability-card__rating" data-rating={rating}>
        {rating}
      </div>
      <div className="affordability-card__gauge" role="img" aria-label={`Affordability rating: ${rating}`}>
        {RATING_ORDER.map((tier, i) => (
          <span
            key={tier}
            className="affordability-card__gauge-segment"
            data-active={i === activeIndex}
            data-tier={tier}
          />
        ))}
      </div>
    </>
  );
}