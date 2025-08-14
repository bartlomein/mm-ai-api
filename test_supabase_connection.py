#!/usr/bin/env python3
"""
Test Supabase connection and configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Checking Supabase Configuration")
print("=" * 50)

# Check environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

print("📋 Current Configuration:")
print(f"   SUPABASE_URL: {supabase_url}")
print(f"   SUPABASE_ANON_KEY: {'Set' if supabase_key else 'Not set'}")
print(f"   Key length: {len(supabase_key) if supabase_key else 0} characters")

print("\n⚠️  Issues Found:")
if not supabase_url or supabase_url == "https://xxx.supabase.co":
    print("   ❌ SUPABASE_URL is not properly configured")
    print("   📝 You need to set your actual Supabase project URL")
    print("\n📚 How to get your Supabase URL:")
    print("   1. Go to https://app.supabase.com")
    print("   2. Select your project")
    print("   3. Go to Settings > API")
    print("   4. Copy the 'Project URL' (looks like: https://abcdefghijk.supabase.co)")
    print("   5. Update your .env file with the actual URL")
else:
    print("   ✅ SUPABASE_URL appears to be configured")

if not supabase_key or supabase_key == "xxx":
    print("\n   ❌ SUPABASE_ANON_KEY is not properly configured")
    print("   📝 You need to set your actual Supabase anon key")
    print("\n📚 How to get your Supabase Anon Key:")
    print("   1. Go to https://app.supabase.com")
    print("   2. Select your project")
    print("   3. Go to Settings > API")
    print("   4. Copy the 'anon public' key")
    print("   5. Update your .env file with the actual key")
else:
    print("   ✅ SUPABASE_ANON_KEY appears to be configured")

# Try to connect if credentials look valid
if supabase_url and supabase_url != "https://xxx.supabase.co" and supabase_key and supabase_key != "xxx":
    print("\n🔌 Testing Connection...")
    try:
        from supabase import create_client, Client
        
        client = create_client(supabase_url, supabase_key)
        
        # Try a simple query to test connection
        result = client.table("briefings").select("id").limit(1).execute()
        print("   ✅ Successfully connected to Supabase!")
        
        # Check if tables exist
        try:
            result = client.table("user_profiles").select("id").limit(1).execute()
            print("   ✅ user_profiles table exists")
        except:
            print("   ⚠️  user_profiles table not found - run setup_supabase.sql")
            
        try:
            result = client.table("briefings").select("id").limit(1).execute()
            print("   ✅ briefings table exists")
        except:
            print("   ⚠️  briefings table not found - run setup_supabase.sql")
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n   Possible causes:")
        print("   1. Invalid URL or API key")
        print("   2. Tables not created (run SQL migrations)")
        print("   3. Network/firewall issues")

print("\n" + "=" * 50)
print("📝 Next Steps:")
print("1. Update your .env file with actual Supabase credentials")
print("2. Run the SQL migrations in Supabase dashboard")
print("3. Run this test again to verify connection")
print("=" * 50)