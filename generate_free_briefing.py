#!/usr/bin/env python3
"""
MarketMotion briefing generator - Creates 5-minute market briefings
Comprehensive market analysis with full coverage
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.supabase_service import get_supabase_service

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

print("🎯 MarketMotion Briefing Generator")
print("=" * 50)

async def fetch_articles(limit=30):
    """Fetch limited articles for free tier"""
    print("📰 Fetching articles for free briefing...")
    
    api_key = os.getenv("FINLIGHT_API_KEY")
    if not api_key:
        print("❌ FINLIGHT_API_KEY not found in .env")
        return []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.finlight.me/v2/articles",
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-API-KEY": api_key
            },
            json={
                "includeContent": True,
                "includeEntities": False,
                "excludeEmptyContent": True,
                "pageSize": limit  # Fetch fewer articles for free tier
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ Fetched {len(articles)} articles for free briefing")
            return articles
        else:
            print(f"❌ Error fetching articles: {response.status_code}")
            return []

def generate_free_summary(articles):
    """Generate a 5-minute briefing (750 words) for free tier"""
    
    # Prepare article summaries - use more articles for fuller briefing
    article_texts = []
    for article in articles[:25]:  # Use top 25 articles for more content
        title = article.get('title', '')
        content = article.get('content', '')[:400]  # Longer excerpts
        article_texts.append(f"Title: {title}\nSummary: {content}")
    
    articles_text = "\n---\n".join(article_texts)
    
    prompt = f"""
    Create a comprehensive MarketMotion briefing of EXACTLY 750 words (5 minutes of audio).
    This is a FREE TIER briefing - provide solid market coverage with key insights.
    
    Use these articles:
    {articles_text}
    
    STRUCTURE (750 words total):
    1. Opening (20 words): Brief greeting with date. Say "Welcome to your MarketMotion daily briefing"
    2. Market Overview (150 words): Major indices, volume, and overall sentiment
    3. Top Stock Movers (150 words): Cover 5-7 significant movers
    4. Economic News (120 words): Important economic updates and Fed policy
    5. Technology Sector (100 words): Major tech developments
    6. Energy & Commodities (80 words): Oil, gold, and resource updates
    7. International Markets (80 words): Global market movements
    8. Closing (50 words): Wrap-up and outlook

    after each section that has a semicolon, make sure to do a semicolon and line break. 
    
    FORMATTING RULES:
    - Stock tickers: Write as "ticker A-A-P-L --" (spell letters with dashes)
    - Percentages: "five percent" not "5%"
    - Money: "billion dollars" not "$B"
    - Numbers: Write out in words
    - No markdown, no asterisks
    
    IMPORTANT: Start with "Welcome to your MarketMotion daily briefing" 
    
    WRITE EXACTLY 750 WORDS. Provide comprehensive market coverage.
    """
    
    try:
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 1200,
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text.strip()
        
        word_count = len(text.split())
        print(f"✅ Generated free briefing: {word_count} words")
        
        if word_count > 850:
            # Trim if too long
            words = text.split()
            text = " ".join(words[:750])
            print(f"   Trimmed to 750 words")
        
        return text
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return None

def get_briefing_type():
    """Determine briefing type based on time of day"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"

async def generate_audio(text, timestamp):
    """Generate audio using Fish Audio"""
    print("\n🎵 Generating audio file...")
    
    audio_filename = f"free_briefing_{timestamp}.mp3"
    audio_data = None
    
    fish_api_key = os.getenv("FISH_API_KEY")
    if fish_api_key:
        print("🐟 Using Fish Audio TTS...")
        try:
            from fish_audio_sdk import Session, TTSRequest
            import io
            
            session = Session(fish_api_key)
            
            fish_model_id = os.getenv("FISH_MODEL_ID")
            if fish_model_id:
                print(f"   Using voice model: {fish_model_id}")
                request = TTSRequest(
                    text=text,
                    reference_id=fish_model_id
                )
            else:
                print("   Using default Fish Audio voice")
                request = TTSRequest(text=text)
            
            audio_buffer = io.BytesIO()
            chunk_count = 0
            
            print("   Generating audio (5-minute version)...")
            async for chunk in session.tts.awaitable(request):
                audio_buffer.write(chunk)
                chunk_count += 1
                if chunk_count % 30 == 0:
                    print(f"   Received {chunk_count} chunks...")
            
            audio_data = audio_buffer.getvalue()
            
            # Save locally
            with open(audio_filename, 'wb') as f:
                f.write(audio_data)
            
            print(f"✅ Audio generated: {len(audio_data) / 1024:.1f} KB")
            
            # Estimate duration (roughly 150 words per minute)
            duration_seconds = int(len(text.split()) / 150 * 60)
            
            return audio_data, duration_seconds, audio_filename
            
        except Exception as e:
            print(f"❌ Fish Audio TTS failed: {str(e)}")
            return None, None, None
    else:
        print("❌ No FISH_API_KEY found")
        return None, None, None

async def create_free_briefing():
    """Create a 5-minute MarketMotion briefing for free users"""
    
    # Initialize Supabase service
    try:
        supabase = get_supabase_service()
        print("✅ Supabase service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        supabase = None
    
    # Fetch limited articles
    articles = await fetch_articles(limit=30)
    if not articles:
        print("❌ No articles to process")
        return
    
    print("\n🤖 Generating 5-minute MarketMotion briefing...")
    
    # Generate concise summary
    briefing_text = generate_free_summary(articles)
    
    if not briefing_text:
        print("❌ Failed to generate briefing")
        return
    
    # MarketMotion intro is already in the generated text, don't add extra
    # The prompt already includes "Welcome to your MarketMotion daily briefing"
    
    # Save text locally
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"free_briefing_{timestamp}.txt"
    
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write(briefing_text)
    
    word_count = len(briefing_text.split())
    print(f"\n✅ Free briefing text saved: {text_filename}")
    print(f"   Word count: {word_count} words")
    print(f"   Duration: ~{word_count / 150:.1f} minutes")
    
    # Generate audio
    audio_data, duration_seconds, local_audio_file = await generate_audio(briefing_text, timestamp)
    
    # Upload to Supabase if available
    if supabase and audio_data:
        try:
            print("\n☁️  Uploading free briefing to Supabase...")
            
            # Prepare metadata
            now = datetime.now()
            briefing_type = get_briefing_type()
            
            metadata = {
                "generated_at": now.isoformat(),
                "time_of_day": briefing_type,
                "day_of_week": now.strftime("%A"),
                "article_count": len(articles),
                "tier": "free",
                "version": "5-minute",
                "voice_model": os.getenv("FISH_MODEL_ID", "default")
            }
            
            # Upload audio file to free folder
            upload_result = await supabase.upload_briefing_audio(
                file_content=audio_data,
                filename=f"free_{briefing_type}_{timestamp}.mp3",
                briefing_type=f"free_{briefing_type}",  # Special type for free briefings
                date=now,
                metadata=metadata
            )
            
            if upload_result.get("success"):
                print(f"✅ Free briefing uploaded: {upload_result.get('path')}")
                
                # Save briefing metadata
                title = f"MarketMotion {briefing_type.capitalize()} Briefing - {now.strftime('%B %d, %Y')}"
                
                save_result = await supabase.save_briefing_metadata(
                    title=title,
                    briefing_type=f"free_{briefing_type}",
                    briefing_date=now,
                    text_content=briefing_text,
                    audio_file_path=upload_result.get("path"),
                    word_count=word_count,
                    duration_seconds=duration_seconds,
                    metadata=metadata,
                    tier="free"  # Mark as free tier
                )
                
                if save_result.get("success"):
                    print(f"✅ Free briefing metadata saved")
                    print(f"   Briefing ID: {save_result.get('briefing_id')}")
                    print(f"   Access: Available to all registered users")
                else:
                    print(f"⚠️  Failed to save metadata: {save_result.get('error')}")
            else:
                print(f"⚠️  Failed to upload: {upload_result.get('error')}")
                
        except Exception as e:
            print(f"⚠️  Supabase upload error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Free briefing generation complete!")
    print(f"📄 Text: {text_filename}")
    if local_audio_file:
        print(f"🎵 Audio: {local_audio_file}")
    print("⏱️  Duration: 5 minutes")
    print("🎯 MarketMotion briefing ready!")
    print("=" * 50)

if __name__ == "__main__":
    print("🎯 MarketMotion Daily Briefing Generator")
    print("   5-minute comprehensive market analysis")
    print("=" * 50)
    asyncio.run(create_free_briefing())