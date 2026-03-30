import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NewEntry from './pages/NewEntry';
import Entries from './pages/Entries';
import EntryDetail from './pages/EntryDetail';
import Insights from './pages/Insights';
import Login from './pages/Login';
import { getDb, connectSync } from './lib/powersync';
import { getSession } from './lib/auth';
import { supabase } from './lib/supabase';

type AuthState = 'loading' | 'unauthenticated' | 'authenticated' | 'offline';

export default function App() {
  const [ready, setReady] = useState(false);
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [error, setError] = useState<string | null>(null);

  // Init local database
  useEffect(() => {
    getDb()
      .then(() => setReady(true))
      .catch(err => {
        console.error('DB init failed:', err);
        setError(err.message);
      });
  }, []);

  // Check auth state
  useEffect(() => {
    if (!ready) return;

    const powersyncUrl = import.meta.env.VITE_POWERSYNC_URL;
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;

    // If no credentials configured, go straight to offline mode
    if (!powersyncUrl || !supabaseUrl) {
      setAuthState('offline');
      return;
    }

    getSession().then(session => {
      if (session) {
        setAuthState('authenticated');
        connectSync().catch(console.warn);
      } else {
        setAuthState('unauthenticated');
      }
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAuthState('authenticated');
        connectSync().catch(console.warn);
      } else {
        setAuthState('unauthenticated');
      }
    });

    return () => subscription.unsubscribe();
  }, [ready]);

  if (error) {
    return (
      <div className="init-screen error">
        <h2>Initialization Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!ready || authState === 'loading') {
    return (
      <div className="init-screen">
        <div className="init-loader" />
        <h2>FieldSync AI</h2>
        <p>Initializing local database...</p>
      </div>
    );
  }

  if (authState === 'unauthenticated') {
    return (
      <Login
        onAuth={() => setAuthState('authenticated')}
        onSkip={() => setAuthState('offline')}
      />
    );
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entries" element={<Entries />} />
          <Route path="/new" element={<NewEntry />} />
          <Route path="/entry/:id" element={<EntryDetail />} />
          <Route path="/insights" element={<Insights />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
