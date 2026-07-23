import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { formatCurrency, formatNumber } from "../utils/format";
import { affordabilityRatingFromScore, makeCityIcon } from "../utils/mapIcons";

const ONTARIO_CENTER = [46.5, -80.5];
const DEFAULT_ZOOM = 5;

export default function MapPage({ cities }) {
  const mappable = cities.filter((c) => c.latitude != null && c.longitude != null);

  return (
    <div className="map-page">
      <div className="chart-card map-page__card">
        <h2 className="chart-card__title">Ontario Cities Map</h2>
        <p className="chart-card__caption">
          Each marker is a tracked city, colored by affordability (price-to-income ratio). Click a marker for
          details.
        </p>

        <div className="map-page__legend">
          <span className="map-page__legend-item">
            <span className="map-page__legend-dot" style={{ background: "#2f6f5e" }} /> More affordable
          </span>
          <span className="map-page__legend-item">
            <span className="map-page__legend-dot" style={{ background: "#b98a2e" }} /> Moderate
          </span>
          <span className="map-page__legend-item">
            <span className="map-page__legend-dot" style={{ background: "#b5652d" }} /> Less affordable
          </span>
        </div>

        <div className="map-page__container">
          <MapContainer center={ONTARIO_CENTER} zoom={DEFAULT_ZOOM} scrollWheelZoom={true} style={{ height: "100%" }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {mappable.map((c) => {
              const rating =
                c.affordability_score != null ? affordabilityRatingFromScore(c.affordability_score) : "Moderate";
              return (
                <Marker key={c.city} position={[c.latitude, c.longitude]} icon={makeCityIcon(rating)}>
                  <Popup>
                    <div className="map-popup">
                      <p className="map-popup__title">{c.city}</p>
                      <p className="map-popup__line">
                        <span>House price</span>
                        <span>{formatCurrency(c.average_house_price)}</span>
                      </p>
                      <p className="map-popup__line">
                        <span>Median income</span>
                        <span>{formatCurrency(c.median_income)}</span>
                      </p>
                      <p className="map-popup__line">
                        <span>Population</span>
                        <span>{formatNumber(c.population)}</span>
                      </p>
                      <p className="map-popup__line">
                        <span>Price-to-income</span>
                        <span>{c.affordability_score != null ? `${c.affordability_score.toFixed(2)}x` : "—"}</span>
                      </p>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}