#!/usr/bin/env python3
"""
Test script to verify NewsAPI.ai integration and all service methods
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

async def test_newsapi_ai_direct():
    """Test the NewsAPI.ai API endpoint directly"""
    import httpx
    
    api_key = os.getenv("NEWSAPI_AI_KEY")
    if not api_key:
        print("❌ NEWSAPI_AI_KEY not found in .env")
        return False
    
    print("Testing NewsAPI.ai (Event Registry) API connection...")
    
    # Test basic search endpoint
    url = "https://eventregistry.org/api/v1/article/getArticles"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "action": "getArticles",
                    "resultType": "articles",
                    "articlesCount": 1,
                    "lang": "eng",
                    "keyword": "Apple",
                    "apiKey": api_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", {}).get("results", [])
                if articles and len(articles) > 0:
                    print(f"✅ NewsAPI.ai connected! Found article: '{articles[0].get('title', 'N/A')[:50]}...'")
                    return True
                else:
                    print("❌ NewsAPI.ai returned empty data")
                    return False
            else:
                print(f"❌ NewsAPI.ai error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error connecting to NewsAPI.ai: {str(e)}")
        return False

async def test_newsapiai_service():
    """Test our NewsAPIAIService class and all its methods"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    service = NewsAPIAIService()
    
    if not service.api_key:
        print("❌ NewsAPIAIService: API key not configured")
        return
    
    print("\n" + "="*60)
    print("Testing NewsAPIAIService Methods")
    print("="*60)
    
    # Test 1: Basic Search Articles
    print("\n1. Testing Basic Search (keyword: 'finance')...")
    search_result = await service.search_articles(
        keyword="finance",
        max_articles=5
    )
    if search_result and search_result.get("articles"):
        articles = search_result["articles"]
        print(f"✅ Search: Found {len(articles)} articles")
        print(f"   Summary: {search_result.get('summary', 'N/A')}")
        for i, article in enumerate(articles[:2]):
            print(f"   - Article {i+1}: {article.get('title', 'N/A')[:60]}...")
            print(f"     Source: {article.get('source', 'N/A')}")
            print(f"     Published: {article.get('published_at', 'N/A')[:19]}")
    else:
        print("❌ Failed to search articles")
    
    # Test 2: Date Range Search
    print("\n2. Testing Date Range Search (last 3 days)...")
    date_result = await service.fetch_for_date_range(
        days_back=3,
        keyword="stock market",
        max_articles=10
    )
    if date_result and date_result.get("articles"):
        articles = date_result["articles"]
        print(f"✅ Date Range: Found {len(articles)} articles from last 3 days")
        print(f"   Summary: {date_result.get('summary', 'N/A')}")
        metadata = date_result.get("metadata", {})
        print(f"   Total available: {metadata.get('total_results', 'N/A')}")
    else:
        print("❌ Failed to fetch date range articles")
    
    # Test 3: Financial News
    print("\n3. Testing Financial News Fetch...")
    finance_result = await service.fetch_financial_news(max_articles=15)
    if finance_result and finance_result.get("articles"):
        articles = finance_result["articles"]
        print(f"✅ Financial News: Found {len(articles)} financial articles")
        print(f"   Summary: {finance_result.get('summary', 'N/A')}")
        
        # Show some financial concepts found
        all_concepts = []
        for article in articles[:5]:
            all_concepts.extend(article.get("concepts", [])[:3])
        unique_concepts = list(set(all_concepts))[:10]
        if unique_concepts:
            print(f"   Key concepts: {', '.join(unique_concepts)}")
    else:
        print("❌ Failed to fetch financial news")
    
    # Test 4: Recent Headlines
    print("\n4. Testing Recent Headlines (last 48 hours)...")
    headlines_result = await service.get_recent_headlines(
        hours_back=48,
        keyword="cryptocurrency OR bitcoin",
        max_articles=8
    )
    if headlines_result and headlines_result.get("articles"):
        articles = headlines_result["articles"]
        print(f"✅ Recent Headlines: Found {len(articles)} recent articles")
        print(f"   Summary: {headlines_result.get('summary', 'N/A')}")
        for article in articles[:3]:
            print(f"   - {article.get('title', 'N/A')[:70]}...")
    else:
        print("⚠️  No recent headlines found (may be normal depending on timing)")
    
    # Test 5: Trending Topics Analysis
    print("\n5. Testing Trending Topics Analysis...")
    trending_result = await service.get_trending_topics(max_topics=15)
    if trending_result and trending_result.get("topics"):
        topics = trending_result["topics"]
        print(f"✅ Trending Analysis: {trending_result.get('summary', 'N/A')}")
        
        concepts = topics.get("concepts", [])
        categories = topics.get("categories", [])
        
        if concepts:
            print("   Top trending concepts:")
            for concept, count in concepts[:5]:
                print(f"     - {concept}: {count} mentions")
        
        if categories:
            print("   Top categories:")
            for category, count in categories[:3]:
                print(f"     - {category}: {count} articles")
        
        metadata = trending_result.get("metadata", {})
        print(f"   Analyzed {metadata.get('articles_analyzed', 'N/A')} articles")
    else:
        print("❌ Failed to analyze trending topics")
    
    # Test 6: Specific Date Range Search
    print("\n6. Testing Specific Date Range (last week)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    specific_date_result = await service.search_articles(
        keyword="earnings OR IPO",
        date_start=start_date.strftime("%Y-%m-%d"),
        date_end=end_date.strftime("%Y-%m-%d"),
        sort_by="date",
        max_articles=12
    )
    if specific_date_result and specific_date_result.get("articles"):
        articles = specific_date_result["articles"]
        print(f"✅ Specific Dates: Found {len(articles)} articles from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"   Summary: {specific_date_result.get('summary', 'N/A')}")
        
        # Show date distribution
        dates = []
        for article in articles:
            if article.get("published_at"):
                date_str = article["published_at"][:10]
                dates.append(date_str)
        
        if dates:
            unique_dates = sorted(set(dates))
            print(f"   Date range covered: {unique_dates[0]} to {unique_dates[-1]}")
    else:
        print("⚠️  No articles found for specific date range")

async def test_newsapiai_pipeline_integration():
    """Test NewsAPI.ai integration with pipeline service"""
    from src.services.pipeline_service import PipelineService
    
    print("\n" + "="*60)
    print("Testing NewsAPI.ai Pipeline Integration")
    print("="*60)
    
    pipeline = PipelineService()
    
    # Test 1: Multi-source briefing
    print("\n1. Testing Multi-Source Briefing (Finlight + NewsAPI.ai)...")
    try:
        multi_result = await pipeline.generate_multi_source_briefing(
            keyword="technology",
            days_back=2,
            combine_sources=True
        )
        if multi_result.get("status") == "success":
            print("✅ Multi-Source Briefing Generated Successfully")
            sources = multi_result.get("sources", {})
            print(f"   Finlight articles: {sources.get('finlight_articles', 0)}")
            print(f"   NewsAPI.ai articles: {sources.get('newsapi_articles', 0)}")
            print(f"   Total articles: {sources.get('total_articles', 0)}")
            print(f"   Duration: {multi_result.get('duration_seconds', 0):.1f} seconds")
            print(f"   Title: {multi_result.get('title', 'N/A')}")
        else:
            print(f"❌ Multi-source briefing failed: {multi_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Multi-source briefing error: {str(e)}")
    
    # Test 2: Date-filtered briefing
    print("\n2. Testing Date-Filtered Briefing...")
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        date_result = await pipeline.generate_date_filtered_briefing(
            date_start=yesterday,
            keyword="market",
        )
        if date_result.get("status") == "success":
            print("✅ Date-Filtered Briefing Generated Successfully")
            print(f"   Date range: {date_result.get('date_start')} to {date_result.get('date_end', 'today')}")
            print(f"   Articles processed: {date_result.get('articles_processed', 0)}")
            print(f"   Duration: {date_result.get('duration_seconds', 0):.1f} seconds")
            print(f"   Title: {date_result.get('title', 'N/A')}")
        else:
            print(f"❌ Date-filtered briefing failed: {date_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Date-filtered briefing error: {str(e)}")
    
    # Test 3: Trending briefing
    print("\n3. Testing Trending Topics Briefing...")
    try:
        trending_result = await pipeline.generate_trending_briefing()
        if trending_result.get("status") == "success":
            print("✅ Trending Topics Briefing Generated Successfully")
            trending_topics = trending_result.get("trending_topics", [])
            print(f"   Trending topics: {', '.join(trending_topics[:5])}")
            print(f"   Articles processed: {trending_result.get('articles_processed', 0)}")
            print(f"   Duration: {trending_result.get('duration_seconds', 0):.1f} seconds")
            print(f"   Title: {trending_result.get('title', 'N/A')}")
        else:
            print(f"❌ Trending briefing failed: {trending_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Trending briefing error: {str(e)}")

async def test_specific_use_cases():
    """Test specific investor/trader use cases with NewsAPI.ai"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    service = NewsAPIAIService()
    
    print("\n" + "="*60)
    print("Testing Specific Use Cases")
    print("="*60)
    
    # Use Case 1: Earnings Season News
    print("\n📊 Use Case 1: Earnings Season Coverage")
    print("What investors want to hear during earnings season...")
    
    earnings_result = await service.search_articles(
        keyword="earnings OR quarterly results OR revenue",
        max_articles=15,
        sort_by="date"
    )
    
    if earnings_result.get("articles"):
        articles = earnings_result["articles"]
        print(f"Found {len(articles)} earnings-related articles")
        
        # Extract company mentions from titles
        companies = []
        for article in articles[:10]:
            title = article.get("title", "").upper()
            concepts = article.get("concepts", [])
            companies.extend([c for c in concepts if len(c) < 10 and c.isupper()])
        
        unique_companies = list(set(companies))[:8]
        if unique_companies:
            print(f"Companies in the news: {', '.join(unique_companies)}")
        
        print(f"Summary: {earnings_result.get('summary', 'N/A')}")
    
    # Use Case 2: Market Volatility Analysis
    print("\n📊 Use Case 2: Market Volatility News")
    volatility_result = await service.search_articles(
        keyword="volatility OR market decline OR sell-off OR rally",
        days_back=2,
        max_articles=10
    )
    
    if volatility_result.get("articles"):
        articles = volatility_result["articles"]
        print(f"Found {len(articles)} volatility-related articles")
        
        # Check sentiment distribution
        sentiments = [article.get("sentiment", 0) for article in articles if article.get("sentiment") is not None]
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            sentiment_label = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            print(f"Average sentiment: {avg_sentiment:.2f} ({sentiment_label})")
    
    # Use Case 3: Crypto Market News
    print("\n📊 Use Case 3: Cryptocurrency Market Updates")
    crypto_result = await service.search_articles(
        keyword="bitcoin OR cryptocurrency OR ethereum OR blockchain",
        max_articles=12,
        sort_by="date"
    )
    
    if crypto_result.get("articles"):
        articles = crypto_result["articles"]
        print(f"Found {len(articles)} crypto-related articles")
        
        # Extract crypto concepts
        crypto_concepts = []
        for article in articles[:8]:
            concepts = article.get("concepts", [])
            crypto_terms = [c for c in concepts if any(term in c.lower() for term in ['bitcoin', 'crypto', 'ethereum', 'blockchain'])]
            crypto_concepts.extend(crypto_terms)
        
        unique_crypto = list(set(crypto_concepts))[:6]
        if unique_crypto:
            print(f"Crypto topics mentioned: {', '.join(unique_crypto)}")
    
    # Use Case 4: Federal Reserve & Economic Policy
    print("\n📊 Use Case 4: Fed & Economic Policy News")
    fed_result = await service.search_articles(
        keyword="federal reserve OR interest rates OR inflation OR monetary policy",
        max_articles=8,
        sort_by="date"
    )
    
    if fed_result.get("articles"):
        articles = fed_result["articles"]
        print(f"Found {len(articles)} Fed/economic policy articles")
        
        # Check for recent policy mentions
        policy_concepts = []
        for article in articles[:5]:
            concepts = article.get("concepts", [])
            policy_terms = [c for c in concepts if any(term in c.lower() for term in ['rate', 'inflation', 'policy', 'fed'])]
            policy_concepts.extend(policy_terms)
        
        unique_policy = list(set(policy_concepts))[:5]
        if unique_policy:
            print(f"Policy topics: {', '.join(unique_policy)}")

async def main():
    """Run all tests"""
    print("🚀 Starting NewsAPI.ai Service Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API connection first
    api_ok = await test_newsapi_ai_direct()
    
    if api_ok:
        # Test all service methods
        await test_newsapiai_service()
        
        # Test pipeline integration
        await test_newsapiai_pipeline_integration()
        
        # Test specific use cases
        await test_specific_use_cases()
    
    print("\n✅ NewsAPI.ai Service tests completed!")

if __name__ == "__main__":
    asyncio.run(main())