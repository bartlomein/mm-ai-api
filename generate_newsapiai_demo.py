#!/usr/bin/env python3
"""
Demo script showing NewsAPI.ai service capabilities
Generates different types of briefings using the new NewsAPI.ai integration
"""

import asyncio
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def demo_basic_search():
    """Demo basic search functionality"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    print("=" * 60)
    print("📰 NewsAPI.ai Basic Search Demo")
    print("=" * 60)
    
    service = NewsAPIAIService()
    
    # Search for financial news
    print("\n🔍 Searching for 'stock market' news...")
    result = await service.search_articles(
        keyword="stock market",
        max_articles=10,
        sort_by="date"
    )
    
    if result.get("articles"):
        articles = result["articles"]
        print(f"✅ Found {len(articles)} articles")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        
        print("\n📑 Top 3 Articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"   {i}. {article.get('title', 'N/A')}")
            print(f"      Source: {article.get('source', 'N/A')}")
            print(f"      Published: {article.get('published_at', 'N/A')[:19]}")
            print(f"      Concepts: {', '.join(article.get('concepts', [])[:3])}")
            print()
    else:
        print("❌ No articles found")

async def demo_date_filtering():
    """Demo date filtering capabilities"""
    print("=" * 60)
    print("📅 NewsAPI.ai Date Filtering Demo")
    print("=" * 60)
    
    from src.services.newsapiai_service import NewsAPIAIService
    
    service = NewsAPIAIService()
    
    # Get news from last 3 days
    print("\n📆 Fetching news from last 3 days...")
    result = await service.fetch_for_date_range(
        days_back=3,
        keyword="earnings OR IPO",
        max_articles=15
    )
    
    if result.get("articles"):
        articles = result["articles"]
        metadata = result.get("metadata", {})
        
        print(f"✅ Found {len(articles)} articles from last 3 days")
        print(f"📊 Total available: {metadata.get('total_results', 'N/A')}")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        
        # Show date distribution
        dates = {}
        for article in articles:
            if article.get("published_at"):
                date_str = article["published_at"][:10]
                dates[date_str] = dates.get(date_str, 0) + 1
        
        if dates:
            print("\n📈 Articles by date:")
            for date, count in sorted(dates.items()):
                print(f"   {date}: {count} articles")
    else:
        print("❌ No articles found for date range")

async def demo_trending_analysis():
    """Demo trending topics analysis"""
    print("=" * 60)
    print("🔥 NewsAPI.ai Trending Topics Demo")
    print("=" * 60)
    
    from src.services.newsapiai_service import NewsAPIAIService
    
    service = NewsAPIAIService()
    
    print("\n🔍 Analyzing trending topics in financial news...")
    result = await service.get_trending_topics(max_topics=20)
    
    if result.get("topics"):
        topics = result["topics"]
        metadata = result.get("metadata", {})
        
        print(f"✅ Trending analysis completed")
        print(f"📊 Analyzed {metadata.get('articles_analyzed', 'N/A')} articles")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        
        concepts = topics.get("concepts", [])
        categories = topics.get("categories", [])
        
        if concepts:
            print("\n🏆 Top 10 Trending Concepts:")
            for i, (concept, count) in enumerate(concepts[:10], 1):
                print(f"   {i:2}. {concept}: {count} mentions")
        
        if categories:
            print("\n📂 Top Categories:")
            for i, (category, count) in enumerate(categories[:5], 1):
                print(f"   {i}. {category}: {count} articles")
    else:
        print("❌ No trending topics found")

async def demo_multi_source_briefing():
    """Demo multi-source briefing generation"""
    print("=" * 60)
    print("🎙️ Multi-Source Briefing Demo")
    print("=" * 60)
    
    from src.services.pipeline_service import PipelineService
    
    pipeline = PipelineService()
    
    print("\n🔄 Generating briefing with Finlight + NewsAPI.ai sources...")
    print("⏱️  This may take 2-3 minutes for audio generation...")
    
    result = await pipeline.generate_multi_source_briefing(
        keyword="technology",
        days_back=1,
        combine_sources=True
    )
    
    if result.get("status") == "success":
        sources = result.get("sources", {})
        
        print("✅ Multi-source briefing generated successfully!")
        print(f"📰 Finlight articles: {sources.get('finlight_articles', 0)}")
        print(f"📰 NewsAPI.ai articles: {sources.get('newsapi_articles', 0)}")
        print(f"📊 Total articles: {sources.get('total_articles', 0)}")
        print(f"⏱️  Duration: {result.get('duration_seconds', 0):.1f} seconds")
        print(f"🎵 Audio file: {result.get('file_path', 'N/A')}")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        
        # Show first 200 characters of transcript
        transcript = result.get("transcript", "")
        if transcript:
            print(f"\n📜 Transcript preview:")
            print(f"   {transcript[:200]}...")
    else:
        print(f"❌ Briefing generation failed: {result.get('error', 'Unknown error')}")

async def demo_date_specific_briefing():
    """Demo date-specific briefing generation"""
    print("=" * 60)
    print("📅 Date-Specific Briefing Demo")
    print("=" * 60)
    
    from src.services.pipeline_service import PipelineService
    
    pipeline = PipelineService()
    
    # Generate briefing for yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n📆 Generating briefing for {yesterday}...")
    print("⏱️  This may take 2-3 minutes for audio generation...")
    
    result = await pipeline.generate_date_filtered_briefing(
        date_start=yesterday,
        keyword="market OR earnings",
    )
    
    if result.get("status") == "success":
        print("✅ Date-specific briefing generated successfully!")
        print(f"📅 Date range: {result.get('date_start')} to {result.get('date_end', 'today')}")
        print(f"📊 Articles processed: {result.get('articles_processed', 0)}")
        print(f"⏱️  Duration: {result.get('duration_seconds', 0):.1f} seconds")
        print(f"🎵 Audio file: {result.get('file_path', 'N/A')}")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        
        # Show first 200 characters of transcript
        transcript = result.get("transcript", "")
        if transcript:
            print(f"\n📜 Transcript preview:")
            print(f"   {transcript[:200]}...")
    else:
        print(f"❌ Briefing generation failed: {result.get('error', 'Unknown error')}")

async def demo_trending_briefing():
    """Demo trending topics briefing generation"""
    print("=" * 60)
    print("🔥 Trending Topics Briefing Demo")
    print("=" * 60)
    
    from src.services.pipeline_service import PipelineService
    
    pipeline = PipelineService()
    
    print("\n🔥 Generating briefing based on trending topics...")
    print("⏱️  This may take 3-4 minutes for analysis + audio generation...")
    
    result = await pipeline.generate_trending_briefing()
    
    if result.get("status") == "success":
        trending_topics = result.get("trending_topics", [])
        
        print("✅ Trending topics briefing generated successfully!")
        print(f"🔥 Trending topics: {', '.join(trending_topics[:5])}")
        print(f"📊 Articles processed: {result.get('articles_processed', 0)}")
        print(f"⏱️  Duration: {result.get('duration_seconds', 0):.1f} seconds")
        print(f"🎵 Audio file: {result.get('file_path', 'N/A')}")
        print(f"📝 Title: {result.get('title', 'N/A')}")
        
        # Show trend analysis
        trend_analysis = result.get("trend_analysis", "")
        if trend_analysis:
            print(f"\n📈 Trend Analysis: {trend_analysis}")
        
        # Show first 200 characters of transcript
        transcript = result.get("transcript", "")
        if transcript:
            print(f"\n📜 Transcript preview:")
            print(f"   {transcript[:200]}...")
    else:
        print(f"❌ Briefing generation failed: {result.get('error', 'Unknown error')}")

async def main():
    """Run NewsAPI.ai demonstrations"""
    print("🚀 NewsAPI.ai Service Demonstration")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == "search":
            await demo_basic_search()
        elif demo_type == "dates":
            await demo_date_filtering()
        elif demo_type == "trending":
            await demo_trending_analysis()
        elif demo_type == "multi":
            await demo_multi_source_briefing()
        elif demo_type == "date-briefing":
            await demo_date_specific_briefing()
        elif demo_type == "trend-briefing":
            await demo_trending_briefing()
        else:
            print("❌ Unknown demo type. Available options:")
            print("   search          - Basic search functionality")
            print("   dates           - Date filtering")
            print("   trending        - Trending topics analysis")
            print("   multi           - Multi-source briefing")
            print("   date-briefing   - Date-specific briefing")
            print("   trend-briefing  - Trending topics briefing")
    else:
        # Run all basic demos (without audio generation for speed)
        await demo_basic_search()
        await demo_date_filtering()
        await demo_trending_analysis()
        
        print("\n" + "=" * 60)
        print("🎙️ Audio Briefing Demos Available")
        print("=" * 60)
        print("Run with specific arguments to test audio generation:")
        print("  python generate_newsapiai_demo.py multi           # Multi-source briefing")
        print("  python generate_newsapiai_demo.py date-briefing   # Date-specific briefing")
        print("  python generate_newsapiai_demo.py trend-briefing  # Trending topics briefing")
    
    print(f"\n✅ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())