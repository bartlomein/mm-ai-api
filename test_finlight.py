#!/usr/bin/env python3
"""
Test script to verify Finlight API integration
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_finlight_api():
    """Test the Finlight /v2/articles endpoint directly"""
    
    api_key = os.getenv("FINLIGHT_API_KEY")
    if not api_key:
        print("❌ FINLIGHT_API_KEY not found in .env")
        return False
    
    print("Testing Finlight API...")
    print(f"API Key: {api_key[:10]}...")
    
    url = "https://api.finlight.me/v2/articles"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }
    
    payload = {
        "includeContent": True,
        "includeEntities": False,
        "excludeEmptyContent": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                print(f"✅ Success! Fetched {len(articles)} articles")
                
                # Show first 3 articles
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n--- Article {i} ---")
                    print(f"Title: {article.get('title', 'No title')[:100]}")
                    print(f"Source: {article.get('source', 'Unknown')}")
                    print(f"Date: {article.get('publishDate', 'Unknown')}")
                    print(f"Content length: {len(article.get('content', ''))} chars")
                    
                    # Show if it's finance-related
                    content = article.get('content', '').lower()
                    title = article.get('title', '').lower()
                    is_finance = any(kw in title or kw in content[:500] 
                                    for kw in ['stock', 'market', 'invest', 'finance', 'earnings'])
                    print(f"Finance-related: {'Yes' if is_finance else 'No'}")
                
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

async def test_news_service():
    """Test our NewsService class"""
    print("\n" + "="*50)
    print("Testing NewsService...")
    print("="*50)
    
    from src.services.news_service import NewsService
    
    service = NewsService()
    
    # Test general market fetch
    print("\n1. Testing fetch_general_market()...")
    articles = await service.fetch_general_market()
    
    if articles:
        print(f"✅ Fetched {len(articles)} market-related articles")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n   Article {i}: {article.get('title', '')[:80]}...")
    else:
        print("❌ No articles fetched")
    
    # Test ticker-specific fetch
    print("\n2. Testing fetch_for_tickers(['AAPL', 'GOOGL'])...")
    ticker_articles = await service.fetch_for_tickers(['AAPL', 'GOOGL'])
    
    if ticker_articles:
        print(f"✅ Found {len(ticker_articles)} articles mentioning AAPL or GOOGL")
        for article in ticker_articles[:3]:
            ticker = article.get('primary_ticker', 'Unknown')
            title = article.get('title', '')[:60]
            print(f"   [{ticker}] {title}...")
    else:
        print("❌ No ticker-specific articles found")
    
    return bool(articles)

async def main():
    print("="*50)
    print("Finlight API Test")
    print("="*50)
    
    # Test direct API call
    api_ok = await test_finlight_api()
    
    if api_ok:
        # Test our service
        service_ok = await test_news_service()
        
        if service_ok:
            print("\n" + "="*50)
            print("✅ All tests passed! Finlight integration working.")
            print("="*50)
        else:
            print("\n⚠️ Service test failed")
    else:
        print("\n❌ API test failed. Check your FINLIGHT_API_KEY")

if __name__ == "__main__":
    asyncio.run(main())