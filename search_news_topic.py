#!/usr/bin/env python3
"""
Simple script to search for news articles on any topic using NewsAPI.ai
Usage: python search_news_topic.py "biotechnology" [days_back] [max_articles]
       python search_news_topic.py "biotechnology" --time "2025-08-16 10:00" "2025-08-16 15:00" [max_articles]
"""

import asyncio
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_usage():
    print("Usage: python search_news_topic.py <topic> [days_back] [max_articles]")
    print("   or: python search_news_topic.py <topic> --time <start_datetime> <end_datetime> [max_articles]")
    print()
    print("Examples:")
    print("  # Day-based search")
    print("  python search_news_topic.py \"biotechnology\"")
    print("  python search_news_topic.py \"artificial intelligence\" 3")
    print("  python search_news_topic.py \"cryptocurrency\" 7 25")
    print()
    print("  # Time-based search")
    print("  python search_news_topic.py \"Apple earnings\" --time \"2025-08-16 09:00\" \"2025-08-16 17:00\"")
    print("  python search_news_topic.py \"market crash\" --time \"2025-08-16 14:30\" \"2025-08-16 16:00\" 20")
    print("  python search_news_topic.py \"Fed meeting\" --time \"2025-08-15 14:00\" \"2025-08-16 10:00\"")
    print()
    print("Arguments:")
    print("  topic          - The topic to search for (required)")
    print("  days_back      - How many days back to search (default: 1)")
    print("  max_articles   - Maximum articles to return (default: 15)")
    print("  --time         - Use precise datetime filtering")
    print("  start_datetime - Start time in 'YYYY-MM-DD HH:MM' format")
    print("  end_datetime   - End time in 'YYYY-MM-DD HH:MM' format")

async def search_topic_news(topic: str, days_back: int = 1, max_articles: int = 15):
    """Search for news articles on a specific topic"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    print("🔍 NewsAPI.ai Topic Search")
    print("=" * 50)
    print(f"📰 Topic: {topic}")
    print(f"📅 Days back: {days_back}")
    print(f"📊 Max articles: {max_articles}")
    print(f"⏰ Search time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    service = NewsAPIAIService()
    
    if not service.api_key:
        print("❌ Error: NEWSAPI_AI_KEY not found in environment variables")
        print("Please add NEWSAPI_AI_KEY to your .env file")
        return
    
    print("🔍 Searching...")
    
    try:
        # Search for articles on the topic
        result = await service.fetch_for_date_range(
            days_back=days_back,
            keyword=topic,
            max_articles=max_articles
        )
        
        articles = result.get("articles", [])
        metadata = result.get("metadata", {})
        
        if not articles:
            print(f"❌ No articles found for '{topic}' in the past {days_back} day(s)")
            print("Try:")
            print(f"  • Different keywords (e.g., synonyms)")
            print(f"  • Expanding the time range (more days)")
            print(f"  • Broader search terms")
            return
        
        # Display results
        print(f"✅ Found {len(articles)} articles about '{topic}'")
        print(f"📊 Total available: {metadata.get('total_results', 'N/A')}")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        print()
        print("📑 Articles:")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'N/A')
            source = article.get('source', 'Unknown')
            published = article.get('published_at', 'N/A')[:19]
            url = article.get('url', '')
            content = article.get('content', '')
            concepts = article.get('concepts', [])
            sentiment = article.get('sentiment', 0)
            
            # Format published date
            if published != 'N/A':
                try:
                    pub_date = datetime.fromisoformat(published.replace('Z', ''))
                    published = pub_date.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            # Sentiment indicator
            sentiment_icon = "😊" if sentiment > 0.1 else "😔" if sentiment < -0.1 else "😐"
            
            print(f"\n{'='*80}")
            print(f"ARTICLE {i}")
            print(f"{'='*80}")
            print(f"TITLE: {title}")
            print(f"{'-'*80}")
            
            # Show full article content without truncation
            if content:
                print(f"CONTENT:\n{content}")
            
            print(f"{'='*80}")
            print(f"END OF ARTICLE {i}")
            print(f"{'='*80}\n")
        
        # Show date distribution if multiple days
        if days_back > 1:
            print("📈 Articles by Date:")
            dates = {}
            for article in articles:
                if article.get("published_at"):
                    try:
                        date_str = article["published_at"][:10]
                        dates[date_str] = dates.get(date_str, 0) + 1
                    except:
                        pass
            
            for date, count in sorted(dates.items()):
                print(f"    {date}: {count} articles")
            print()
        
        # Show trending concepts if available
        all_concepts = []
        for article in articles:
            all_concepts.extend(article.get("concepts", [])[:3])
        
        if all_concepts:
            concept_counts = {}
            for concept in all_concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
            
            top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            
            print("🔥 Trending Concepts in Results:")
            for concept, count in top_concepts:
                print(f"    • {concept}: {count} mentions")
            print()
        
        print("💡 Tips:")
        print(f"  • Add more days: python search_news_topic.py \"{topic}\" {days_back + 2}")
        print(f"  • Get more articles: python search_news_topic.py \"{topic}\" {days_back} {max_articles + 10}")
        print(f"  • Try related terms: python search_news_topic.py \"{topic} OR related_term\"")
        print(f"  • Use time search: python search_news_topic.py \"{topic}\" --time \"2025-08-16 09:00\" \"2025-08-16 17:00\"")
        
    except Exception as e:
        print(f"❌ Error during search: {str(e)}")
        print("This might be due to:")
        print("  • Network connectivity issues")
        print("  • API rate limits")
        print("  • Invalid search parameters")

async def search_topic_news_by_time(
    topic: str,
    start_datetime: datetime,
    end_datetime: datetime,
    max_articles: int = 15
):
    """Search for news articles on a specific topic with precise time filtering"""
    from src.services.newsapiai_service import NewsAPIAIService
    
    print("🔍 NewsAPI.ai Time-Based Search")
    print("=" * 50)
    print(f"📰 Topic: {topic}")
    print(f"⏰ Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Max articles: {max_articles}")
    print(f"🔍 Search time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    service = NewsAPIAIService()
    
    if not service.api_key:
        print("❌ Error: NEWSAPI_AI_KEY not found in environment variables")
        print("Please add NEWSAPI_AI_KEY to your .env file")
        return
    
    print("🔍 Searching with time filter...")
    
    try:
        # Search for articles with precise time filtering
        result = await service.search_articles_by_time(
            keyword=topic,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            max_articles=max_articles
        )
        
        articles = result.get("articles", [])
        metadata = result.get("metadata", {})
        
        if not articles:
            time_range = f"{start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}"
            print(f"❌ No articles found for '{topic}' between {time_range}")
            print("Try:")
            print(f"  • Expanding the time range")
            print(f"  • Different keywords (e.g., synonyms)")
            print(f"  • Broader search terms")
            return
        
        # Display results
        print(f"✅ Found {len(articles)} articles about '{topic}'")
        if metadata.get("filtered_by_datetime"):
            print(f"⏱️  Time filtered: {metadata.get('articles_after_time_filter', 'N/A')} articles after time filtering")
        print(f"📊 Total available: {metadata.get('total_results', 'N/A')}")
        print(f"📄 Summary: {result.get('summary', 'N/A')}")
        print()
        print("📑 Articles:")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'N/A')
            source = article.get('source', 'Unknown')
            published = article.get('published_at', 'N/A')
            url = article.get('url', '')
            content = article.get('content', '')
            concepts = article.get('concepts', [])
            sentiment = article.get('sentiment', 0)
            
            # Format published date with time
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
            
            # Sentiment indicator
            sentiment_icon = "😊" if sentiment > 0.1 else "😔" if sentiment < -0.1 else "😐"
            
            print(f"\n{'='*80}")
            print(f"ARTICLE {i}")
            print(f"{'='*80}")
            print(f"TITLE: {title}")
            print(f"{'-'*80}")
            
            # Show full article content without truncation
            if content:
                print(f"CONTENT:\n{content}")
            
            print(f"{'='*80}")
            print(f"END OF ARTICLE {i}")
            print(f"{'='*80}\n")
        
        # Show time distribution of articles
        print("⏰ Articles by Hour:")
        hour_counts = {}
        for article in articles:
            if article.get("published_at"):
                try:
                    if article["published_at"].endswith('Z'):
                        pub_date = datetime.fromisoformat(article["published_at"].replace('Z', '+00:00'))
                    else:
                        pub_date = datetime.fromisoformat(article["published_at"])
                    hour_key = pub_date.strftime('%Y-%m-%d %H:00')
                    hour_counts[hour_key] = hour_counts.get(hour_key, 0) + 1
                except:
                    pass
        
        for hour, count in sorted(hour_counts.items()):
            print(f"    {hour}: {count} articles")
        print()
        
        # Show trending concepts if available
        all_concepts = []
        for article in articles:
            all_concepts.extend(article.get("concepts", [])[:3])
        
        if all_concepts:
            concept_counts = {}
            for concept in all_concepts:
                concept_counts[concept] = concept_counts.get(concept, 0) + 1
            
            top_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            
            print("🔥 Trending Concepts in Results:")
            for concept, count in top_concepts:
                print(f"    • {concept}: {count} mentions")
            print()
        
        print("💡 Tips:")
        start_str = start_datetime.strftime('%Y-%m-%d %H:%M')
        end_str = end_datetime.strftime('%Y-%m-%d %H:%M')
        print(f"  • Expand time: python search_news_topic.py \"{topic}\" --time \"{start_str}\" \"{end_str}\" {max_articles + 10}")
        print(f"  • Earlier period: python search_news_topic.py \"{topic}\" --time \"2025-08-15 09:00\" \"{start_str}\"")
        print(f"  • Try day search: python search_news_topic.py \"{topic}\" 1")
        
    except Exception as e:
        print(f"❌ Error during time-based search: {str(e)}")
        print("This might be due to:")
        print("  • Network connectivity issues")
        print("  • API rate limits")
        print("  • Invalid datetime format")
        print("  • Invalid search parameters")

def parse_datetime(datetime_str: str) -> datetime:
    """Parse datetime string in various formats"""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m-%d %H:%M",  # Current year assumed
        "%H:%M"  # Today assumed
    ]
    
    for fmt in formats:
        try:
            if fmt == "%m-%d %H:%M":
                # Add current year
                return datetime.strptime(f"{datetime.now().year}-{datetime_str}", f"%Y-{fmt}")
            elif fmt == "%H:%M":
                # Add current date
                today = datetime.now().strftime("%Y-%m-%d")
                return datetime.strptime(f"{today} {datetime_str}", "%Y-%m-%d %H:%M")
            else:
                return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime: {datetime_str}")

async def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    # Check for time-based search
    if "--time" in sys.argv:
        try:
            time_index = sys.argv.index("--time")
            
            # Ensure we have enough arguments for time-based search
            if len(sys.argv) < time_index + 3:
                print("❌ Error: --time requires start_datetime and end_datetime")
                print_usage()
                return
            
            topic = sys.argv[1]
            start_datetime_str = sys.argv[time_index + 1]
            end_datetime_str = sys.argv[time_index + 2]
            
            # Parse max_articles if provided
            max_articles = 15
            if len(sys.argv) > time_index + 3:
                try:
                    max_articles = int(sys.argv[time_index + 3])
                    if max_articles < 1:
                        print("❌ Error: max_articles must be at least 1")
                        return
                    if max_articles > 100:
                        print("⚠️  Warning: Limiting to 100 articles maximum")
                        max_articles = 100
                except ValueError:
                    print("❌ Error: max_articles must be a number")
                    print_usage()
                    return
            
            # Parse datetime strings
            try:
                start_datetime = parse_datetime(start_datetime_str)
                end_datetime = parse_datetime(end_datetime_str)
            except ValueError as e:
                print(f"❌ Error parsing datetime: {e}")
                print("Supported formats:")
                print("  • YYYY-MM-DD HH:MM")
                print("  • YYYY-MM-DD HH:MM:SS")
                print("  • YYYY-MM-DD (assumes 00:00)")
                print("  • MM-DD HH:MM (current year)")
                print("  • HH:MM (today)")
                return
            
            # Validate datetime range
            if start_datetime >= end_datetime:
                print("❌ Error: start_datetime must be before end_datetime")
                return
            
            # Validate topic
            if not topic.strip():
                print("❌ Error: Topic cannot be empty")
                print_usage()
                return
            
            # Run time-based search
            await search_topic_news_by_time(topic.strip(), start_datetime, end_datetime, max_articles)
            
        except ValueError as e:
            print(f"❌ Error: {e}")
            print_usage()
            return
    
    else:
        # Traditional day-based search
        topic = sys.argv[1]
        days_back = 1
        max_articles = 15
        
        if len(sys.argv) >= 3:
            try:
                days_back = int(sys.argv[2])
                if days_back < 1:
                    print("❌ Error: days_back must be at least 1")
                    return
            except ValueError:
                print("❌ Error: days_back must be a number")
                print_usage()
                return
        
        if len(sys.argv) >= 4:
            try:
                max_articles = int(sys.argv[3])
                if max_articles < 1:
                    print("❌ Error: max_articles must be at least 1")
                    return
                if max_articles > 100:
                    print("⚠️  Warning: Limiting to 100 articles maximum")
                    max_articles = 100
            except ValueError:
                print("❌ Error: max_articles must be a number")
                print_usage()
                return
        
        # Validate topic
        if not topic.strip():
            print("❌ Error: Topic cannot be empty")
            print_usage()
            return
        
        # Run day-based search
        await search_topic_news(topic.strip(), days_back, max_articles)

if __name__ == "__main__":
    asyncio.run(main())