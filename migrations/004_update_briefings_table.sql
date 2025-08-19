-- Migration: Update existing briefings table with user_id and blurb fields
-- File: 004_update_briefings_table.sql

-- Skip adding user_id - briefings are shared content, not user-specific

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

-- Add unique constraint for upsert functionality (one briefing per date/type/tier)
ALTER TABLE briefings ADD CONSTRAINT unique_daily_briefing 
    UNIQUE (briefing_date, briefing_type, tier);

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own briefings" ON briefings;
DROP POLICY IF EXISTS "Everyone can view public briefings" ON briefings; 
DROP POLICY IF EXISTS "Users can manage own briefings" ON briefings;

-- RLS should already be enabled, but ensure it
-- ALTER TABLE briefings ENABLE ROW LEVEL SECURITY; -- Skip this line if it causes errors

-- Create new RLS policies for briefings table (tier-based access, not user-specific)
CREATE POLICY "Free users can view free briefings" ON briefings
    FOR SELECT USING (tier = 'free' OR is_public = true);

CREATE POLICY "Premium users can view all briefings" ON briefings
    FOR SELECT USING (auth.role() = 'authenticated'); -- Premium users see everything

-- Only service role can manage briefings (system-generated)  
CREATE POLICY "Service role can manage briefings" ON briefings
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Create additional indexes (check if they exist first)
CREATE INDEX IF NOT EXISTS idx_briefings_tier ON briefings(tier);
CREATE INDEX IF NOT EXISTS idx_briefings_date ON briefings(briefing_date);
CREATE INDEX IF NOT EXISTS idx_briefings_tier_date ON briefings(tier, briefing_date);
CREATE INDEX IF NOT EXISTS idx_briefings_public ON briefings(is_public) WHERE is_public = true;