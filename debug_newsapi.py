#!/usr/bin/env python3
"""
Debug script to test NewsAPI.ai directly
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

# Simple test without complex imports
import json

async def test_newsapi_directly():
    """Test NewsAPI.ai with direct HTTP calls to diagnose the issue"""
    
    try:
        import httpx
    except ImportError:
        print("❌ httpx not installed. Installing...")
        os.system("pip install httpx")
        import httpx
    
    api_key = os.getenv("NEWSAPI_AI_KEY")
    if not api_key:
        print("❌ NEWSAPI_AI_KEY not found")
        return
    
    print(f"✅ API key found (length: {len(api_key)})")
    
    base_url = "https://eventregistry.org/api/v1"
    
    # Test 1: Simple search without date filtering (like morning script fallback)
    print("\n--- Test 1: Simple search (no date filter) ---")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/article/getArticles",
                headers={"Content-Type": "application/json"},
                json={
                    "action": "getArticles",
                    "resultType": "articles",
                    "articlesSortBy": "date",
                    "articlesCount": 10,
                    "lang": "eng",
                    "dataType": "news",
                    "keyword": "world",
                    "apiKey": api_key
                }
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", {}).get("results", [])
                print(f"Articles found: {len(articles)}")
                if articles:
                    print(f"First article title: {articles[0].get('title', 'No title')[:100]}")
            else:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"Error in test 1: {e}")
    
    # Test 2: Date-filtered search (like evening script)
    print("\n--- Test 2: Date-filtered search (last 18 hours) ---")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=18)
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{base_url}/article/getArticles",
                headers={"Content-Type": "application/json"},
                json={
                    "action": "getArticles",
                    "resultType": "articles",
                    "articlesSortBy": "date",
                    "articlesCount": 10,
                    "lang": "eng",
                    "dataType": "news",
                    "keyword": "news",
                    "dateStart": start_date.strftime('%Y-%m-%d'),
                    "dateEnd": end_date.strftime('%Y-%m-%d'),
                    "apiKey": api_key
                }
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", {}).get("results", [])
                print(f"Articles found: {len(articles)}")
                if articles:
                    print(f"First article title: {articles[0].get('title', 'No title')[:100]}")
                else:
                    print("No articles returned despite 200 status")
                    print(f"Full response structure: {list(data.keys())}")
            else:
                print(f"Error response: {response.text}")
                
    except Exception as e:
        print(f"Error in test 2: {e}")

if __name__ == "__main__":
    asyncio.run(test_newsapi_directly())