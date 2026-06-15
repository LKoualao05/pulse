import type { Indicator } from "../api/types";
import { CATEGORY_LABELS } from "../lib/format";

interface Props {
  indicators: Indicator[];
  value: string;
  onChange: (key: string) => void;
}

export default function IndicatorPicker({ indicators, value, onChange }: Props) {
  // Group options by category for a tidier dropdown.
  const byCategory = new Map<string, Indicator[]>();
  for (const ind of indicators) {
    const list = byCategory.get(ind.category) ?? [];
    list.push(ind);
    byCategory.set(ind.category, list);
  }

  return (
    <div className="field">
      <label htmlFor="indicator">Indicator</label>
      <select
        id="indicator"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {[...byCategory.entries()].map(([cat, list]) => (
          <optgroup key={cat} label={CATEGORY_LABELS[cat] ?? cat}>
            {list.map((ind) => (
              <option key={ind.key} value={ind.key}>
                {ind.name}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </div>
  );
}
