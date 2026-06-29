import { useEffect, useState } from "react";
import { get, post } from "../../api/client";

export default function Admin() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");

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

  useEffect(() => { fetchUsers(); }, []);

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

  async function togglePlan(id, newPlan) {
    try {
      await post(`/api/admin/users/${id}/plan`, { plan: newPlan });
      setUsers((prev) =>
        prev.map((u) => u.id === id ? { ...u, plan: newPlan } : u)
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
      <h1 className="page-title">Admin <span>Panel</span></h1>
      <p className="page-subtitle">Manage client accounts and activations.</p>

      <div className="admin-filters">
        {["all", "pending", "active"].map((f) => (
          <button
            key={f}
            className={`admin-filter-btn${filter === f ? " active" : ""}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading && <p className="page-subtitle">Loading users…</p>}
      {error && <p className="login-error">{error}</p>}

      {!loading && !error && filtered.length === 0 && (
        <p className="page-subtitle">No users found.</p>
      )}

      {!loading && filtered.map((u) => (
        <div key={u.email} className="admin-user-card">
          <div className="admin-user-info">
            <span className="admin-user-name">{u.name}</span>
            <span className="admin-user-email">{u.email}</span>
            <span className="admin-user-date">
              Joined {new Date(u.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="admin-user-actions">
            <span className={`admin-badge ${u.is_active ? "badge-active" : "badge-pending"}`}>
              {u.is_active ? "Active" : "Pending"}
            </span>
            <button
              className={`admin-action-btn ${u.is_active ? "btn-deactivate" : "btn-activate"}`}
              onClick={() => toggleActive(u.email, !u.is_active)}
            >
              {u.is_active ? "Deactivate" : "Activate"}
            </button>
            <span className={`admin-badge ${u.plan === "business" ? "badge-active" : "badge-pending"}`}>
              {u.plan === "business" ? "Business" : "Free"}
            </span>
            <button
              className={`admin-action-btn ${u.plan === "business" ? "btn-deactivate" : "btn-activate"}`}
              onClick={() => togglePlan(u.id, u.plan === "business" ? "free" : "business")}
            >
              {u.plan === "business" ? "Set Free" : "Set Business"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
