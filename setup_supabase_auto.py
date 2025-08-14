#!/usr/bin/env python3
"""
Automated Supabase setup script
Sets up tables and storage bucket for MarketMotion
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import time

# Load environment variables
load_dotenv()

print("🚀 MarketMotion - Supabase Setup")
print("=" * 60)

# Get credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    sys.exit(1)

print("✅ Credentials loaded")
print(f"   Project: {url}")

# For table creation, we need to use the Supabase dashboard
print("\n" + "=" * 60)
print("📋 MANUAL SETUP REQUIRED")
print("=" * 60)
print("\nSince the tables need to be created via the Supabase dashboard,")
print("please follow these steps:\n")

print("1️⃣  Open your Supabase project:")
print(f"   {url.replace('.supabase.co', '.supabase.com/project/').replace('https://', 'https://app.')}")

print("\n2️⃣  Go to SQL Editor (left sidebar)")

print("\n3️⃣  Click 'New Query' and paste this SQL:\n")

sql_script = """
-- =====================================================
-- COPY EVERYTHING BELOW THIS LINE
-- =====================================================

-- 1. Create user profiles table
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    is_paid_subscriber BOOLEAN DEFAULT FALSE,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'premium')),
    subscription_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create briefings metadata table with tier support
CREATE TABLE IF NOT EXISTS public.briefings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    briefing_type TEXT NOT NULL CHECK (briefing_type IN ('morning', 'afternoon', 'evening', 'free_morning', 'free_afternoon', 'free_evening', 'custom')),
    briefing_date DATE NOT NULL,
    word_count INTEGER,
    duration_seconds INTEGER,
    text_content TEXT,
    audio_file_path TEXT,
    text_file_path TEXT,
    tier TEXT DEFAULT 'premium' CHECK (tier IN ('free', 'premium')),
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_briefings_date ON public.briefings(briefing_date DESC);
CREATE INDEX IF NOT EXISTS idx_briefings_type ON public.briefings(briefing_type);
CREATE INDEX IF NOT EXISTS idx_briefings_tier ON public.briefings(tier);
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription ON public.user_profiles(is_paid_subscriber);

-- 4. Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.briefings ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies for user_profiles
CREATE POLICY "Users can view own profile" 
ON public.user_profiles FOR SELECT 
USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
ON public.user_profiles FOR UPDATE 
USING (auth.uid() = id);

-- 6. RLS Policies for briefings
-- Free briefings viewable by authenticated users
CREATE POLICY "Free briefings viewable by authenticated users" 
ON public.briefings FOR SELECT 
USING (
    tier = 'free' 
    AND auth.uid() IS NOT NULL
);

-- Paid users can view all briefings
CREATE POLICY "Paid users can view all briefings" 
ON public.briefings FOR SELECT 
USING (
    auth.uid() IN (
        SELECT id FROM public.user_profiles 
        WHERE is_paid_subscriber = true
        AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
    )
);

-- Public briefings viewable by all
CREATE POLICY "Public briefings viewable by all" 
ON public.briefings FOR SELECT 
USING (is_public = true);

-- 7. Function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email)
    VALUES (new.id, new.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 8. Trigger for new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 9. Helper function to check if user is paid subscriber
CREATE OR REPLACE FUNCTION public.is_paid_subscriber(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.user_profiles
        WHERE id = user_id
        AND is_paid_subscriber = true
        AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 10. View for free briefings
CREATE OR REPLACE VIEW public.free_briefings AS
SELECT 
    id,
    title,
    briefing_type,
    briefing_date,
    word_count,
    duration_seconds,
    created_at
FROM public.briefings
WHERE tier = 'free'
ORDER BY briefing_date DESC, created_at DESC;

-- 11. View for today's briefings
CREATE OR REPLACE VIEW public.todays_briefings AS
SELECT 
    id,
    title,
    briefing_type,
    tier,
    briefing_date,
    word_count,
    duration_seconds,
    created_at,
    CASE 
        WHEN tier = 'free' THEN true
        WHEN is_public = true THEN true
        ELSE false
    END as is_accessible_free
FROM public.briefings
WHERE briefing_date = CURRENT_DATE
ORDER BY 
    CASE 
        WHEN briefing_type LIKE 'free_%' THEN 1
        ELSE 2
    END,
    created_at DESC;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON public.free_briefings TO anon, authenticated;
GRANT SELECT ON public.todays_briefings TO anon, authenticated;
GRANT ALL ON public.briefings TO authenticated;
GRANT ALL ON public.user_profiles TO authenticated;

-- =====================================================
-- COPY EVERYTHING ABOVE THIS LINE
-- =====================================================
"""

print(sql_script)

print("\n4️⃣  Click 'Run' to execute the SQL")

print("\n5️⃣  Create Storage Bucket:")
print("   a. Go to Storage (left sidebar)")
print("   b. Click 'New bucket'")
print("   c. Name: briefings")
print("   d. Set 'Public' to OFF (private)")
print("   e. Click 'Create'")

print("\n6️⃣  Set Storage Policies:")
print("   a. Click on the 'briefings' bucket")
print("   b. Go to 'Policies' tab")
print("   c. Click 'New Policy' → 'For full customization'")
print("   d. Create these policies:\n")

print("   Policy 1 - Authenticated users can read free briefings:")
print("   - Name: Read free briefings")
print("   - Allowed operation: SELECT")
print("   - Target roles: authenticated")
print("   - Policy definition:")
print("     (bucket_id = 'briefings' AND path LIKE '%/free_%')")

print("\n   Policy 2 - Paid users can read all briefings:")
print("   - Name: Paid users read all")
print("   - Allowed operation: SELECT")
print("   - Target roles: authenticated")
print("   - Policy definition:")
print("     (bucket_id = 'briefings' AND auth.uid() IN (")
print("       SELECT id FROM public.user_profiles")
print("       WHERE is_paid_subscriber = true))")

print("\n" + "=" * 60)
print("✅ Once you've completed these steps, run:")
print("   python test_supabase_connection.py")
print("\nThen you can generate briefings with:")
print("   ./generate_free_briefing.py     # 3-minute free tier")
print("   ./generate_briefing_supabase.py # 5-minute premium")
print("   ./generate_all_briefings.py     # Both tiers")
print("=" * 60)