-- Migration: Create topic_briefings table for topic-specific briefings
-- File: 003_create_topic_briefings_table.sql

-- Create topic_briefings table
CREATE TABLE topic_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    title TEXT NOT NULL, -- Auto-generated title like "Biotechnology News - August 18, 2025"
    briefing_date DATE NOT NULL,
    briefing_time TIMESTAMPTZ NOT NULL DEFAULT now(), -- When briefing was created
    word_count INTEGER,
    duration_seconds INTEGER,
    text_content TEXT,
    audio_file_path TEXT,
    text_file_path TEXT,
    blurb TEXT, -- 2-sentence highlights summary
    metadata JSONB DEFAULT '{}', -- Additional briefing metadata (sources, article count, etc.)
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Ensure one topic briefing per user per topic per day
    UNIQUE(user_id, topic_id, briefing_date)
);

-- Add RLS policies for topic briefings
ALTER TABLE topic_briefings ENABLE ROW LEVEL SECURITY;

-- Users can only see their own topic briefings
CREATE POLICY "Users can view own topic briefings" ON topic_briefings
    FOR SELECT USING (auth.uid() = user_id);

-- Users can manage their own topic briefings
CREATE POLICY "Users can manage own topic briefings" ON topic_briefings
    FOR ALL USING (auth.uid() = user_id);

-- Create indexes for efficient querying
CREATE INDEX idx_topic_briefings_user_id ON topic_briefings(user_id);
CREATE INDEX idx_topic_briefings_topic_id ON topic_briefings(topic_id);
CREATE INDEX idx_topic_briefings_date ON topic_briefings(briefing_date);
CREATE INDEX idx_topic_briefings_user_date ON topic_briefings(user_id, briefing_date);
CREATE INDEX idx_topic_briefings_user_topic_date ON topic_briefings(user_id, topic_id, briefing_date);