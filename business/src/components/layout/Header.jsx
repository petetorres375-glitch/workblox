import { useAuth } from "../../contexts/AuthContext";

const NAV_ITEMS = [
  { id: "hiring", label: "Hiring Manager" },
  { id: "batch-ats", label: "Batch ATS" },
  { id: "job-desc", label: "Job Description" },
  { id: "proposal", label: "Proposal" },
  { id: "contract", label: "Contract" },
  { id: "customer", label: "Customer Response" },
  { id: "review", label: "Review Request" },
  { id: "social", label: "Social Media" },
  { id: "ad-copy", label: "Ad Copy" },
  { id: "policy", label: "Policy" },
  { id: "sop", label: "SOP" },
  { id: "meeting", label: "Meeting Notes" },
  { id: "email", label: "Business Email" },
  { id: "contacts", label: "Contacts" },
];

export default function Header({ active, onSelect }) {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="header-top">
        <div className="brand">
          <span className="brand-name">
            Torres<span className="brand-accent">Tech</span> Remote
          </span>
          <div className="brand-divider" />
          <span className="brand-product">Workblox Business</span>
        </div>
        <div className="header-user">
          <span className="header-user-name">{user?.name}</span>
          <button className="header-signout" onClick={logout}>Sign out</button>
        </div>
      </div>
      <nav className="tool-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={active === item.id ? "active" : ""}
            onClick={() => onSelect(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
