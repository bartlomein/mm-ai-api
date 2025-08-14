#!/usr/bin/env python3
"""
Generate both free (3-minute) and premium (5-minute) briefings
Run this script to create briefings for all user tiers
"""

import asyncio
import subprocess
import sys
from datetime import datetime

def run_script(script_path, description):
    """Run a Python script and capture output"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_path}:")
        print(e.stdout)
        print(e.stderr)
        return False

async def generate_all_briefings():
    """Generate both free and premium briefings"""
    
    print("=" * 80)
    print("📰 MARKET BRIEF AI - DAILY BRIEFING GENERATOR")
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"⏰ Time: {datetime.now().strftime('%I:%M %p')}")
    print("=" * 80)
    
    success_count = 0
    total_count = 2
    
    # Generate free briefing first (3 minutes)
    print("\n" + "─" * 60)
    print("Step 1/2: Generating FREE TIER briefing (3 minutes)")
    print("─" * 60)
    if run_script("generate_free_briefing.py", "Free Tier Briefing Generator"):
        success_count += 1
        print("✅ Free briefing generated successfully")
    else:
        print("⚠️  Free briefing generation failed")
    
    # Generate premium briefing (5 minutes)
    print("\n" + "─" * 60)
    print("Step 2/2: Generating PREMIUM briefing (5 minutes)")
    print("─" * 60)
    if run_script("generate_briefing_supabase.py", "Premium Briefing Generator"):
        success_count += 1
        print("✅ Premium briefing generated successfully")
    else:
        print("⚠️  Premium briefing generation failed")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 GENERATION SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully generated: {success_count}/{total_count} briefings")
    
    if success_count == total_count:
        print("🎉 All briefings generated successfully!")
        print("\n📱 User Access:")
        print("   • Free users: 3-minute briefing available")
        print("   • Premium users: Full 5-minute briefing + free briefing")
    else:
        print(f"⚠️  Some briefings failed. Please check the logs above.")
    
    print("\n💾 Storage:")
    print("   • Local files: Saved as backup")
    print("   • Supabase: Uploaded with proper access control")
    
    print("\n🔒 Access Control:")
    print("   • Free briefings: All registered users")
    print("   • Premium briefings: Paid subscribers only")
    
    print("=" * 80)

if __name__ == "__main__":
    print("🎯 Starting daily briefing generation...")
    asyncio.run(generate_all_briefings())