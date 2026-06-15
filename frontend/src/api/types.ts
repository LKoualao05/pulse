// Types mirroring the FastAPI response models (app/schemas.py).

export interface Source {
  key: string;
  name: string;
  url: string;
  license: string;
  license_url: string;
  attribution: string;
  accessed_at: string;
  notes: string;
}

export interface Indicator {
  key: string;
  source_key: string;
  name: string;
  unit: string;
  category: string;
  description: string;
  value_type: "numeric" | "categorical";
}

export interface SeriesPoint {
  year: number;
  value: number | null;
  value_text: string | null;
}

export interface CountrySeries {
  country_iso3: string;
  country_name: string;
  points: SeriesPoint[];
}

export interface SeriesResponse {
  indicator: Indicator;
  source: Source;
  series: CountrySeries[];
}

export interface CountryRef {
  iso3: string;
  name: string;
}

export interface IndicatorSummary {
  indicator_key: string;
  name: string;
  unit: string;
  category: string;
  value_type: string;
  observation_count: number;
  countries: number;
  year_min: number | null;
  year_max: number | null;
  latest_year: number | null;
  global_latest_mean: number | null;
  top_country: string | null;
  top_value: number | null;
}

export interface SummaryResponse {
  generated_at: string;
  indicators: IndicatorSummary[];
}

// Phase 3 — the Claude "Explain this chart" endpoint.
export interface ExplainResponse {
  summary: string;
  model: string;
  generated_by: "claude" | "fallback";
}
