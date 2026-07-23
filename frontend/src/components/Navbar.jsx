import { NavLink } from "react-router-dom";
import { formatMonthYear } from "../utils/format";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/charts", label: "Charts" },
  { to: "/calculator", label: "Calculator" },
  { to: "/map", label: "Map" },
];

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
        {NAV_ITEMS.map(({ to, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `navbar__nav-link${isActive ? " navbar__nav-link--active" : ""}`}
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}