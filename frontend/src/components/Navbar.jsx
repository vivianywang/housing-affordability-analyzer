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
    </header>
  );
}