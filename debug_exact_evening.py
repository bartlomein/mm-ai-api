#!/usr/bin/env python3
"""
Debug by exactly mimicking the evening script's import and initialization
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Fix for Python 3.13+ compatibility with pydub (exactly like evening script)
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop

# CRITICAL: Load environment variables BEFORE any imports that use them (exactly like evening script)
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path (exactly like evening script)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import exactly like evening script
from src.services.newsapiai_service import NewsAPIAIService

async def debug_exact_evening():
    """Test with exact same setup as evening script"""
    
    print("Testing with EXACT evening script setup...")
    
    # Initialize exactly like evening script  
    newsapiai_service = NewsAPIAIService()
    
    print("\n=== Testing world news (exactly like evening script) ===")
    
    # Calculate date range exactly like evening script
    hours_back = 18
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours_back)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # First try with date range (exactly like evening script line 117-123)
    result = await newsapiai_service.search_articles(
        keyword="news",  # Simple keyword
        date_start=start_date.strftime("%Y-%m-%d"),
        date_end=end_date.strftime("%Y-%m-%d"),
        max_articles=150,  # Get even more articles for evening recap
        sort_by="date"
    )
    
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    if result:
        articles = result.get("articles", [])
        print(f"Articles found: {len(articles)}")
        
        # Check if it would trigger the fallback (exactly like evening script line 126)
        if not result or not result.get("articles") or len(result.get("articles", [])) < 5:
            print("   🔄 Would trigger broader world news search...")
            
            # Test the fallback (exactly like evening script line 128-132)
            result = await newsapiai_service.search_articles(
                keyword="world",
                max_articles=150,  # Get even more articles
                sort_by="date"
            )
            
            articles = result.get("articles", []) if result else []
            print(f"Fallback 1 articles found: {len(articles)}")
            
            # Second fallback if still no results (exactly like evening script line 135-141)
            if not result or not result.get("articles") or len(result.get("articles", [])) < 5:
                print("   🔄 Would trigger very broad news search...")
                result = await newsapiai_service.search_articles(
                    keyword="breaking news international",
                    max_articles=150,
                    sort_by="date"
                )
                articles = result.get("articles", []) if result else []
                print(f"Fallback 2 articles found: {len(articles)}")
        
        final_articles = result.get("articles", []) if result else []
        print(f"Final articles that would be returned: {len(final_articles)}")
        
        # Return exactly like evening script (line 143-145)
        final_result = final_articles[:75]  # Return top 75 for selection
        print(f"After [:75] slice: {len(final_result)} articles")
        
    else:
        print("❌ No result returned!")

if __name__ == "__main__":
    asyncio.run(debug_exact_evening())