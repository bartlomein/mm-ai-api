#!/usr/bin/env python3
"""
Test parallel vs sequential execution to find the issue
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_premium_evening_briefing_v2 import PremiumEveningBriefingV2

async def test_sequential_execution():
    """Test the exact same calls but sequentially instead of in parallel"""
    
    print("=== Testing SEQUENTIAL execution ===")
    generator = PremiumEveningBriefingV2()
    
    # Execute the same functions as fetch_all_data() but sequentially
    print("\n1. Fetching trading data...")
    trading_data = await generator.fetch_trading_data()
    print(f"   Trading data: {type(trading_data)}")
    
    print("\n2. Fetching world news...")
    world_news = await generator.fetch_world_news()
    print(f"   World news: {len(world_news)} articles")
    
    print("\n3. Fetching USA news...")
    usa_news = await generator.fetch_usa_news()
    print(f"   USA news: {len(usa_news)} articles")
    
    print("\n4. Fetching finance news...")
    finance_news = await generator.fetch_finance_news()
    print(f"   Finance news: finlight={len(finance_news.get('finlight', []))}, newsapi={len(finance_news.get('newsapi', []))}")
    
    print("\n5. Fetching tech news...")
    tech_news = await generator.fetch_tech_news()
    print(f"   Tech news: {len(tech_news)} articles")
    
    return {
        "trading_data": trading_data,
        "world_news": world_news,
        "usa_news": usa_news,
        "finance_news": finance_news,
        "tech_news": tech_news
    }

async def test_parallel_execution():
    """Test the original parallel execution"""
    
    print("\n=== Testing PARALLEL execution (original) ===")
    generator = PremiumEveningBriefingV2()
    
    # This is the exact same as the original fetch_all_data()
    all_data = await generator.fetch_all_data()
    
    print(f"World news: {len(all_data.get('world_news', []))} articles")
    print(f"USA news: {len(all_data.get('usa_news', []))} articles") 
    print(f"Finance news: finlight={len(all_data.get('finance_news', {}).get('finlight', []))}, newsapi={len(all_data.get('finance_news', {}).get('newsapi', []))}")
    print(f"Tech news: {len(all_data.get('tech_news', []))} articles")
    
    return all_data

async def main():
    """Compare sequential vs parallel execution"""
    
    # Test sequential first
    sequential_data = await test_sequential_execution()
    
    # Wait a bit before parallel test
    print("\n" + "="*60)
    print("Waiting 5 seconds before parallel test...")
    await asyncio.sleep(5)
    
    # Test parallel
    parallel_data = await test_parallel_execution()
    
    # Compare results
    print("\n" + "="*60)
    print("COMPARISON:")
    print(f"Sequential - World: {len(sequential_data.get('world_news', []))} | USA: {len(sequential_data.get('usa_news', []))} | Tech: {len(sequential_data.get('tech_news', []))}")
    print(f"Parallel   - World: {len(parallel_data.get('world_news', []))} | USA: {len(parallel_data.get('usa_news', []))} | Tech: {len(parallel_data.get('tech_news', []))}")

if __name__ == "__main__":
    asyncio.run(main())