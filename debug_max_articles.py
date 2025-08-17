#!/usr/bin/env python3
"""
Test if max_articles parameter is causing the issue
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from services.newsapiai_service import NewsAPIAIService

async def test_max_articles():
    """Test different max_articles values to see if that's the issue"""
    
    service = NewsAPIAIService()
    
    # Calculate the same date range as evening script
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=18)
    
    print(f"Testing with date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Test different max_articles values
    test_values = [5, 10, 50, 100, 150]
    
    for max_articles in test_values:
        print(f"\n=== Testing max_articles={max_articles} ===")
        
        try:
            result = await service.search_articles(
                keyword="news",
                date_start=start_date.strftime('%Y-%m-%d'),
                date_end=end_date.strftime('%Y-%m-%d'),
                max_articles=max_articles,
                sort_by="date"
            )
            
            articles = result.get("articles", [])
            metadata = result.get("metadata", {})
            
            print(f"Articles returned: {len(articles)}")
            print(f"Total available: {metadata.get('total_results', 'Unknown')}")
            
            if len(articles) == 0:
                print("❌ FAILED - No articles returned")
            else:
                print("✅ SUCCESS - Articles returned")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    # Test the exact call that the evening script makes on first try
    print(f"\n=== Testing EXACT evening script first call ===")
    try:
        result = await service.search_articles(
            keyword="news",  # Simple keyword
            date_start=start_date.strftime("%Y-%m-%d"),
            date_end=end_date.strftime("%Y-%m-%d"),
            max_articles=150,  # Get even more articles for evening recap
            sort_by="date"
        )
        
        articles = result.get("articles", [])
        print(f"Exact evening script call: {len(articles)} articles")
        
        if articles:
            print("✅ Evening script call would work!")
        else:
            print("❌ Evening script call fails!")
            
    except Exception as e:
        print(f"❌ Evening script call error: {e}")

if __name__ == "__main__":
    asyncio.run(test_max_articles())