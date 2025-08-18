-- Migration: Update existing briefings table with user_id and blurb fields
-- File: 004_update_briefings_table.sql

-- Add user_id column to link briefings to users (check if exists first)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'briefings' AND column_name = 'user_id') THEN
        ALTER TABLE briefings ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add blurb column for 2-sentence highlights (check if exists first)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'briefings' AND column_name = 'blurb') THEN
        ALTER TABLE briefings ADD COLUMN blurb TEXT;
    END IF;
END $$;

-- Add briefing_time column for creation timestamp (check if exists first)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'briefings' AND column_name = 'briefing_time') THEN
        ALTER TABLE briefings ADD COLUMN briefing_time TIMESTAMPTZ DEFAULT now();
    END IF;
END $$;

-- Update existing briefing_type constraint to include more types (including existing values)
ALTER TABLE briefings DROP CONSTRAINT IF EXISTS briefings_briefing_type_check;
ALTER TABLE briefings ADD CONSTRAINT briefings_briefing_type_check 
    CHECK (briefing_type IN (
        'morning', 'midday', 'evening', 'afternoon',
        'free_morning', 'free_midday', 'free_evening', 'free_afternoon', 
        'custom', 'premium_morning', 'premium_midday', 'premium_evening', 'premium_afternoon'
    ));

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own briefings" ON briefings;
DROP POLICY IF EXISTS "Everyone can view public briefings" ON briefings; 
DROP POLICY IF EXISTS "Users can manage own briefings" ON briefings;

-- RLS should already be enabled, but ensure it
-- ALTER TABLE briefings ENABLE ROW LEVEL SECURITY; -- Skip this line if it causes errors

-- Create new RLS policies for briefings table
CREATE POLICY "Users can view own briefings" ON briefings
    FOR SELECT USING (auth.uid() = user_id OR is_public = true);

-- Allow users to manage their own briefings  
CREATE POLICY "Users can manage own briefings" ON briefings
    FOR ALL USING (auth.uid() = user_id);

-- Create additional indexes (check if they exist first)
CREATE INDEX IF NOT EXISTS idx_briefings_user_id ON briefings(user_id);
CREATE INDEX IF NOT EXISTS idx_briefings_user_date ON briefings(user_id, briefing_date);
CREATE INDEX IF NOT EXISTS idx_briefings_user_tier ON briefings(user_id, tier);
CREATE INDEX IF NOT EXISTS idx_briefings_public ON briefings(is_public) WHERE is_public = true;