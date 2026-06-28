import { useAuth } from "../../contexts/AuthContext";

const NAV_ITEMS = [
  { id: "ats", label: "ATS Analyzer" },
  { id: "doc", label: "Doc Analyzer" },
  { id: "linux", label: "Linux" },
  { id: "mac", label: "Mac" },
  { id: "resume", label: "Resume Builder" },
  { id: "windows", label: "Windows" },
  { id: "workflow", label: "Workflow" },
];

export default function Header({ active, onSelect }) {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <div className="brand">
        <span className="brand-name">
          Torres<span className="brand-accent">Tech</span> Remote
        </span>
        <div className="brand-divider" />
        <span className="brand-product">Workblox</span>
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
      <div className="header-user">
        <span className="header-user-name">{user?.name}</span>
        <button className="header-signout" onClick={logout}>Sign out</button>
      </div>
    </header>
  );
}
