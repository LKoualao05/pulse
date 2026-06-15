import type { IndicatorSummary } from "../api/types";
import { CATEGORY_LABELS, formatValue, shortUnit } from "../lib/format";

interface Props {
  summary: IndicatorSummary;
  selected: boolean;
  onClick: () => void;
}

export default function StatCard({ summary, selected, onClick }: Props) {
  const isCategorical = summary.value_type === "categorical";
  const headline = isCategorical
    ? `${summary.countries}`
    : formatValue(summary.global_latest_mean, summary.unit);

  return (
    <button
      className={`card stat-card clickable${selected ? " selected" : ""}`}
      onClick={onClick}
      aria-pressed={selected}
    >
      <span className="cat">{CATEGORY_LABELS[summary.category] ?? summary.category}</span>
      <span className="value">{headline}</span>
      <span className="label">{summary.name}</span>
      <span className="meta">
        {isCategorical
          ? `${summary.countries} countries reporting · ${summary.latest_year ?? "—"}`
          : `global avg · ${shortUnit(summary.unit)} · ${summary.latest_year ?? "—"}`}
      </span>
    </button>
  );
}
