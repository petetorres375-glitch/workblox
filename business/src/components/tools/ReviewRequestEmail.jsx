import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

export default function ReviewRequestEmail() {
  const { loading, error, call } = useApi();
  const [businessName, setBusinessName] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [serviceProvided, setServiceProvided] = useState("");
  const [platforms, setPlatforms] = useState("Google, Yelp");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/review-request", {
      business_name: businessName,
      customer_name: customerName,
      service_provided: serviceProvided,
      platforms,
    }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Review Request <span>Email</span></h1>
      <p className="page-subtitle">Write a friendly, natural email asking customers to leave a review.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Your business name *" value={businessName} onChange={(e) => setBusinessName(e.target.value)} required disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Customer's name (optional)" value={customerName} onChange={(e) => setCustomerName(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Service or product provided" value={serviceProvided} onChange={(e) => setServiceProvided(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Review platforms (e.g. Google, Yelp)" value={platforms} onChange={(e) => setPlatforms(e.target.value)} disabled={loading} style={inputStyle} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Writing…" : "Write Review Request"}</button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          {data.subject && (
            <div className="result-card">
              <p className="result-label">Subject Line</p>
              <p style={{ fontWeight: 600 }}>{data.subject}</p>
            </div>
          )}
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Email Body</p>
              <button className="copy-btn" onClick={() => navigator.clipboard.writeText(`Subject: ${data.subject}\n\n${data.body}`)}>Copy</button>
            </div>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.body}</p>
          </div>
          {data.timing_advice && (
            <div className="result-card">
              <p className="result-label">Timing Advice</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.timing_advice}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
