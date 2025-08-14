# Supabase Storage Policies Setup

## How to Add Storage Policies

### Step 1: Go to Storage Policies
1. Open your Supabase project: https://app.supabase.com/project/soknenrlcrkesshjxbyn
2. Click **Storage** in the left sidebar
3. Click on the **briefings** bucket
4. Click the **Policies** tab

### Step 2: Create Upload Policy (INSERT)

Click **New Policy** → **For full customization** and create this policy:

**Policy 1: Allow Service Role to Upload**
- **Policy name**: `Service role uploads`
- **Target roles**: Check `authenticated` 
- **WITH CHECK expression**:
```sql
true
```
- **Operations**: Check `INSERT`
- Click **Review** then **Save policy**

### Step 3: Create Download Policies (SELECT)

Click **New Policy** → **For full customization** again:

**Policy 2: Authenticated users can read free briefings**
- **Policy name**: `Read free briefings`
- **Target roles**: Check `authenticated`
- **USING expression**:
```sql
(path_tokens[4] ILIKE 'free_%')
```
- **Operations**: Check `SELECT`
- Click **Review** then **Save policy**

**Policy 3: Public can read public briefings**
- **Policy name**: `Public read public briefings`
- **Target roles**: Check `anon` and `authenticated`
- **USING expression**:
```sql
(path_tokens[5] ILIKE 'public_%')
```
- **Operations**: Check `SELECT`
- Click **Review** then **Save policy**

## Alternative: Quick SQL Method

If you prefer, you can run this SQL in the SQL Editor instead:

```sql
-- Storage policies for briefings bucket
-- Run this AFTER creating the bucket

-- Allow authenticated users to upload (for service role)
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'briefings');

-- Allow authenticated users to read free briefings
CREATE POLICY "Authenticated read free briefings"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'briefings' AND 
    (storage.filename(name) ILIKE 'free_%' OR auth.uid() IN (
        SELECT id FROM public.user_profiles 
        WHERE is_paid_subscriber = true
    ))
);

-- Allow service role to manage all files
CREATE POLICY "Service role full access"
ON storage.objects
TO service_role
USING (bucket_id = 'briefings')
WITH CHECK (bucket_id = 'briefings');
```

## What These Policies Do

1. **Service role uploads**: Allows the backend service to upload files
2. **Read free briefings**: Authenticated users can download free tier briefings
3. **Paid users read all**: Paid subscribers can download all briefings (handled by the second part of the authenticated read policy)

## Test After Adding Policies

Run this to test:
```bash
./generate_free_briefing.py
```

The upload should now work!