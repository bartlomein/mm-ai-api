from typing import Dict, List, Optional
import os
import uuid
from datetime import datetime
import aiofiles

from .news_service import NewsService
from .summary_service import SummaryService
from .audio_service import AudioService
from .fmp_service import FMPService

class PipelineService:
    def __init__(self):
        self.news_service = NewsService()
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        self.fmp_service = FMPService()
        
        # Create temp directory for audio files (before Supabase integration)
        self.temp_dir = "/tmp/audio_briefings"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def generate_general_briefing(self, voice: Optional[str] = None) -> Dict:
        """
        Generate a general market briefing for free tier
        This will be called once daily at 6 AM EST
        """
        try:
            print("Step 1: Fetching general market news...")
            # 1. Fetch general market news
            articles = await self.news_service.fetch_general_market()
            
            if not articles:
                raise Exception("No articles fetched from news service")
            
            print(f"Fetched {len(articles)} articles")
            
            print("Step 2: Generating AI summary...")
            # 2. Generate AI summary
            script = await self.summary_service.create_general_script(articles)
            
            if not script:
                raise Exception("Failed to generate summary script")
            
            print(f"Generated script: {len(script)} characters")
            
            print("Step 3: Generating audio...")
            # 3. Generate audio
            audio_bytes = await self.audio_service.generate_audio(script, voice=voice, tier="free")
            
            if not audio_bytes:
                raise Exception("Failed to generate audio")
            
            print(f"Generated audio: {len(audio_bytes)} bytes")
            
            # 4. Save to temp file (later will upload to Supabase)
            file_id = str(uuid.uuid4())
            file_path = os.path.join(self.temp_dir, f"{file_id}.mp3")
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_bytes)
            
            print(f"Saved audio to: {file_path}")
            
            # 5. Prepare response
            duration = self.audio_service.estimate_duration(script)
            
            return {
                "id": file_id,
                "title": f"Morning Market Update - {datetime.now().strftime('%B %d')}",
                "file_path": file_path,
                "audio_url": f"/api/test/audio/{file_id}",  # Temporary URL
                "transcript": script,
                "duration_seconds": duration,
                "articles_processed": len(articles),
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            print(f"Pipeline error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def generate_personalized_briefing(self, tickers: List[str], voice: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
        """
        Generate a personalized briefing for premium tier
        """
        try:
            print(f"Step 1: Fetching news for tickers: {tickers}")
            # 1. Fetch news for specific tickers
            articles = await self.news_service.fetch_for_tickers(tickers)
            
            if not articles:
                # Fall back to general news if no ticker-specific news
                articles = await self.news_service.fetch_general_market()
            
            print(f"Fetched {len(articles)} articles")
            
            print("Step 2: Generating personalized AI summary...")
            # 2. Generate personalized summary
            script = await self.summary_service.create_personalized_script(articles, tickers)
            
            print(f"Generated script: {len(script)} characters")
            
            print("Step 3: Generating premium audio...")
            # 3. Generate audio with selected or premium voice
            audio_bytes = await self.audio_service.generate_audio(script, voice=voice, tier="premium")
            
            print(f"Generated audio: {len(audio_bytes)} bytes")
            
            # 4. Save to temp file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(self.temp_dir, f"{file_id}.mp3")
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_bytes)
            
            print(f"Saved audio to: {file_path}")
            
            # 5. Prepare response
            duration = self.audio_service.estimate_duration(script)
            
            return {
                "id": file_id,
                "title": f"Personalized Brief - {', '.join(tickers[:3])}",
                "file_path": file_path,
                "audio_url": f"/api/test/audio/{file_id}",
                "transcript": script,
                "duration_seconds": duration,
                "tickers": tickers,
                "articles_processed": len(articles),
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            print(f"Personalized pipeline error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def generate_market_data_briefing(self, focus_areas: Optional[List[str]] = None, voice: Optional[str] = None) -> Dict:
        """
        Generate a briefing based on real-time market data from FMP
        Focus areas: indices, crypto, movers, sectors, calendar, premarket, intraday
        """
        try:
            print("Step 1: Fetching real-time market data from FMP...")
            
            # Default focus areas if not specified
            if focus_areas is None:
                focus_areas = ["indices", "crypto", "movers", "sectors"]
            
            market_data_parts = []
            
            # Fetch different types of market data based on focus areas
            if "indices" in focus_areas:
                indices = await self.fmp_service.get_market_indices()
                if indices.get("summary"):
                    market_data_parts.append(f"Market Indices: {indices['summary']}")
            
            if "premarket" in focus_areas:
                premarket = await self.fmp_service.get_premarket_data()
                if premarket.get("summary"):
                    market_data_parts.append(f"Premarket Activity: {premarket['summary']}")
            
            if "crypto" in focus_areas:
                crypto = await self.fmp_service.get_crypto_overview()
                if crypto.get("summary"):
                    market_data_parts.append(f"Cryptocurrency Markets: {crypto['summary']}")
            
            if "movers" in focus_areas:
                movers = await self.fmp_service.get_market_movers()
                if movers.get("summary"):
                    market_data_parts.append(f"Market Movers: {movers['summary']}")
            
            if "sectors" in focus_areas:
                sectors = await self.fmp_service.get_sector_performance()
                if sectors.get("summary"):
                    market_data_parts.append(f"Sector Performance: {sectors['summary']}")
            
            if "calendar" in focus_areas:
                calendar = await self.fmp_service.get_economic_calendar()
                if calendar.get("summary"):
                    market_data_parts.append(f"Economic Events: {calendar['summary']}")
            
            # Combine all market data
            market_data_text = "\n\n".join(market_data_parts)
            
            print(f"Collected {len(market_data_parts)} market data sections")
            
            # Step 2: Fetch recent news for context
            print("Step 2: Fetching recent news for context...")
            articles = await self.news_service.fetch_general_market()
            
            # Step 3: Create enhanced script with market data
            print("Step 3: Generating AI summary with market data...")
            
            # Prepare enhanced prompt with market data
            enhanced_prompt = f"""
            Create a professional 5-minute market briefing using the following real-time market data and recent news.
            
            REAL-TIME MARKET DATA:
            {market_data_text}
            
            RECENT NEWS CONTEXT:
            {len(articles)} recent articles available for additional context.
            
            Format this as a natural, conversational briefing that a professional financial analyst would deliver.
            Include specific numbers and percentages from the market data.
            Make it exactly 750-850 words for a 5-minute audio briefing.
            """
            
            # Use summary service with enhanced data
            script = await self.summary_service.create_market_data_script(articles[:10], enhanced_prompt)
            
            if not script:
                # Fallback to simple market data summary
                script = await self.fmp_service.generate_market_briefing(focus_areas)
            
            print(f"Generated script: {len(script)} characters")
            
            # Step 4: Generate audio
            print("Step 4: Generating audio...")
            audio_bytes = await self.audio_service.generate_audio(script, voice=voice, tier="premium")
            
            print(f"Generated audio: {len(audio_bytes)} bytes")
            
            # Step 5: Save audio file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(self.temp_dir, f"{file_id}.mp3")
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_bytes)
            
            print(f"Saved audio to: {file_path}")
            
            # Prepare response
            duration = self.audio_service.estimate_duration(script)
            
            return {
                "id": file_id,
                "title": f"Market Data Brief - {datetime.now().strftime('%B %d, %H:%M')}",
                "file_path": file_path,
                "audio_url": f"/api/test/audio/{file_id}",
                "transcript": script,
                "duration_seconds": duration,
                "focus_areas": focus_areas,
                "data_sections": len(market_data_parts),
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            print(f"Market data pipeline error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def generate_intraday_update(self, symbols: List[str], hours: int = 8, voice: Optional[str] = None) -> Dict:
        """
        Generate an intraday update for specific symbols
        Answers questions like 'How has SPY done in the past 8 hours?'
        """
        try:
            print(f"Generating {hours}-hour update for {symbols}...")
            
            # Get intraday performance for each symbol
            summaries = []
            for symbol in symbols:
                print(f"Fetching intraday data for {symbol}...")
                intraday = await self.fmp_service.get_intraday_performance(symbol, "5min")
                if intraday.get("summary"):
                    summaries.append(intraday["summary"])
            
            if not summaries:
                raise Exception("No intraday data available")
            
            # Create script
            script = f"""
            Market Update - {datetime.now().strftime('%I:%M %p ET')}
            
            Here's how your watched symbols have performed over the past {hours} hours:
            
            {' '.join(summaries)}
            
            This intraday movement reflects current market sentiment and trading activity.
            """
            
            # Generate audio
            audio_bytes = await self.audio_service.generate_audio(script, voice=voice)
            
            # Save audio
            file_id = str(uuid.uuid4())
            file_path = os.path.join(self.temp_dir, f"{file_id}.mp3")
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_bytes)
            
            return {
                "id": file_id,
                "title": f"{hours}-Hour Update - {', '.join(symbols)}",
                "file_path": file_path,
                "audio_url": f"/api/test/audio/{file_id}",
                "transcript": script,
                "symbols": symbols,
                "hours": hours,
                "generated_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            print(f"Intraday update error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }