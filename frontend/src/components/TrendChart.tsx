import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesResponse } from "../api/types";
import { SERIES_COLORS, shortUnit } from "../lib/format";

const axisStyle = { fontSize: 12, fill: "#6b7a8d" };

export default function TrendChart({ data }: { data: SeriesResponse }) {
  const { indicator, series } = data;

  if (series.length === 0) {
    return (
      <div className="state">
        No data for this selection. Try different countries.
      </div>
    );
  }

  // --- Categorical indicators → a compact table (latest reported value) ---
  if (indicator.value_type === "categorical") {
    return (
      <table className="cat-table">
        <thead>
          <tr>
            <th>Country</th>
            <th>{indicator.name}</th>
            <th>Year</th>
          </tr>
        </thead>
        <tbody>
          {series.map((cs) => {
            const last = cs.points[cs.points.length - 1];
            return (
              <tr key={cs.country_iso3}>
                <td>{cs.country_name}</td>
                <td>{last?.value_text ?? "—"}</td>
                <td>{last?.year ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }

  // --- Determine whether this is a single-year snapshot ---
  const years = new Set<number>();
  for (const cs of series) for (const p of cs.points) years.add(p.year);
  const isSnapshot = years.size <= 1;

  if (isSnapshot) {
    // Bar chart comparing countries for the single available year.
    const barData = series
      .map((cs) => ({
        country: cs.country_name,
        value: cs.points[0]?.value ?? null,
      }))
      .filter((d) => d.value !== null);

    return (
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ee" vertical={false} />
            <XAxis dataKey="country" tick={axisStyle} interval={0} angle={-15} height={50} textAnchor="end" />
            <YAxis tick={axisStyle} width={56} />
            <Tooltip
              formatter={(v: number) => [`${v} ${shortUnit(indicator.unit)}`, indicator.name]}
            />
            <Bar dataKey="value" fill={SERIES_COLORS[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // --- Time series → multi-line chart, merged by year ---
  const byYear = new Map<number, Record<string, number | string>>();
  for (const cs of series) {
    for (const p of cs.points) {
      if (p.value === null) continue;
      const row = byYear.get(p.year) ?? { year: p.year };
      row[cs.country_name] = p.value;
      byYear.set(p.year, row);
    }
  }
  const lineData = [...byYear.values()].sort(
    (a, b) => (a.year as number) - (b.year as number),
  );

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={lineData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ee" vertical={false} />
          <XAxis dataKey="year" tick={axisStyle} />
          <YAxis tick={axisStyle} width={56} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((cs, i) => (
            <Line
              key={cs.country_iso3}
              type="monotone"
              dataKey={cs.country_name}
              stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
