#!/usr/bin/env python3
"""
Test the specific keywords the evening script uses
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

async def test_keywords():
    """Test the exact keywords used by the evening script"""
    
    service = NewsAPIAIService()
    
    # Test keywords that work vs don't work
    test_cases = [
        ("test", "Simple test keyword"),
        ("world", "World keyword (used in fallback)"),
        ("news", "News keyword (evening script first try)"),
        ("United States", "USA keyword (evening script)"),
        ("technology AI software", "Tech keyword (evening script)"),
        ("breaking news international", "Breaking news (evening script fallback)"),
        ("stock market finance economy", "Finance keyword (evening script)"),
    ]
    
    for keyword, description in test_cases:
        print(f"\n=== Testing: {description} ===")
        print(f"Keyword: '{keyword}'")
        
        try:
            result = await service.search_articles(
                keyword=keyword,
                max_articles=5,
                sort_by="date"
            )
            
            articles = result.get("articles", [])
            metadata = result.get("metadata", {})
            
            print(f"Articles found: {len(articles)}")
            print(f"Total results available: {metadata.get('total_results', 'Unknown')}")
            
            if articles:
                print(f"First article: {articles[0].get('title', 'No title')[:100]}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Test with date filtering (what evening script does first)
    print(f"\n=== Testing with date filtering (evening script first attempt) ===")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=18)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        result = await service.search_articles(
            keyword="news",
            date_start=start_date.strftime('%Y-%m-%d'),
            date_end=end_date.strftime('%Y-%m-%d'),
            max_articles=5,
            sort_by="date"
        )
        
        articles = result.get("articles", [])
        metadata = result.get("metadata", {})
        
        print(f"Articles found with date filter: {len(articles)}")
        print(f"Total results available: {metadata.get('total_results', 'Unknown')}")
        
        if articles:
            print(f"First article: {articles[0].get('title', 'No title')[:100]}")
        
    except Exception as e:
        print(f"Error with date filter: {e}")

if __name__ == "__main__":
    asyncio.run(test_keywords())