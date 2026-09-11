import { useMemo, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { postForm, postBlob } from "../../api/client";

function money(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(2) : "0.00";
}

export default function ExpenseOrganizer() {
  const { t, i18n } = useTranslation("expenseOrganizer");
  const { loading, error, call } = useApi();
  const [files, setFiles] = useState([]);
  const [categoriesInput, setCategoriesInput] = useState("");
  const [dateRange, setDateRange] = useState("this_month");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [data, setData] = useState(null);
  const [entries, setEntries] = useState([]);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState(null);

  function handleFiles(fileList) {
    setFiles(Array.from(fileList).slice(0, 10));
    setData(null);
    setEntries([]);
    setExportError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    fd.append("categories", categoriesInput);
    fd.append("date_range", dateRange);
    fd.append("start_date", startDate);
    fd.append("end_date", endDate);
    fd.append("language", i18n.language);
    const result = await call(() => postForm("/api/biz/expenses", fd));
    if (result) {
      setData(result);
      setEntries(result.entries);
    }
  }

  // Totals are recomputed from the edited rows, not taken from the response --
  // the table is editable, so the figures have to follow the user's corrections.
  const totals = useMemo(() => {
    const byCategory = {};
    entries.forEach((entry) => {
      const amount = Number(entry.amount) || 0;
      byCategory[entry.category] = (byCategory[entry.category] || 0) + amount;
    });
    return byCategory;
  }, [entries]);

  const grandTotal = useMemo(
    () => entries.reduce((sum, entry) => sum + (Number(entry.amount) || 0), 0),
    [entries]
  );

  function updateEntry(index, key, value) {
    setEntries((prev) => prev.map((entry, i) => (i === index ? { ...entry, [key]: value } : entry)));
  }

  function removeEntry(index) {
    setEntries((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleExport() {
    setExporting(true);
    setExportError(null);
    try {
      const blob = await postBlob("/api/biz/expenses/export", {
        entries,
        filename: "expenses",
        labels: [
          t("columns.date"), t("columns.vendor"), t("columns.amount"),
          t("columns.category"), t("columns.source"), t("columns.notes"),
        ],
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "expenses.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExporting(false);
    }
  }

  const inputStyle = {
    padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)",
    borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none",
  };
  const selectStyle = { ...inputStyle, background: "var(--surface)", cursor: "pointer" };
  const categoryOptions = data?.categories || [];

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <div
          className={`drop-zone${dragOver || files.length ? " active" : ""}`}
          onClick={() => document.getElementById("expense-files").click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        >
          <input id="expense-files" type="file" multiple
            accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.pdf,.csv,.xlsx"
            onChange={(e) => handleFiles(e.target.files)} />
          <p className="drop-label">{files.length ? t("filesSelected", { count: files.length }) : t("dropLabel")}</p>
          <p className="drop-hint">{t("dropHint")}</p>
        </div>
        <p className="retention-note">{t("retentionNote")}</p>

        {files.length > 0 && (
          <div>
            {files.map((f, i) => (
              <p key={i} style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>📄 {f.name}</p>
            ))}
          </div>
        )}

        <input type="text" placeholder={t("categoriesPlaceholder")} value={categoriesInput}
          onChange={(e) => setCategoriesInput(e.target.value)} disabled={loading} style={inputStyle} />

        <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
          <span className="field-label">{t("dateRangeLabel")}</span>
          <select value={dateRange} onChange={(e) => setDateRange(e.target.value)} disabled={loading} style={selectStyle}>
            <option value="this_month">{t("dateRangeOptions.this_month")}</option>
            <option value="last_month">{t("dateRangeOptions.last_month")}</option>
            <option value="custom">{t("dateRangeOptions.custom")}</option>
            <option value="all">{t("dateRangeOptions.all")}</option>
          </select>
        </label>

        {dateRange === "custom" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <span className="field-label">{t("startDate")}</span>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} disabled={loading} style={inputStyle} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              <span className="field-label">{t("endDate")}</span>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} disabled={loading} style={inputStyle} />
            </label>
          </div>
        )}

        <button type="submit" className="submit-btn" disabled={loading || !files.length}>
          {loading ? t("organizing") : t("organize")}
        </button>
      </form>

      {error && <div className="error-banner no-print">{error}</div>}

      {data?.errors?.length > 0 && (
        <div className="result-card">
          <p className="result-label">{t("skippedLabel")}</p>
          {data.errors.map((item, i) => (
            <p key={i} style={{ fontSize: "0.85rem", color: "#dc2626", marginBottom: "0.25rem" }}>
              {item.filename} — {item.error}
            </p>
          ))}
        </div>
      )}

      {data && (
        <>
          {data.filtered_out > 0 && (
            <p className="page-subtitle">{t("filteredOut", { count: data.filtered_out })}</p>
          )}

          {entries.length === 0 ? (
            <div className="result-card"><p style={{ fontSize: "0.9rem" }}>{t("noEntries")}</p></div>
          ) : (
            <>
              <div className="result-card">
                <div className="result-header">
                  <p className="result-label">{t("entriesLabel")}</p>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-hint)" }}>{t("editHint")}</span>
                </div>

                <div className="clean-table-scroll">
                  <div className="expense-table">
                    <div className="expense-table-header">
                      <div className="expense-col-date">{t("columns.date")}</div>
                      <div className="expense-col-vendor">{t("columns.vendor")}</div>
                      <div className="expense-col-amount">{t("columns.amount")}</div>
                      <div className="expense-col-category">{t("columns.category")}</div>
                      <div className="expense-col-source">{t("columns.source")}</div>
                      <div className="expense-col-notes">{t("columns.notes")}</div>
                      <div className="expense-col-actions" />
                    </div>
                    {entries.map((entry, i) => (
                      <div key={i} className={`expense-row${entry.confidence === "low" ? " needs-review" : ""}`}>
                        <div className="expense-col-date">
                          <input type="date" value={entry.date || ""} onChange={(e) => updateEntry(i, "date", e.target.value)} />
                        </div>
                        <div className="expense-col-vendor">
                          <input type="text" value={entry.vendor || ""} onChange={(e) => updateEntry(i, "vendor", e.target.value)} />
                        </div>
                        <div className="expense-col-amount">
                          <input type="number" step="0.01" min="0" value={entry.amount}
                            onChange={(e) => updateEntry(i, "amount", e.target.value)} />
                        </div>
                        <div className="expense-col-category">
                          <select value={entry.category} onChange={(e) => updateEntry(i, "category", e.target.value)}>
                            {[...new Set([...categoryOptions, entry.category].filter(Boolean))].map((c) => (
                              <option key={c} value={c}>{c}</option>
                            ))}
                          </select>
                        </div>
                        <div className="expense-col-source" title={entry.source}>{entry.source}</div>
                        <div className="expense-col-notes">
                          <input type="text" value={entry.notes || ""} placeholder={entry.reason || ""}
                            onChange={(e) => updateEntry(i, "notes", e.target.value)} />
                          {entry.confidence === "low" && (
                            <span className="clean-flag" style={{ background: "#fef3c7", color: "#b45309" }}>
                              {t("needsReview")}
                            </span>
                          )}
                        </div>
                        <div className="expense-col-actions">
                          <button type="button" className="copy-btn" onClick={() => removeEntry(i)}>{t("remove")}</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="result-card">
                <p className="result-label">{t("totalsLabel")}</p>
                {Object.entries(totals).sort((a, b) => b[1] - a[1]).map(([category, amount]) => (
                  <div key={category} className="expense-total-row">
                    <span>{category}</span>
                    <span style={{ fontWeight: 600 }}>{money(amount)}</span>
                  </div>
                ))}
                <div className="expense-total-row expense-grand-total">
                  <span>{t("grandTotal")}</span>
                  <span>{money(grandTotal)}</span>
                </div>
              </div>

              {exportError && <div className="error-banner no-print">{exportError}</div>}
              <button type="button" className="submit-btn no-print" onClick={handleExport} disabled={exporting}>
                {exporting ? t("exporting") : t("export")}
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}
