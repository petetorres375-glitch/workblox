import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { get, post } from "../../api/client";

export default function PendingRequests() {
  const { t } = useTranslation("admin");
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pendingActionId, setPendingActionId] = useState(null);

  async function fetchRequests() {
    try {
      const data = await get("/api/admin/tool-requests");
      setRequests(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchRequests(); }, []);

  async function act(requestId, action) {
    setPendingActionId(requestId);
    try {
      await post(`/api/admin/tool-requests/${requestId}/${action}`, {});
      setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
    } catch (err) {
      alert(err.message);
    } finally {
      setPendingActionId(null);
    }
  }

  if (loading) return <p className="page-subtitle">{t("requests.loading")}</p>;
  if (error) return <p className="login-error">{error}</p>;
  if (requests.length === 0) return <p className="page-subtitle">{t("requests.none")}</p>;

  return (
    <div>
      {requests.map((r) => (
        <div key={r.request_id} className="admin-user-card">
          <div className="admin-user-info">
            <span className="admin-user-name">{r.tool_name}</span>
            <span className="admin-user-email">{r.user_name} ({r.user_email})</span>
            <span className="admin-user-date">
              {t("joined", { date: new Date(r.requested_at).toLocaleDateString() })}
            </span>
          </div>
          <div className="admin-user-actions">
            <button
              className="admin-action-btn btn-activate"
              disabled={pendingActionId === r.request_id}
              onClick={() => act(r.request_id, "grant")}
            >
              {t("requests.grant")}
            </button>
            <button
              className="admin-action-btn btn-deactivate"
              disabled={pendingActionId === r.request_id}
              onClick={() => act(r.request_id, "dismiss")}
            >
              {t("requests.dismiss")}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
