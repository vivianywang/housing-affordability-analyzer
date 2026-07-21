import CitySelector from "../components/CitySelector";
import SummaryCards from "../components/SummaryCards";
import AffordabilityCard from "../components/AffordabilityCard";

export default function Dashboard({ cities, selectedCity, onSelectCity, cityData, cityDataLoading }) {
  return (
    <div className="app__main">
      <CitySelector cities={cities} selectedCity={selectedCity} onSelectCity={onSelectCity} />
      <SummaryCards cityData={cityData} loading={cityDataLoading} />
      <AffordabilityCard cityData={cityDataLoading ? null : cityData} />
    </div>
  );
}