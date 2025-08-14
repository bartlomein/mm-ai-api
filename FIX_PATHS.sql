-- Fix duplicate 'briefings/' prefix in storage paths
-- Run this in Supabase SQL Editor

-- 1. Update existing records to remove the duplicate prefix
UPDATE briefings
SET audio_file_path = SUBSTRING(audio_file_path FROM 11)
WHERE audio_file_path LIKE 'briefings/%';

-- 2. Verify the changes
SELECT 
    id, 
    title, 
    audio_file_path,
    created_at
FROM briefings 
ORDER BY created_at DESC;

-- Expected result: paths should now be like:
-- 2025/08/11/free_afternoon/free_afternoon_20250811_135122.mp3
-- Instead of:
-- briefings/2025/08/11/free_afternoon/free_afternoon_20250811_135122.mp3