import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data) {
  const lines = ["BUSINESS EMAIL DRAFT", "=".repeat(60)];
  if (data.subject) lines.push(`Subject: ${data.subject}`);
  lines.push("", data.body || "");
  if (data.call_to_action) lines.push("", "CALL TO ACTION", "-".repeat(40), data.call_to_action);
  return lines.join("\n");
}

function buildMd(data) {
  const lines = ["# Business Email Draft"];
  if (data.subject) lines.push("", `**Subject:** ${data.subject}`);
  lines.push("", "## Email Body", data.body || "");
  if (data.call_to_action) lines.push("", "## Call to Action", data.call_to_action);
  return lines.join("\n");
}

export default function BusinessEmailDrafter() {
  const { loading, error, call } = useApi();
  const [purpose, setPurpose] = useState("");
  const [recipient, setRecipient] = useState("");
  const [keyPoints, setKeyPoints] = useState("");
  const [tone, setTone] = useState("professional");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/business-email", { purpose, recipient, key_points: keyPoints, tone }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Business <span>Email</span></h1>
      <p className="page-subtitle">Draft clear, professional business emails for any situation.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder="Purpose of the email (e.g. Follow up on proposal, Reschedule meeting) *" value={purpose} onChange={(e) => setPurpose(e.target.value)} required rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <input type="text" placeholder="Recipient / their role (e.g. John — Hiring Manager)" value={recipient} onChange={(e) => setRecipient(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder="Key points to include" value={keyPoints} onChange={(e) => setKeyPoints(e.target.value)} rows={3} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <select value={tone} onChange={(e) => setTone(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
          {["professional", "friendly", "formal", "assertive", "apologetic"].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
        </select>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Drafting…" : "Draft Email"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Business Email Draft</strong></div>
          {data.subject && (
            <div className="result-card">
              <p className="result-label">Subject Line</p>
              <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>{data.subject}</p>
            </div>
          )}
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Email Body</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(`Subject: ${data.subject}\n\n${data.body}`)}>Copy</button>
            </div>
            <p style={{ fontSize: "0.92rem", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>{data.body}</p>
          </div>
          {data.call_to_action && (
            <div className="result-card">
              <p className="result-label">Call to Action</p>
              <p style={{ fontSize: "0.9rem" }}>{data.call_to_action}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(purpose) || "business_email"}
            subject={`Business Email${data.subject ? ` — ${data.subject}` : ""}`}
            txtContent={buildTxt(data)}
            mdContent={buildMd(data)}
          />
        </>
      )}
    </div>
  );
}
