function extractNumbers(text) {
  const matches = text.match(/\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%?/g) || [];
  return new Set(matches.map((m) => m.replace(/[\s.,]/g, "")));
}

function highlightExcerpt(excerpt, answerText) {
  const numbers = extractNumbers(answerText);
  const parts = excerpt.split(/(\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%?)/g);

  return parts.map((part, i) => {
    const normalized = part.replace(/[\s.,]/g, "");
    const isMatch = normalized.length > 1 && numbers.has(normalized);
    return isMatch ? <mark key={i}>{part}</mark> : part;
  });
}

function similarityLabel(score) {
  if (score >= 60) return { text: "Élevée", className: "high" };
  if (score >= 30) return { text: "Moyenne", className: "medium" };
  return { text: "Faible", className: "low" };
}

export default function SourcePanel({ sources, answerText }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="source-panel">
      {sources.map((s, i) => {
        const label = similarityLabel(s.similarity);
        return (
          <div className="source-card" key={i}>
            <div className="source-card-head">
              <span className="source-filename">{s.filename}</span>
              <span className="source-meta">page {s.page} · {s.type}</span>
              <span className={`similarity-tag ${label.className}`}>
                Similarité {label.text} · {s.similarity}%
              </span>
            </div>
            <div className="source-excerpt">{highlightExcerpt(s.excerpt, answerText)}</div>
          </div>
        );
      })}
    </div>
  );
}