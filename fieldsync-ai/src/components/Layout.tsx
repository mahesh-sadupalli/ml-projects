import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  List,
  Brain,
  Search,
  Wifi,
  WifiOff,
  Menu,
  X,
  Zap,
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/entries', icon: List, label: 'Entries' },
  { path: '/new', icon: PlusCircle, label: 'New Entry' },
  { path: '/insights', icon: Brain, label: 'AI Insights' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  window.addEventListener('online', () => setIsOnline(true));
  window.addEventListener('offline', () => setIsOnline(false));

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${mobileNavOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <Zap size={22} className="logo-icon" />
            <div>
              <h1 className="logo-text">FieldSync</h1>
              <span className="logo-sub">AI</span>
            </div>
          </div>
          <button className="mobile-close" onClick={() => setMobileNavOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => setMobileNavOpen(false)}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className={`sync-status ${isOnline ? 'online' : 'offline'}`}>
            {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
            <span>{isOnline ? 'Online — Ready to sync' : 'Offline — Local mode'}</span>
          </div>
          <div className="powersync-badge">
            Powered by PowerSync
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNavOpen(true)}>
            <Menu size={20} />
          </button>
          <div className="topbar-search">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search entries..."
              className="search-input"
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const val = (e.target as HTMLInputElement).value;
                  if (val) window.location.href = `/entries?q=${encodeURIComponent(val)}`;
                }
              }}
            />
          </div>
          <div className={`online-dot ${isOnline ? 'on' : 'off'}`} />
        </header>

        <div className="page-content">
          {children}
        </div>
      </main>

      {/* Mobile overlay */}
      {mobileNavOpen && <div className="mobile-overlay" onClick={() => setMobileNavOpen(false)} />}
    </div>
  );
}
