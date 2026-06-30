import { useState, useEffect, useCallback } from "react";
import { get, post, put, del, postForm, postBlob } from "../../api/client";

const TYPES = ["Client", "Vendor", "Partner", "Employee", "Personal", "Other"];

const EMPTY_FORM = {
  first_name: "", last_name: "", middle_init: "",
  company: "", contact_type: "Client",
  phones: [""], emails: [""],
  street: "", apt: "", city: "", state: "", zip: "", notes: "",
};

// ── Shared styles ──────────────────────────────────────────────────────────────

const S = {
  input: {
    padding: "0.65rem 0.85rem",
    border: "1.5px solid var(--border)",
    borderRadius: "var(--radius)",
    fontFamily: "inherit",
    fontSize: "0.9rem",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
    background: "#fff",
  },
  select: {
    padding: "0.65rem 0.85rem",
    border: "1.5px solid var(--border)",
    borderRadius: "var(--radius)",
    fontFamily: "inherit",
    fontSize: "0.9rem",
    outline: "none",
    background: "#fff",
    cursor: "pointer",
  },
  btn: {
    padding: "0.6rem 1.1rem",
    borderRadius: "var(--radius)",
    border: "none",
    cursor: "pointer",
    fontFamily: "inherit",
    fontSize: "0.88rem",
    fontWeight: 600,
  },
  btnPrimary: {
    background: "var(--orange)",
    color: "#fff",
  },
  btnGhost: {
    background: "transparent",
    color: "var(--text-muted)",
    border: "1.5px solid var(--border)",
  },
  btnDanger: {
    background: "transparent",
    color: "#dc2626",
    border: "none",
    padding: "0.3rem 0.5rem",
    cursor: "pointer",
    fontFamily: "inherit",
    fontSize: "0.82rem",
  },
};

// ── Dynamic list (phones / emails) ─────────────────────────────────────────────

function MultiInput({ values, onChange, placeholder, type = "text" }) {
  function update(i, val) {
    const next = [...values];
    next[i] = val;
    onChange(next);
  }
  function add() { onChange([...values, ""]); }
  function remove(i) { onChange(values.filter((_, idx) => idx !== i)); }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
      {values.map((v, i) => (
        <div key={i} style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
          <input
            type={type}
            value={v}
            onChange={(e) => update(i, e.target.value)}
            placeholder={placeholder}
            style={{ ...S.input, flex: 1 }}
          />
          {values.length > 1 && (
            <button type="button" onClick={() => remove(i)} style={S.btnDanger} title="Remove">✕</button>
          )}
        </div>
      ))}
      <button type="button" onClick={add}
        style={{ ...S.btn, ...S.btnGhost, alignSelf: "flex-start", padding: "0.35rem 0.75rem", fontSize: "0.82rem" }}>
        + Add {placeholder}
      </button>
    </div>
  );
}

// ── Contact form (add / edit) ──────────────────────────────────────────────────

function ContactForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial || EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function set(key, val) { setForm((f) => ({ ...f, [key]: val })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const payload = {
      ...form,
      phones: form.phones.filter(Boolean),
      emails: form.emails.filter(Boolean),
    };
    try {
      const result = initial?.id
        ? await put(`/api/biz/contacts/${initial.id}`, payload)
        : await post("/api/biz/contacts", payload);
      onSave(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const row = { display: "flex", gap: "0.75rem" };
  const half = { flex: 1 };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.85rem",
      background: "#fff", border: "1.5px solid var(--border)", borderRadius: "var(--radius-lg)",
      padding: "1.5rem", marginBottom: "1.5rem" }}>

      <p style={{ fontWeight: 700, fontSize: "1rem", margin: 0, color: "var(--text)" }}>
        {initial?.id ? "Edit Contact" : "Add Contact"}
      </p>

      <div style={row}>
        <div style={half}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>First Name *</label>
          <input style={S.input} value={form.first_name} onChange={(e) => set("first_name", e.target.value)} placeholder="First name" required />
        </div>
        <div style={{ width: 72 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>MI</label>
          <input style={S.input} value={form.middle_init} onChange={(e) => set("middle_init", e.target.value)} placeholder="M" maxLength={1} />
        </div>
        <div style={half}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Last Name</label>
          <input style={S.input} value={form.last_name} onChange={(e) => set("last_name", e.target.value)} placeholder="Last name" />
        </div>
      </div>

      <div style={row}>
        <div style={half}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Company</label>
          <input style={S.input} value={form.company} onChange={(e) => set("company", e.target.value)} placeholder="Company or organization" />
        </div>
        <div style={{ width: 160 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Type</label>
          <select style={{ ...S.select, width: "100%" }} value={form.contact_type} onChange={(e) => set("contact_type", e.target.value)}>
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Phone(s)</label>
        <MultiInput values={form.phones} onChange={(v) => set("phones", v)} placeholder="Phone" type="tel" />
      </div>

      <div>
        <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Email(s)</label>
        <MultiInput values={form.emails} onChange={(v) => set("emails", v)} placeholder="Email" type="email" />
      </div>

      <div style={row}>
        <div style={{ flex: 2 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Street</label>
          <input style={S.input} value={form.street} onChange={(e) => set("street", e.target.value)} placeholder="Street address" />
        </div>
        <div style={{ width: 90 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Apt / Suite</label>
          <input style={S.input} value={form.apt} onChange={(e) => set("apt", e.target.value)} placeholder="Apt" />
        </div>
      </div>

      <div style={row}>
        <div style={half}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>City</label>
          <input style={S.input} value={form.city} onChange={(e) => set("city", e.target.value)} placeholder="City" />
        </div>
        <div style={{ width: 90 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>State</label>
          <input style={S.input} value={form.state} onChange={(e) => set("state", e.target.value)} placeholder="State" maxLength={30} />
        </div>
        <div style={{ width: 90 }}>
          <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Zip</label>
          <input style={S.input} value={form.zip} onChange={(e) => set("zip", e.target.value)} placeholder="Zip" maxLength={10} />
        </div>
      </div>

      <div>
        <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "0.3rem" }}>Notes</label>
        <textarea style={{ ...S.input, resize: "vertical" }} rows={2} value={form.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Optional notes" />
      </div>

      {error && <p style={{ color: "#dc2626", fontSize: "0.85rem", margin: 0 }}>{error}</p>}

      <div style={{ display: "flex", gap: "0.6rem" }}>
        <button type="submit" style={{ ...S.btn, ...S.btnPrimary }} disabled={loading}>
          {loading ? "Saving…" : (initial?.id ? "Save Changes" : "Add Contact")}
        </button>
        <button type="button" style={{ ...S.btn, ...S.btnGhost }} onClick={onCancel} disabled={loading}>Cancel</button>
      </div>
    </form>
  );
}

// ── Import flow ────────────────────────────────────────────────────────────────

function ImportPanel({ onImported, onCancel }) {
  const [step, setStep] = useState("upload"); // "upload" | "preview"
  const [parsed, setParsed] = useState([]);
  const [parseLoading, setParseLoading] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState(null);

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setParseError(null);
    setParseLoading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await postForm("/api/biz/contacts/parse", fd);
      if (!data.contacts?.length) {
        setParseError("No contacts found in that file.");
      } else {
        setParsed(data.contacts);
        setStep("preview");
      }
    } catch (err) {
      setParseError(err.message);
    } finally {
      setParseLoading(false);
    }
  }

  function updateType(i, type) {
    setParsed((prev) => prev.map((c, idx) => idx === i ? { ...c, contact_type: type } : c));
  }

  function removeRow(i) {
    setParsed((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleConfirm() {
    setImportError(null);
    setImportLoading(true);
    try {
      const data = await post("/api/biz/contacts/import", { contacts: parsed });
      onImported(data.imported);
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImportLoading(false);
    }
  }

  if (step === "upload") {
    return (
      <div style={{ background: "#fff", border: "1.5px solid var(--border)", borderRadius: "var(--radius-lg)",
        padding: "2rem", marginBottom: "1.5rem", textAlign: "center" }}>
        <p style={{ fontWeight: 700, fontSize: "1rem", marginBottom: "0.5rem" }}>Import Contacts</p>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "1.25rem" }}>
          Upload a <strong>.vcf</strong> (vCard) or <strong>.csv</strong> file exported from your phone, Google Contacts, Outlook, or Mac Contacts.
        </p>
        <label style={{ ...S.btn, ...S.btnPrimary, display: "inline-block", cursor: "pointer" }}>
          {parseLoading ? "Parsing…" : "Choose File"}
          <input type="file" accept=".vcf,.csv" onChange={handleFile} style={{ display: "none" }} disabled={parseLoading} />
        </label>
        {parseError && <p style={{ color: "#dc2626", fontSize: "0.85rem", marginTop: "0.75rem" }}>{parseError}</p>}
        <div style={{ marginTop: "1rem" }}>
          <button style={{ ...S.btn, ...S.btnGhost }} onClick={onCancel}>Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: "#fff", border: "1.5px solid var(--border)", borderRadius: "var(--radius-lg)",
      padding: "1.5rem", marginBottom: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <p style={{ fontWeight: 700, fontSize: "1rem", margin: 0 }}>
          Preview — {parsed.length} contact{parsed.length !== 1 ? "s" : ""} found
        </p>
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: 0 }}>
          Set type per contact, remove any you don't want, then confirm.
        </p>
      </div>

      <div style={{ overflowX: "auto", marginBottom: "1rem" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--border)" }}>
              {["Name", "Company", "Type", "Phones", "Emails", ""].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "0.5rem 0.6rem",
                  color: "var(--text-muted)", fontWeight: 600, fontSize: "0.78rem" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {parsed.map((c, i) => {
              const name = [c.first_name, c.middle_init ? c.middle_init + "." : "", c.last_name].filter(Boolean).join(" ");
              return (
                <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.5rem 0.6rem", fontWeight: 600 }}>{name || "—"}</td>
                  <td style={{ padding: "0.5rem 0.6rem", color: "var(--text-muted)" }}>{c.company || "—"}</td>
                  <td style={{ padding: "0.5rem 0.6rem" }}>
                    <select value={c.contact_type} onChange={(e) => updateType(i, e.target.value)}
                      style={{ ...S.select, fontSize: "0.82rem", padding: "0.3rem 0.5rem" }}>
                      {TYPES.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: "0.5rem 0.6rem", color: "var(--text-muted)", fontSize: "0.82rem" }}>
                    {c.phones.join(", ") || "—"}
                  </td>
                  <td style={{ padding: "0.5rem 0.6rem", color: "var(--text-muted)", fontSize: "0.82rem" }}>
                    {c.emails.join(", ") || "—"}
                  </td>
                  <td style={{ padding: "0.5rem 0.6rem" }}>
                    <button onClick={() => removeRow(i)} style={S.btnDanger} title="Remove">✕</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {importError && <p style={{ color: "#dc2626", fontSize: "0.85rem", marginBottom: "0.75rem" }}>{importError}</p>}

      <div style={{ display: "flex", gap: "0.6rem" }}>
        <button style={{ ...S.btn, ...S.btnPrimary }} onClick={handleConfirm}
          disabled={importLoading || parsed.length === 0}>
          {importLoading ? "Importing…" : `Import ${parsed.length} Contact${parsed.length !== 1 ? "s" : ""}`}
        </button>
        <button style={{ ...S.btn, ...S.btnGhost }} onClick={() => setStep("upload")} disabled={importLoading}>Back</button>
        <button style={{ ...S.btn, ...S.btnGhost }} onClick={onCancel} disabled={importLoading}>Cancel</button>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function Contacts() {
  const [view, setView]               = useState("list"); // "list" | "add" | "edit" | "import"
  const [editingContact, setEditing]  = useState(null);
  const [contacts, setContacts]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [search, setSearch]           = useState("");
  const [typeFilter, setTypeFilter]   = useState("All");
  const [selected, setSelected]       = useState(new Set());
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState(null);
  const [successMsg, setSuccessMsg]   = useState(null);

  const fetchContacts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get("/api/biz/contacts");
      setContacts(data.contacts || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchContacts(); }, [fetchContacts]);

  // Client-side filter
  const filtered = contacts.filter((c) => {
    if (typeFilter !== "All" && c.contact_type !== typeFilter) return false;
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.first_name.toLowerCase().includes(q) ||
      c.last_name.toLowerCase().includes(q) ||
      c.company.toLowerCase().includes(q) ||
      c.phones.some((p) => p.includes(q)) ||
      c.emails.some((e) => e.includes(q))
    );
  });

  function flash(msg) {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 3000);
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this contact?")) return;
    try {
      await del(`/api/biz/contacts/${id}`);
      setContacts((prev) => prev.filter((c) => c.id !== id));
      setSelected((prev) => { const s = new Set(prev); s.delete(id); return s; });
    } catch (err) {
      setError(err.message);
    }
  }

  function handleSave(saved) {
    setContacts((prev) => {
      const exists = prev.find((c) => c.id === saved.id);
      return exists
        ? prev.map((c) => (c.id === saved.id ? saved : c))
        : [...prev, saved].sort((a, b) => a.last_name.localeCompare(b.last_name) || a.first_name.localeCompare(b.first_name));
    });
    setView("list");
    setEditing(null);
    flash(saved.id && editingContact?.id ? "Contact updated." : "Contact added.");
  }

  function handleImported(count) {
    setView("list");
    fetchContacts();
    flash(`${count} contact${count !== 1 ? "s" : ""} imported.`);
  }

  function toggleSelect(id) {
    setSelected((prev) => {
      const s = new Set(prev);
      s.has(id) ? s.delete(id) : s.add(id);
      return s;
    });
  }

  function toggleAll() {
    if (selected.size === filtered.length && filtered.length > 0) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((c) => c.id)));
    }
  }

  async function handleExport() {
    setExportError(null);
    setExportLoading(true);
    try {
      const ids = selected.size > 0 ? [...selected] : null;
      const blob = await postBlob("/api/biz/contacts/export/pdf", { ids });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = ids?.length === 1
        ? `${(contacts.find((c) => c.id === ids[0])?.last_name || "contact").toLowerCase()}.pdf`
        : "contacts_directory.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExportLoading(false);
    }
  }

  const allChecked = filtered.length > 0 && selected.size === filtered.length;
  const someChecked = selected.size > 0 && selected.size < filtered.length;
  const exportLabel = exportLoading
    ? "Exporting…"
    : selected.size > 0
    ? `Export PDF (${selected.size})`
    : "Export All PDF";

  return (
    <div>
      <h1 className="page-title">Contacts</h1>
      <p className="page-subtitle">Manage your business contacts. Import from any device or add them manually.</p>

      {/* ── Action bar ── */}
      {view === "list" && (
        <div style={{ display: "flex", gap: "0.6rem", marginBottom: "1.25rem", flexWrap: "wrap", alignItems: "center" }}>
          <input
            type="search"
            placeholder="Search contacts…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ ...S.input, flex: "1 1 200px", maxWidth: 320 }}
          />
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
            style={{ ...S.select, flex: "0 0 auto" }}>
            <option>All</option>
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
          <div style={{ flex: 1 }} />
          <button style={{ ...S.btn, ...S.btnGhost }} onClick={() => { setEditing(null); setView("import"); }}>
            ↑ Import
          </button>
          <button style={{ ...S.btn, ...S.btnGhost }} onClick={handleExport} disabled={exportLoading || contacts.length === 0}>
            {exportLabel}
          </button>
          <button style={{ ...S.btn, ...S.btnPrimary }} onClick={() => { setEditing(null); setView("add"); }}>
            + Add Contact
          </button>
        </div>
      )}

      {/* ── Success / error banners ── */}
      {successMsg && (
        <div style={{ background: "#dcfce7", color: "#166534", borderRadius: "var(--radius)",
          padding: "0.6rem 1rem", marginBottom: "1rem", fontSize: "0.88rem" }}>
          {successMsg}
        </div>
      )}
      {(error || exportError) && (
        <div className="error-banner" style={{ marginBottom: "1rem" }}>{error || exportError}</div>
      )}

      {/* ── Subviews ── */}
      {view === "add" && (
        <ContactForm
          initial={{ ...EMPTY_FORM }}
          onSave={handleSave}
          onCancel={() => setView("list")}
        />
      )}
      {view === "edit" && editingContact && (
        <ContactForm
          initial={editingContact}
          onSave={handleSave}
          onCancel={() => { setView("list"); setEditing(null); }}
        />
      )}
      {view === "import" && (
        <ImportPanel onImported={handleImported} onCancel={() => setView("list")} />
      )}

      {/* ── Contact list ── */}
      {view === "list" && (
        <>
          {loading && <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Loading…</p>}

          {!loading && contacts.length === 0 && (
            <div style={{ textAlign: "center", padding: "3rem 1rem", color: "var(--text-muted)" }}>
              <p style={{ fontSize: "1rem", marginBottom: "0.5rem" }}>No contacts yet.</p>
              <p style={{ fontSize: "0.88rem" }}>Add one manually or import a file from your phone or computer.</p>
            </div>
          )}

          {!loading && contacts.length > 0 && filtered.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No contacts match your search.</p>
          )}

          {!loading && filtered.length > 0 && (
            <div style={{ background: "#fff", border: "1.5px solid var(--border)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
              {/* Table header with select-all */}
              <div style={{ display: "flex", alignItems: "center", padding: "0.6rem 1rem",
                borderBottom: "2px solid var(--border)", background: "#fafafa" }}>
                <input type="checkbox" checked={allChecked} ref={(el) => { if (el) el.indeterminate = someChecked; }}
                  onChange={toggleAll} style={{ marginRight: "0.75rem", cursor: "pointer" }} />
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 600, flex: 1 }}>
                  NAME
                </span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 600, width: 160 }}>COMPANY</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 600, width: 90 }}>TYPE</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 600, width: 140 }}>PHONE</span>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", fontWeight: 600, flex: 1 }}>EMAIL</span>
                <span style={{ width: 80 }} />
              </div>

              {filtered.map((c, idx) => {
                const name = [c.first_name, c.middle_init ? c.middle_init + "." : "", c.last_name].filter(Boolean).join(" ");
                const isLast = idx === filtered.length - 1;
                return (
                  <div key={c.id} style={{ display: "flex", alignItems: "center", padding: "0.75rem 1rem",
                    borderBottom: isLast ? "none" : "1px solid var(--border)",
                    background: selected.has(c.id) ? "#eff6ff" : "transparent" }}>
                    <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggleSelect(c.id)}
                      style={{ marginRight: "0.75rem", cursor: "pointer" }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{name || "—"}</span>
                    </div>
                    <div style={{ width: 160, fontSize: "0.85rem", color: "var(--text-muted)", overflow: "hidden",
                      textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.company || "—"}
                    </div>
                    <div style={{ width: 90 }}>
                      <span style={{ fontSize: "0.75rem", background: "#eff6ff", color: "var(--orange)",
                        borderRadius: 4, padding: "0.15rem 0.5rem", fontWeight: 600 }}>
                        {c.contact_type}
                      </span>
                    </div>
                    <div style={{ width: 140, fontSize: "0.83rem", color: "var(--text-muted)",
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.phones[0] || "—"}
                      {c.phones.length > 1 && <span style={{ color: "var(--text-hint)", fontSize: "0.75rem" }}> +{c.phones.length - 1}</span>}
                    </div>
                    <div style={{ flex: 1, fontSize: "0.83rem", color: "var(--text-muted)",
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.emails[0] || "—"}
                      {c.emails.length > 1 && <span style={{ color: "var(--text-hint)", fontSize: "0.75rem" }}> +{c.emails.length - 1}</span>}
                    </div>
                    <div style={{ width: 80, display: "flex", gap: "0.25rem", justifyContent: "flex-end" }}>
                      <button title="Edit" onClick={() => { setEditing({ ...c, phones: c.phones.length ? c.phones : [""], emails: c.emails.length ? c.emails : [""] }); setView("edit"); }}
                        style={{ ...S.btnDanger, color: "var(--orange)" }}>✏</button>
                      <button title="Delete" onClick={() => handleDelete(c.id)} style={S.btnDanger}>🗑</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {!loading && contacts.length > 0 && (
            <p style={{ fontSize: "0.8rem", color: "var(--text-hint)", marginTop: "0.75rem" }}>
              {filtered.length} of {contacts.length} contact{contacts.length !== 1 ? "s" : ""}
              {selected.size > 0 && ` · ${selected.size} selected`}
            </p>
          )}
        </>
      )}
    </div>
  );
}
