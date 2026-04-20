import { useEffect, useState } from "react";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

type Health = { status: string; database_configured: boolean };

type ItemsResponse =
  | { items: { id: number; name: string }[]; detail?: string }
  | null;

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [items, setItems] = useState<ItemsResponse>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!apiBaseUrl) {
      setError("VITE_API_BASE_URL is not set. Configure it for local dev or deploy.");
      return;
    }

    const base = apiBaseUrl.replace(/\/$/, "");

    void (async () => {
      try {
        const h = await fetch(`${base}/health`);
        if (!h.ok) {
          throw new Error(`Health check failed: ${h.status}`);
        }
        setHealth((await h.json()) as Health);

        const i = await fetch(`${base}/api/items`);
        if (!i.ok) {
          throw new Error(`Items request failed: ${i.status}`);
        }
        setItems((await i.json()) as ItemsResponse);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Request failed");
      }
    })();
  }, []);

  return (
    <>
      <h1>Micro-SaaS template</h1>
      <p>React frontend talking to the FastAPI Lambda API.</p>

      {error ? (
        <div className="card error" role="alert">
          {error}
        </div>
      ) : null}

      {!error && health ? (
        <div className="card">
          <strong>API</strong>
          <p>
            Status: {health.status}
            <br />
            Database configured: {String(health.database_configured)}
          </p>
        </div>
      ) : null}

      {!error && items ? (
        <div className="card">
          <strong>Items</strong>
          {items.detail ? <p>{items.detail}</p> : null}
          {items.items.length === 0 ? (
            <p>No items yet.</p>
          ) : (
            <ul>
              {items.items.map((it) => (
                <li key={it.id}>
                  #{it.id} — {it.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </>
  );
}
