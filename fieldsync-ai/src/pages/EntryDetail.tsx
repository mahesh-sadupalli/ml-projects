import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Trash2,
  MapPin,
  Clock,
  Tag,
  Brain,
  AlertTriangle,
  CheckCircle2,
  Edit3,
} from 'lucide-react';
import { useEntry } from '../hooks/useDatabase';
import { deleteEntry } from '../lib/store';

const priorityConfig: Record<string, { color: string; bg: string; label: string }> = {
  critical: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.1)', label: 'CRITICAL' },
  high: { color: '#ff9500', bg: 'rgba(255,149,0,0.1)', label: 'HIGH' },
  medium: { color: '#ffcc00', bg: 'rgba(255,204,0,0.1)', label: 'MEDIUM' },
  low: { color: '#34c759', bg: 'rgba(52,199,89,0.1)', label: 'LOW' },
};

const sentimentConfig: Record<string, { color: string; label: string }> = {
  positive: { color: '#34c759', label: 'Positive' },
  neutral: { color: '#8e8e93', label: 'Neutral' },
  negative: { color: '#ff3b5c', label: 'Negative' },
  urgent: { color: '#ff9500', label: 'Urgent' },
};

export default function EntryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { entry, loading } = useEntry(id);

  if (loading) return <div className="page-loading">Loading...</div>;
  if (!entry) return <div className="page-loading">Entry not found</div>;

  const prio = priorityConfig[entry.ai_priority] || priorityConfig.low;
  const sent = sentimentConfig[entry.ai_sentiment] || sentimentConfig.neutral;
  const tags: string[] = (() => {
    try { return JSON.parse(entry.tags || '[]'); } catch { return []; }
  })();

  const handleDelete = async () => {
    if (confirm('Delete this entry? This cannot be undone.')) {
      await deleteEntry(entry.id);
      navigate('/entries');
    }
  };

  return (
    <div className="entry-detail">
      <div className="detail-topbar">
        <Link to="/entries" className="btn-ghost">
          <ArrowLeft size={16} /> Back
        </Link>
        <div className="detail-actions">
          <button className="btn-ghost btn-danger" onClick={handleDelete}>
            <Trash2 size={16} /> Delete
          </button>
        </div>
      </div>

      <div className="detail-layout">
        {/* Main Content */}
        <div className="detail-main">
          <div className="detail-header">
            <span className="entry-category">{entry.category}</span>
            <h1 className="detail-title">{entry.title}</h1>
            <div className="detail-meta">
              <span><Clock size={14} /> {new Date(entry.created_at).toLocaleString()}</span>
              {entry.location_name && <span><MapPin size={14} /> {entry.location_name}</span>}
            </div>
          </div>

          <div className="detail-content">
            <h3 className="content-label">Observation</h3>
            <div className="content-body">{entry.content}</div>
          </div>

          {tags.length > 0 && (
            <div className="detail-tags">
              <h3 className="content-label">Tags</h3>
              <div className="tags-list">
                {tags.map(t => (
                  <span key={t} className="tag"><Tag size={10} />{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* AI Sidebar */}
        <div className="detail-sidebar">
          <div className="ai-panel">
            <h3 className="ai-panel-title"><Brain size={16} /> AI Analysis</h3>

            <div className="ai-section">
              <span className="ai-section-label">Priority</span>
              <div className="ai-badge" style={{ color: prio.color, background: prio.bg }}>
                {entry.ai_priority === 'critical' || entry.ai_priority === 'high'
                  ? <AlertTriangle size={14} />
                  : <CheckCircle2 size={14} />}
                {prio.label}
              </div>
            </div>

            <div className="ai-section">
              <span className="ai-section-label">Sentiment</span>
              <div className="ai-badge" style={{ color: sent.color, background: `${sent.color}15` }}>
                {sent.label}
              </div>
            </div>

            <div className="ai-section">
              <span className="ai-section-label">AI Summary</span>
              <p className="ai-summary">{entry.ai_summary}</p>
            </div>

            <div className="ai-section">
              <span className="ai-section-label">Status</span>
              <span className={`status-pill status-${entry.status}`}>
                {entry.status}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
