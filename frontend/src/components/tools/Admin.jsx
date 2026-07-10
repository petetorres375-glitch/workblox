import { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { get, post } from "../../api/client";
import AdminToolsEditor from "./AdminToolsEditor";
import PendingRequests from "./PendingRequests";
import ToolSelectionDashboard from "./ToolSelectionDashboard";

const FILTER_IDS = ["all", "pending", "active"];
const VIEW_IDS = ["users", "requests", "dashboard"];

export default function Admin() {
  const { t } = useTranslation("admin");
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [view, setView] = useState("users");
  const [killSwitch, setKillSwitch] = useState({ personal_enabled: true, business_enabled: true });
  const [ksLoading, setKsLoading] = useState(false);
  const [expandedUserId, setExpandedUserId] = useState(null);

  async function fetchUsers() {
    try {
      const data = await get("/api/admin/users");
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchKillSwitch() {
    try {
      const data = await get("/api/admin/kill-switch");
      setKillSwitch(data);
    } catch (_) {}
  }

  async function toggleKillSwitch(key) {
    setKsLoading(true);
    try {
      const updated = { [key]: !killSwitch[key] };
      await post("/api/admin/kill-switch", updated);
      setKillSwitch((prev) => ({ ...prev, ...updated }));
    } catch (err) {
      alert(err.message);
    } finally {
      setKsLoading(false);
    }
  }

  useEffect(() => { fetchUsers(); fetchKillSwitch(); }, []);

  async function toggleActive(email, activate) {
    const action = activate ? "activate" : "deactivate";
    try {
      await post(`/api/admin/users/${encodeURIComponent(email)}/${action}`, {});
      setUsers((prev) =>
        prev.map((u) => u.email === email ? { ...u, is_active: activate } : u)
      );
    } catch (err) {
      alert(err.message);
    }
  }

  async function toggleAccess(id, field, nextValue) {
    try {
      await post(`/api/admin/users/${id}/access`, { [field]: nextValue });
      setUsers((prev) =>
        prev.map((u) => u.id === id ? { ...u, [field]: nextValue } : u)
      );
    } catch (err) {
      alert(err.message);
    }
  }

  const filtered = users.filter((u) => {
    if (filter === "pending") return !u.is_active;
    if (filter === "active") return u.is_active;
    return true;
  });

  return (
    <div>
      <h1 className="page-title"><Trans t={t} i18nKey="title"><span /></Trans></h1>
      <p className="page-subtitle">{t("subtitle")}</p>

      <div className="admin-filters">
        {VIEW_IDS.map((v) => (
          <button
            key={v}
            className={`admin-filter-btn${view === v ? " active" : ""}`}
            onClick={() => setView(v)}
          >
            {t(`views.${v}`)}
          </button>
        ))}
      </div>

      {view === "dashboard" ? (
        <ToolSelectionDashboard />
      ) : view === "requests" ? (
        <PendingRequests />
      ) : (
        <>
          <div className="admin-user-card" style={{ marginBottom: "24px" }}>
            <div className="admin-user-info">
              <span className="admin-user-name">{t("killSwitch.heading")}</span>
              <span className="admin-user-email">{t("killSwitch.description")}</span>
            </div>
            <div className="admin-user-actions">
              <span className={`admin-badge ${killSwitch.personal_enabled ? "badge-active" : "badge-pending"}`}>
                {t("killSwitch.personal")} {killSwitch.personal_enabled ? t("killSwitch.on") : t("killSwitch.off")}
              </span>
              <button
                className={`admin-action-btn ${killSwitch.personal_enabled ? "btn-deactivate" : "btn-activate"}`}
                onClick={() => toggleKillSwitch("personal_enabled")}
                disabled={ksLoading}
              >
                {killSwitch.personal_enabled ? t("killSwitch.disablePersonal") : t("killSwitch.enablePersonal")}
              </button>
              <span className={`admin-badge ${killSwitch.business_enabled ? "badge-active" : "badge-pending"}`}>
                {t("killSwitch.business")} {killSwitch.business_enabled ? t("killSwitch.on") : t("killSwitch.off")}
              </span>
              <button
                className={`admin-action-btn ${killSwitch.business_enabled ? "btn-deactivate" : "btn-activate"}`}
                onClick={() => toggleKillSwitch("business_enabled")}
                disabled={ksLoading}
              >
                {killSwitch.business_enabled ? t("killSwitch.disableBusiness") : t("killSwitch.enableBusiness")}
              </button>
            </div>
          </div>

          <div className="admin-filters">
            {FILTER_IDS.map((f) => (
              <button
                key={f}
                className={`admin-filter-btn${filter === f ? " active" : ""}`}
                onClick={() => setFilter(f)}
              >
                {t(`filters.${f}`)}
              </button>
            ))}
          </div>

          {loading && <p className="page-subtitle">{t("loading")}</p>}
          {error && <p className="login-error">{error}</p>}

          {!loading && !error && filtered.length === 0 && (
            <p className="page-subtitle">{t("noUsers")}</p>
          )}

          {!loading && filtered.map((u) => (
            <div key={u.email} className="admin-user-card" style={{ flexDirection: "column", alignItems: "stretch" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                <div className="admin-user-info">
                  <span className="admin-user-name">{u.name}</span>
                  <span className="admin-user-email">{u.email}</span>
                  <span className="admin-user-date">
                    {t("joined", { date: new Date(u.created_at).toLocaleDateString() })}
                  </span>
                </div>
                <div className="admin-user-actions">
                  <span className={`admin-badge ${u.is_active ? "badge-active" : "badge-pending"}`}>
                    {u.is_active ? t("status.active") : t("status.pending")}
                  </span>
                  <button
                    className={`admin-action-btn ${u.is_active ? "btn-deactivate" : "btn-activate"}`}
                    onClick={() => toggleActive(u.email, !u.is_active)}
                  >
                    {u.is_active ? t("actions.deactivate") : t("actions.activate")}
                  </button>
                  <span className={`admin-badge ${u.has_personal ? "badge-active" : "badge-pending"}`}>
                    {t("access.personal")} {u.has_personal ? t("access.on") : t("access.off")}
                  </span>
                  <button
                    className={`admin-action-btn ${u.has_personal ? "btn-deactivate" : "btn-activate"}`}
                    onClick={() => toggleAccess(u.id, "has_personal", !u.has_personal)}
                  >
                    {u.has_personal ? t("access.revokePersonal") : t("access.grantPersonal")}
                  </button>
                  <span className={`admin-badge ${u.has_business ? "badge-active" : "badge-pending"}`}>
                    {t("access.business")} {u.has_business ? t("access.on") : t("access.off")}
                  </span>
                  <button
                    className={`admin-action-btn ${u.has_business ? "btn-deactivate" : "btn-activate"}`}
                    onClick={() => toggleAccess(u.id, "has_business", !u.has_business)}
                  >
                    {u.has_business ? t("access.revokeBusiness") : t("access.grantBusiness")}
                  </button>
                  <button
                    className="admin-action-btn btn-deactivate"
                    onClick={() => setExpandedUserId(expandedUserId === u.id ? null : u.id)}
                  >
                    {expandedUserId === u.id ? t("tools.hide") : t("tools.manage")}
                  </button>
                </div>
              </div>
              {expandedUserId === u.id && <AdminToolsEditor userId={u.id} />}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
