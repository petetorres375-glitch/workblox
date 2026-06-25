import { useRef, useState } from "react";
import { postForm } from "../../api/client";
import { useApi } from "../../hooks/useApi";
import Button from "../ui/Button";
import ErrorBanner from "../ui/ErrorBanner";
import Spinner from "../ui/Spinner";

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
    <div className="tool-area">
      <h2>Doc Analyzer</h2>
      <p className="subtitle">Upload a PDF, TXT, or MD file — get a structured AI summary.</p>

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
            <p className="drop-label" style={{ color: "var(--color-text)" }}>{file.name}</p>
          ) : (
            <>
              <p className="drop-label">Drop a file here or click to browse</p>
              <p className="drop-hint">PDF, TXT, or MD — max 10 MB</p>
            </>
          )}
        </div>

        <div style={{ marginTop: 16 }}>
          <Button type="submit" disabled={loading || !file}>
            {loading ? "Analyzing..." : "Analyze"}
          </Button>
        </div>
      </form>

      {loading && <Spinner />}
      <ErrorBanner message={error} />

      {result && !loading && (
        <div className="result-block">
          <Section title="Summary" content={result.summary} />
          <Section title="Key Data Points" content={result.key_data_points} />
          <Section title="Action Items" content={result.action_items} />
          <Section title="Red Flags" content={result.red_flags} />
        </div>
      )}
    </div>
  );
}

function Section({ title, content }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h3>{title}</h3>
      {Array.isArray(content) ? (
        <ul className="section-list" style={{ marginTop: 8 }}>
          {content.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      ) : (
        <p style={{ fontSize: "0.9rem", lineHeight: 1.6, marginTop: 8 }}>{content}</p>
      )}
    </div>
  );
}
