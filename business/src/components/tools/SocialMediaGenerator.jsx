import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";

const PLATFORM_COLORS = { LinkedIn: "#0077b5", Instagram: "#e1306c", Facebook: "#1877f2", Twitter: "#1da1f2", TikTok: "#000000" };

export default function SocialMediaGenerator() {
  const { loading, error, call } = useApi();
  const [topic, setTopic] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [platforms, setPlatforms] = useState("LinkedIn, Instagram, Facebook");
  const [tone, setTone] = useState("professional");
  const [goal, setGoal] = useState("engagement");
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const result = await call(() => post("/api/biz/social-media", { topic, business_name: businessName, platforms, tone, goal }));
    if (result) setData(result);
  }

  const inputStyle = { padding: "0.75rem 0.9rem", border: "1.5px solid var(--border)", borderRadius: "var(--radius)", fontFamily: "inherit", fontSize: "0.92rem", outline: "none" };

  return (
    <div>
      <h1 className="page-title">Social Media <span>Generator</span></h1>
      <p className="page-subtitle">Generate platform-ready social media content for your business.</p>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder="Topic or content idea *" value={topic} onChange={(e) => setTopic(e.target.value)} required rows={2} disabled={loading}
          style={{ ...inputStyle, resize: "vertical" }} />
        <input type="text" placeholder="Business name" value={businessName} onChange={(e) => setBusinessName(e.target.value)} disabled={loading} style={inputStyle} />
        <input type="text" placeholder="Platforms (e.g. LinkedIn, Instagram, Facebook)" value={platforms} onChange={(e) => setPlatforms(e.target.value)} disabled={loading} style={inputStyle} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <select value={tone} onChange={(e) => setTone(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["professional", "casual", "humorous", "inspiring", "educational"].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
          <select value={goal} onChange={(e) => setGoal(e.target.value)} disabled={loading} style={{ ...inputStyle, background: "var(--surface)", cursor: "pointer" }}>
            {["engagement", "awareness", "leads", "sales", "education"].map(g => <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>)}
          </select>
        </div>
        <button type="submit" className="submit-btn" disabled={loading}>{loading ? "Generating…" : "Generate Posts"}</button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {data && (
        <>
          {(data.posts || []).map((post, i) => (
            <div key={i} className="result-card">
              <div className="result-header">
                <p className="result-label" style={{ color: PLATFORM_COLORS[post.platform] || "var(--text-hint)" }}>{post.platform}</p>
                <button className="copy-btn" onClick={() => navigator.clipboard.writeText(post.content + (post.hashtags?.length ? "\n\n" + post.hashtags.map(h => `#${h}`).join(" ") : ""))}>Copy</button>
              </div>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65, marginBottom: "0.75rem", whiteSpace: "pre-wrap" }}>{post.content}</p>
              {post.hashtags?.length > 0 && (
                <p style={{ fontSize: "0.82rem", color: "var(--orange)", wordBreak: "break-word" }}>
                  {post.hashtags.map(h => `#${h}`).join(" ")}
                </p>
              )}
              {post.best_time_to_post && (
                <p style={{ fontSize: "0.78rem", color: "var(--text-hint)", marginTop: "0.5rem" }}>Best time: {post.best_time_to_post}</p>
              )}
            </div>
          ))}
          {data.content_tips?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Content Tips</p>
              <ul className="section-list">{data.content_tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
