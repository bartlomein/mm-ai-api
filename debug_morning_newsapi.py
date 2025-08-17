#!/usr/bin/env python3
"""
Test just the NewsAPI.ai parts of the morning script to see how it works
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Import exactly like morning script
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_premium_morning_briefing_v2 import PremiumMorningBriefingV2

async def test_morning_newsapi():
    """Test just the NewsAPI.ai calls from the morning script"""
    
    print("=== Testing morning script's NewsAPI.ai methods ===")
    generator = PremiumMorningBriefingV2()
    
    # Test each method individually like the evening script tests
    print("\n--- Testing morning fetch_world_news() ---")
    world_news = await generator.fetch_world_news(hours_back=12)
    print(f"Morning world news: {len(world_news)} articles")
    if world_news:
        print(f"First article: {world_news[0].get('title', 'No title')[:100]}")
    
    print("\n--- Testing morning fetch_usa_news() ---")
    usa_news = await generator.fetch_usa_news(hours_back=12)
    print(f"Morning USA news: {len(usa_news)} articles")
    if usa_news:
        print(f"First article: {usa_news[0].get('title', 'No title')[:100]}")
    
    print("\n--- Testing morning fetch_tech_news() ---")
    tech_news = await generator.fetch_tech_news(hours_back=12)
    print(f"Morning tech news: {len(tech_news)} articles")
    if tech_news:
        print(f"First article: {tech_news[0].get('title', 'No title')[:100]}")
    
    print("\n--- Testing morning fetch_finance_news() ---")
    finance_news = await generator.fetch_finance_news(hours_back=12)
    print(f"Morning finance news: finlight={len(finance_news.get('finlight', []))}, newsapi={len(finance_news.get('newsapi', []))}")
    
    print(f"\n=== Summary ===")
    print(f"Morning script - World: {len(world_news)} | USA: {len(usa_news)} | Tech: {len(tech_news)} | Finance: {len(finance_news.get('newsapi', []))}")

if __name__ == "__main__":
    asyncio.run(test_morning_newsapi())