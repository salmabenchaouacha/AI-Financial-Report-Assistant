function extractFigures(markdown) {
  const matches = [...markdown.matchAll(/\*\*([\d\s.,]{3,}%?)\*\*/g)];
  const seen = new Set();
  const figures = [];
  for (const m of matches) {
    const value = m[1].trim();
    if (seen.has(value) || figures.length >= 4) continue;
    seen.add(value);
    figures.push(value);
  }
  return figures;
}

export default function KeyFigures({ answerText }) {
  const figures = extractFigures(answerText);
  if (figures.length === 0) return null;

  return (
    <div className="answer-block">
      <div className="answer-eyebrow">Key figures</div>
      <div className="key-figures-grid">
        {figures.map((f, i) => (
          <div className="key-figure" key={i}>
            <div className="key-figure-value num">{f}</div>
            <div className="key-figure-label">Valeur relevée</div>
          </div>
        ))}
      </div>
    </div>
  );
}