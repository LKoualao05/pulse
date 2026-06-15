import type {
  CountryRef,
  ExplainResponse,
  Indicator,
  SeriesResponse,
  Source,
  SummaryResponse,
} from "./types";

// In dev this is empty so requests go to /api and Vite proxies them to the
// backend. In production set VITE_API_BASE to the deployed API origin.
const BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Could not reach the Pulse API. Is the backend running?");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* ignore non-JSON bodies */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getSources: () => request<Source[]>("/api/sources"),
  getSummary: () => request<SummaryResponse>("/api/summary"),
  getIndicators: () => request<Indicator[]>("/api/indicators"),
  getCountries: (key: string) =>
    request<CountryRef[]>(`/api/indicators/${encodeURIComponent(key)}/countries`),
  getSeries: (key: string, countries: string[], yearFrom?: number) => {
    const params = new URLSearchParams();
    if (countries.length) params.set("countries", countries.join(","));
    if (yearFrom) params.set("year_from", String(yearFrom));
    const qs = params.toString();
    return request<SeriesResponse>(
      `/api/indicators/${encodeURIComponent(key)}/series${qs ? `?${qs}` : ""}`,
    );
  },
  explain: (key: string, countries: string[]) =>
    request<ExplainResponse>("/api/explain", {
      method: "POST",
      body: JSON.stringify({ indicator_key: key, countries }),
    }),
};
