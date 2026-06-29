import { useState } from "react";
import { post } from "../../api/client";

function triggerDownload(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function slug(text) {
  return (text || "").toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "") || "report";
}

export default function ReportToolbar({ filename, subject, txtContent, mdContent, htmlContent }) {
  const [emailTo, setEmailTo] = useState(localStorage.getItem("wbb_email") || "");
  const [emailSent, setEmailSent] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError] = useState(null);

  async function handleEmail(e) {
    e.preventDefault();
    setEmailLoading(true);
    setEmailError(null);
    setEmailSent(false);
    try {
      await post("/api/biz/send-report", {
        email: emailTo,
        subject,
        content_txt: txtContent,
        content_html: htmlContent || txtContent,
      });
      setEmailSent(true);
    } catch (err) {
      setEmailError(err.message);
    } finally {
      setEmailLoading(false);
    }
  }

  return (
    <>
      <div className="report-toolbar no-print">
        <div className="report-toolbar-group">
          <span className="report-toolbar-label">Download</span>
          <button className="toolbar-btn" onClick={() => triggerDownload(txtContent, `${filename}.txt`, "text/plain")}>TXT</button>
          <button className="toolbar-btn" onClick={() => triggerDownload(mdContent || txtContent, `${filename}.md`, "text/markdown")}>MD</button>
          <button className="toolbar-btn" onClick={() => window.print()}>Print / PDF</button>
        </div>
        <div className="report-toolbar-divider" />
        <form className="report-toolbar-group" onSubmit={handleEmail}>
          <span className="report-toolbar-label">Email</span>
          <input
            type="email"
            className="toolbar-email-input"
            value={emailTo}
            onChange={(e) => { setEmailTo(e.target.value); setEmailSent(false); }}
            placeholder="recipient@email.com"
            required
            disabled={emailLoading}
          />
          <button type="submit" className="toolbar-btn toolbar-btn-primary" disabled={emailLoading}>
            {emailLoading ? "Sending…" : "Send"}
          </button>
        </form>
      </div>
      {emailSent && <p className="report-toolbar-success no-print">Report sent to {emailTo}</p>}
      {emailError && <div className="error-banner no-print" style={{ marginTop: "0.5rem" }}>{emailError}</div>}
    </>
  );
}
