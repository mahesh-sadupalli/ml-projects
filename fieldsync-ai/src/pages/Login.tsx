import { useState } from 'react';
import { Zap, LogIn, UserPlus, Loader2, Wifi, WifiOff } from 'lucide-react';
import { signIn, signUp } from '../lib/auth';

interface LoginProps {
  onAuth: () => void;
  onSkip: () => void;
}

export default function Login({ onAuth, onSkip }: LoginProps) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (mode === 'signup') {
        await signUp(email, password);
        setSuccess('Account created! Check your email to confirm, then log in.');
        setMode('login');
      } else {
        await signIn(email, password);
        onAuth();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="logo">
            <Zap size={28} className="logo-icon" />
            <div>
              <h1 className="logo-text" style={{ fontSize: 24 }}>FieldSync</h1>
              <span className="logo-sub">AI</span>
            </div>
          </div>
          <p className="login-tagline">Offline-first field intelligence, powered by AI</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="Min 6 characters"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          {error && <div className="login-error">{error}</div>}
          {success && <div className="login-success">{success}</div>}

          <button type="submit" className="btn-primary login-btn" disabled={loading}>
            {loading ? <Loader2 size={16} className="spin" /> :
              mode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />}
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="login-toggle">
          {mode === 'login' ? (
            <p>No account? <button className="link-btn" onClick={() => { setMode('signup'); setError(''); }}>Sign up</button></p>
          ) : (
            <p>Have an account? <button className="link-btn" onClick={() => { setMode('login'); setError(''); }}>Sign in</button></p>
          )}
        </div>

        <div className="login-divider"><span>or</span></div>

        <button className="btn-ghost login-skip" onClick={onSkip}>
          <WifiOff size={14} />
          Continue in offline-only mode
        </button>

        <p className="login-footnote">
          Sign in to enable cloud sync across devices via PowerSync + Supabase.
          Offline mode stores everything locally.
        </p>
      </div>
    </div>
  );
}
