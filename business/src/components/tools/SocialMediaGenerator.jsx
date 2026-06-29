import { useState } from "react";
import { useApi } from "../../hooks/useApi";
import { post } from "../../api/client";
import ReportToolbar, { slug } from "../ui/ReportToolbar";

const PLATFORM_COLORS = { LinkedIn: "#0077b5", Instagram: "#e1306c", Facebook: "#1877f2", Twitter: "#1da1f2", TikTok: "#000000" };

function buildTxt(data, topic) {
  const lines = [`SOCIAL MEDIA POSTS${topic ? ` — ${topic.toUpperCase()}` : ""}`, "=".repeat(60)];
  (data.posts || []).forEach((p) => {
    lines.push("", p.platform.toUpperCase(), "-".repeat(40), p.content || "");
    if (p.hashtags?.length) lines.push("", p.hashtags.map(h => `#${h}`).join(" "));
    if (p.best_time_to_post) lines.push(`Best time to post: ${p.best_time_to_post}`);
  });
  if (data.content_tips?.length) {
    lines.push("", "CONTENT TIPS", "-".repeat(40));
    data.content_tips.forEach((t, i) => lines.push(`${i + 1}. ${t}`));
  }
  return lines.join("\n");
}

function buildMd(data, topic) {
  const lines = [`# Social Media Posts${topic ? ` — ${topic}` : ""}`];
  (data.posts || []).forEach((p) => {
    lines.push("", `## ${p.platform}`, p.content || "");
    if (p.hashtags?.length) lines.push("", p.hashtags.map(h => `#${h}`).join(" "));
    if (p.best_time_to_post) lines.push(``, `*Best time: ${p.best_time_to_post}*`);
  });
  if (data.content_tips?.length) { lines.push("", "## Content Tips"); data.content_tips.forEach((t) => lines.push(`- ${t}`)); }
  return lines.join("\n");
}

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

      <form onSubmit={handleSubmit} className="no-print" style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <textarea placeholder="Topic or content idea *" value={topic} onChange={(e) => setTopic(e.target.value)} required rows={2} disabled={loading} style={{ ...inputStyle, resize: "vertical" }} />
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

      {error && <div className="error-banner no-print">{error}</div>}

      {data && (
        <>
          <div className="print-header" style={{ display: "none" }}><strong>Social Media Posts{topic ? ` — ${topic}` : ""}</strong></div>
          {(data.posts || []).map((p, i) => (
            <div key={i} className="result-card">
              <div className="result-header">
                <p className="result-label" style={{ color: PLATFORM_COLORS[p.platform] || "var(--text-hint)" }}>{p.platform}</p>
                <button className="copy-btn no-print" onClick={() => navigator.clipboard.writeText(p.content + (p.hashtags?.length ? "\n\n" + p.hashtags.map(h => `#${h}`).join(" ") : ""))}>Copy</button>
              </div>
              <p style={{ fontSize: "0.92rem", lineHeight: 1.65, marginBottom: "0.75rem", whiteSpace: "pre-wrap" }}>{p.content}</p>
              {p.hashtags?.length > 0 && (
                <p style={{ fontSize: "0.82rem", color: "var(--orange)", wordBreak: "break-word" }}>{p.hashtags.map(h => `#${h}`).join(" ")}</p>
              )}
              {p.best_time_to_post && (
                <p style={{ fontSize: "0.78rem", color: "var(--text-hint)", marginTop: "0.5rem" }}>Best time: {p.best_time_to_post}</p>
              )}
            </div>
          ))}
          {data.content_tips?.length > 0 && (
            <div className="result-card">
              <p className="result-label">Content Tips</p>
              <ul className="section-list">{data.content_tips.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </div>
          )}
          <ReportToolbar
            filename={slug(topic) || "social_media_posts"}
            subject={`Social Media Posts${topic ? ` — ${topic}` : ""}`}
            txtContent={buildTxt(data, topic)}
            mdContent={buildMd(data, topic)}
          />
        </>
      )}
    </div>
  );
}
