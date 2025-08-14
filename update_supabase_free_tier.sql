-- Update Supabase schema to support free tier briefings
-- Run this after the initial setup_supabase.sql

-- 1. Update briefing_type constraint to include free tier types
ALTER TABLE public.briefings 
DROP CONSTRAINT IF EXISTS briefings_briefing_type_check;

ALTER TABLE public.briefings 
ADD CONSTRAINT briefings_briefing_type_check 
CHECK (briefing_type IN ('morning', 'afternoon', 'evening', 'free_morning', 'free_afternoon', 'free_evening', 'custom'));

-- 2. Add tier column to briefings table
ALTER TABLE public.briefings 
ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'premium' 
CHECK (tier IN ('free', 'premium'));

-- 3. Update RLS policies to allow free users to access free briefings

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Public briefings are viewable by all" ON public.briefings;
DROP POLICY IF EXISTS "Paid users can view all briefings" ON public.briefings;

-- New policy: Anyone authenticated can view free tier briefings
CREATE POLICY "Free briefings viewable by authenticated users" 
ON public.briefings FOR SELECT 
USING (
    tier = 'free' 
    AND auth.uid() IS NOT NULL
);

-- New policy: Paid users can view all briefings
CREATE POLICY "Paid users can view all briefings" 
ON public.briefings FOR SELECT 
USING (
    auth.uid() IN (
        SELECT id FROM public.user_profiles 
        WHERE is_paid_subscriber = true
        AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
    )
);

-- New policy: Public briefings (if marked) are viewable by everyone
CREATE POLICY "Public briefings viewable by all" 
ON public.briefings FOR SELECT 
USING (is_public = true);

-- 4. Create view for free tier briefings
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

-- 5. Create view for today's briefings (both free and premium)
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

-- 6. Storage policies for free briefings
-- Note: Run these after creating the storage bucket
/*
-- Allow authenticated users to read free briefings
CREATE POLICY "Authenticated users can read free briefings"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'briefings' AND
    auth.uid() IS NOT NULL AND
    (
        -- Free briefings (path contains 'free_')
        path LIKE '%/free_%' OR
        -- Or user is paid subscriber
        auth.uid() IN (
            SELECT id FROM public.user_profiles 
            WHERE is_paid_subscriber = true
            AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
        )
    )
);
*/

-- 7. Function to get user's accessible briefings
CREATE OR REPLACE FUNCTION public.get_user_briefings(user_id UUID)
RETURNS TABLE (
    id UUID,
    title TEXT,
    briefing_type TEXT,
    tier TEXT,
    briefing_date DATE,
    word_count INTEGER,
    duration_seconds INTEGER,
    audio_file_path TEXT,
    can_access BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id,
        b.title,
        b.briefing_type,
        b.tier,
        b.briefing_date,
        b.word_count,
        b.duration_seconds,
        b.audio_file_path,
        CASE 
            -- Free tier briefings accessible to all authenticated users
            WHEN b.tier = 'free' THEN true
            -- Public briefings accessible to all
            WHEN b.is_public = true THEN true
            -- Premium briefings only for paid users
            WHEN EXISTS (
                SELECT 1 FROM public.user_profiles p
                WHERE p.id = user_id 
                AND p.is_paid_subscriber = true
                AND (p.subscription_expires_at IS NULL OR p.subscription_expires_at > NOW())
            ) THEN true
            ELSE false
        END as can_access
    FROM public.briefings b
    ORDER BY b.briefing_date DESC, b.created_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 8. Function to get briefing with access check
CREATE OR REPLACE FUNCTION public.get_briefing_with_access(
    briefing_id UUID,
    user_id UUID
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    briefing_type TEXT,
    tier TEXT,
    text_content TEXT,
    audio_file_path TEXT,
    can_access BOOLEAN,
    access_reason TEXT
) AS $$
DECLARE
    is_paid BOOLEAN;
    briefing_tier TEXT;
    briefing_public BOOLEAN;
BEGIN
    -- Check if user is paid subscriber
    SELECT is_paid_subscriber INTO is_paid
    FROM public.user_profiles
    WHERE id = user_id 
    AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW());
    
    -- Get briefing details
    SELECT tier, is_public INTO briefing_tier, briefing_public
    FROM public.briefings
    WHERE id = briefing_id;
    
    RETURN QUERY
    SELECT 
        b.id,
        b.title,
        b.briefing_type,
        b.tier,
        CASE 
            WHEN briefing_tier = 'free' THEN b.text_content
            WHEN briefing_public = true THEN b.text_content
            WHEN is_paid = true THEN b.text_content
            ELSE NULL
        END as text_content,
        CASE 
            WHEN briefing_tier = 'free' THEN b.audio_file_path
            WHEN briefing_public = true THEN b.audio_file_path
            WHEN is_paid = true THEN b.audio_file_path
            ELSE NULL
        END as audio_file_path,
        CASE 
            WHEN briefing_tier = 'free' THEN true
            WHEN briefing_public = true THEN true
            WHEN is_paid = true THEN true
            ELSE false
        END as can_access,
        CASE 
            WHEN briefing_tier = 'free' THEN 'Free tier content'
            WHEN briefing_public = true THEN 'Public briefing'
            WHEN is_paid = true THEN 'Premium subscriber access'
            ELSE 'Premium subscription required'
        END as access_reason
    FROM public.briefings b
    WHERE b.id = briefing_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant permissions
GRANT SELECT ON public.free_briefings TO anon, authenticated;
GRANT SELECT ON public.todays_briefings TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_user_briefings TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_briefing_with_access TO authenticated;