import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar from "../ui/ReportToolbar";

function buildTxt(data) {
  const lines = ["CUSTOMER RESPONSE DRAFT", "=".repeat(60)];
  if (data.subject) lines.push(`Subject: ${data.subject}`);
  lines.push("", data.response_draft || "");
  if (data.key_points_addressed?.length) {
    lines.push("", "POINTS ADDRESSED", "-".repeat(40));
    data.key_points_addressed.forEach((p, i) => lines.push(`${i + 1}. ${p}`));
  }
  if (data.follow_up_suggested) lines.push("", "SUGGESTED FOLLOW-UP", "-".repeat(40), data.follow_up_suggested);
  return lines.join("\n");
}

function buildMd(data) {
  const lines = ["# Customer Response Draft"];
  if (data.subject) lines.push("", `**Subject:** ${data.subject}`);
  lines.push("", "## Response", data.response_draft || "");
  if (data.key_points_addressed?.length) { lines.push("", "## Points Addressed"); data.key_points_addressed.forEach((p) => lines.push(`- ${p}`)); }
  if (data.follow_up_suggested) lines.push("", "## Suggested Follow-Up", data.follow_up_suggested);
  return lines.join("\n");
}

export default function CustomerResponseDrafter() {
  const { loading, error, call } = useApi();
  const [customerMessage, setCustomerMessage] = useState("");
  const [context, setContext] = useState("");
  const [tone, setTone] = useState("professional");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/customer-response", { customer_message: customerMessage, context, tone }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Customer <span>Response</span></h1>
      <p className="page-subtitle">Draft professional, empathetic responses to customer messages and complaints.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder="Paste the customer's message *" value={customerMessage} onChange={(e) => setCustomerMessage(e.target.value)} required rows={4} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <textarea placeholder="Context (e.g. what happened, order details, etc.)" value={context} onChange={(e) => setContext(e.target.value)} rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <select value={tone} onChange={(e) => setTone(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
          {["professional", "empathetic", "apologetic", "firm", "friendly"].map(t => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Drafting…" : "Draft Response"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Customer Response Draft</strong></div>
          {data.subject && (
            <div className="result-card">
              <p className="result-label">Subject Line</p>
              <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>{data.subject}</p>
            </div>
          )}
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Response Draft</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(data.response_draft)}>Copy</button>
            </div>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.response_draft}</p>
          </div>
          {data.key_points_addressed?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Points Addressed</p>
              <ul className="section-list">{data.key_points_addressed.map((p, i) => <li key={i}>{p}</li>)}</ul>
            </div>
          )}
          {data.follow_up_suggested && (
            <div className="result-card">
              <p className="result-label">Suggested Follow-Up</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.follow_up_suggested}</p>
            </div>
          )}
          <ReportToolbar
            filename="customer_response"
            subject="Customer Response Draft"
            txtContent={buildTxt(data)}
            mdContent={buildMd(data)}
          />
        </>
      )}
    </div>
  );
}
