#!/usr/bin/env python3
"""
Debug the specific instance created by the evening script
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_premium_evening_briefing_v2 import PremiumEveningBriefingV2

async def debug_evening_instance():
    """Debug the exact service instance created by the evening script"""
    
    print("=== Creating evening script instance ===")
    generator = PremiumEveningBriefingV2()
    
    # Access the service directly
    service = generator.newsapiai_service
    
    print(f"Service class: {service.__class__}")
    print(f"Service API key: {'✓' if service.api_key else '✗'} (len: {len(service.api_key) if service.api_key else 0})")
    print(f"Service base_url: {service.base_url}")
    
    # Test the service directly (bypassing evening script methods)
    print(f"\n=== Testing service directly (bypassing evening script methods) ===")
    
    result = await service.search_articles(
        keyword="news",
        max_articles=5,
        sort_by="date"
    )
    
    print(f"Direct service call result: {len(result.get('articles', []))} articles")
    
    # Test with date filter
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=18)
    
    result_with_date = await service.search_articles(
        keyword="news",
        date_start=start_date.strftime('%Y-%m-%d'),
        date_end=end_date.strftime('%Y-%m-%d'),
        max_articles=5,
        sort_by="date"
    )
    
    print(f"Direct service call with date filter: {len(result_with_date.get('articles', []))} articles")
    
    # Now test the evening script method to see where it differs
    print(f"\n=== Testing evening script method ===")
    
    world_news = await generator.fetch_world_news(hours_back=18)
    print(f"Evening script method result: {len(world_news)} articles")

if __name__ == "__main__":
    asyncio.run(debug_evening_instance())