import { useEffect, useState } from "react";

export default function LoadingMessage({ messages, interval = 1700 }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
    const id = setInterval(() => {
      setIndex((i) => (i + 1) % messages.length);
    }, interval);
    return () => clearInterval(id);
  }, [messages, interval]);

  return <span className="loading-ticker">{messages[index]}</span>;
}