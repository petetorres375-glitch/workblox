import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { get, post, put } from "../../api/client";

const CONTACTS_KEY = "contacts";

export default function ToolPicker({ variant = "settings", onDone }) {
  const { t } = useTranslation(["toolPicker", "nav"]);
  const [tools, setTools] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [activeKeys, setActiveKeys] = useState(new Set());
  const [pendingKeys, setPendingKeys] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isSignup = variant === "signup";

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [toolList, entitlements] = await Promise.all([
          get("/api/tools?app=business"),
          get("/api/entitlements?app=business"),
        ]);
        if (cancelled) return;
        setTools(toolList);
        setSelected(new Set([...entitlements.tool_keys, ...entitlements.pending_keys]));
        setActiveKeys(new Set(entitlements.tool_keys));
        setPendingKeys(new Set(entitlements.pending_keys));
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  function toggle(key) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function handleSave() {
    if (selected.size === 0) {
      setError(t("errorMinOne"));
      return;
    }
    // Contacts is the one tool with real stored per-user data -- deselecting
    // an ACTIVE Contacts grant deletes that data server-side, so confirm
    // before submitting. A merely-pending (never-granted) Contacts request
    // has no data to lose, so it's excluded from this check.
    const removingContacts = activeKeys.has(CONTACTS_KEY) && !selected.has(CONTACTS_KEY);
    if (removingContacts && !window.confirm(t("contactsDeleteConfirm"))) {
      return;
    }

    setSaving(true);
    setError("");
    try {
      if (isSignup) {
        // Signup's first pick is granted immediately -- unlike every later
        // Settings change, a brand-new client isn't left staring at an
        // empty app waiting for approval.
        await put("/api/entitlements", { tool_keys: Array.from(selected), app: "business" });
      } else {
        const result = await post("/api/entitlements/sync", { tool_keys: Array.from(selected), app: "business" });
        setActiveKeys(new Set(result.tool_keys));
        setPendingKeys(new Set(result.pending_keys));
        setSelected(new Set([...result.tool_keys, ...result.pending_keys]));
      }
      onDone?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const body = loading ? (
    <p className="page-subtitle">{t("loading")}</p>
  ) : (
    <>
      <h1 className={isSignup ? "welcome-title" : "page-title"}>
        {t(isSignup ? "signupTitle" : "settingsTitle")}
      </h1>
      <p className="page-subtitle">{t(isSignup ? "signupSubtitle" : "settingsSubtitle")}</p>

      <div className="tool-picker-list">
        {tools.map((tool) => (
          <label key={tool.key} className="tool-picker-item">
            <input
              type="checkbox"
              checked={selected.has(tool.key)}
              onChange={() => toggle(tool.key)}
            />
            <span>{t(`nav:${tool.key}`)}</span>
            {!isSignup && pendingKeys.has(tool.key) && selected.has(tool.key) && (
              <span className="tool-picker-pending-tag">{t("pendingApproval")}</span>
            )}
          </label>
        ))}
      </div>

      <p className="tool-picker-count">{t("selectedCount", { count: selected.size })}</p>

      {error && <p className="login-error">{error}</p>}

      <button type="button" className="submit-btn" onClick={handleSave} disabled={saving}>
        {t(isSignup ? "continueButton" : "saveButton")}
      </button>
    </>
  );

  if (isSignup) {
    return (
      <div className="login-page">
        <div className="login-card">{body}</div>
      </div>
    );
  }

  return <div>{body}</div>;
}
