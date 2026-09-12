import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { postForm, postBlob } from "../../api/client";

const FLAG_COLORS = {
  duplicate: { bg: "#fef3c7", fg: "#b45309" },
  ambiguous_date: { bg: "#fef3c7", fg: "#b45309" },
  unparseable_date: { bg: "#fef2f2", fg: "#dc2626" },
};

// The summary is assembled from the engine's own counts rather than sent down
// as a prepared sentence -- the backend stays language-agnostic, and every
// number here traces back to work data_cleaner actually did.
function buildSummary(counts, t) {
  const parts = [];
  if (counts.dates_fixed) parts.push(t("summaryDates", { count: counts.dates_fixed }));
  if (counts.duplicates_merged) parts.push(t("summaryMerged", { count: counts.duplicates_merged }));
  if (counts.rows_flagged) parts.push(t("summaryFlagged", { count: counts.rows_flagged }));
  if (counts.cells_trimmed) parts.push(t("summaryTrimmed", { count: counts.cells_trimmed }));
  if (!parts.length) return t("summaryClean");
  return `${t("summaryLead")} ${parts.join(", ")}.`;
}

function baseName(filename) {
  return (filename || "data").replace(/\.[^.]+$/, "");
}

export default function DataCleanup() {
  const { t, i18n } = useTranslation("dataCleanup");
  const { loading, error, call } = useApi();
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState("");
  const [dateFormat, setDateFormat] = useState("auto");
  const [duplicateHandling, setDuplicateHandling] = useState("flag");
  const [dragOver, setDragOver] = useState(false);
  const [data, setData] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  function handleFiles(fileList) {
    const next = fileList?.[0];
    if (!next) return;
    setFile(next);
    setData(null);
    setDownloadError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("description", description);
    fd.append("date_format", dateFormat);
    fd.append("duplicate_handling", duplicateHandling);
    fd.append("language", i18n.language);
    const result = await call(() => postForm("/api/biz/data-cleanup", fd));
    if (result) setData(result);
  }

  async function handleDownload() {
    setDownloading(true);
    setDownloadError(null);
    try {
      const blob = await postBlob("/api/biz/data-cleanup/download", {
        headers: data.headers,
        rows: data.rows,
        format: data.source_format,
        filename: `${baseName(file?.name)}_cleaned`,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${baseName(file?.name)}_cleaned.${data.source_format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(err.message);
    } finally {
      setDownloading(false);
    }
  }

  const inputStyle = {
    padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)",
    borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none",
  };
  const selectStyle = { ...inputStyle, background: "var(--surface)", cursor: "pointer" };

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <div
          className={`drop-zone${dragOver || file ? " active" : ""}`}
          onClick={() => document.getElementById("cleanup-file").click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        >
          <input id="cleanup-file" type="file" accept=".xlsx,.csv" onChange={(e) => handleFiles(e.target.files)} />
          <p className="drop-label">{file ? file.name : t("dropLabel")}</p>
          <p className="drop-hint">{t("dropHint")}</p>
        </div>
        <p className="retention-note">{t("retentionNote")}</p>

        <input type="text" placeholder={t("descriptionPlaceholder")} value={description}
          onChange={(e) => setDescription(e.target.value)} disabled={loading} style={inputStyle} />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            <span className="field-label">{t("dateFormatLabel")}</span>
            <select value={dateFormat} onChange={(e) => setDateFormat(e.target.value)} disabled={loading} style={selectStyle}>
              <option value="auto">{t("dateFormatOptions.auto")}</option>
              <option value="mdy">{t("dateFormatOptions.mdy")}</option>
              <option value="dmy">{t("dateFormatOptions.dmy")}</option>
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
            <span className="field-label">{t("duplicateLabel")}</span>
            <select value={duplicateHandling} onChange={(e) => setDuplicateHandling(e.target.value)} disabled={loading} style={selectStyle}>
              <option value="flag">{t("duplicateOptions.flag")}</option>
              <option value="merge">{t("duplicateOptions.merge")}</option>
            </select>
          </label>
        </div>

        <button type="submit" className="submit-btn" disabled={loading || !file}>
          {loading ? t("cleaning") : t("clean")}
        </button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="result-card">
            <p className="result-label">{t("summaryLabel")}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.6 }}>{buildSummary(data.counts, t)}</p>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
              {t("rowCount", { before: data.total_rows_in, after: data.total_rows_out })}
            </p>
          </div>

          <div className="result-card">
            <div className="result-header">
              <p className="result-label">{t("previewLabel")}</p>
              <span style={{ fontSize: "0.78rem", color: "var(--text-hint)" }}>
                {t("previewCount", { shown: data.preview.length, total: data.total_rows_out })}
              </span>
            </div>

            <div className="clean-table-scroll">
              <div className="clean-table" style={{ minWidth: `${Math.max(data.headers.length * 150, 400)}px` }}>
                <div className="clean-table-header">
                  {data.headers.map((h) => (
                    <div key={h} className="clean-cell">{h}</div>
                  ))}
                  <div className="clean-cell clean-col-flags">{t("statusColumn")}</div>
                </div>
                {data.preview.map((row, i) => (
                  <div key={i} className="clean-row">
                    {row.after.map((value, j) => {
                      const changed = row.changed.includes(j) && row.before[j] !== value;
                      return (
                        <div key={j} className={`clean-cell${changed ? " changed" : ""}`}>
                          {changed && <span className="clean-before">{row.before[j] || t("blank")}</span>}
                          <span>{value || <span style={{ color: "var(--text-hint)" }}>{t("blank")}</span>}</span>
                        </div>
                      );
                    })}
                    <div className="clean-cell clean-col-flags">
                      {row.flags.map((flag) => {
                        const color = FLAG_COLORS[flag] || { bg: "#f5f5f5", fg: "#666" };
                        return (
                          <span key={flag} className="clean-flag" style={{ background: color.bg, color: color.fg }}>
                            {t(`flags.${flag}`)}
                          </span>
                        );
                      })}
                      {row.merged_count > 0 && (
                        <span className="clean-flag" style={{ background: "#dcfce7", color: "#16a34a" }}>
                          {t("mergedTag", { count: row.merged_count })}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {downloadError && <div className="error-banner no-print">{downloadError}</div>}
          <button type="button" className="submit-btn no-print" onClick={handleDownload} disabled={downloading}>
            {downloading ? t("preparing") : t("download")}
          </button>
        </>
      )}
    </div>
  );
}
