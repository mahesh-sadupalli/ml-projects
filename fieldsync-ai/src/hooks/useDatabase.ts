import { useState, useEffect, useCallback } from 'react';
import type { Entry } from '../types/schema';
import * as store from '../lib/store';

export function useEntries() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const data = await store.getAllEntries();
    setEntries(data);
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { entries, loading, refresh };
}

export function useEntry(id: string | undefined) {
  const [entry, setEntry] = useState<Entry | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) { setLoading(false); return; }
    store.getEntry(id).then(e => { setEntry(e); setLoading(false); });
  }, [id]);

  return { entry, loading };
}

export function useSearch(query: string) {
  const [results, setResults] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query.trim()) { setResults([]); return; }
    setLoading(true);
    const timer = setTimeout(async () => {
      const data = await store.searchEntries(query);
      setResults(data);
      setLoading(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return { results, loading };
}

export function useStats() {
  const [stats, setStats] = useState<Awaited<ReturnType<typeof store.getStats>> | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const data = await store.getStats();
    setStats(data);
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { stats, loading, refresh };
}
