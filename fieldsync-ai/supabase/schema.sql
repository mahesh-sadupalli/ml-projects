-- FieldSync AI - Supabase Database Schema
-- Run this in Supabase SQL Editor (supabase.com > your project > SQL Editor)

-- 1. Create tables

CREATE TABLE IF NOT EXISTS public.entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'General',
  tags JSONB DEFAULT '[]'::jsonb,
  location_lat DOUBLE PRECISION,
  location_lng DOUBLE PRECISION,
  location_name TEXT DEFAULT '',
  ai_summary TEXT DEFAULT '',
  ai_sentiment TEXT DEFAULT 'neutral',
  ai_priority TEXT DEFAULT 'low',
  status TEXT DEFAULT 'draft',
  media_urls JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT DEFAULT '',
  color TEXT DEFAULT '#6366f1',
  entry_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.ai_insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id UUID REFERENCES public.entries(id) ON DELETE CASCADE,
  insight_type TEXT NOT NULL,
  content TEXT NOT NULL,
  confidence DOUBLE PRECISION DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Enable Row Level Security

ALTER TABLE public.entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_insights ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies - users can only access their own data

CREATE POLICY "Users can view own entries"
  ON public.entries FOR SELECT
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own entries"
  ON public.entries FOR INSERT
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own entries"
  ON public.entries FOR UPDATE
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own entries"
  ON public.entries FOR DELETE
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can view own projects"
  ON public.projects FOR SELECT
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own projects"
  ON public.projects FOR INSERT
  WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own projects"
  ON public.projects FOR UPDATE
  USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own projects"
  ON public.projects FOR DELETE
  USING (auth.uid() = owner_id);

-- ai_insights: accessible if user owns the parent entry
CREATE POLICY "Users can view own insights"
  ON public.ai_insights FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.entries WHERE entries.id = ai_insights.entry_id AND entries.owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own insights"
  ON public.ai_insights FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.entries WHERE entries.id = ai_insights.entry_id AND entries.owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own insights"
  ON public.ai_insights FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.entries WHERE entries.id = ai_insights.entry_id AND entries.owner_id = auth.uid()
    )
  );

-- 4. Create the PowerSync publication (REQUIRED for PowerSync to work)

CREATE PUBLICATION powersync FOR TABLE
  public.entries,
  public.projects,
  public.ai_insights;

-- 5. Updated_at trigger

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER entries_updated_at
  BEFORE UPDATE ON public.entries
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Done! Your Supabase backend is ready for PowerSync.
