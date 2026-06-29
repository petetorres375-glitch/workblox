import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

function buildTxt(data) {
  const lines = ["MEETING NOTES", "=".repeat(60), `Date: ${data.date_placeholder || ""}`, `Attendees: ${data.attendees_placeholder || ""}`, "", "SUMMARY", "-".repeat(40), data.meeting_summary || ""];
  if (data.decisions_made?.length) {
    lines.push("", "DECISIONS MADE", "-".repeat(40));
    data.decisions_made.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (data.action_items?.length) {
    lines.push("", "ACTION ITEMS", "-".repeat(40));
    data.action_items.forEach((a, i) => lines.push(`${i + 1}. ${a.task} — ${a.owner} (Due: ${a.due_date})`));
  }
  if (data.next_steps?.length) {
    lines.push("", "NEXT STEPS", "-".repeat(40));
    data.next_steps.forEach((s, i) => lines.push(`${i + 1}. ${s}`));
  }
  if (data.follow_up_meeting) lines.push("", "FOLLOW-UP MEETING", "-".repeat(40), data.follow_up_meeting);
  return lines.join("\n");
}

function buildMd(data) {
  const lines = ["# Meeting Notes", "", `**Date:** ${data.date_placeholder || ""}`, `**Attendees:** ${data.attendees_placeholder || ""}`, "", "## Summary", data.meeting_summary || ""];
  if (data.decisions_made?.length) { lines.push("", "## Decisions Made"); data.decisions_made.forEach((d) => lines.push(`- ${d}`)); }
  if (data.action_items?.length) {
    lines.push("", "## Action Items", "", "| Task | Owner | Due |", "|---|---|---|");
    data.action_items.forEach((a) => lines.push(`| ${a.task} | ${a.owner} | ${a.due_date} |`));
  }
  if (data.next_steps?.length) { lines.push("", "## Next Steps"); data.next_steps.forEach((s) => lines.push(`- ${s}`)); }
  if (data.follow_up_meeting) lines.push("", "## Follow-Up Meeting", data.follow_up_meeting);
  return lines.join("\n");
}

export default function MeetingNotesCleaner() {
  const { loading, error, call } = useApi();
  const [rawNotes, setRawNotes] = useState("");
  const [context, setContext] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/meeting-notes", { raw_notes: rawNotes, context }));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title">Meeting Notes <span>Cleaner</span></h1>
      <p className="page-subtitle">Paste messy meeting notes and get a clean, structured summary with action items.</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder="Meeting context (e.g. Q3 planning, client kickoff)" value={context} onChange={(e) => setContext(e.target.value)} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <textarea placeholder="Paste your raw meeting notes here *" value={rawNotes} onChange={(e) => setRawNotes(e.target.value)} required rows={8} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Cleaning…" : "Clean Meeting Notes"}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Meeting Notes{context ? ` — ${context}` : ""}</strong></div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">Summary</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(buildTxt(data))}>Copy All</button>
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-hint)", marginBottom: "0.5rem" }}>{data.date_placeholder} · {data.attendees_placeholder}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.meeting_summary}</p>
          </div>
          {data.decisions_made?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Decisions Made</p>
              <ul className="section-list">{data.decisions_made.map((d, i) => <li key={i}>{d}</li>)}</ul>
            </div>
          )}
          {data.action_items?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Action Items</p>
              {data.action_items.map((item, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.6rem", padding: "0.5rem 0", borderBottom: i < data.action_items.length - 1 ? "1px solid var(--border)" : "none" }}>
                  <span style={{ fontSize: "0.9rem" }}>{item.task}</span>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", whiteSpace: "nowrap", marginLeft: "1rem" }}>{item.owner} · {item.due_date}</span>
                </div>
              ))}
            </div>
          )}
          {data.next_steps?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Next Steps</p>
              <ul className="section-list">{data.next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </div>
          )}
          {data.follow_up_meeting && (
            <div className="result-card">
              <p className="result-label">Follow-Up Meeting</p>
              <p style={{ fontSize: "0.9rem" }}>{data.follow_up_meeting}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(context) || "meeting_notes"}
            subject={`Meeting Notes${context ? ` — ${context}` : ""}`}
            txtContent={buildTxt(data)}
            mdContent={buildMd(data)}
          />
        </>
      )}
    </div>
  );
}
