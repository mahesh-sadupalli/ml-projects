import { getDb, generateId } from './powersync';
import { analyzeLocally } from './ai';
import { supabase } from './supabase';
import type { Entry, Project, AiInsight } from '../types/schema';

async function getOwnerId(): Promise<string> {
  try {
    const { data: { user } } = await supabase.auth.getUser();
    return user?.id || 'local-user';
  } catch {
    return 'local-user';
  }
}

// ── Entries ──

export async function createEntry(data: {
  title: string;
  content: string;
  category?: string;
  location_lat?: number;
  location_lng?: number;
  location_name?: string;
  projectId?: string;
}): Promise<Entry> {
  const db = await getDb();
  const id = generateId();
  const now = new Date().toISOString();

  // Run AI analysis locally
  const analysis = analyzeLocally(data.title, data.content);

  const entry: Entry = {
    id,
    title: data.title,
    content: data.content,
    category: data.category || analysis.suggestedCategory,
    tags: JSON.stringify(analysis.suggestedTags),
    location_lat: data.location_lat || null,
    location_lng: data.location_lng || null,
    location_name: data.location_name || '',
    ai_summary: analysis.summary,
    ai_sentiment: analysis.sentiment,
    ai_priority: analysis.priority,
    status: 'draft',
    media_urls: '[]',
    created_at: now,
    updated_at: now,
    owner_id: await getOwnerId(),
  };

  await db.execute(
    `INSERT INTO entries (id, title, content, category, tags, location_lat, location_lng, location_name, ai_summary, ai_sentiment, ai_priority, status, media_urls, created_at, updated_at, owner_id)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [entry.id, entry.title, entry.content, entry.category, entry.tags, entry.location_lat, entry.location_lng, entry.location_name, entry.ai_summary, entry.ai_sentiment, entry.ai_priority, entry.status, entry.media_urls, entry.created_at, entry.updated_at, entry.owner_id]
  );

  // Store AI insight
  await createInsight(id, 'summary', analysis.summary, 0.85);

  return entry;
}

export async function getAllEntries(): Promise<Entry[]> {
  const db = await getDb();
  const result = await db.getAll<Entry>('SELECT * FROM entries ORDER BY created_at DESC');
  return result;
}

export async function getEntry(id: string): Promise<Entry | null> {
  const db = await getDb();
  const result = await db.getOptional<Entry>('SELECT * FROM entries WHERE id = ?', [id]);
  return result || null;
}

export async function updateEntry(id: string, data: Partial<Entry>): Promise<void> {
  const db = await getDb();
  const fields = Object.keys(data).filter(k => k !== 'id');
  const values = fields.map(k => (data as Record<string, unknown>)[k]);
  const sets = fields.map(k => `${k} = ?`).join(', ');
  await db.execute(`UPDATE entries SET ${sets}, updated_at = ? WHERE id = ?`, [...values, new Date().toISOString(), id]);
}

export async function deleteEntry(id: string): Promise<void> {
  const db = await getDb();
  await db.execute('DELETE FROM entries WHERE id = ?', [id]);
  await db.execute('DELETE FROM ai_insights WHERE entry_id = ?', [id]);
}

export async function getEntriesByCategory(category: string): Promise<Entry[]> {
  const db = await getDb();
  return db.getAll<Entry>('SELECT * FROM entries WHERE category = ? ORDER BY created_at DESC', [category]);
}

export async function searchEntries(query: string): Promise<Entry[]> {
  const db = await getDb();
  const q = `%${query}%`;
  return db.getAll<Entry>(
    'SELECT * FROM entries WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? OR category LIKE ? ORDER BY created_at DESC',
    [q, q, q, q]
  );
}

// ── Projects ──

export async function createProject(name: string, description: string, color: string): Promise<Project> {
  const db = await getDb();
  const id = generateId();
  const now = new Date().toISOString();
  const project: Project = { id, name, description, color, entry_count: 0, created_at: now, owner_id: 'local-user' };
  await db.execute(
    'INSERT INTO projects (id, name, description, color, entry_count, created_at, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [project.id, project.name, project.description, project.color, 0, project.created_at, project.owner_id]
  );
  return project;
}

export async function getAllProjects(): Promise<Project[]> {
  const db = await getDb();
  return db.getAll<Project>('SELECT * FROM projects ORDER BY created_at DESC');
}

// ── AI Insights ──

export async function createInsight(entryId: string, type: string, content: string, confidence: number): Promise<void> {
  const db = await getDb();
  const id = generateId();
  await db.execute(
    'INSERT INTO ai_insights (id, entry_id, insight_type, content, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?)',
    [id, entryId, type, content, confidence, new Date().toISOString()]
  );
}

export async function getInsightsForEntry(entryId: string): Promise<AiInsight[]> {
  const db = await getDb();
  return db.getAll<AiInsight>('SELECT * FROM ai_insights WHERE entry_id = ? ORDER BY created_at DESC', [entryId]);
}

// ── Stats ──

export async function getStats() {
  const db = await getDb();
  const totalEntries = await db.getOptional<{ count: number }>('SELECT COUNT(*) as count FROM entries');
  const categories = await db.getAll<{ category: string; count: number }>(
    'SELECT category, COUNT(*) as count FROM entries GROUP BY category ORDER BY count DESC'
  );
  const priorities = await db.getAll<{ ai_priority: string; count: number }>(
    'SELECT ai_priority, COUNT(*) as count FROM entries GROUP BY ai_priority'
  );
  const sentiments = await db.getAll<{ ai_sentiment: string; count: number }>(
    'SELECT ai_sentiment, COUNT(*) as count FROM entries GROUP BY ai_sentiment'
  );
  const recentEntries = await db.getAll<Entry>('SELECT * FROM entries ORDER BY created_at DESC LIMIT 5');

  return {
    totalEntries: totalEntries?.count || 0,
    categories,
    priorities,
    sentiments,
    recentEntries,
  };
}
