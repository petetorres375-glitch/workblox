import { useRef, useState } from "react";
import { postForm } from "../../api/client";
import { useApi } from "../../hooks/useApi";

export default function DocAnalyzer() {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState(null);
  const fileRef = useRef();
  const { loading, error, call } = useApi();

  function handleFile(f) {
    if (f) setFile(f);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const data = await call(() => postForm("/api/doc", fd));
    if (data) setResult(data);
  }

  return (
    <>
      <h1 className="page-title">Doc <span>Analyzer</span></h1>
      <p className="page-subtitle">Upload a PDF, TXT, or MD file — get a structured AI summary.</p>

      <form onSubmit={handleSubmit}>
        <div
          className={`drop-zone${dragOver ? " active" : ""}`}
          onClick={() => fileRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {file ? (
            <p className="drop-label" style={{ color: "#111" }}>{file.name}</p>
          ) : (
            <>
              <p className="drop-label">Drop a file here or click to browse</p>
              <p className="drop-hint">PDF, TXT, or MD — max 10 MB</p>
            </>
          )}
        </div>

        <button type="submit" className="submit-btn" disabled={loading || !file}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {error && <div className="error-banner" style={{ marginTop: 16 }}>{error}</div>}

      {result && !loading && (
        <div style={{ marginTop: 24 }}>
          <DocSection title="Summary" content={result.summary} />
          <DocSection title="Key Data Points" content={result.key_data_points} />
          <DocSection title="Action Items" content={result.action_items} />
          <DocSection title="Red Flags" content={result.red_flags} />
        </div>
      )}
    </>
  );
}

function DocSection({ title, content }) {
  return (
    <div className="result-card">
      <div className="result-label">{title}</div>
      {Array.isArray(content) ? (
        <ul className="section-list">
          {content.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      ) : (
        <p className="explanation-text">{content}</p>
      )}
    </div>
  );
}
