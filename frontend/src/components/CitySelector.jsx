export default function CitySelector({ cities, selectedCity, onSelectCity }) {
    return (
      <div className="city-selector">
        <label className="city-selector__label" htmlFor="city-select">
          Select city
        </label>
        <select
          id="city-select"
          className="city-selector__select"
          value={selectedCity ?? ""}
          onChange={(event) => onSelectCity(event.target.value)}
        >
          {cities.map((c) => (
            <option key={c.city} value={c.city}>
              {c.city}
            </option>
          ))}
        </select>
      </div>
    );
  }