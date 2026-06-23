import { useEffect, useState } from 'react';

type Props<T> = {
  title: string;
  load: () => Promise<T>;
  render: (data: T) => JSX.Element;
};

export default function ResourcePage<T>({ title, load, render }: Props<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let active = true;
    load()
      .then((value) => {
        if (active) {
          setData(value);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : 'API request failed');
        }
      });
    return () => {
      active = false;
    };
  }, [load]);

  return (
    <section className="workspace standalone-page">
      <header className="topbar">
        <h1>{title}</h1>
      </header>
      {error ? <section className="state-panel error-state">{error}</section> : null}
      {!data && !error ? <section className="state-panel">Loading...</section> : null}
      {data ? render(data) : null}
    </section>
  );
}
