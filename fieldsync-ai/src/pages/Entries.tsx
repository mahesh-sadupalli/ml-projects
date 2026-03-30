import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { PlusCircle, Filter, SortAsc } from 'lucide-react';
import EntryCard from '../components/EntryCard';
import { useEntries, useSearch } from '../hooks/useDatabase';

export default function Entries() {
  const [searchParams] = useSearchParams();
  const searchQ = searchParams.get('q') || '';
  const { entries, loading } = useEntries();
  const { results: searchResults } = useSearch(searchQ);
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [sortBy, setSortBy] = useState<'date' | 'priority'>('date');

  const data = searchQ ? searchResults : entries;

  const categories = useMemo(() => {
    const cats = new Set(data.map(e => e.category));
    return ['all', ...Array.from(cats)];
  }, [data]);

  const filtered = useMemo(() => {
    let result = [...data];
    if (filterCategory !== 'all') result = result.filter(e => e.category === filterCategory);
    if (filterPriority !== 'all') result = result.filter(e => e.ai_priority === filterPriority);
    if (sortBy === 'priority') {
      const order = { critical: 0, high: 1, medium: 2, low: 3 };
      result.sort((a, b) => (order[a.ai_priority as keyof typeof order] ?? 4) - (order[b.ai_priority as keyof typeof order] ?? 4));
    }
    return result;
  }, [data, filterCategory, filterPriority, sortBy]);

  return (
    <div className="entries-page">
      <div className="page-header">
        <div>
          <h2 className="page-title">
            {searchQ ? `Search: "${searchQ}"` : 'All Entries'}
          </h2>
          <p className="page-subtitle">{filtered.length} field observations</p>
        </div>
        <Link to="/new" className="btn-primary">
          <PlusCircle size={16} /> New Entry
        </Link>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <Filter size={14} />
          <select className="filter-select" value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
            {categories.map(c => <option key={c} value={c}>{c === 'all' ? 'All Categories' : c}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <select className="filter-select" value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div className="filter-group">
          <SortAsc size={14} />
          <select className="filter-select" value={sortBy} onChange={e => setSortBy(e.target.value as 'date' | 'priority')}>
            <option value="date">Newest First</option>
            <option value="priority">Priority</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="page-loading">Loading entries...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state-box">
          <h4>No entries found</h4>
          <p>Create your first field observation to get started.</p>
          <Link to="/new" className="btn-primary" style={{ marginTop: 16 }}>
            <PlusCircle size={16} /> Create Entry
          </Link>
        </div>
      ) : (
        <div className="entries-grid">
          {filtered.map(entry => (
            <EntryCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
