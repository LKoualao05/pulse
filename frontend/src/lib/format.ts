// Small formatting helpers shared across components.

export function formatValue(value: number | null, unit: string): string {
  if (value === null || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  let num: string;
  if (abs >= 1000) num = value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  else if (abs >= 10) num = value.toFixed(1);
  else num = value.toFixed(2);

  if (unit.includes("US$")) return `$${num}`;
  if (unit.startsWith("%")) return `${num}%`;
  return num;
}

export function shortUnit(unit: string): string {
  return unit
    .replace("per 100,000 population", "per 100k")
    .replace("current US$", "US$")
    .replace("% of total labor force", "% labor force")
    .replace("% of population", "% of pop.");
}

// A calm, qualitative palette for chart lines (color-blind-considerate).
export const SERIES_COLORS = [
  "#2f7e9e", // teal-blue
  "#e9a23b", // amber
  "#7b6cae", // muted violet
  "#3f9e7a", // green
  "#cc6b8e", // rose
  "#5b8def", // blue
  "#b06a3b", // terracotta
  "#6aa84f", // leaf
];

export const CATEGORY_LABELS: Record<string, string> = {
  outcome: "Outcome",
  burden: "Burden",
  capacity: "System capacity",
  context: "Context",
  governance: "Governance",
};
