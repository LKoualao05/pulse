import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Source } from "../api/types";

export default function About() {
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    api.getSources().then(setSources).catch(() => setSources([]));
  }, []);

  return (
    <div className="container prose">
      <h1>About Pulse</h1>
      <p>
        Pulse is a small, open observatory that makes public mental-health and
        well-being data legible to non-experts and to the nonprofits who serve
        them. It presents only <strong>aggregate, country-level</strong> figures
        drawn from reputable, openly licensed sources.
      </p>

      <h2>What this is — and isn’t</h2>
      <p>
        Pulse never ingests, stores, or displays individual-level data, personal
        posts, names, or identifiable crisis content. There is no scraping of
        forums, social media, or help-line data. Distressing statistics are
        always accompanied by crisis-resource information (see the footer on
        every page).
      </p>

      <h2>Methodology</h2>
      <p>
        A small Python pipeline fetches each dataset directly from its provider’s
        API, validates and harmonizes country codes to ISO-3166 alpha-3 (dropping
        regional and world aggregates), de-duplicates, and writes versioned data
        files. The web app reads those processed files. A daily automated job
        refreshes the data and only commits when the figures actually change.
      </p>

      <h2>Data sources &amp; licensing</h2>
      <p>
        Each indicator carries its source’s license, shown beneath every chart.
        We use only series we are permitted to redistribute.{" "}
        <strong>
          Our World in Data’s IHME-derived prevalence series are explicitly
          non-redistributable, so they are deliberately excluded.
        </strong>
      </p>

      <div className="source-list">
        {sources.map((s) => (
          <div key={s.key} className="card source-item">
            <h3>{s.name}</h3>
            <p style={{ margin: "0 0 6px" }}>{s.attribution}</p>
            <p style={{ margin: 0, fontSize: "0.85rem" }}>
              <a className="license-pill" href={s.license_url} target="_blank" rel="noreferrer">
                {s.license}
              </a>{" "}
              · <a href={s.url} target="_blank" rel="noreferrer">provider site ↗</a>{" "}
              · accessed {s.accessed_at}
            </p>
            {s.notes && (
              <p style={{ margin: "8px 0 0", fontSize: "0.82rem", color: "var(--muted)" }}>
                {s.notes}
              </p>
            )}
          </div>
        ))}
      </div>

      <h2>Disclaimer</h2>
      <p style={{ fontSize: "0.9rem" }}>
        Pulse is an educational, non-commercial project. It is not medical advice
        and figures should be verified against their original sources before use.
      </p>
    </div>
  );
}
