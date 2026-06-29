import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data, clientName) {
  const header = clientName ? `PROPOSAL — ${clientName.toUpperCase()}` : "PROPOSAL";
  const lines = [header, "=".repeat(60), "", "EXECUTIVE SUMMARY", "-".repeat(40), data.executive_summary || ""];
  if (data.scope_of_work?.length) {
    lines.push("", "SCOPE OF WORK", "-".repeat(40));
    data.scope_of_work.forEach((s, i) => lines.push(`${i + 1}. ${s}`));
  }
  if (data.deliverables?.length) {
    lines.push("", "DELIVERABLES", "-".repeat(40));
    data.deliverables.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (data.line_items?.length) {
    lines.push("", "LINE ITEMS", "-".repeat(40));
    lines.push("Description                          Qty    Unit Price    Total");
    data.line_items.forEach((item) => {
      lines.push(`${item.description.padEnd(36)} ${String(item.quantity).padEnd(6)} $${String(Number(item.unit_price).toLocaleString()).padEnd(13)} $${Number(item.total).toLocaleString()}`);
    });
    if (data.subtotal != null) lines.push("", `TOTAL: $${Number(data.subtotal).toLocaleString()}`);
  }
  if (data.terms) lines.push("", "TERMS", "-".repeat(40), data.terms);
  return lines.join("\n");
}

function buildMd(data, clientName) {
  const lines = [`# ${clientName ? `Proposal — ${clientName}` : "Proposal"}`, "", "## Executive Summary", data.executive_summary || ""];
  if (data.scope_of_work?.length) { lines.push("", "## Scope of Work"); data.scope_of_work.forEach((s) => lines.push(`- ${s}`)); }
  if (data.deliverables?.length) { lines.push("", "## Deliverables"); data.deliverables.forEach((d) => lines.push(`- ${d}`)); }
  if (data.line_items?.length) {
    lines.push("", "## Line Items", "", "| Description | Qty | Unit Price | Total |", "|---|---|---|---|");
    data.line_items.forEach((item) => lines.push(`| ${item.description} | ${item.quantity} | $${Number(item.unit_price).toLocaleString()} | $${Number(item.total).toLocaleString()} |`));
    if (data.subtotal != null) lines.push("", `**Total: $${Number(data.subtotal).toLocaleString()}**`);
  }
  if (data.terms) lines.push("", "## Terms", data.terms);
  return lines.join("\n");
}

export default function ProposalGenerator() {
  const { loading, error, call } = useApi();
  const [clientName, setClientName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [services, setServices] = useState("");
  const [budgetRange, setBudgetRange] = useState("");
  const [timeline, setTimeline] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/proposal", { client_name: clientName, project_description: projectDescription, services, budget_range: budgetRange, timeline }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Proposal <span>Generator</span></h1>
      <p className="page-subtitle">Create professional proposals and quotes for clients.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Client name" value={clientName} onChange={(e) => setClientName(e.target.value)} disabled={loading} style={inputStyle} />
        <textarea placeholder="Project description *" value={projectDescription} onChange={(e) => setProjectDescription(e.target.value)} required rows={3} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <textarea placeholder="Services to include" value={services} onChange={(e) => setServices(e.target.value)} rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
        <input type="text" placeholder="Budget range (e.g. $5,000–$10,000)" value={budgetRange} onChange={(e) => setBudgetRange(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Timeline (e.g. 4–6 weeks)" value={timeline} onChange={(e) => setTimeline(e.target.value)} disabled={loading} style={inputStyle} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Generating…" : "Generate Proposal"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>{clientName ? `Proposal — ${clientName}` : "Proposal"}</strong></div>
          <div className="result-card">
            <p className="result-label">Executive Summary</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.executive_summary}</p>
          </div>
          {data.scope_of_work?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Scope of Work</p>
              <ul className="section-list">{data.scope_of_work.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </div>
          )}
          {data.deliverables?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Deliverables</p>
              <ul className="section-list">{data.deliverables.map((d, i) => <li key={i}>{d}</li>)}</ul>
            </div>
          )}
          {data.line_items?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Line Items</p>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)" }}>
                    {["Description", "Qty", "Unit Price", "Total"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "0.4rem 0.5rem", color: "var(--text-muted)", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.line_items.map((item, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: "0.4rem 0.5rem" }}>{item.description}</td>
                      <td style={{ padding: "0.4rem 0.5rem" }}>{item.quantity}</td>
                      <td style={{ padding: "0.4rem 0.5rem" }}>${Number(item.unit_price).toLocaleString()}</td>
                      <td style={{ padding: "0.4rem 0.5rem", fontWeight: 700 }}>${Number(item.total).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                {data.subtotal != null && (
                  <tfoot>
                    <tr>
                      <td colSpan={3} style={{ padding: "0.5rem 0.5rem", textAlign: "right", fontWeight: 700 }}>Total</td>
                      <td style={{ padding: "0.5rem 0.5rem", fontWeight: 800, color: "var(--orange)" }}>${Number(data.subtotal).toLocaleString()}</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          )}
          {data.terms && (
            <div className="result-card">
              <p className="result-label">Terms</p>
              <p style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{data.terms}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(clientName) || "proposal"}
            subject={`Proposal${clientName ? ` — ${clientName}` : ""}`}
            txtContent={buildTxt(data, clientName)}
            mdContent={buildMd(data, clientName)}
          />
        </>
      )}
    </div>
  );
}
