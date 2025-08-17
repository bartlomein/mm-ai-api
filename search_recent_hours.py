#!/usr/bin/env python3
"""
Search for news articles from the past N hours
Usage: python search_recent_hours.py "biotechnology" 8 [max_articles]
"""

import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def search_recent_hours(topic: str, hours_back: int = 8, max_articles: int = 15):
    """Search for articles from the past N hours"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    print(f"🔍 NewsAPI.ai Recent Hours Search")
    print("=" * 50)
    print(f"📰 Topic: {topic}")
    print(f"⏰ Hours back: {hours_back}")
    print(f"📊 Max articles: {max_articles}")
    print(f"🔍 Search time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    service = NewsAPIAIService()
    
    if not service.api_key:
        print("❌ Error: NEWSAPI_AI_KEY not found in environment variables")
        return
    
    print("🔍 Searching recent hours...")
    
    try:
        result = await service.get_recent_headlines(
            hours_back=hours_back,
            keyword=topic,
            max_articles=max_articles
        )
        
        articles = result.get("articles", [])
        metadata = result.get("metadata", {})
        
        if not articles:
            print(f"❌ No articles found for '{topic}' in the past {hours_back} hours")
            return
        
        print(f"✅ Found {len(articles)} articles about '{topic}' in the past {hours_back} hours")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        print()
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'N/A')
            source = article.get('source', 'Unknown')
            published = article.get('published_at', 'N/A')
            content = article.get('content', '')
            sentiment = article.get('sentiment', 0)
            
            # Format time
            formatted_time = 'N/A'
            if published != 'N/A':
                try:
                    if published.endswith('Z'):
                        pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    else:
                        pub_date = datetime.fromisoformat(published)
                    formatted_time = pub_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = published[:19] if len(published) >= 19 else published
            
            sentiment_icon = "😊" if sentiment > 0.1 else "😔" if sentiment < -0.1 else "😐"
            
            print(f"{i:2}. {title}")
            print(f"    📰 {source} | ⏰ {formatted_time} | {sentiment_icon} {sentiment:.2f}")
            
            if content:
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"    📝 {content_preview}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    if len(sys.argv) < 3:
        print("Usage: python search_recent_hours.py <topic> <hours_back> [max_articles]")
        print("Example: python search_recent_hours.py 'biotechnology' 8 20")
        return
    
    topic = sys.argv[1]
    hours_back = int(sys.argv[2])
    max_articles = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    
    await search_recent_hours(topic, hours_back, max_articles)

if __name__ == "__main__":
    asyncio.run(main())