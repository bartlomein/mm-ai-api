-- Setup script for Market Brief AI Supabase integration
-- Run this in your Supabase SQL editor

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

-- 2. Create briefings metadata table
CREATE TABLE IF NOT EXISTS public.briefings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    briefing_type TEXT NOT NULL CHECK (briefing_type IN ('morning', 'afternoon', 'evening', 'custom')),
    briefing_date DATE NOT NULL,
    word_count INTEGER,
    duration_seconds INTEGER,
    text_content TEXT,
    audio_file_path TEXT,
    text_file_path TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_briefings_date ON public.briefings(briefing_date DESC);
CREATE INDEX IF NOT EXISTS idx_briefings_type ON public.briefings(briefing_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription ON public.user_profiles(is_paid_subscriber);

-- 4. Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.briefings ENABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies for user_profiles
-- Users can read their own profile
CREATE POLICY "Users can view own profile" 
ON public.user_profiles FOR SELECT 
USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" 
ON public.user_profiles FOR UPDATE 
USING (auth.uid() = id);

-- 6. Create RLS policies for briefings
-- Public briefings are viewable by everyone
CREATE POLICY "Public briefings are viewable by all" 
ON public.briefings FOR SELECT 
USING (is_public = true);

-- Paid subscribers can view all briefings
CREATE POLICY "Paid users can view all briefings" 
ON public.briefings FOR SELECT 
USING (
    EXISTS (
        SELECT 1 FROM public.user_profiles 
        WHERE id = auth.uid() 
        AND is_paid_subscriber = true
        AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
    )
);

-- 7. Create function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email)
    VALUES (new.id, new.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 8. Create trigger for new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 9. Create storage bucket for briefings (run in Dashboard or via API)
-- Note: Storage buckets need to be created via Dashboard or API
-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('briefings', 'briefings', false);

-- 10. Storage policies for briefings bucket
-- Allow authenticated users to read briefings if they're paid subscribers
-- Note: These policies need to be created after the bucket exists
/*
CREATE POLICY "Paid users can read briefings"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'briefings' AND
    auth.uid() IN (
        SELECT id FROM public.user_profiles 
        WHERE is_paid_subscriber = true
        AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
    )
);

CREATE POLICY "Service role can upload briefings"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'briefings' AND
    auth.role() = 'service_role'
);
*/

-- 11. Helper function to check if user is paid subscriber
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

-- 12. View for latest briefings (useful for dashboard)
CREATE OR REPLACE VIEW public.latest_briefings AS
SELECT 
    id,
    title,
    briefing_type,
    briefing_date,
    word_count,
    duration_seconds,
    is_public,
    created_at
FROM public.briefings
ORDER BY briefing_date DESC, created_at DESC
LIMIT 30;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON public.latest_briefings TO anon, authenticated;
GRANT ALL ON public.briefings TO authenticated;
GRANT ALL ON public.user_profiles TO authenticated;