#!/usr/bin/env python3
"""
Premium Evening Briefing Generator V2
Generates comprehensive evening market briefings using multiple data sources:
- FMP: Daily trading data, market performance, sector analysis
- NewsAPI.ai: World, USA, finance, and tech news from last 18 hours
- Finlight: Financial market news
Focus: Full day recap with comprehensive market analysis (10-15 minute briefing)
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

class PremiumEveningBriefingV2:
    """Orchestrates the generation of premium evening briefings."""
    
    def __init__(self):
        """Initialize all required services."""
        self.fmp_service = FMPService()
        self.newsapiai_service = NewsAPIAIService()
        self.news_service = NewsService()  # Finlight
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        
    async def fetch_trading_data(self) -> Dict[str, Any]:
        """Fetch comprehensive daily trading data - full day recap for evening briefing."""
        print("\n📊 Fetching comprehensive daily trading data...")
        
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        current_day = datetime.now().weekday()
        is_weekend = current_day in [5, 6]
        
        trading_data = {}
        
        if not is_weekend:
            print("   📈 Fetching full day market data (weekday)...")
            
            # Get comprehensive market data in parallel
            market_tasks = await asyncio.gather(
                self.fmp_service.get_market_indices(),
                self.fmp_service.get_market_movers(),
                self.fmp_service.get_sector_performance(),
                self.fmp_service.get_intraday_performance("SPY", interval="1hour"),
                self.fmp_service.get_intraday_performance("QQQ", interval="1hour"),
                self.fmp_service.get_intraday_performance("DIA", interval="1hour"),
                return_exceptions=True
            )
            
            # Process results
            indices = market_tasks[0] if not isinstance(market_tasks[0], Exception) else {}
            movers = market_tasks[1] if not isinstance(market_tasks[1], Exception) else {}
            sectors = market_tasks[2] if not isinstance(market_tasks[2], Exception) else {}
            spy_intraday = market_tasks[3] if not isinstance(market_tasks[3], Exception) else {}
            qqq_intraday = market_tasks[4] if not isinstance(market_tasks[4], Exception) else {}
            dia_intraday = market_tasks[5] if not isinstance(market_tasks[5], Exception) else {}
            
            trading_data = {
                "indices": indices,
                "market_movers": movers,
                "sector_performance": sectors,
                "spy_intraday": spy_intraday,
                "qqq_intraday": qqq_intraday,
                "dia_intraday": dia_intraday,
                "summary": "Full day trading data available"
            }
        else:
            print("   🚫 Markets closed (weekend)")
            trading_data = {"summary": "Markets closed - Weekend"}
        
        # Fetch crypto data (24/7 market - always fetch)
        print("   ₿ Fetching crypto data (24/7)...")
        crypto_data = await self.fmp_service.get_crypto_overview()
        trading_data["crypto"] = crypto_data
        
        return trading_data
    
    async def fetch_world_news(self, hours_back: int = 18) -> List[Dict]:
        """Fetch world news from NewsAPI.ai (comprehensive daily coverage)."""
        print("\n🌍 Fetching world news (last 18 hours)...")
        
        # Try to use date-based search without complex keywords
        from datetime import datetime, timedelta
        
        # Calculate date range for last 18 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        # First try with date range
        result = await self.newsapiai_service.search_articles(
            keyword="news",  # Simple keyword
            date_start=start_date.strftime("%Y-%m-%d"),
            date_end=end_date.strftime("%Y-%m-%d"),
            max_articles=100,  # Stay within API limit
            sort_by="date"
        )
        
        # If no results with date range, try broader search (especially for weekends)
        if not result or not result.get("articles") or len(result.get("articles", [])) < 5:
            print("   🔄 Trying broader world news search...")
            result = await self.newsapiai_service.search_articles(
                keyword="world",
                max_articles=100,  # Stay within API limit
                sort_by="date"
            )
        
        # If still no results, try very broad search
        if not result or not result.get("articles") or len(result.get("articles", [])) < 5:
            print("   🔄 Trying very broad news search...")
            result = await self.newsapiai_service.search_articles(
                keyword="breaking news international",
                max_articles=100,
                sort_by="date"
            )
        
        articles = result.get("articles", []) if result else []
        print(f"   📰 Found {len(articles)} world articles")
        return articles[:75]  # Return top 75 for selection
    
    async def fetch_usa_news(self, hours_back: int = 18) -> List[Dict]:
        """Fetch USA domestic news from NewsAPI.ai (comprehensive daily coverage)."""
        print("\n🇺🇸 Fetching USA news (last 18 hours)...")
        
        # Just get recent US news without complex filtering
        result = await self.newsapiai_service.search_articles(
            keyword="United States",
            max_articles=100,  # Stay within API limit
            sort_by="date"
        )
        
        articles = result.get("articles", []) if result else []
        return articles[:75]  # Return top 75 for selection
    
    async def fetch_finance_news(self, hours_back: int = 18) -> Dict[str, List[Dict]]:
        """Fetch finance news from both Finlight and NewsAPI.ai."""
        print("\n💰 Fetching finance news from multiple sources...")
        
        # Fetch from Finlight - they return 100 articles by default
        finlight_articles = await self.news_service.fetch_general_market()
        
        # Fetch from NewsAPI.ai - get more financial news
        newsapi_result = await self.newsapiai_service.search_articles(
            keyword="stock market finance economy",
            max_articles=75,  # Get more articles
            sort_by="date"
        )
        newsapi_articles = newsapi_result.get("articles", []) if newsapi_result else []
        
        return {
            "finlight": finlight_articles[:50],  # Keep more articles for evening
            "newsapi": newsapi_articles[:50]     # Keep more articles for evening
        }
    
    async def fetch_tech_news(self, hours_back: int = 18) -> List[Dict]:
        """Fetch technology news from NewsAPI.ai."""
        print("\n💻 Fetching tech news (last 18 hours)...")
        
        # Get more tech news without complex filtering
        result = await self.newsapiai_service.search_articles(
            keyword="technology AI software",
            max_articles=100,  # Stay within API limit
            sort_by="date"
        )
        
        articles = result.get("articles", []) if result else []
        return articles[:75]  # Return top 75 for selection
    
    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all data sources in parallel."""
        print("\n🚀 Starting parallel data fetch from all sources...")
        
        # Run all fetches in parallel for efficiency
        results = await asyncio.gather(
            self.fetch_trading_data(),
            self.fetch_world_news(),
            self.fetch_usa_news(),
            self.fetch_finance_news(),
            self.fetch_tech_news(),
            return_exceptions=True
        )
        
        # Handle any errors gracefully
        trading_data = results[0] if not isinstance(results[0], Exception) else {"summary": "Trading data unavailable"}
        world_news = results[1] if not isinstance(results[1], Exception) else []
        usa_news = results[2] if not isinstance(results[2], Exception) else []
        finance_news = results[3] if not isinstance(results[3], Exception) else {"finlight": [], "newsapi": []}
        tech_news = results[4] if not isinstance(results[4], Exception) else []
        
        return {
            "trading_data": trading_data,
            "world_news": world_news,
            "usa_news": usa_news,
            "finance_news": finance_news,
            "tech_news": tech_news,
            "fetch_time": datetime.now().isoformat()
        }
    
    def select_top_stories(self, all_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Select the most relevant stories from each category (more for evening recap)."""
        print("\n📰 Selecting top stories from each category...")
        
        selected = {
            "world": [],
            "usa": [],
            "finance": [],
            "tech": []
        }
        
        # Select more stories for comprehensive evening recap
        world_news = all_data.get("world_news", [])
        selected["world"] = world_news[:50] if world_news else []
        
        # Select more USA news stories for evening
        usa_news = all_data.get("usa_news", [])
        selected["usa"] = usa_news[:35] if usa_news else []
        
        # Combine and select more finance stories
        finance = all_data.get("finance_news", {})
        finlight = finance.get("finlight", [])[:35]
        newsapi = finance.get("newsapi", [])[:25]
        
        # Merge finance sources, preferring diversity
        selected["finance"] = finlight[:20] + newsapi[:15] if finlight and newsapi else finlight + newsapi
        
        # Select more tech stories for evening
        tech_news = all_data.get("tech_news", [])
        selected["tech"] = tech_news[:35] if tech_news else []
        
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
        briefing_parts.append(f"PREMIUM EVENING MARKET BRIEFING")
        briefing_parts.append(f"Generated: {current_time.strftime('%B %d, %Y at %I:%M %p ET')}")
        briefing_parts.append("=" * 80)
        
        # Section 1: Daily Trading Recap (ENHANCED for evening)
        briefing_parts.append("\n📊 DAILY TRADING RECAP")
        briefing_parts.append("-" * 40)
        trading_data = all_data.get("trading_data", {})
        
        # Market indices
        indices = trading_data.get("indices", {})
        if indices and indices.get("data"):
            briefing_parts.append("Major Indices Performance:")
            for item in indices["data"]:
                symbol = item.get("symbol", "")
                price = item.get("price", 0)
                change = item.get("change", 0)
                pct = item.get("changesPercentage", 0)
                briefing_parts.append(f"  • {symbol}: ${price:.2f} ({change:+.2f}, {pct:+.2f}%)")
        
        # Market movers - more detailed for evening
        movers = trading_data.get("market_movers", {})
        if movers:
            if movers.get("gainers"):
                briefing_parts.append("\nTop Daily Gainers:")
                for gainer in movers["gainers"][:5]:  # Show more for evening
                    symbol = gainer.get("symbol", "")
                    price = gainer.get("price", 0)
                    pct = gainer.get("changesPercentage", 0)
                    briefing_parts.append(f"  • {symbol}: ${price:.2f} (+{pct:.2f}%)")
            
            if movers.get("losers"):
                briefing_parts.append("\nTop Daily Losers:")
                for loser in movers["losers"][:5]:  # Show more for evening
                    symbol = loser.get("symbol", "")
                    price = loser.get("price", 0)
                    pct = loser.get("changesPercentage", 0)
                    briefing_parts.append(f"  • {symbol}: ${price:.2f} ({pct:.2f}%)")
            
            if movers.get("most_active"):
                briefing_parts.append("\nMost Active Stocks:")
                for active in movers["most_active"][:5]:  # Show most active for evening
                    symbol = active.get("symbol", "")
                    price = active.get("price", 0)
                    volume = active.get("volume", 0)
                    briefing_parts.append(f"  • {symbol}: ${price:.2f} (Vol: {volume:,})")
        
        # Sector performance - comprehensive for evening
        sectors = trading_data.get("sector_performance", {})
        if sectors and sectors.get("sectors"):
            briefing_parts.append("\nSector Performance (Full Day):")
            for sector in sectors["sectors"][:8]:  # Show more sectors
                name = sector.get("sector", "")
                pct = sector.get("changesPercentage", 0)
                briefing_parts.append(f"  • {name}: {pct:+.2f}%")
        
        # Crypto (24/7)
        crypto = trading_data.get("crypto", {})
        if crypto and crypto.get("cryptos"):
            briefing_parts.append("\nCryptocurrency (24hr Performance):")
            for item in crypto["cryptos"][:5]:  # Show more crypto for evening
                symbol = item.get("symbol", "").replace("USD", "")
                price = item.get("price", 0)
                change_pct = item.get("changePercent", 0)
                briefing_parts.append(f"  • {symbol}: ${price:,.2f} ({change_pct:+.2f}%)")
        elif crypto and crypto.get("summary"):
            briefing_parts.append("\nCryptocurrency: " + crypto.get("summary", ""))
        
        if trading_data.get("summary") == "Markets closed - Weekend":
            briefing_parts.append("Markets are closed for the weekend.")
        
        # Section 2: World News Digest (Expanded)
        briefing_parts.append("\n🌍 WORLD NEWS DIGEST")
        briefing_parts.append("-" * 40)
        world_stories = selected_stories.get("world", [])
        if world_stories:
            for i, story in enumerate(world_stories[:30], 1):  # Show more world news for evening
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                # Show full content
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant world news in the past 18 hours.")
        
        # Section 3: USA Market News (Expanded)
        briefing_parts.append("\n🇺🇸 USA MARKET NEWS")
        briefing_parts.append("-" * 40)
        usa_stories = selected_stories.get("usa", [])
        if usa_stories:
            for i, story in enumerate(usa_stories[:20], 1):  # Show more USA stories
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant USA news in the past 18 hours.")
        
        # Section 4: Financial Sector Updates (Expanded)
        briefing_parts.append("\n💰 FINANCIAL SECTOR UPDATES")
        briefing_parts.append("-" * 40)
        finance_stories = selected_stories.get("finance", [])
        if finance_stories:
            for i, story in enumerate(finance_stories[:20], 1):  # Show more finance stories
                # Check for source - Finlight has 'source' as string, NewsAPI has it as dict or missing 'url' field
                is_finlight = "url" not in story or (isinstance(story.get("source"), str))
                source_tag = "[Finlight]" if is_finlight else "[NewsAPI.ai]"
                briefing_parts.append(f"\n{i}. {source_tag} {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant financial news in the past 18 hours.")
        
        # Section 5: Technology Highlights (Expanded)
        briefing_parts.append("\n💻 TECHNOLOGY HIGHLIGHTS")
        briefing_parts.append("-" * 40)
        tech_stories = selected_stories.get("tech", [])
        if tech_stories:
            for i, story in enumerate(tech_stories[:20], 1):  # Show more tech stories
                briefing_parts.append(f"\n{i}. {story.get('title', 'No title')}")
                content = story.get("content", "No content available")
                briefing_parts.append(f"\n{content}\n")
        else:
            briefing_parts.append("No significant tech news in the past 18 hours.")
        
        # Section 6: Market Synthesis
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
        briefing_parts.append("  • Financial Modeling Prep (FMP) - Market data & daily trading recap")
        briefing_parts.append("  • NewsAPI.ai - World, USA, and tech news")
        briefing_parts.append("  • Finlight - Financial market news")
        
        briefing_parts.append("\n" + "=" * 80)
        briefing_parts.append("END OF BRIEFING")
        
        return "\n".join(briefing_parts)
    
    async def summarize_and_select_articles(self, all_data: Dict[str, Any], selected_stories: Dict[str, List[Dict]]) -> str:
        """Use Gemini to summarize articles and select most important for 15-minute evening briefing."""
        print("\n🤖 Using Gemini to analyze and select most important articles...")
        
        # Prepare all articles with category labels
        all_articles = []
        
        # Add world news (more for evening)
        for article in selected_stories.get("world", [])[:30]:
            all_articles.append({
                "category": "WORLD",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add USA news (more for evening)
        for article in selected_stories.get("usa", [])[:20]:
            all_articles.append({
                "category": "USA",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add finance news (more for evening)
        for article in selected_stories.get("finance", [])[:20]:
            all_articles.append({
                "category": "FINANCE",
                "title": article.get("title", ""),
                "content": article.get("content", ""),
                "source": article.get("source", "")
            })
        
        # Add tech news (more for evening)
        for article in selected_stories.get("tech", [])[:20]:
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
        
        # Get trading data for context
        trading_data = all_data.get("trading_data", {})
        
        # Format trading data for prompt
        trading_summary = ""
        if trading_data.get("summary") == "Markets closed - Weekend":
            trading_summary = "Markets are closed for the weekend."
        else:
            # Build comprehensive trading summary
            indices = trading_data.get("indices", {})
            crypto = trading_data.get("crypto", {})
            movers = trading_data.get("market_movers", {})
            sectors = trading_data.get("sector_performance", {})
            
            if indices and indices.get("data"):
                trading_summary += "MARKET INDICES (DAILY PERFORMANCE):\n"
                for item in indices["data"]:
                    symbol = item.get("symbol", "")
                    price = item.get("price", 0)
                    pct = item.get("changesPercentage", 0)
                    trading_summary += f"  {symbol}: ${price:.2f} ({pct:+.2f}%)\n"
            
            if movers and movers.get("gainers"):
                trading_summary += "\nTOP DAILY GAINERS:\n"
                for gainer in movers["gainers"][:5]:
                    symbol = gainer.get("symbol", "")
                    pct = gainer.get("changesPercentage", 0)
                    trading_summary += f"  {symbol}: +{pct:.2f}%\n"
            
            if movers and movers.get("losers"):
                trading_summary += "\nTOP DAILY LOSERS:\n"
                for loser in movers["losers"][:5]:
                    symbol = loser.get("symbol", "")
                    pct = loser.get("changesPercentage", 0)
                    trading_summary += f"  {symbol}: {pct:.2f}%\n"
            
            if sectors and sectors.get("sectors"):
                trading_summary += "\nSECTOR PERFORMANCE:\n"
                for sector in sectors["sectors"][:5]:
                    name = sector.get("sector", "")
                    pct = sector.get("changesPercentage", 0)
                    trading_summary += f"  {name}: {pct:+.2f}%\n"
            
            if crypto and crypto.get("cryptos"):
                trading_summary += "\nCRYPTO (24hr):\n"
                for item in crypto["cryptos"][:5]:
                    symbol = item.get("symbol", "").replace("USD", "")
                    price = item.get("price", 0)
                    pct = item.get("changePercent", 0)
                    trading_summary += f"  {symbol}: ${price:,.2f} ({pct:+.2f}%)\n"
        
        # Get the current day name for closing
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_day = day_names[datetime.now().weekday()]
        
        # Create prompt for Gemini
        prompt = f"""
        You are a senior financial news editor creating a premium evening briefing for investors.
        
        TASK: Analyze the following {len(all_articles)} news articles and create a 15-minute professional evening briefing.
        
        Current Date: {datetime.now().strftime('%B %d, %Y')}
        Current Time: Evening wrap-up
        Market Status: {'Weekend - Markets Closed' if datetime.now().weekday() in [5, 6] else 'Weekday - Markets Closed'}
        
        DAILY TRADING RECAP:
        {trading_summary}
        
        ARTICLES TO ANALYZE:
        {articles_text}
        
        YOUR MISSION:
        1. SUMMARIZE each article accurately - use ONLY information from the article, NEVER make up details
        2. SELECT the 25-30 most important articles based on:
           - Market impact and relevance to investors
           - Breaking news or major developments
           - Geographic/sector diversity
           - Full day coverage (past 18 hours)
        
        3. CREATE a 15-minute briefing (2250 words) with this EXACT structure:
           
           START WITH: "Welcome to your MarketMotion Evening briefing. It's [date]. [If weekday and markets were open: 'Markets closed with...' followed by daily recap. If weekend: 'Markets are closed for the weekend, but here's what's happening in the world.']"
           Example weekday opening: "Welcome to your MarketMotion Evening briefing. It's August seventeenth. Markets closed with the S and P five hundred at five thousand four hundred, up point four percent. The Nasdaq finished at eighteen thousand two hundred, up half a percent."
           Example weekend opening: "Welcome to your MarketMotion Evening briefing. It's August seventeenth. Markets are closed for the weekend, but here's what's happening in the world."
           
           Then say "Today's top stories..." and provide 4-5 most critical developments (450 words total)
           
           Then say "Market highlights..." and cover key financial/economic news with trading performance analysis (450 words)
           
           Then say "Global developments..." and cover international news comprehensively (400 words)
           
           Then say "Technology and innovation..." and cover tech news in detail (350 words)
           
           Then say "Sector analysis..." and cover other sectors with trading performance (350 words)
           
           Then say "Looking ahead..." and provide forward-looking analysis for tomorrow/week (250 words)
           
           End with: "That concludes your MarketMotion Evening briefing. Have a great {current_day} evening!"
        
        CRITICAL FORMATTING RULES:
        - NO ASTERISKS anywhere in the text
        - NO BOLD formatting (no ** or *)
        - NO section headers in brackets or capitals
        - Use periods (.) instead of colons for section transitions: "Today's top stories." not "Today's top stories:"
        - For smooth transitions between sections, you can say things like "Moving to market highlights." or "Now for global developments."
        - Write everything as clean, flowing text ready for TTS
        
        ACCURACY RULES:
        - Use ONLY information from the provided articles and trading data
        - NO HALLUCINATION: Never invent facts, numbers, or quotes
        - If an article lacks detail, say "reports indicate" or "according to sources"
        - Include source attribution naturally in the text
        - Write in professional broadcast style
        - Use present tense for current events, past tense for completed market activity (if markets were open)
        
        ANTI-DUPLICATION RULES:
        - NEVER repeat the same event, company, or story across different sections
        - Before covering any story, check: "Have I already mentioned this event/company/topic?"
        - Each company, leader, country, or major event should only appear ONCE in the entire briefing
        - If similar stories exist, choose the most important one and ignore the rest
        - Ensure each section covers DIFFERENT topics - no overlap between sections
        
        FORMAT FOR TTS:
        - Stock tickers: "ticker A-B-C --" (spell out with dashes)
        - Percentages: "five percent" not "5%"
        - Large numbers: "two point five billion" not "2.5B"
        - Dates: "January fifteenth" not "Jan 15"
        - Company names: spell out abbreviations on first mention
        - NEVER use pipe characters (|) - use periods or commas for natural pauses
        - Separate statements with periods, not pipes: "S and P closed at 5,400, up one percent. Nasdaq finished at 18,200, up half a percent."
        - Section headers need double line breaks for longer TTS pauses: "Today's top stories.\n\nContent starts here"
        - Transition phrases need double line breaks: "Moving to market highlights.\n\nContent continues"
        - Individual stories within sections separated by single line breaks for natural flow
        
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
        """Generate the complete premium evening briefing."""
        print("\n" + "=" * 80)
        print("🌅 PREMIUM EVENING BRIEFING GENERATOR V2")
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
        raw_filename = f"premium_evening_raw_data_{timestamp}.txt"
        raw_briefing_text = self.format_for_briefing(all_data, selected_stories)
        with open(raw_filename, "w", encoding="utf-8") as f:
            f.write(raw_briefing_text)
        print(f"\n📊 Raw data saved to: {raw_filename}")
        print(f"   Raw data: {len(raw_briefing_text.split())} words")
        
        # Save Gemini-processed briefing
        filename = f"premium_evening_briefing_v2_{timestamp}.txt"
        
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
            print("   ⏱️ Estimated duration: ~12-15 minutes")
            print("   🐟 Using Fish Audio service (this may take 3-5 minutes)...")
            
            try:
                # Generate audio from the Gemini briefing text (returns bytes)
                audio_bytes = await self.audio_service.generate_audio(
                    text=gemini_briefing,  # Use the clean Gemini text
                    tier="premium"  # Use premium tier for best quality
                )
                
                # Save the audio bytes to a file
                audio_file = f"premium_evening_audio_{timestamp}.mp3"
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
                "trading_data_available": all_data["trading_data"].get("summary") != "Trading data unavailable",
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
    generator = PremiumEveningBriefingV2()
    
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
    print(f"📝 Gemini briefing: {result['gemini_word_count']} words (15-minute target)")
    print(f"📄 Raw articles: {result['raw_word_count']} words")
    print(f"\n📈 Content Summary:")
    print(f"   📊 Trading data available: {result['data_summary']['trading_data_available']}")
    print(f"   📰 Total articles analyzed: {result['data_summary']['total_articles']}")
    print(f"      🌍 World: {result['data_summary']['world_news']} stories")
    print(f"      🇺🇸 USA: {result['data_summary']['usa_news']} stories")
    print(f"      💰 Finance: {result['data_summary']['finance_news']} stories")
    print(f"      💻 Tech: {result['data_summary']['tech_news']} stories")
    if result.get('audio_file'):
        print(f"\n🎧 Audio briefing ready to play: {result['audio_file']}")
    else:
        print("\n💡 Audio generation was skipped or failed")
    

if __name__ == "__main__":
    asyncio.run(main())