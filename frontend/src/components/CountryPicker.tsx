import { useMemo, useState } from "react";
import type { CountryRef } from "../api/types";

interface Props {
  available: CountryRef[];
  selected: string[]; // iso3
  onChange: (selected: string[]) => void;
  max?: number;
}

export default function CountryPicker({
  available,
  selected,
  onChange,
  max = 8,
}: Props) {
  const [query, setQuery] = useState("");
  const nameByIso = useMemo(
    () => new Map(available.map((c) => [c.iso3, c.name])),
    [available],
  );

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return available
      .filter(
        (c) =>
          !selected.includes(c.iso3) &&
          (c.name.toLowerCase().includes(q) || c.iso3.toLowerCase().includes(q)),
      )
      .slice(0, 6);
  }, [query, available, selected]);

  const atMax = selected.length >= max;

  function add(iso3: string) {
    if (atMax || selected.includes(iso3)) return;
    onChange([...selected, iso3]);
    setQuery("");
  }
  function remove(iso3: string) {
    onChange(selected.filter((c) => c !== iso3));
  }

  return (
    <div className="field">
      <label htmlFor="country-search">
        Countries {atMax && <span style={{ color: "var(--warn)" }}>(max {max})</span>}
      </label>
      <input
        id="country-search"
        type="search"
        placeholder={atMax ? "Maximum reached — remove one to add another" : "Search to add a country…"}
        value={query}
        disabled={atMax}
        onChange={(e) => setQuery(e.target.value)}
        list="country-matches"
      />
      {matches.length > 0 && (
        <div className="chips" style={{ marginTop: "var(--s2)" }}>
          {matches.map((c) => (
            <button
              key={c.iso3}
              className="chip"
              style={{ cursor: "pointer" }}
              onClick={() => add(c.iso3)}
            >
              + {c.name}
            </button>
          ))}
        </div>
      )}
      <div className="chips">
        {selected.map((iso3) => (
          <span key={iso3} className="chip">
            {nameByIso.get(iso3) ?? iso3}
            <button onClick={() => remove(iso3)} aria-label={`Remove ${iso3}`}>
              ×
            </button>
          </span>
        ))}
        {selected.length === 0 && (
          <span style={{ color: "var(--muted)", fontSize: "0.84rem" }}>
            No countries selected — showing the global picture.
          </span>
        )}
      </div>
    </div>
  );
}
