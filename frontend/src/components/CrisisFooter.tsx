// Crisis-resource information shown on every page, per the project's ethics
// rules. Non-intrusive but always present.
export default function CrisisFooter() {
  return (
    <aside className="crisis" role="note" aria-label="Crisis resources">
      <div className="container crisis-inner">
        <strong>Need support now?</strong>
        <span>
          US: call or text <strong>988</strong> (Suicide &amp; Crisis Lifeline).
        </span>
        <span>
          Outside the US, find a helpline at{" "}
          <a href="https://findahelpline.com" target="_blank" rel="noreferrer">
            findahelpline.com
          </a>
          .
        </span>
        <span>If you are in immediate danger, contact your local emergency number.</span>
      </div>
    </aside>
  );
}
