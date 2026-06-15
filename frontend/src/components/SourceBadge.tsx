import type { Source } from "../api/types";

export default function SourceBadge({ source }: { source: Source }) {
  return (
    <div className="source-badge">
      <span>Source: {source.attribution}</span>
      <a
        className="license-pill"
        href={source.license_url}
        target="_blank"
        rel="noreferrer"
        title={source.notes || source.license}
      >
        {source.license}
      </a>
      <a href={source.url} target="_blank" rel="noreferrer">
        provider ↗
      </a>
      <span>· accessed {source.accessed_at}</span>
    </div>
  );
}
