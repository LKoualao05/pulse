import { useState } from "react";
import CrisisFooter from "./components/CrisisFooter";
import Header from "./components/Header";
import About from "./pages/About";
import Dashboard from "./pages/Dashboard";

type View = "dashboard" | "about";

export default function App() {
  const [view, setView] = useState<View>("dashboard");

  return (
    <div className="app">
      <Header view={view} onNavigate={setView} />
      <main>{view === "dashboard" ? <Dashboard /> : <About />}</main>

      <footer className="site-footer">
        <div className="container site-footer-inner">
          <span>
            Pulse · a public well-being observatory · educational &amp;
            non-commercial.
          </span>
          <span>Data: WHO · World Bank · Our World in Data.</span>
        </div>
      </footer>

      <CrisisFooter />
    </div>
  );
}
