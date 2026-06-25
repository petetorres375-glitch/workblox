const NAV_ITEMS = [
  { id: "doc", label: "Doc Analyzer" },
  { id: "workflow", label: "Workflow" },
  { id: "linux", label: "Linux" },
  { id: "windows", label: "Windows" },
  { id: "mac", label: "Mac" },
];

export default function Header({ active, onSelect }) {
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
    </header>
  );
}
