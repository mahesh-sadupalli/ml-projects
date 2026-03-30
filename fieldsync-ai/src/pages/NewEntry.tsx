import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Send,
  MapPin,
  Sparkles,
  Loader2,
  Tag,
  AlertTriangle,
} from 'lucide-react';
import { createEntry } from '../lib/store';
import { analyzeLocally } from '../lib/ai';

const CATEGORIES = ['General', 'Infrastructure', 'Health', 'Environment', 'Agriculture', 'Community', 'Safety'];

export default function NewEntry() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [locationName, setLocationName] = useState('');
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<ReturnType<typeof analyzeLocally> | null>(null);

  // Live AI preview as user types
  const handleContentChange = (val: string) => {
    setContent(val);
    if (title.length > 3 && val.length > 20) {
      const analysis = analyzeLocally(title, val);
      setPreview(analysis);
      if (!category) setCategory(analysis.suggestedCategory);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setSaving(true);
    try {
      const entry = await createEntry({
        title: title.trim(),
        content: content.trim(),
        category: category || undefined,
        location_name: locationName || undefined,
      });
      navigate(`/entry/${entry.id}`);
    } catch (err) {
      console.error('Failed to save:', err);
      setSaving(false);
    }
  };

  return (
    <div className="new-entry-page">
      <div className="page-header">
        <div>
          <h2 className="page-title">New Field Entry</h2>
          <p className="page-subtitle">Record your observation — AI analyzes as you type</p>
        </div>
      </div>

      <div className="new-entry-layout">
        {/* Form */}
        <form className="entry-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Title</label>
            <input
              type="text"
              className="form-input"
              placeholder="Brief title for this observation..."
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Observation Details</label>
            <textarea
              className="form-textarea"
              placeholder="Describe what you observed in detail. Include conditions, measurements, context..."
              rows={8}
              value={content}
              onChange={e => handleContentChange(e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Category</label>
              <select
                className="form-select"
                value={category}
                onChange={e => setCategory(e.target.value)}
              >
                <option value="">Auto-detect</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label"><MapPin size={14} /> Location</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Site B, North sector"
                value={locationName}
                onChange={e => setLocationName(e.target.value)}
              />
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={saving || !title.trim() || !content.trim()}>
            {saving ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
            {saving ? 'Saving...' : 'Save Entry'}
          </button>
        </form>

        {/* Live AI Preview */}
        <div className="ai-preview-panel">
          <div className="ai-preview-header">
            <Sparkles size={16} />
            <span>Live AI Analysis</span>
          </div>

          {preview ? (
            <div className="ai-preview-content">
              <div className="ai-field">
                <span className="ai-field-label">Category</span>
                <span className="ai-field-value cat-badge">{preview.suggestedCategory}</span>
              </div>

              <div className="ai-field">
                <span className="ai-field-label">Priority</span>
                <span className={`ai-field-value priority-badge priority-${preview.priority}`}>
                  {preview.priority === 'critical' || preview.priority === 'high' ? <AlertTriangle size={12} /> : null}
                  {preview.priority.toUpperCase()}
                </span>
              </div>

              <div className="ai-field">
                <span className="ai-field-label">Sentiment</span>
                <span className={`ai-field-value sentiment-badge sentiment-${preview.sentiment}`}>
                  {preview.sentiment}
                </span>
              </div>

              <div className="ai-field">
                <span className="ai-field-label">Summary</span>
                <p className="ai-summary-text">{preview.summary}</p>
              </div>

              <div className="ai-field">
                <span className="ai-field-label">Suggested Tags</span>
                <div className="ai-tags">
                  {preview.suggestedTags.map(t => (
                    <span key={t} className="ai-tag"><Tag size={10} />{t}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="ai-preview-empty">
              <Sparkles size={32} className="ai-empty-icon" />
              <p>Start typing your observation and AI will analyze it in real-time</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
