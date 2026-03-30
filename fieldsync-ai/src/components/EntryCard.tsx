import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  Tag,
  ArrowRight,
} from 'lucide-react';
import type { Entry } from '../types/schema';

const priorityConfig = {
  critical: { color: '#ff3b5c', bg: 'rgba(255,59,92,0.1)', icon: AlertTriangle, label: 'CRITICAL' },
  high: { color: '#ff9500', bg: 'rgba(255,149,0,0.1)', icon: AlertTriangle, label: 'HIGH' },
  medium: { color: '#ffcc00', bg: 'rgba(255,204,0,0.1)', icon: Clock, label: 'MEDIUM' },
  low: { color: '#34c759', bg: 'rgba(52,199,89,0.1)', icon: CheckCircle2, label: 'LOW' },
};

const sentimentEmoji: Record<string, string> = {
  positive: '&#x1f7e2;',
  neutral: '&#x26aa;',
  negative: '&#x1f534;',
  urgent: '&#x1f534;',
};

export default function EntryCard({ entry }: { entry: Entry }) {
  const prio = priorityConfig[entry.ai_priority as keyof typeof priorityConfig] || priorityConfig.low;
  const PrioIcon = prio.icon;
  const tags: string[] = (() => {
    try { return JSON.parse(entry.tags || '[]'); } catch { return []; }
  })();
  const timeAgo = getTimeAgo(entry.created_at);

  return (
    <Link to={`/entry/${entry.id}`} className="entry-card">
      <div className="entry-card-priority-bar" style={{ background: prio.color }} />
      <div className="entry-card-body">
        <div className="entry-card-top">
          <span className="entry-category">{entry.category}</span>
          <span className="entry-priority-badge" style={{ color: prio.color, background: prio.bg }}>
            <PrioIcon size={12} />
            {prio.label}
          </span>
        </div>

        <h3 className="entry-title">{entry.title}</h3>

        <p className="entry-summary">{entry.ai_summary || entry.content.slice(0, 120)}</p>

        <div className="entry-tags">
          {tags.slice(0, 3).map(t => (
            <span key={t} className="tag"><Tag size={10} />{t}</span>
          ))}
        </div>

        <div className="entry-card-footer">
          <span className="entry-time"><Clock size={12} />{timeAgo}</span>
          {entry.location_name && (
            <span className="entry-location"><MapPin size={12} />{entry.location_name}</span>
          )}
          <span className="entry-view-link">View <ArrowRight size={12} /></span>
        </div>
      </div>
    </Link>
  );
}

function getTimeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}
