import { useEffect, useState, useCallback } from "react";
import Navbar from "./components/Navbar";
import CitySelector from "./components/CitySelector";
import SummaryCards from "./components/SummaryCards";
import AffordabilityCard from "./components/AffordabilityCard";
import Footer from "./components/Footer";
import { api, BackendUnreachableError } from "./api";
import "./App.css";

export default function App() {
  const [cities, setCities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const [selectedCity, setSelectedCity] = useState(null);
  const [cityData, setCityData] = useState(null);
  const [cityDataLoading, setCityDataLoading] = useState(false);

  const [cityCache, setCityCache] = useState({});

  const [initError, setInitError] = useState(null);
  const [initLoading, setInitLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    Promise.all([api.getCities(), api.getSummary(), api.getMetadata()])
      .then(([citiesData, summaryData, metadataData]) => {
        if (cancelled) return;
        setCities(citiesData);
        setSummary(summaryData);
        setMetadata(metadataData);
        setSelectedCity(citiesData[0]?.city ?? null);
        setInitLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setInitError(
          err instanceof BackendUnreachableError
            ? "Unable to connect to backend. Please start the Flask server."
            : "Something went wrong loading city data."
        );
        setInitLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const loadCity = useCallback(
    (cityName) => {
      if (cityCache[cityName]) {
        setCityData(cityCache[cityName]);
        return;
      }
      setCityDataLoading(true);
      api
        .getCity(cityName)
        .then((data) => {
          setCityCache((prev) => ({ ...prev, [cityName]: data }));
          setCityData(data);
        })
        .catch(() => {
          setCityData(null);
        })
        .finally(() => setCityDataLoading(false));
    },
    [cityCache]
  );

  useEffect(() => {
    if (selectedCity) loadCity(selectedCity);
  }, [selectedCity, loadCity]);

  if (initLoading) {
    return (
      <div className="app-status">
        <p>Loading…</p>
      </div>
    );
  }

  if (initError) {
    return (
      <div className="app-status app-status--error">
        <p>{initError}</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Navbar lastUpdated={metadata?.last_updated} cityCount={summary?.city_count} />

      <main className="app__main">
        <CitySelector cities={cities} selectedCity={selectedCity} onSelectCity={setSelectedCity} />

        <SummaryCards cityData={cityData} loading={cityDataLoading} />

        <AffordabilityCard cityData={cityDataLoading ? null : cityData} />
      </main>

      <Footer />
    </div>
  );
}