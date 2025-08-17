#!/usr/bin/env python3
"""
Quick test of evening script EST functionality
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_premium_evening_briefing_v2 import PremiumEveningBriefingV2, get_est_time, is_weekend_est

async def test_est_functionality():
    """Test EST functionality in evening script"""
    
    print("=== Testing EST timezone functions ===")
    
    est_time = get_est_time()
    is_weekend = is_weekend_est()
    
    print(f"EST time: {est_time}")
    print(f"EST weekday: {est_time.weekday()} (0=Mon, 6=Sun)")
    print(f"Is weekend in EST: {is_weekend}")
    print(f"Formatted: {est_time.strftime('%B %d, %Y at %I:%M %p ET')}")
    
    print(f"\n=== Testing evening script instantiation ===")
    generator = PremiumEveningBriefingV2()
    print(f"Evening script created successfully!")
    
    # Test one simple fetch to make sure EST doesn't break anything
    print(f"\n=== Testing simple news fetch ===")
    world_news = await generator.fetch_world_news(hours_back=18)
    print(f"World news articles: {len(world_news)}")

if __name__ == "__main__":
    asyncio.run(test_est_functionality())