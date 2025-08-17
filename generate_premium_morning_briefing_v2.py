#!/usr/bin/env python3
"""
Premium Morning Briefing Generator V2
Generates comprehensive morning market briefings using multiple data sources:
- FMP: Economic calendar, premarket data, crypto prices
- NewsAPI.ai: World, USA, finance, and tech news from last 12 hours
- Finlight: Financial market news
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Fix for Python 3.13+ compatibility with pydub
try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop

from pydub import AudioSegment

# CRITICAL: Load environment variables BEFORE any imports that use them
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.fmp_service import FMPService
from src.services.newsapiai_service import NewsAPIAIService
from src.services.news_service import NewsService
from src.services.summary_service import SummaryService
from src.services.audio_service import AudioService

class PremiumMorningBriefingV2:
    """Orchestrates the generation of premium morning briefings."""
    
    def __init__(self):
        """Initialize all required services."""
        self.fmp_service = FMPService()
        self.newsapiai_service = NewsAPIAIService()
        self.news_service = NewsService()  # Finlight
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        
    async def fetch_economic_calendar(self) -> Dict[str, Any]:
        """Fetch today's economic calendar events from FMP."""
        print("\n📅 Fetching economic calendar...")
        
        # Get today and this week's events
        today = datetime.now().strftime("%Y-%m-%d")
        week_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        calendar_data = await self.fmp_service.get_economic_calendar(
            from_date=today,
            to_date=week_end,
            country="US"  # Focus on US events for morning briefing
        )
        
        # Separate today's events from the week
        today_events = []
        week_events = []
        
        if calendar_data and "events" in calendar_data:
            for event in calendar_data["events"]:
                event_date = event.get("date", "").split("T")[0]
                if event_date == today:
                    today_events.append(event)
                else:
                    week_events.append(event)
        
        return {
            "today": today_events,
            "week": week_events,
            "summary": calendar_data.get("summary", "") if calendar_data else "No economic events scheduled."
        }
    
    async def fetch_premarket_data(self) -> Dict[str, Any]:
        """Fetch premarket data for indices and crypto."""
        print("\n📊 Fetching premarket data...")
        
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        current_day = datetime.now().weekday()
        is_weekend = current_day in [5, 6]
        
        indices_premarket = {}
        if not is_weekend:
            # Only fetch index premarket data on weekdays
            print("   📈 Fetching index premarket (weekday)...")
            indices_premarket = await self.fmp_service.get_premarket_data(
                symbols=["SPY", "QQQ", "DIA"]  # DIA as proxy for DJI
            )
        else:
            print("   🚫 Skipping index premarket (weekend)")
            indices_premarket = {"summary": "Markets closed - Weekend"}
        
        # Fetch crypto data (24/7 market - always fetch)
        print("   ₿ Fetching crypto data (24/7)...")
        crypto_data = await self.fmp_service.get_crypto_overview()
        
        return {
            "indices": indices_premarket,
            "crypto": crypto_data
        }
    
    async def fetch_world_news(self, hours_back: int = 12) -> List[Dict]:
        """Fetch world news from NewsAPI.ai."""
        print("\n🌍 Fetching world news (last 12 hours)...")
        
        # Try to use date-based search without complex keywords
        from datetime import datetime, timedelta
        
        # Calculate date range for last 12 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        # First try with date range
        result = await self.newsapiai_service.search_articles(
            keyword="news",  # Simple keyword
            date_start=start_date.strftime("%Y-%m-%d"),
            date_end=end_date.strftime("%Y-%m-%d"),
            max_articles=100,  # Get LOTS more articles
            sort_by="date"
        )
        
        # If no results with date range, try without
        if not result or not result.get("articles"):
            result = await self.newsapiai_service.search_articles(
                keyword="world",
                max_articles=100,  # Get LOTS more articles
                sort_by="date"
            )
        
        articles = result.get("articles", []) if result else []
        return articles[:50]  # Return top 50 for selection
    
    async def fetch_usa_news(self, hours_back: int = 12) -> List[Dict]:
        """Fetch USA domestic news from NewsAPI.ai."""
        print("\n🇺🇸 Fetching USA news (last 12 hours)...")
        
        # Just get recent US news without complex filtering
        result = await self.newsapiai_service.search_articles(
            keyword="United States",
            max_articles=100,  # Get LOTS more articles
            sort_by="date"
        )
        
        articles = result.get("articles", []) if result else []
        return articles[:50]  # Return top 50 for selection
    
    async def fetch_finance_news(self, hours_back: int = 12) -> Dict[str, List[Dict]]:
        """Fetch finance news from both Finlight and NewsAPI.ai."""
        print("\n💰 Fetching finance news from multiple sources...")
        
        # Fetch from Finlight - they return 100 articles by default
        finlight_articles = await self.news_service.fetch_general_market()
        
        # Fetch from NewsAPI.ai - get more financial news
        newsapi_result = await self.newsapiai_service.search_articles(
            keyword="stock market finance economy",
            max_articles=50,  # Get more articles
            sort_by="date"
        )
        newsapi_articles = newsapi_result.get("articles", []) if newsapi_result else []
        
        return {
            "finlight": finlight_articles[:30],  # Keep more articles
            "newsapi": newsapi_articles[:30]     # Keep more articles
        }
    
    async def fetch_tech_news(self, hours_back: int = 12) -> List[Dict]:
        """Fetch technology news from NewsAPI.ai."""
        print("\n💻 Fetching tech news (last 12 hours)...")
        
        # Get more tech news without complex filtering
        result = await self.newsapiai_service.search_articles(
            keyword="technology AI software",
            max_articles=100,  # Get LOTS more articles
            sort_by="date"
        )
        
        articles = result.get("articles", []) if result else []
        return articles[:50]  # Return top 50 for selection
    
    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all data sources in parallel."""
        print("\n🚀 Starting parallel data fetch from all sources...")
        
        # Run all fetches in parallel for efficiency
        results = await asyncio.gather(
            self.fetch_economic_calendar(),
            self.fetch_premarket_data(),
            self.fetch_world_news(),
            self.fetch_usa_news(),
            self.fetch_finance_news(),
            self.fetch_tech_news(),
            return_exceptions=True
        )
        
        # Handle any errors gracefully
        economic_calendar = results[0] if not isinstance(results[0], Exception) else {"today": [], "week": [], "summary": "Calendar data unavailable"}
        premarket = results[1] if not isinstance(results[1], Exception) else {"indices": {}, "crypto": {}}
        world_news = results[2] if not isinstance(results[2], Exception) else []
        usa_news = results[3] if not isinstance(results[3], Exception) else []
        finance_news = results[4] if not isinstance(results[4], Exception) else {"finlight": [], "newsapi": []}
        tech_news = results[5] if not isinstance(results[5], Exception) else []
        
        return {
            "economic_calendar": economic_calendar,
            "premarket": premarket,
            "world_news": world_news,
            "usa_news": usa_news,
            "finance_news": finance_news,
            "tech_news": tech_news,
            "fetch_time": datetime.now().isoformat()
        }
    
    def select_top_stories(self, all_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Select the most relevant stories from each category."""
        print("\n📰 Selecting top stories from each category...")
        
        selected = {
            "world": [],
            "usa": [],
            "finance": [],
            "tech": []
        }
        
        # Select top 30 world news stories (massively increased for Gemini analysis)
        world_news = all_data.get("world_news", [])
        selected["world"] = world_news[:30] if world_news else []
        
        # Select top 20 USA news stories (increased for Gemini)
        usa_news = all_data.get("usa_news", [])
        selected["usa"] = usa_news[:20] if usa_news else []
        
        # Combine and select top finance stories
        finance = all_data.get("finance_news", {})
        finlight = finance.get("finlight", [])[:20]
        newsapi = finance.get("newsapi", [])[:20]
        
        # Merge finance sources, preferring diversity
        selected["finance"] = finlight[:12] + newsapi[:8] if finlight and newsapi else finlight + newsapi
        
        # Select top 20 tech stories (increased for Gemini)
        tech_news = all_data.get("tech_news", [])
        selected["tech"] = tech_news[:20] if tech_news else []
        
        # Print selection summary
        print(f"  - World news: {len(selected['world'])} stories")
        print(f"  - USA news: {len(selected['usa'])} stories")
        print(f"  - Finance news: {len(selected['finance'])} stories")
        print(f"  - Tech news: {len(selected['tech'])} stories")
        
        return selected
    
    def format_for_briefing(self, all_data: Dict[str, Any], selected_stories: Dict[str, List[Dict]]) -> str:
        """Format all data into a structured briefing text."""
        print("\n📝 Formatting briefing content...")
        
        briefing_parts = []
        
        # Header
        current_time = datetime.now()
        briefing_parts.append(f"PREMIUM MORNING MARKET BRIEFING")
        briefing_parts.append(f"Generated: {current_time.strftime('%B %d, %Y at %I:%M %p ET')}")
        briefing_parts.append("=" * 80)
        
        # Section 1: Economic Calendar
        briefing_parts.append("\n📅 ECONOMIC CALENDAR")
        briefing_parts.append("-" * 40)
        calendar = all_data.get("economic_calendar", {})
        today_events = calendar.get("today", [])
        
        if today_events:
            briefing_parts.append(f"Today's Events ({len(today_events)} total):")
            for event in today_events[:5]:  # Top 5 events
                time = event.get("date", "").split("T")[1][:5] if "T" in event.get("date", "") else "TBD"
                briefing_parts.append(f"  • {time} ET - {event.get('event', 'Unknown Event')}")
                if event.get("impact") == "High":
                    briefing_parts.append(f"    Impact: HIGH | Previous: {event.get('previous', 'N/A')} | Estimate: {event.get('estimate', 'N/A')}")
        else:
            briefing_parts.append("No major economic events scheduled for today.")
        
        # Section 2: Premarket Overview
        briefing_parts.append("\n📊 PREMARKET OVERVIEW")
        briefing_parts.append("-" * 40)
        premarket = all_data.get("premarket", {})
        
        # Indices premarket
        indices = premarket.get("indices", {})
        if indices and indices.get("data"):
            briefing_parts.append("Index Futures:")
            for item in indices["data"]:
                symbol = item.get("symbol", "")
                price = item.get("preMarketPrice", 0)
                change = item.get("preMarketChange", 0)
                pct = item.get("preMarketChangePercent", 0)
                if symbol == "DIA":
                    symbol = "DJI (via DIA)"
                briefing_parts.append(f"  • {symbol}: ${price:.2f} ({change:+.2f}, {pct:+.2f}%)")
        elif indices and indices.get("summary"):
            # Show summary message (e.g., weekend closure)
            briefing_parts.append(f"Index Futures: {indices.get('summary', 'No premarket data available')}")
        
        # Crypto premarket (24/7)
        crypto = premarket.get("crypto", {})
        if crypto and crypto.get("cryptos"):
            briefing_parts.append("\nCryptocurrency (24hr):")
            for item in crypto["cryptos"][:3]:  # BTC, ETH, and one more
                symbol = item.get("symbol", "").replace("USD", "")
                price = item.get("price", 0)
                change_pct = item.get("changePercent", 0)
                briefing_parts.append(f"  • {symbol}: ${price:,.2f} ({change_pct:+.2f}%)")
        elif crypto and crypto.get("summary"):
            briefing_parts.append("\nCryptocurrency: " + crypto.get("summary", ""))
        
        if not indices and not crypto:
            briefing_parts.append("Market data temporarily unavailable.")
        
        # Section 3: World News Digest
        briefing_parts.append("\n🌍 WORLD NEWS DIGEST")
        briefing_parts.append("-" * 40)
        world_stories = selected_stories.get("world", [])
        if world_stories:
            for i, story in enumerate(world_stories[:20], 1):  # Show 20 world news stories for Gemini
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                # Show full content
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant world news in the past 12 hours.")
        
        # Section 4: USA Market News
        briefing_parts.append("\n🇺🇸 USA MARKET NEWS")
        briefing_parts.append("-" * 40)
        usa_stories = selected_stories.get("usa", [])
        if usa_stories:
            for i, story in enumerate(usa_stories[:10], 1):  # Show 10 USA stories
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant USA news in the past 12 hours.")
        
        # Section 5: Financial Sector Updates
        briefing_parts.append("\n💰 FINANCIAL SECTOR UPDATES")
        briefing_parts.append("-" * 40)
        finance_stories = selected_stories.get("finance", [])
        if finance_stories:
            for i, story in enumerate(finance_stories[:10], 1):  # Show 10 finance stories
                # Check for source - Finlight has 'source' as string, NewsAPI has it as dict or missing 'url' field
                is_finlight = "url" not in story or (isinstance(story.get("source"), str))
                source_tag = "[Finlight]" if is_finlight else "[NewsAPI.ai]"
                briefing_parts.append(f"\n{i}. {source_tag} {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant financial news in the past 12 hours.")
        
        # Section 6: Technology Highlights
        briefing_parts.append("\n💻 TECHNOLOGY HIGHLIGHTS")
        briefing_parts.append("-" * 40)
        tech_stories = selected_stories.get("tech", [])
        if tech_stories:
            for i, story in enumerate(tech_stories[:10], 1):  # Show 10 tech stories
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant tech news in the past 12 hours.")
        
        # Section 7: Market Synthesis
        briefing_parts.append("\n🎯 MARKET SYNTHESIS")
        briefing_parts.append("-" * 40)
        
        # Calculate some quick stats
        total_stories = sum(len(stories) for stories in selected_stories.values())
        briefing_parts.append(f"Total stories analyzed: {total_stories}")
        
        # Sentiment summary if available
        all_sentiments = []
        for category_stories in selected_stories.values():
            for story in category_stories:
                if "sentiment" in story and story["sentiment"] is not None:
                    all_sentiments.append(story["sentiment"])
        
        if all_sentiments:
            avg_sentiment = sum(all_sentiments) / len(all_sentiments)
            sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
            briefing_parts.append(f"Overall news sentiment: {sentiment_label} ({avg_sentiment:.2f})")
        
        # Data sources
        briefing_parts.append("\nData Sources:")
        briefing_parts.append("  • Financial Modeling Prep (FMP) - Market data & calendar")
        briefing_parts.append("  • NewsAPI.ai - World, USA, and tech news")
        briefing_parts.append("  • Finlight - Financial market news")
        
        briefing_parts.append("\n" + "=" * 80)
        briefing_parts.append("END OF BRIEFING")
        
        return "\n".join(briefing_parts)
    
    async def summarize_and_select_articles(self, all_data: Dict[str, Any], selected_stories: Dict[str, List[Dict]]) -> str:
        """Use Gemini to summarize articles and select most important for 10-minute briefing."""
        print("\n🤖 Using Gemini to analyze and select most important articles...")
        
        # Prepare all articles with category labels
        all_articles = []
        
        # Add world news
        for article in selected_stories.get("world", [])[:20]:
            all_articles.append({
                "category": "WORLD",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add USA news
        for article in selected_stories.get("usa", [])[:10]:
            all_articles.append({
                "category": "USA",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add finance news
        for article in selected_stories.get("finance", [])[:10]:
            all_articles.append({
                "category": "FINANCE",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add tech news
        for article in selected_stories.get("tech", [])[:10]:
            all_articles.append({
                "category": "TECH",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Format articles for Gemini
        articles_text = ""
        for i, article in enumerate(all_articles, 1):
            articles_text += f"\n[ARTICLE {i} - {article['category']}]\n"
            articles_text += f"Title: {article['title']}\n"
            articles_text += f"Source: {article['source']}\n"
            articles_text += f"Content: {article['content'][:2000]}\n"  # Limit each to 2000 chars
            articles_text += "-" * 40 + "\n"
        
        # Get market data for context
        premarket = all_data.get("premarket", {})
        crypto = premarket.get("crypto", {})
        crypto_summary = crypto.get("summary", "") if crypto else ""
        
        # Get the current day name for closing
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_day = day_names[datetime.now().weekday()]
        
        # Create prompt for Gemini
        prompt = f"""
        You are a senior financial news editor creating a premium morning briefing for investors.
        
        TASK: Analyze the following {len(all_articles)} news articles and create a 10-minute professional morning briefing.
        
        Current Date: {datetime.now().strftime('%B %d, %Y')}
        Market Status: {'Weekend - Markets Closed' if datetime.now().weekday() in [5, 6] else 'Weekday'}
        Crypto Overview: {crypto_summary}
        
        ARTICLES TO ANALYZE:
        {articles_text}
        
        YOUR MISSION:
        1. SUMMARIZE each article accurately - use ONLY information from the article, NEVER make up details
        2. SELECT the 15-20 most important articles based on:
           - Market impact and relevance to investors
           - Breaking news or major developments
           - Geographic/sector diversity
           - Timeliness (prefer very recent news)
        
        3. CREATE a 10-minute briefing (1500 words) with this EXACT structure:
           
           START WITH: "Welcome to your MarketMotion Daily briefing. It's [date], and [market status]. [crypto overview if relevant - use periods to separate crypto prices, not pipes]"
           Example opening: "Welcome to your MarketMotion Daily briefing. It's August seventeenth, and markets are closed for the weekend. Bitcoin is at one hundred eighteen thousand dollars, up point eight percent. Ethereum is at four thousand five hundred dollars, up three percent."
           
           Then say "Top stories..." and provide 3-4 most critical developments (400 words total)
           
           Then say "Market movers..." and cover key financial/economic news (300 words)
           
           Then say "Global developments..." and cover international news (300 words)
           
           Then say "Technology and innovation..." and cover tech news (250 words)
           
           Then say "Sector highlights..." and cover other sectors (200 words)
           
           End with: "That concludes your MarketMotion Daily briefing. Have a great {current_day}!"
        
        CRITICAL FORMATTING RULES:
        - NO ASTERISKS anywhere in the text
        - NO BOLD formatting (no ** or *)
        - NO section headers in brackets or capitals
        - Use ellipses (...) instead of colons for section transitions: "Top stories..." not "Top stories:"
        - For smooth transitions between sections, you can say things like "Moving to market movers..." or "Now for global developments..."
        - Write everything as clean, flowing text ready for TTS
        
        ACCURACY RULES:
        - Use ONLY information from the provided articles
        - NO HALLUCINATION: Never invent facts, numbers, or quotes
        - If an article lacks detail, say "reports indicate" or "according to sources"
        - Include source attribution naturally in the text
        - Write in professional broadcast style
        - Use present tense for current events
        
        FORMAT FOR TTS:
        - Stock tickers: "ticker A-B-C --" (spell out with dashes)
        - Percentages: "five percent" not "5%"
        - Large numbers: "two point five billion" not "2.5B"
        - Dates: "January fifteenth" not "Jan 15"
        - Company names: spell out abbreviations on first mention
        - NEVER use pipe characters (|) - use periods or commas for natural pauses
        - Separate statements with periods, not pipes: "Bitcoin at $118,000, up one percent. Ethereum at $4,500, up two percent."
        
        Generate the clean, TTS-ready briefing now:
        """
        
        # Call Gemini
        try:
            response = self.summary_service.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini error: {str(e)}")
            return "Error generating summary. Please check Gemini API configuration."
    
    def stitch_audio_with_intro(self, main_audio_file: str, intro_file: str = "intro1.mp3") -> str:
        """
        Stitch an intro audio file to the beginning of the main audio file.
        
        Args:
            main_audio_file: Path to the main briefing audio file
            intro_file: Path to the intro audio file (default: intro1.mp3)
        
        Returns:
            Path to the combined audio file
        """
        try:
            print(f"\n🎵 Adding intro to audio briefing...")
            
            # Check if intro file exists
            if not os.path.exists(intro_file):
                print(f"⚠️ Intro file '{intro_file}' not found. Skipping intro...")
                return main_audio_file
            
            # Load audio files
            print(f"   📁 Loading intro: {intro_file}")
            intro_audio = AudioSegment.from_mp3(intro_file)
            
            print(f"   📁 Loading main audio: {main_audio_file}")
            main_audio = AudioSegment.from_mp3(main_audio_file)
            
            # Combine audio files (intro + main)
            print(f"   🔗 Stitching audio files...")
            combined_audio = intro_audio + main_audio
            
            # Generate output filename
            base_name = os.path.splitext(main_audio_file)[0]
            output_file = f"{base_name}_with_intro.mp3"
            
            # Export combined audio
            print(f"   💾 Saving combined audio...")
            combined_audio.export(output_file, format="mp3")
            
            # Calculate durations
            intro_duration = len(intro_audio) / 1000  # Convert to seconds
            main_duration = len(main_audio) / 1000
            total_duration = len(combined_audio) / 1000
            
            print(f"\n✅ Audio successfully combined!")
            print(f"   🎵 Intro duration: {intro_duration:.1f} seconds")
            print(f"   📻 Main duration: {main_duration/60:.1f} minutes")
            print(f"   ⏱️ Total duration: {total_duration/60:.1f} minutes")
            print(f"   📁 Output file: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Error stitching audio: {str(e)}")
            print(f"   Returning original file without intro")
            return main_audio_file
    
    async def generate_briefing(self, create_audio: bool = False) -> Dict[str, Any]:
        """Generate the complete premium morning briefing."""
        print("\n" + "=" * 80)
        print("🌅 PREMIUM MORNING BRIEFING GENERATOR V2")
        print("=" * 80)
        
        # Step 1: Fetch all data
        all_data = await self.fetch_all_data()
        
        # Step 2: Select top stories
        selected_stories = self.select_top_stories(all_data)
        
        # Step 3: Use Gemini to summarize and select most important articles
        gemini_briefing = await self.summarize_and_select_articles(all_data, selected_stories)
        
        # Step 4: Combine raw data and Gemini summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data file
        raw_filename = f"premium_morning_raw_data_{timestamp}.txt"
        raw_briefing_text = self.format_for_briefing(all_data, selected_stories)
        with open(raw_filename, "w", encoding="utf-8") as f:
            f.write(raw_briefing_text)
        print(f"\n📊 Raw data saved to: {raw_filename}")
        print(f"   Raw data: {len(raw_briefing_text.split())} words")
        
        # Save Gemini-processed briefing
        filename = f"premium_morning_briefing_v2_{timestamp}.txt"
        
        # Save clean TTS-ready version (just the Gemini content)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(gemini_briefing)
        
        print(f"✅ AI Briefing saved to: {filename}")
        print(f"📄 AI Briefing length: {len(gemini_briefing.split())} words")
        
        # Step 5: Create audio if requested
        audio_file = None
        if create_audio:
            print("\n🎙️ Generating audio briefing with Fish Audio...")
            print("   📝 Text length:", len(gemini_briefing.split()), "words")
            print("   ⏱️ Estimated duration: ~7-10 minutes")
            print("   🐟 Using Fish Audio service (this may take 2-3 minutes)...")
            
            try:
                # Generate audio from the Gemini briefing text (returns bytes)
                audio_bytes = await self.audio_service.generate_audio(
                    text=gemini_briefing,  # Use the clean Gemini text
                    tier="premium"  # Use premium tier for best quality
                )
                
                # Save the audio bytes to a file
                audio_file = f"premium_morning_audio_{timestamp}.mp3"
                with open(audio_file, 'wb') as f:
                    f.write(audio_bytes)
                
                # Calculate file size
                file_size_mb = len(audio_bytes) / (1024 * 1024)
                estimated_duration = len(gemini_briefing.split()) / 150  # Approximate 150 words per minute
                
                print(f"\n✅ Audio successfully generated!")
                print(f"   🎵 File: {audio_file}")
                print(f"   ⏱️ Estimated duration: {estimated_duration:.1f} minutes")
                print(f"   📁 Size: {file_size_mb:.1f} MB")
                
                # Stitch intro audio to the beginning
                final_audio_file = self.stitch_audio_with_intro(audio_file)
                
                # Update audio_file to point to the combined version
                if final_audio_file != audio_file:
                    audio_file = final_audio_file
                
            except Exception as e:
                print(f"❌ Audio generation failed: {str(e)}")
                audio_file = None
        
        # Return results
        return {
            "success": True,
            "briefing_file": filename,
            "raw_data_file": raw_filename,
            "audio_file": audio_file,
            "gemini_word_count": len(gemini_briefing.split()),
            "raw_word_count": len(raw_briefing_text.split()),
            "data_summary": {
                "economic_events": len(all_data["economic_calendar"]["today"]),
                "world_news": len(selected_stories["world"]),
                "usa_news": len(selected_stories["usa"]),
                "finance_news": len(selected_stories["finance"]),
                "tech_news": len(selected_stories["tech"]),
                "total_articles": sum([
                    len(selected_stories["world"]),
                    len(selected_stories["usa"]),
                    len(selected_stories["finance"]),
                    len(selected_stories["tech"])
                ])
            },
            "timestamp": timestamp
        }


async def main():
    """Main execution function."""
    generator = PremiumMorningBriefingV2()
    
    # Generate briefing WITH audio
    result = await generator.generate_briefing(create_audio=True)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 GENERATION SUMMARY")
    print("=" * 80)
    print(f"✅ AI Briefing: {result['briefing_file']}")
    print(f"📊 Raw data file: {result['raw_data_file']}")
    if result.get('audio_file'):
        print(f"🎵 Audio file: {result['audio_file']}")
    print(f"📝 Gemini briefing: {result['gemini_word_count']} words (10-minute target)")
    print(f"📄 Raw articles: {result['raw_word_count']} words")
    print(f"\n📈 Articles Analyzed:")
    print(f"   Total: {result['data_summary']['total_articles']} articles")
    print(f"   🌍 World: {result['data_summary']['world_news']} stories")
    print(f"   🇺🇸 USA: {result['data_summary']['usa_news']} stories")
    print(f"   💰 Finance: {result['data_summary']['finance_news']} stories")
    print(f"   💻 Tech: {result['data_summary']['tech_news']} stories")
    print(f"   📅 Economic events: {result['data_summary']['economic_events']}")
    if result.get('audio_file'):
        print(f"\n🎧 Audio briefing ready to play: {result['audio_file']}")
    else:
        print("\n💡 Audio generation was skipped or failed")
    

if __name__ == "__main__":
    asyncio.run(main())