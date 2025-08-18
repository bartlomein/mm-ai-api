-- Migration: Create topics table for stock market sectors and industries
-- File: 001_create_topics_table.sql

-- Create topics table
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE, -- "biotechnology", "artificial_intelligence", "renewable_energy" 
    display_name TEXT NOT NULL, -- "Biotechnology", "Artificial Intelligence", "Renewable Energy"
    category TEXT NOT NULL, -- "healthcare", "technology", "energy", "finance", "industrial", "consumer"
    description TEXT, -- Brief description of the topic/sector
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Add RLS policies for topics table
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;

-- Allow everyone to read active topics (for subscription selection)
CREATE POLICY "Everyone can view active topics" ON topics
    FOR SELECT USING (is_active = true);

-- Create indexes for efficient querying
CREATE INDEX idx_topics_category ON topics(category);
CREATE INDEX idx_topics_active ON topics(is_active);
CREATE INDEX idx_topics_name ON topics(name);

-- Add constraint for valid categories
ALTER TABLE topics ADD CONSTRAINT valid_category 
    CHECK (category IN ('healthcare', 'technology', 'energy', 'finance', 'industrial', 'consumer', 'materials', 'utilities', 'real_estate', 'communication'));