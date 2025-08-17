#!/usr/bin/env python3
"""
Debug the exact evening script execution path
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import the actual evening script class
from generate_premium_evening_briefing_v2 import PremiumEveningBriefingV2

async def debug_evening_script():
    """Debug the exact evening script execution to find where results are lost"""
    
    print("Creating PremiumEveningBriefingV2 instance...")
    generator = PremiumEveningBriefingV2()
    
    # Test the exact methods called by the evening script
    print("\n--- Testing fetch_world_news() ---")
    try:
        world_news = await generator.fetch_world_news(hours_back=18)
        print(f"fetch_world_news returned: {len(world_news)} articles")
        if world_news:
            print(f"First article: {world_news[0].get('title', 'No title')[:100]}")
        else:
            print("❌ fetch_world_news returned empty list!")
    except Exception as e:
        print(f"❌ Error in fetch_world_news: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- Testing fetch_usa_news() ---")
    try:
        usa_news = await generator.fetch_usa_news(hours_back=18)
        print(f"fetch_usa_news returned: {len(usa_news)} articles")
        if usa_news:
            print(f"First article: {usa_news[0].get('title', 'No title')[:100]}")
        else:
            print("❌ fetch_usa_news returned empty list!")
    except Exception as e:
        print(f"❌ Error in fetch_usa_news: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- Testing fetch_tech_news() ---")
    try:
        tech_news = await generator.fetch_tech_news(hours_back=18)
        print(f"fetch_tech_news returned: {len(tech_news)} articles")
        if tech_news:
            print(f"First article: {tech_news[0].get('title', 'No title')[:100]}")
        else:
            print("❌ fetch_tech_news returned empty list!")
    except Exception as e:
        print(f"❌ Error in fetch_tech_news: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n--- Testing fetch_all_data() ---")
    try:
        all_data = await generator.fetch_all_data()
        print(f"fetch_all_data returned: {type(all_data)}")
        print(f"Keys: {list(all_data.keys())}")
        
        world_news = all_data.get("world_news", [])
        usa_news = all_data.get("usa_news", [])
        tech_news = all_data.get("tech_news", [])
        
        print(f"World news in all_data: {len(world_news)} articles")
        print(f"USA news in all_data: {len(usa_news)} articles")
        print(f"Tech news in all_data: {len(tech_news)} articles")
        
    except Exception as e:
        print(f"❌ Error in fetch_all_data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_evening_script())