import { useEffect, useMemo, useState } from "react";
import { ApiError, api } from "../api/client";
import type {
  CountryRef,
  Indicator,
  IndicatorSummary,
  SeriesResponse,
} from "../api/types";
import CountryPicker from "../components/CountryPicker";
import ExplainPanel from "../components/ExplainPanel";
import IndicatorPicker from "../components/IndicatorPicker";
import SourceBadge from "../components/SourceBadge";
import StatCard from "../components/StatCard";
import TrendChart from "../components/TrendChart";
import { shortUnit } from "../lib/format";

const DEFAULT_COUNTRIES = ["USA", "GBR", "JPN", "IND", "BRA"];
const MAX_COUNTRIES = 8;

export default function Dashboard() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [summaries, setSummaries] = useState<IndicatorSummary[]>([]);
  const [indicatorKey, setIndicatorKey] = useState<string>("");
  const [available, setAvailable] = useState<CountryRef[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [series, setSeries] = useState<SeriesResponse | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);

  // Initial load: indicators + summary.
  useEffect(() => {
    (async () => {
      try {
        const [inds, summary] = await Promise.all([
          api.getIndicators(),
          api.getSummary(),
        ]);
        setIndicators(inds);
        setSummaries(summary.indicators);
        const preferred = inds.find((i) => i.key === "suicide_rate") ?? inds[0];
        if (preferred) setIndicatorKey(preferred.key);
      } catch (e) {
        setBootError(e instanceof Error ? e.message : "Failed to load.");
      }
    })();
  }, []);

  // When indicator changes: load its country list and seed a sensible default.
  useEffect(() => {
    if (!indicatorKey) return;
    let cancelled = false;
    (async () => {
      try {
        const list = await api.getCountries(indicatorKey);
        if (cancelled) return;
        setAvailable(list);
        const codes = new Set(list.map((c) => c.iso3));
        setCountries((prev) => {
          const kept = prev.filter((c) => codes.has(c));
          if (kept.length) return kept;
          return DEFAULT_COUNTRIES.filter((c) => codes.has(c)).slice(0, MAX_COUNTRIES);
        });
      } catch (e) {
        if (!cancelled) setChartError(e instanceof Error ? e.message : "Failed.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [indicatorKey]);

  // Fetch the series whenever the indicator or country set changes.
  useEffect(() => {
    if (!indicatorKey || countries.length === 0) {
      setSeries(null);
      return;
    }
    let cancelled = false;
    setLoadingChart(true);
    setChartError(null);
    (async () => {
      try {
        const data = await api.getSeries(indicatorKey, countries);
        if (!cancelled) setSeries(data);
      } catch (e) {
        if (!cancelled) {
          setChartError(
            e instanceof ApiError ? e.message : "Could not load the chart data.",
          );
        }
      } finally {
        if (!cancelled) setLoadingChart(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [indicatorKey, countries]);

  const currentSummary = useMemo(
    () => summaries.find((s) => s.indicator_key === indicatorKey),
    [summaries, indicatorKey],
  );
  const isSnapshot =
    currentSummary?.year_min != null &&
    currentSummary.year_min === currentSummary.year_max;

  if (bootError) {
    return (
      <div className="container">
        <div className="error-box">
          <strong>Couldn’t reach the Pulse API.</strong>
          <p style={{ margin: "8px 0 0" }}>{bootError}</p>
          <p style={{ margin: "8px 0 0", fontSize: "0.86rem" }}>
            Start the backend with{" "}
            <code>uvicorn app.main:app --reload</code> in <code>backend/</code>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <section className="hero">
        <h1>The state of mental health &amp; well-being, in public data</h1>
        <p>
          Explore aggregate, country-level indicators from the World Health
          Organization, the World Bank and Our World in Data. Every figure is
          public, licensed, and traceable to its source.
        </p>
      </section>

      <div className="stat-grid">
        {summaries.map((s) => (
          <StatCard
            key={s.indicator_key}
            summary={s}
            selected={s.indicator_key === indicatorKey}
            onClick={() => setIndicatorKey(s.indicator_key)}
          />
        ))}
      </div>

      <div className="card panel">
        <div className="controls">
          <IndicatorPicker
            indicators={indicators}
            value={indicatorKey}
            onChange={setIndicatorKey}
          />
          <CountryPicker
            available={available}
            selected={countries}
            onChange={setCountries}
            max={MAX_COUNTRIES}
          />
        </div>
      </div>

      <div className="card chart-card">
        <div className="chart-head">
          <div>
            <h2>{series?.indicator.name ?? currentSummary?.name ?? "—"}</h2>
            <div className="sub">
              {currentSummary
                ? `${shortUnit(currentSummary.unit)} · ${currentSummary.countries} countries · ${currentSummary.year_min}–${currentSummary.year_max}`
                : ""}
            </div>
          </div>
        </div>

        {isSnapshot && (
          <div className="notice">
            ⓘ This indicator is a single-year snapshot ({currentSummary?.year_min}),
            shown as a country comparison rather than a trend.
          </div>
        )}

        {loadingChart && (
          <div className="state">
            <div className="spinner" />
            Loading data…
          </div>
        )}
        {!loadingChart && chartError && (
          <div className="error-box">{chartError}</div>
        )}
        {!loadingChart && !chartError && countries.length === 0 && (
          <div className="state">Add a country above to chart this indicator.</div>
        )}
        {!loadingChart && !chartError && series && countries.length > 0 && (
          <>
            <TrendChart data={series} />
            <ExplainPanel indicatorKey={indicatorKey} countries={countries} />
            <SourceBadge source={series.source} />
          </>
        )}
      </div>
    </div>
  );
}
