import { useState } from 'react';
import {
  FileText,
  AlertTriangle,
  TrendingUp,
  Brain,
  Activity,
  BarChart3,
  Database,
  Loader2,
} from 'lucide-react';
import StatCard from '../components/StatCard';
import EntryCard from '../components/EntryCard';
import { useStats } from '../hooks/useDatabase';
import { seedDatabase } from '../lib/seed';

export default function Dashboard() {
  const { stats, loading, refresh } = useStats();
  const [seeding, setSeeding] = useState(false);

  const handleSeed = async () => {
    setSeeding(true);
    await seedDatabase();
    await refresh();
    setSeeding(false);
  };

  if (loading || !stats) {
    return <div className="page-loading">Initializing FieldSync AI...</div>;
  }

  const criticalCount = stats.priorities.find(p => p.ai_priority === 'critical')?.count || 0;
  const highCount = stats.priorities.find(p => p.ai_priority === 'high')?.count || 0;

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h2 className="page-title">Command Dashboard</h2>
          <p className="page-subtitle">Real-time field intelligence overview</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard
          label="Total Entries"
          value={stats.totalEntries}
          icon={FileText}
          color="#6366f1"
          subtitle="field observations"
        />
        <StatCard
          label="Critical Alerts"
          value={criticalCount + highCount}
          icon={AlertTriangle}
          color="#ef4444"
          subtitle="need attention"
        />
        <StatCard
          label="Categories"
          value={stats.categories.length}
          icon={BarChart3}
          color="#06b6d4"
          subtitle="active categories"
        />
        <StatCard
          label="AI Insights"
          value={stats.totalEntries}
          icon={Brain}
          color="#8b5cf6"
          subtitle="auto-analyzed"
        />
      </div>

      {/* Charts Row */}
      <div className="dashboard-grid">
        {/* Category Breakdown */}
        <div className="dash-panel">
          <h3 className="panel-title"><BarChart3 size={16} /> Category Breakdown</h3>
          {stats.categories.length === 0 ? (
            <p className="empty-text">No entries yet. Create your first field observation!</p>
          ) : (
            <div className="category-bars">
              {stats.categories.map(cat => {
                const pct = stats.totalEntries > 0 ? (cat.count / stats.totalEntries) * 100 : 0;
                return (
                  <div key={cat.category} className="cat-bar-row">
                    <span className="cat-bar-label">{cat.category}</span>
                    <div className="cat-bar-track">
                      <div
                        className="cat-bar-fill"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="cat-bar-count">{cat.count}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Priority Distribution */}
        <div className="dash-panel">
          <h3 className="panel-title"><Activity size={16} /> Priority Distribution</h3>
          {stats.priorities.length === 0 ? (
            <p className="empty-text">No data yet</p>
          ) : (
            <div className="priority-grid">
              {['critical', 'high', 'medium', 'low'].map(p => {
                const count = stats.priorities.find(x => x.ai_priority === p)?.count || 0;
                const colors: Record<string, string> = { critical: '#ff3b5c', high: '#ff9500', medium: '#ffcc00', low: '#34c759' };
                return (
                  <div key={p} className="priority-item">
                    <div className="priority-ring" style={{ borderColor: colors[p], color: colors[p] }}>
                      {count}
                    </div>
                    <span className="priority-label">{p}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sentiment Overview */}
        <div className="dash-panel">
          <h3 className="panel-title"><TrendingUp size={16} /> Sentiment Analysis</h3>
          {stats.sentiments.length === 0 ? (
            <p className="empty-text">No data yet</p>
          ) : (
            <div className="sentiment-list">
              {stats.sentiments.map(s => {
                const colors: Record<string, string> = { positive: '#34c759', neutral: '#8e8e93', negative: '#ff3b5c', urgent: '#ff9500' };
                const icons: Record<string, string> = { positive: '+', neutral: '~', negative: '-', urgent: '!' };
                return (
                  <div key={s.ai_sentiment} className="sentiment-item">
                    <div className="sentiment-dot" style={{ background: colors[s.ai_sentiment] || '#8e8e93' }}>
                      {icons[s.ai_sentiment] || '~'}
                    </div>
                    <span className="sentiment-name">{s.ai_sentiment}</span>
                    <span className="sentiment-count">{s.count}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Entries */}
      <div className="dash-section">
        <h3 className="section-title">Recent Field Entries</h3>
        {stats.recentEntries.length === 0 ? (
          <div className="empty-state-box">
            <Brain size={48} className="empty-icon" />
            <h4>No field entries yet</h4>
            <p>Start by creating your first field observation, or load demo data to explore the app.</p>
            <button className="btn-primary" style={{ marginTop: 16 }} onClick={handleSeed} disabled={seeding}>
              {seeding ? <Loader2 size={16} className="spin" /> : <Database size={16} />}
              {seeding ? 'Loading demo data...' : 'Load Demo Data (12 entries)'}
            </button>
          </div>
        ) : (
          <div className="entries-grid">
            {stats.recentEntries.map(entry => (
              <EntryCard key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
