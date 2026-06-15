interface Props {
  view: "dashboard" | "about";
  onNavigate: (view: "dashboard" | "about") => void;
}

export default function Header({ view, onNavigate }: Props) {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="brand">
          <span className="dot" aria-hidden />
          <span>
            Pulse <small>Well-Being Observatory</small>
          </span>
        </div>
        <nav className="nav">
          <button
            className={view === "dashboard" ? "active" : ""}
            onClick={() => onNavigate("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={view === "about" ? "active" : ""}
            onClick={() => onNavigate("about")}
          >
            About &amp; Sources
          </button>
        </nav>
      </div>
    </header>
  );
}
