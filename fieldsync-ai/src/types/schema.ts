import { column, Schema, Table } from '@powersync/web';

const entries = new Table({
  id: column.text,
  title: column.text,
  content: column.text,
  category: column.text,
  tags: column.text, // JSON array as string
  location_lat: column.real,
  location_lng: column.real,
  location_name: column.text,
  ai_summary: column.text,
  ai_sentiment: column.text,
  ai_priority: column.text,
  status: column.text, // draft | synced | flagged
  media_urls: column.text, // JSON array as string
  created_at: column.text,
  updated_at: column.text,
  owner_id: column.text,
});

const projects = new Table({
  id: column.text,
  name: column.text,
  description: column.text,
  color: column.text,
  entry_count: column.integer,
  created_at: column.text,
  owner_id: column.text,
});

const ai_insights = new Table({
  id: column.text,
  entry_id: column.text,
  insight_type: column.text, // summary | pattern | anomaly | suggestion
  content: column.text,
  confidence: column.real,
  created_at: column.text,
});

export const AppSchema = new Schema({ entries, projects, ai_insights });

export type Entry = {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string;
  location_lat: number | null;
  location_lng: number | null;
  location_name: string;
  ai_summary: string;
  ai_sentiment: string;
  ai_priority: string;
  status: string;
  media_urls: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
};

export type Project = {
  id: string;
  name: string;
  description: string;
  color: string;
  entry_count: number;
  created_at: string;
  owner_id: string;
};

export type AiInsight = {
  id: string;
  entry_id: string;
  insight_type: string;
  content: string;
  confidence: number;
  created_at: string;
};
