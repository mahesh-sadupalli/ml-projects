import { useMemo } from 'react';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Lightbulb,
  Target,
} from 'lucide-react';
import { useEntries } from '../hooks/useDatabase';

export default function Insights() {
  const { entries, loading } = useEntries();

  const analysis = useMemo(() => {
    if (entries.length === 0) return null;

    // Category distribution
    const catCount: Record<string, number> = {};
    entries.forEach(e => { catCount[e.category] = (catCount[e.category] || 0) + 1; });
    const topCategory = Object.entries(catCount).sort((a, b) => b[1] - a[1])[0];

    // Priority analysis
    const critical = entries.filter(e => e.ai_priority === 'critical');
    const high = entries.filter(e => e.ai_priority === 'high');

    // Sentiment trend
    const positive = entries.filter(e => e.ai_sentiment === 'positive').length;
    const negative = entries.filter(e => e.ai_sentiment === 'negative').length;
    const sentimentRatio = entries.length > 0 ? ((positive / entries.length) * 100).toFixed(0) : '0';

    // Location clusters
    const locations: Record<string, number> = {};
    entries.forEach(e => { if (e.location_name) locations[e.location_name] = (locations[e.location_name] || 0) + 1; });
    const topLocations = Object.entries(locations).sort((a, b) => b[1] - a[1]).slice(0, 5);

    // Generate insights
    const insights: Array<{ type: string; icon: typeof Brain; color: string; title: string; body: string }> = [];

    if (critical.length > 0) {
      insights.push({
        type: 'alert',
        icon: AlertTriangle,
        color: '#ff3b5c',
        title: `${critical.length} Critical Alert${critical.length > 1 ? 's' : ''} Detected`,
        body: `Critical entries: ${critical.map(e => e.title).join(', ')}. These require immediate attention.`,
      });
    }

    if (topCategory) {
      insights.push({
        type: 'pattern',
        icon: BarChart3,
        color: '#6366f1',
        title: `"${topCategory[0]}" is Your Top Category`,
        body: `${topCategory[1]} of ${entries.length} entries (${((topCategory[1] / entries.length) * 100).toFixed(0)}%) fall under ${topCategory[0]}. This indicates a strong focus area.`,
      });
    }

    insights.push({
      type: 'sentiment',
      icon: TrendingUp,
      color: positive > negative ? '#34c759' : '#ff9500',
      title: `Sentiment: ${sentimentRatio}% Positive`,
      body: `Out of ${entries.length} entries, ${positive} are positive and ${negative} are negative. ${positive > negative ? 'Overall conditions are trending positively.' : 'There may be underlying issues to address.'}`,
    });

    if (high.length > 0) {
      insights.push({
        type: 'recommendation',
        icon: Lightbulb,
        color: '#ff9500',
        title: `${high.length} High Priority Items Pending`,
        body: `Consider escalating: ${high.slice(0, 3).map(e => e.title).join(', ')}${high.length > 3 ? ` and ${high.length - 3} more` : ''}.`,
      });
    }

    if (entries.length >= 5) {
      insights.push({
        type: 'milestone',
        icon: Target,
        color: '#06b6d4',
        title: 'Data Collection Milestone',
        body: `You've collected ${entries.length} field observations. The more data you collect, the more accurate AI patterns become.`,
      });
    }

    return { insights, topLocations, catCount, sentimentRatio, topCategory };
  }, [entries]);

  if (loading) return <div className="page-loading">Analyzing data...</div>;

  return (
    <div className="insights-page">
      <div className="page-header">
        <div>
          <h2 className="page-title">AI Insights</h2>
          <p className="page-subtitle">Patterns and intelligence from {entries.length} field observations</p>
        </div>
      </div>

      {!analysis || entries.length === 0 ? (
        <div className="empty-state-box">
          <Brain size={48} className="empty-icon" />
          <h4>Not enough data yet</h4>
          <p>Create field entries and AI will automatically discover patterns, anomalies, and actionable insights.</p>
        </div>
      ) : (
        <div className="insights-grid">
          {analysis.insights.map((insight, i) => (
            <div key={i} className="insight-card" style={{ '--accent': insight.color } as React.CSSProperties}>
              <div className="insight-icon" style={{ background: `${insight.color}15`, color: insight.color }}>
                <insight.icon size={20} />
              </div>
              <div className="insight-body">
                <h4 className="insight-title">{insight.title}</h4>
                <p className="insight-text">{insight.body}</p>
              </div>
              <span className="insight-type">{insight.type}</span>
            </div>
          ))}

          {/* Location Heatmap */}
          {analysis.topLocations.length > 0 && (
            <div className="insight-card wide">
              <div className="insight-icon" style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
                <BarChart3 size={20} />
              </div>
              <div className="insight-body">
                <h4 className="insight-title">Location Activity</h4>
                <div className="location-bars">
                  {analysis.topLocations.map(([loc, count]) => (
                    <div key={loc} className="loc-bar-row">
                      <span className="loc-name">{loc}</span>
                      <div className="loc-bar-track">
                        <div className="loc-bar-fill" style={{ width: `${(count / entries.length) * 100}%` }} />
                      </div>
                      <span className="loc-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
