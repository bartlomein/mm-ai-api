from typing import Dict, List, Optional
import os
import uuid
from datetime import datetime
import aiofiles

from .news_service import NewsService
from .summary_service import SummaryService
from .audio_service import AudioService

class PipelineService:
    def __init__(self):
        self.news_service = NewsService()
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        
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