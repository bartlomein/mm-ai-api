# How to Get Your Supabase Service Role Key

## Steps:

1. **Go to your Supabase project settings**:
   👉 https://app.supabase.com/project/soknenrlcrkesshjxbyn/settings/api

2. **Find the "Service Role" section** (below the anon key)

3. **Copy the service_role key** (it starts with `eyJ...`)
   - ⚠️ This key has FULL ACCESS to your database
   - Keep it SECRET and never expose it in client-side code

4. **Add it to your .env file**:
   ```bash
   SUPABASE_SERVICE_KEY=eyJ...your-service-role-key-here...
   ```

## Why You Need This

The service role key bypasses Row Level Security (RLS) and allows your backend to:
- Upload files to storage
- Insert records into tables
- Perform admin operations

The anon key we were using before respects RLS policies, which is why uploads were blocked.

## After Adding the Key

Run this to test:
```bash
./generate_free_briefing.py
```

The upload should work now!