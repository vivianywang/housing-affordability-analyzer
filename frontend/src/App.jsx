import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [cities, setCities] = useState([]);

  useEffect(() => {
    axios
      .get("http://127.0.0.1:5000/cities")
      .then((response) => {
        setCities(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>🏠 Housing Affordability Analyzer</h1>

      <ul>
        {cities.map((city) => (
          <li key={city.city}>
            {city.city}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;