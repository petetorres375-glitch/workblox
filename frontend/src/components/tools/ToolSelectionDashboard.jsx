import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { get } from "../../api/client";

const SOURCE_FILTERS = ["all", "self_service", "admin_manual", "plan_default"];

function Bar({ name, count, maxCount }) {
  const pct = Math.round((count / maxCount) * 100);
  return (
    <div className="tool-bar-row">
      <span className="tool-bar-label">{name}</span>
      <div className="tool-bar-track">
        <div className="tool-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="tool-bar-value">{count}</span>
    </div>
  );
}

export default function ToolSelectionDashboard() {
  const { t } = useTranslation("admin");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");

  useEffect(() => {
    get("/api/admin/entitlements/summary")
      .then(setRows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = sourceFilter === "all" ? rows : rows.filter((r) => r.source === sourceFilter);

  const counts = useMemo(() => {
    const byTool = new Map();
    for (const r of filtered) {
      if (!byTool.has(r.tool_key)) {
        byTool.set(r.tool_key, { name: r.tool_name, app: r.app, count: 0 });
      }
      byTool.get(r.tool_key).count += 1;
    }
    return [...byTool.values()];
  }, [filtered]);

  const personalCounts = counts.filter((c) => c.app === "personal").sort((a, b) => b.count - a.count);
  const businessCounts = counts.filter((c) => c.app === "business").sort((a, b) => b.count - a.count);
  const maxCount = Math.max(1, ...counts.map((c) => c.count));

  if (loading) return <p className="page-subtitle">{t("dashboard.loading")}</p>;
  if (error) return <p className="login-error">{error}</p>;

  return (
    <div>
      <div className="admin-filters">
        {SOURCE_FILTERS.map((f) => (
          <button
            key={f}
            className={`admin-filter-btn${sourceFilter === f ? " active" : ""}`}
            onClick={() => setSourceFilter(f)}
          >
            {t(`dashboard.sourceFilters.${f}`)}
          </button>
        ))}
      </div>

      <div className="stat-tile" style={{ marginBottom: "1.5rem" }}>
        <span className="stat-tile-label">{t("dashboard.totalSelections")}</span>
        <span className="stat-tile-value">{filtered.length}</span>
      </div>

      <h2 className="dashboard-section-title">{t("dashboard.personalTools")}</h2>
      {personalCounts.length === 0 && <p className="page-subtitle">{t("dashboard.noData")}</p>}
      {personalCounts.map((c) => <Bar key={c.name} name={c.name} count={c.count} maxCount={maxCount} />)}

      <h2 className="dashboard-section-title">{t("dashboard.businessTools")}</h2>
      {businessCounts.length === 0 && <p className="page-subtitle">{t("dashboard.noData")}</p>}
      {businessCounts.map((c) => <Bar key={c.name} name={c.name} count={c.count} maxCount={maxCount} />)}
    </div>
  );
}
