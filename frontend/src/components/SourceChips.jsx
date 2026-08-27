import { useState } from "react";
import { FileText } from "lucide-react";

function extractNumbers(text) {
  const matches = text.match(/\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%?/g) || [];
  return new Set(matches.map((m) => m.replace(/[\s.,]/g, "")));
}

function highlight(excerpt, answerText) {
  const numbers = extractNumbers(answerText);
  const parts = excerpt.split(/(\d{1,3}(?:[\s.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?%?)/g);
  return parts.map((part, i) => {
    const normalized = part.replace(/[\s.,]/g, "");
    return normalized.length > 1 && numbers.has(normalized) ? <mark key={i}>{part}</mark> : part;
  });
}

function similarityClass(score) {
  if (score >= 60) return "badge-indexed";
  if (score >= 30) return "badge-uploaded";
  return "badge-error";
}

export default function SourceChips({ sources, answerText }) {
  const [openIndex, setOpenIndex] = useState(null);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="answer-block">
      <div className="answer-eyebrow">Sources</div>
      <div className="source-chip-row">
        {sources.map((s, i) => (
          <span
            className="source-chip"
            key={i}
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
          >
            <FileText size={12} /> {s.filename} · Page {s.page}
            <span className={`badge ${similarityClass(s.similarity)}`} style={{ marginLeft: 4 }}>
              {s.similarity}%
            </span>
          </span>
        ))}
      </div>
      {openIndex !== null && (
        <div className="source-detail">{highlight(sources[openIndex].excerpt, answerText)}</div>
      )}
    </div>
  );
}