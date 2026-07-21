import { useEffect, useState, useCallback } from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Dashboard from "./pages/Dashboard";
import Charts from "./pages/Charts";
import { api, BackendUnreachableError } from "./api";
import { buildCalculatePayload } from "./utils/affordability";
import "./App.css";

export default function App() {
  const [cities, setCities] = useState([]);
  const [summary, setSummary] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const [selectedCity, setSelectedCity] = useState(null);
  const [cityData, setCityData] = useState(null);
  const [cityDataLoading, setCityDataLoading] = useState(false);

  // Keyed by city name -- avoids re-fetching a city already viewed this
  // session.
  const [cityCache, setCityCache] = useState({});

  // Charts page data. Lazily loaded on first visit (see ensureChartsData
  // below) and kept here rather than in Charts.jsx itself, so navigating
  // Dashboard -> Charts -> Dashboard -> Charts only fetches once.
  const [ranking, setRanking] = useState(null);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [paymentByCity, setPaymentByCity] = useState({});

  const [initError, setInitError] = useState(null);
  const [initLoading, setInitLoading] = useState(true);

  // Initial load: cities list (for the selector + charts), the cross-city
  // summary (for the "N cities" count in the header), and metadata (for
  // the "last updated" line).
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
          // A single city lookup failing (e.g. a typo'd name) shouldn't
          // take down the whole page -- just leave the cards showing
          // their loading/empty state rather than throwing.
          setCityData(null);
        })
        .finally(() => setCityDataLoading(false));
    },
    [cityCache]
  );

  useEffect(() => {
    if (selectedCity) loadCity(selectedCity);
  }, [selectedCity, loadCity]);

  // Called by the Charts page on mount. No-ops on every visit after the
  // first, since `ranking` is only ever set once here.
  const ensureChartsData = useCallback(() => {
    if (ranking || rankingLoading || cities.length === 0) return;
    setRankingLoading(true);

    Promise.all([
      api.getRanking(),
      Promise.all(
        cities.map((c) =>
          api
            .calculate(buildCalculatePayload(c))
            .then((result) => [c.city, result])
            .catch(() => [c.city, null])
        )
      ),
    ])
      .then(([rankingData, pairs]) => {
        setRanking(rankingData);
        setPaymentByCity(Object.fromEntries(pairs.filter(([, result]) => result !== null)));
      })
      .finally(() => setRankingLoading(false));
  }, [cities, ranking, rankingLoading]);

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

      <main className="app__content">
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard
                cities={cities}
                selectedCity={selectedCity}
                onSelectCity={setSelectedCity}
                cityData={cityData}
                cityDataLoading={cityDataLoading}
              />
            }
          />
          <Route
            path="/charts"
            element={
              <Charts
                cities={cities}
                ranking={ranking}
                rankingLoading={rankingLoading}
                paymentByCity={paymentByCity}
                onEnterPage={ensureChartsData}
              />
            }
          />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}