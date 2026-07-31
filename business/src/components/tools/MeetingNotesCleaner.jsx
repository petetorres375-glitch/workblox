import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";
import { reportTitle } from "../../utils/reportLabels";

function buildTxt(data, t) {
  const lines = [reportTitle(t), "=".repeat(60), `Date: ${data.date_placeholder || ""}`, `Attendees: ${data.attendees_placeholder || ""}`, "", t("summary"), "-".repeat(40), data.meeting_summary || ""];
  if (data.decisions_made?.length) {
    lines.push("", t("decisionsMade"), "-".repeat(40));
    data.decisions_made.forEach((d, i) => lines.push(`${i + 1}. ${d}`));
  }
  if (data.action_items?.length) {
    lines.push("", t("actionItems"), "-".repeat(40));
    data.action_items.forEach((a, i) => lines.push(`${i + 1}. ${a.task} — ${a.owner} (Due: ${a.due_date})`));
  }
  if (data.next_steps?.length) {
    lines.push("", t("nextSteps"), "-".repeat(40));
    data.next_steps.forEach((s, i) => lines.push(`${i + 1}. ${s}`));
  }
  if (data.follow_up_meeting) lines.push("", t("followUpMeeting"), "-".repeat(40), data.follow_up_meeting);
  return lines.join("\n");
}

function buildMd(data, t) {
  const lines = [`# ${reportTitle(t)}`, "", `**Date:** ${data.date_placeholder || ""}`, `**Attendees:** ${data.attendees_placeholder || ""}`, "", `## ${t("summary")}`, data.meeting_summary || ""];
  if (data.decisions_made?.length) { lines.push("", `## ${t("decisionsMade")}`); data.decisions_made.forEach((d) => lines.push(`- ${d}`)); }
  if (data.action_items?.length) {
    lines.push("", `## ${t("actionItems")}`, "", "| Task | Owner | Due |", "|---|---|---|");
    data.action_items.forEach((a) => lines.push(`| ${a.task} | ${a.owner} | ${a.due_date} |`));
  }
  if (data.next_steps?.length) { lines.push("", `## ${t("nextSteps")}`); data.next_steps.forEach((s) => lines.push(`- ${s}`)); }
  if (data.follow_up_meeting) lines.push("", `## ${t("followUpMeeting")}`, data.follow_up_meeting);
  return lines.join("\n");
}

export default function MeetingNotesCleaner() {
  const { t, i18n } = useTranslation("meetingNotes");
  const { loading, error, call } = useApi();
  const [rawNotes, setRawNotes] = useState("");
  const [context, setContext] = useState("");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/meeting-notes", { raw_notes: rawNotes, context, language: i18n.language }));
    if (result) setData(result);
  }

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <input type="text" placeholder={t("contextPlaceholder")} value={context} onChange={(e) => setContext(e.target.value)} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" }} />
        <textarea placeholder={t("rawNotesPlaceholder")} value={rawNotes} onChange={(e) => setRawNotes(e.target.value)} required rows={8} disabled={loading}
          style={{ padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none", resize: "vertical" }} />
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? t("cleaning") : t("clean")}</button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Meeting Notes{context ? ` — ${context}` : ""}</strong></div>
          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("summary")}</p>
              <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(buildTxt(data, t))}>{t("copyAll")}</button>
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-hint)", marginBottom: "0.5rem" }}>{data.date_placeholder} · {data.attendees_placeholder}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.meeting_summary}</p>
          </div>
          {data.decisions_made?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("decisionsMade")}</p>
              <ul className="section-list">{data.decisions_made.map((d, i) => <li key={i}>{d}</li>)}</ul>
            </div>
          )}
          {data.action_items?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("actionItems")}</p>
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
              <p className="result-label">{t("nextSteps")}</p>
              <ul className="section-list">{data.next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </div>
          )}
          {data.follow_up_meeting && (
            <div className="result-card">
              <p className="result-label">{t("followUpMeeting")}</p>
              <p style={{ fontSize: "0.9rem" }}>{data.follow_up_meeting}</p>
            </div>
          )}
          <ReportToolbar
            filename={slug(context) || "meeting_notes"}
            subject={`${reportTitle(t)}${context ? ` — ${context}` : ""}`}
            txtContent={buildTxt(data, t)}
            mdContent={buildMd(data, t)}
          />
        </>
      )}
    </div>
  );
}
