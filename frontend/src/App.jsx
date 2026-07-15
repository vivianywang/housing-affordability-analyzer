import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [cities, setCities] = useState([]);
  const [metadata, setMetadata] = useState([]);

  const [income, setIncome] = useState("");
  const [downPayment, setDownPayment] = useState("");
  const [interestRate, setInterestRate] = useState(4.5);
  const [term, setTerm] = useState(25);
  const [city, setCity] = useState("");

  const [result, setResult] = useState(null);

  useEffect(() => {
    axios
      .get("http://127.0.0.1:5000/cities")
      .then((response) => {
        setCities(response.data);

        // Select the first city by default
        if (response.data.length > 0) {
          setCity(response.data[0].city);
        }
      })
      .catch((error) => {
        console.error(error);
      });

    axios
      .get("http://127.0.0.1:5000/metadata")
      .then((response) => {
        setMetadata(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  const calculate = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/calculate",
        {
          income,
          down_payment: downPayment,
          interest_rate: interestRate,
          term,
          city,
        }
      );

      setResult(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>🏠 Housing Affordability Analyzer</h1>

      {metadata.length > 0 && (
        <div style={{ fontSize: "14px", color: "#666", marginBottom: "20px" }}>
          {metadata.map((m) => (
            <span key={m.source} style={{ marginRight: "16px" }}>
              {m.source}: {m.status === "ok" ? "updated" : m.status}{" "}
              ({new Date(m.last_updated).toLocaleDateString()})
            </span>
          ))}
        </div>
      )}

      <div> 
        <p>Annual Income</p>
        <input
          type="number"
          value={income}
          onChange={(e) => setIncome(e.target.value)}
        />

        <p>Down Payment</p>
        <input
          type="number"
          value={downPayment}
          onChange={(e) => setDownPayment(e.target.value)}
        />

        <p>Interest Rate (%)</p>
        <input
          type="number"
          step="0.1"
          value={interestRate}
          onChange={(e) => setInterestRate(e.target.value)}
        />

        <p>Mortgage Term (Years)</p>
        <select
          value={term}
          onChange={(e) => setTerm(Number(e.target.value))}
        >
          <option value={25}>25</option>
          <option value={30}>30</option>
        </select>

        <p>City</p>
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
        >
          {cities.map((c) => (
            <option key={c.city} value={c.city}>
              {c.city}
            </option>
          ))}
        </select>

        <br />
        <br />

        <button onClick={calculate}>
          Calculate
        </button>
      </div>

      {result && (
        <div style={{ marginTop: "30px" }}>
          <h2>Housing Affordability Results</h2>

          <p><strong>Selected City:</strong> {result.city}</p>
          <p><strong>Average House Price:</strong> ${result.house_price.toLocaleString()}</p>
          <p><strong>Loan Amount:</strong> ${result.loan_amount.toLocaleString()}</p>
          <p><strong>Monthly Mortgage Payment:</strong> ${result.monthly_payment.toLocaleString()}</p>
          <p><strong>Debt-to-Income Ratio:</strong> {result.dti}%</p>
          <p><strong>Affordability Rating:</strong> {result.rating}</p>
        </div>
      )}
    </div>
  );
}

export default App;