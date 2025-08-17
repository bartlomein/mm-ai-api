#!/usr/bin/env python3
"""
Debug script to test the NewsAPIAIService wrapper directly
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv()

from services.newsapiai_service import NewsAPIAIService

async def test_service_wrapper():
    """Test the actual NewsAPIAIService wrapper to see where it fails"""
    
    print("Testing NewsAPIAIService wrapper...")
    service = NewsAPIAIService()
    
    # Test 1: Simple search (what works in morning script)
    print("\n--- Test 1: Simple search (no date filter) ---")
    try:
        result = await service.search_articles(
            keyword="world",
            max_articles=10,
            sort_by="date"
        )
        
        print(f"Service returned: {type(result)}")
        if result:
            print(f"Result keys: {list(result.keys())}")
            articles = result.get("articles", [])
            print(f"Articles found: {len(articles)}")
            if articles:
                print(f"First article title: {articles[0].get('title', 'No title')[:100]}")
                print(f"First article content length: {len(articles[0].get('content', ''))}")
        else:
            print("Service returned None/empty result")
            
    except Exception as e:
        print(f"Error in test 1: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Date-filtered search (what fails in evening script)
    print("\n--- Test 2: Date-filtered search (last 18 hours) ---")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=18)
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        result = await service.search_articles(
            keyword="news",
            date_start=start_date.strftime('%Y-%m-%d'),
            date_end=end_date.strftime('%Y-%m-%d'),
            max_articles=10,
            sort_by="date"
        )
        
        print(f"Service returned: {type(result)}")
        if result:
            print(f"Result keys: {list(result.keys())}")
            articles = result.get("articles", [])
            print(f"Articles found: {len(articles)}")
            if articles:
                print(f"First article title: {articles[0].get('title', 'No title')[:100]}")
                print(f"First article content length: {len(articles[0].get('content', ''))}")
            else:
                print("No articles in result despite non-empty response")
                print(f"Metadata: {result.get('metadata', {})}")
        else:
            print("Service returned None/empty result")
            
    except Exception as e:
        print(f"Error in test 2: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_service_wrapper())