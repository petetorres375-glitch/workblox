import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { post } from "../../api/client";
import { useApi } from "../../hooks/useApi";

export default function LinuxHelper() {
  const { t, i18n } = useTranslation("linuxHelper");
  const [problem, setProblem] = useState("");
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const { loading, error, call } = useApi();

  async function handleSubmit(e) {
    e.preventDefault();
    const data = await call(() => post("/api/linux", { problem, language: i18n.language }));
    if (data) setResult(data);
  }

  function copy() {
    navigator.clipboard.writeText(result.command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <form onSubmit={handleSubmit}>
        <div className="search-box">
          <input
            type="text"
            placeholder={t("placeholder")}
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
          />
          <button type="submit" disabled={loading || !problem.trim()}>
            {loading ? t("thinking") : t("ask")}
          </button>
        </div>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {result && !loading && (
        <>
          {result.gui_steps?.length > 0 && result.gui_steps[0] !== "No GUI method available for this task." && (
            <div className="result-card">
              <div className="result-label">{t("result.guiSteps")}</div>
              <ol className="warning-list" style={{ paddingLeft: "1.2rem" }}>
                {result.gui_steps.map((s, i) => <li key={i} style={{ marginBottom: "0.4rem" }}>{s}</li>)}
              </ol>
            </div>
          )}

          <div className="result-card">
            <div className="result-header">
              <div className="result-label">{t("result.command")}</div>
              <button className="copy-btn" onClick={copy}>{copied ? t("result.copied") : t("result.copy")}</button>
            </div>
            <div className="command-box">{result.command}</div>
          </div>

          <div className="result-card">
            <div className="result-label">{t("result.explanation")}</div>
            <p className="explanation-text">{result.explanation}</p>
          </div>

          {result.warnings?.length > 0 && result.warnings[0] !== "None." && (
            <div className="result-card">
              <div className="result-label">{t("result.warnings")}</div>
              <ul className="warning-list">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </>
      )}
    </>
  );
}
