import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useApi } from "../../hooks/useApi";
import { postForm } from "../../api/client";
import { compressImage } from "../../utils/imageCapture";
import ReportToolbar from "../ui/ReportToolbar";
import { reportTitle } from "../../utils/reportLabels";

const MAX_PHOTOS = 6;
const RISK_COLOR = { low: "#16a34a", medium: "#b45309", high: "#dc2626" };
const IMAGE_EXTENSIONS = /\.(jpe?g|png|heic|heif|webp|gif|bmp|tiff?)$/i;

function isImageFile(f) {
  // Some browsers (drag-and-drop especially) report HEIC files with no
  // useful MIME type, so fall back to checking the extension too.
  return f.type.startsWith("image/") || IMAGE_EXTENSIONS.test(f.name);
}

// Exported reports reuse the same translated labels as the on-screen result,
// so a report reads in the language it was generated in. Headings are left in
// their natural case: uppercasing is wrong for Turkish (i -> I) and a no-op for
// every non-cased script, and the PDF finds headings by the ---- rule anyway.
function buildTxt(data, fileName, t) {
  const subject = data.document_type || fileName || "";
  const lines = [`${reportTitle(t)} — ${subject}`.trim(), "=".repeat(60)];
  if (data.overall_risk) lines.push(t(`risk.${data.overall_risk}`));
  lines.push("", t("documentOverview"), "-".repeat(40), data.summary || "");
  if (data.key_obligations?.length) {
    lines.push("", t("keyObligations"), "-".repeat(40));
    data.key_obligations.forEach((o, i) => lines.push(`${i + 1}. ${o}`));
  }
  if (data.payment_terms) lines.push("", t("paymentTerms"), "-".repeat(40), data.payment_terms);
  if (data.red_flags?.length) {
    lines.push("", t("redFlags"), "-".repeat(40));
    data.red_flags.forEach((f, i) => lines.push(`${i + 1}. ${f}`));
  }
  if (data.missing_standard_clauses?.length) {
    lines.push("", t("missingClauses"), "-".repeat(40));
    data.missing_standard_clauses.forEach((c, i) => lines.push(`${i + 1}. ${c}`));
  }
  if (data.recommendation) lines.push("", t("recommendation"), "-".repeat(40), data.recommendation);
  return lines.join("\n");
}

function buildMd(data, fileName, t) {
  const subject = data.document_type || fileName || "";
  const lines = [`# ${reportTitle(t)} — ${subject}`.trim()];
  if (data.overall_risk) lines.push(``, `**${t(`risk.${data.overall_risk}`)}**`);
  lines.push("", `## ${t("documentOverview")}`, data.summary || "");
  if (data.key_obligations?.length) { lines.push("", `## ${t("keyObligations")}`); data.key_obligations.forEach((o) => lines.push(`- ${o}`)); }
  if (data.payment_terms) lines.push("", `## ${t("paymentTerms")}`, data.payment_terms);
  if (data.red_flags?.length) { lines.push("", `## ${t("redFlags")}`); data.red_flags.forEach((f) => lines.push(`- ${f}`)); }
  if (data.missing_standard_clauses?.length) { lines.push("", `## ${t("missingClauses")}`); data.missing_standard_clauses.forEach((c) => lines.push(`- ${c}`)); }
  if (data.recommendation) lines.push("", `## ${t("recommendation")}`, data.recommendation);
  return lines.join("\n");
}

export default function ContractAnalyzer() {
  const { t, i18n } = useTranslation("contractAnalyzer");
  const { loading, error, call } = useApi();
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [photos, setPhotos] = useState([]); // [{ id, blob, previewUrl }]
  const [photoError, setPhotoError] = useState(null);
  const [data, setData] = useState(null);

  function clearPhotos() {
    photos.forEach((p) => URL.revokeObjectURL(p.previewUrl));
    setPhotos([]);
  }

  function handleFile(f) {
    if (f) { clearPhotos(); setFile(f); setData(null); }
  }

  async function addPhotoFiles(rawFiles) {
    const files = Array.from(rawFiles || []).filter(Boolean);
    if (files.length === 0) return;
    if (photos.length + files.length > MAX_PHOTOS) {
      setPhotoError(t("photo.limit", { max: MAX_PHOTOS }));
      return;
    }
    setPhotoError(null);
    setFile(null);
    setData(null);
    const added = [];
    for (const rawFile of files) {
      let blob;
      try {
        blob = await compressImage(rawFile);
      } catch {
        // Couldn't decode client-side (e.g. HEIC on a browser with no HEIC
        // decoder) — upload the original file and let the backend normalize it.
        blob = rawFile;
      }
      added.push({ id: `${Date.now()}-${photos.length + added.length}`, blob, previewUrl: URL.createObjectURL(rawFile) });
    }
    setPhotos((prev) => [...prev, ...added]);
  }

  // The drop-zone now accepts either a document or one/more photos — route
  // dropped/selected files to whichever pipeline fits instead of always
  // treating them as a single document.
  function handleDroppedOrSelected(fileList) {
    const files = Array.from(fileList || []).filter(Boolean);
    if (files.length === 0) return;
    const images = files.filter(isImageFile);
    if (images.length > 0) {
      addPhotoFiles(images);
      return;
    }
    handleFile(files[0]);
  }

  async function handlePhotoInput(e) {
    // Snapshot into a plain array before clearing the input — e.target.files
    // is a live FileList tied to the input, and resetting .value (needed so
    // picking the same file again still fires onChange) can empty it out
    // from under an async consumer if we hold onto the live list instead.
    const files = Array.from(e.target.files || []);
    e.target.value = "";
    await addPhotoFiles(files);
  }

  function removePhoto(id) {
    setPhotos((prev) => {
      const target = prev.find((p) => p.id === id);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((p) => p.id !== id);
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file && photos.length === 0) return;
    const fd = new FormData();
    if (photos.length > 0) {
      photos.forEach((p, i) => fd.append("images", p.blob, `photo-${i + 1}.jpg`));
    } else {
      fd.append("file", file);
    }
    fd.append("language", i18n.language);
    const result = await call(() => postForm("/api/biz/contract", fd));
    if (result) setData(result);
  }

  const baseName = file ? file.name.replace(/\.[^.]+$/, "") : "contract";

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit} className="no-print">
        <div
          className={`drop-zone${dragOver ? " active" : ""}${file ? " active" : ""}`}
          onClick={() => document.getElementById("contract-file").click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleDroppedOrSelected(e.dataTransfer.files); }}
        >
          <input id="contract-file" type="file" accept=".pdf,.txt,.docx,.doc" onChange={(e) => handleDroppedOrSelected(e.target.files)} />
          <p className="drop-label">{file ? file.name : t("dropLabel")}</p>
          <p className="drop-hint">{t("dropHint")}</p>
        </div>

        <div className="photo-capture">
          <div className="photo-capture-divider">{t("photo.or")}</div>
          <div className="photo-capture-buttons">
            <label className="photo-capture-btn">
              {t("photo.take")}
              <input type="file" accept="image/*" capture="environment" onChange={handlePhotoInput} />
            </label>
            <label className="photo-capture-btn">
              {t("photo.choose")}
              <input type="file" accept="image/*" multiple onChange={handlePhotoInput} />
            </label>
          </div>
          <p className="photo-capture-hint">{t("photo.hint")}</p>
          {photoError && <div className="error-banner" style={{ marginTop: 8 }}>{photoError}</div>}
          {photos.length > 0 && (
            <div className="photo-thumbs">
              {photos.map((p, i) => (
                <PhotoThumb
                  key={p.id}
                  photo={p}
                  label={t("photo.pageLabel", { n: i + 1 })}
                  removeLabel={t("photo.removeLabel", { n: i + 1 })}
                  onRemove={() => removePhoto(p.id)}
                />
              ))}
            </div>
          )}
        </div>

        <button type="submit" className="submit-btn" disabled={loading || (!file && photos.length === 0)}>{loading ? t("analyzing") : t("analyze")}</button>
      </form>

      {error && <div className="error-banner no-print" style={{ marginTop: "1rem" }}>{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Contract Analysis — {data.document_type || baseName}</strong></div>
          <div className="result-card" style={{ marginTop: "1.5rem" }}>
            <div className="result-header">
              <p className="result-label">{t("documentOverview")}</p>
              {data.overall_risk && (
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: RISK_COLOR[data.overall_risk] || "#666", textTransform: "uppercase" }}>
                  {t(`risk.${data.overall_risk}`)}
                </span>
              )}
            </div>
            <p style={{ fontWeight: 700, marginBottom: "0.4rem" }}>{data.document_type}</p>
            <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.summary}</p>
          </div>
          {data.key_obligations?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("keyObligations")}</p>
              <ul className="section-list">{data.key_obligations.map((o, i) => <li key={i}>{o}</li>)}</ul>
            </div>
          )}
          {data.payment_terms && (
            <div className="result-card">
              <p className="result-label">{t("paymentTerms")}</p>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.payment_terms}</p>
            </div>
          )}
          {data.red_flags?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("redFlags")}</p>
              <ul className="warning-list">{data.red_flags.map((f, i) => <li key={i}>{f}</li>)}</ul>
            </div>
          )}
          {data.missing_standard_clauses?.length > 0 && (
            <div className="result-card">
              <p className="result-label">{t("missingClauses")}</p>
              <ul className="warning-list">{data.missing_standard_clauses.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </div>
          )}
          {data.recommendation && (
            <div className="result-card">
              <p className="result-label">{t("recommendation")}</p>
              <p style={{ fontSize: "0.95rem", lineHeight: 1.65 }}>{data.recommendation}</p>
            </div>
          )}
          <ReportToolbar
            filename={`${baseName}_analysis`}
            subject={`${reportTitle(t)} — ${data.document_type || baseName}`}
            txtContent={buildTxt(data, baseName, t)}
            mdContent={buildMd(data, baseName, t)}
          />
        </>
      )}
    </div>
  );
}

function PhotoThumb({ photo, label, removeLabel, onRemove }) {
  const [broken, setBroken] = useState(false);
  return (
    <div className="photo-thumb">
      {!broken ? (
        <img src={photo.previewUrl} alt={label} onError={() => setBroken(true)} />
      ) : (
        <div className="photo-thumb-fallback">{label}</div>
      )}
      <button type="button" onClick={onRemove} aria-label={removeLabel}>&times;</button>
    </div>
  );
}
