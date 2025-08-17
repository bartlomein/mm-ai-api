#!/usr/bin/env python3
"""
Debug the normalization process to see where articles are lost
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

# Monkey patch the service to add debug logging
class DebugNewsAPIAIService(NewsAPIAIService):
    async def search_articles(self, *args, **kwargs):
        """Override to add detailed debugging"""
        
        # Get the raw response first by calling the parent _make_request directly
        keyword = kwargs.get('keyword', 'world')
        date_start = kwargs.get('date_start')
        date_end = kwargs.get('date_end')
        max_articles = kwargs.get('max_articles', 50)
        sort_by = kwargs.get('sort_by', 'date')
        
        print(f"\n🔍 DEBUG: Starting search with keyword='{keyword}', date_start={date_start}, date_end={date_end}")
        
        # Build query like the original
        query_data = {
            "action": "getArticles",
            "resultType": "articles",
            "articlesSortBy": sort_by,
            "articlesCount": max_articles,
            "lang": "eng",
            "dataType": "news"
        }
        
        if keyword:
            query_data["keyword"] = keyword
            query_data["keywordsLoc"] = "body,title"
        
        if date_start:
            query_data["dateStart"] = date_start
        if date_end:
            query_data["dateEnd"] = date_end
            
        # Add exclusions
        query_data["ignoreSourceUri"] = ["timesofindia.com", "timesofindia.indiatimes.com"]
        
        print(f"🔍 DEBUG: Query data: {query_data}")
        
        # Make the request
        response = await self._make_request("article/getArticles", data=query_data)
        
        print(f"🔍 DEBUG: Raw response type: {type(response)}")
        if response:
            print(f"🔍 DEBUG: Response keys: {list(response.keys())}")
            
            # Check articles structure
            articles_data = response.get("articles", {})
            print(f"🔍 DEBUG: Articles data type: {type(articles_data)}")
            print(f"🔍 DEBUG: Articles data keys: {list(articles_data.keys()) if isinstance(articles_data, dict) else 'Not a dict'}")
            
            raw_articles = articles_data.get("results", [])
            print(f"🔍 DEBUG: Raw articles count: {len(raw_articles)}")
            
            if raw_articles:
                print(f"🔍 DEBUG: First raw article keys: {list(raw_articles[0].keys())}")
                print(f"🔍 DEBUG: First raw article title: {raw_articles[0].get('title', 'NO TITLE')}")
                print(f"🔍 DEBUG: First raw article body: {raw_articles[0].get('body', 'NO BODY')[:100]}...")
            else:
                print(f"🔍 DEBUG: No articles in results")
                print(f"🔍 DEBUG: Total results from API: {articles_data.get('totalResults', 'NO TOTAL')}")
        else:
            print(f"🔍 DEBUG: Response is None/empty")
        
        # Now call the original method to see where normalization fails
        result = await super().search_articles(*args, **kwargs)
        
        print(f"🔍 DEBUG: Final result articles count: {len(result.get('articles', []))}")
        
        return result

async def debug_normalization():
    """Test the normalization process step by step"""
    
    print("Testing normalization process...")
    service = DebugNewsAPIAIService()
    
    # Test simple search
    print("\n=== Testing simple world search ===")
    result = await service.search_articles(
        keyword="world",
        max_articles=5,
        sort_by="date"
    )

if __name__ == "__main__":
    asyncio.run(debug_normalization())