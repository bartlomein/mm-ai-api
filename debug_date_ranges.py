#!/usr/bin/env python3
"""
Test different date ranges to find the issue
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

async def test_date_ranges():
    """Test different date ranges to see which works and which doesn't"""
    
    service = NewsAPIAIService()
    
    now = datetime.now()
    
    # Test different hour ranges
    test_ranges = [
        (6, "6 hours (narrow)"),
        (12, "12 hours (morning script)"),  
        (18, "18 hours (evening script)"),
        (24, "24 hours (full day)"),
        (48, "48 hours (2 days)"),
    ]
    
    for hours, description in test_ranges:
        print(f"\n=== Testing {description} ===")
        
        start_date = now - timedelta(hours=hours)
        end_date = now
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        try:
            result = await service.search_articles(
                keyword="news",
                date_start=start_date.strftime('%Y-%m-%d'),
                date_end=end_date.strftime('%Y-%m-%d'),
                max_articles=10,
                sort_by="date"
            )
            
            articles = result.get("articles", [])
            metadata = result.get("metadata", {})
            
            print(f"Articles found: {len(articles)}")
            print(f"Total available: {metadata.get('total_results', 'Unknown')}")
            
            if articles:
                first_date = articles[0].get('published_at', 'No date')
                print(f"First article date: {first_date}")
                print(f"First article: {articles[0].get('title', 'No title')[:80]}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Test without date filtering (what works)
    print(f"\n=== Testing NO date filter (control) ===")
    try:
        result = await service.search_articles(
            keyword="news",
            max_articles=10,
            sort_by="date"
        )
        
        articles = result.get("articles", [])
        print(f"Articles found: {len(articles)}")
        
        if articles:
            print(f"First article: {articles[0].get('title', 'No title')[:80]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_date_ranges())