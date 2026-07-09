import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { get, post } from "../../api/client";

// A user's manual tool grants, editable inline in their admin card. Unlike
// the self-service ToolPicker (batch-select then Save), this mirrors the
// rest of Admin.jsx's existing convention: each checkbox is its own
// immediate action, same as the activate/plan-toggle buttons beside it.
export default function AdminToolsEditor({ userId }) {
  const { t } = useTranslation("admin");
  const [tools, setTools] = useState([]);
  const [enabled, setEnabled] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [pendingKey, setPendingKey] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      get("/api/tools"),
      get(`/api/admin/users/${userId}/entitlements`),
    ]).then(([toolList, entitlements]) => {
      if (cancelled) return;
      setTools(toolList);
      setEnabled(new Set(entitlements.tool_keys));
    }).catch((err) => {
      if (!cancelled) setError(err.message);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [userId]);

  async function toggle(key) {
    const nextEnabled = !enabled.has(key);
    setPendingKey(key);
    setError("");
    // Optimistic update -- the checkbox reflects the click immediately
    // rather than flickering back to its old state for the round-trip,
    // and rolls back only if the request actually fails.
    setEnabled((prev) => {
      const next = new Set(prev);
      if (nextEnabled) next.add(key);
      else next.delete(key);
      return next;
    });
    try {
      await post(`/api/admin/users/${userId}/entitlements`, { tool_key: key, enabled: nextEnabled });
    } catch (err) {
      setError(err.message);
      setEnabled((prev) => {
        const next = new Set(prev);
        if (nextEnabled) next.delete(key);
        else next.add(key);
        return next;
      });
    } finally {
      setPendingKey(null);
    }
  }

  if (loading) return <p className="page-subtitle">{t("tools.loading")}</p>;

  const personalTools = tools.filter((tool) => tool.app === "personal");
  const businessTools = tools.filter((tool) => tool.app === "business");

  return (
    <div className="admin-tools-editor">
      {error && <p className="login-error">{error}</p>}
      <div className="admin-tools-group">
        {personalTools.map((tool) => (
          <label key={tool.key} className="tool-picker-item">
            <input
              type="checkbox"
              checked={enabled.has(tool.key)}
              disabled={pendingKey === tool.key}
              onChange={() => toggle(tool.key)}
            />
            <span>{tool.name}</span>
          </label>
        ))}
      </div>
      <div className="admin-tools-group">
        {businessTools.map((tool) => (
          <label key={tool.key} className="tool-picker-item">
            <input
              type="checkbox"
              checked={enabled.has(tool.key)}
              disabled={pendingKey === tool.key}
              onChange={() => toggle(tool.key)}
            />
            <span>{tool.name}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
