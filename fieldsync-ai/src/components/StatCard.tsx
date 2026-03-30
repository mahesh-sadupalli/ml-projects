import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  color: string;
  subtitle?: string;
}

export default function StatCard({ label, value, icon: Icon, color, subtitle }: StatCardProps) {
  return (
    <div className="stat-card" style={{ '--accent': color } as React.CSSProperties}>
      <div className="stat-card-icon" style={{ background: `${color}15`, color }}>
        <Icon size={20} />
      </div>
      <div className="stat-card-info">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-value">{value}</span>
        {subtitle && <span className="stat-card-sub">{subtitle}</span>}
      </div>
    </div>
  );
}
