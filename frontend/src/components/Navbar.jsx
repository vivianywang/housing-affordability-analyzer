import { NavLink } from "react-router-dom";
import { formatMonthYear } from "../utils/format";

export default function Navbar({ lastUpdated, cityCount }) {
  return (
    <header className="navbar">
      <div className="navbar__title-row">
        <span className="navbar__mark" aria-hidden="true" />
        <h1 className="navbar__title">Housing Affordability Analyzer</h1>
      </div>
      <p className="navbar__subtitle">
        {cityCount ? `${cityCount} Ontario cities` : "Ontario housing data"} from Statistics Canada
        {lastUpdated && (
          <>
            {" "}
            <span className="navbar__updated">· Last updated {formatMonthYear(lastUpdated)}</span>
          </>
        )}
      </p>

      <nav className="navbar__nav" aria-label="Pages">
        <NavLink to="/" end className={({ isActive }) => `navbar__nav-link${isActive ? " navbar__nav-link--active" : ""}`}>
          Dashboard
        </NavLink>
        <NavLink
          to="/charts"
          className={({ isActive }) => `navbar__nav-link${isActive ? " navbar__nav-link--active" : ""}`}
        >
          Charts
        </NavLink>
        <span className="navbar__nav-link navbar__nav-link--upcoming">Calculator</span>
        <span className="navbar__nav-link navbar__nav-link--upcoming">Map</span>
      </nav>
    </header>
  );
}