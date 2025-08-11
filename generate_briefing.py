#!/usr/bin/env python3
"""
Simple script to fetch articles, create AI-summarized briefing, and generate audio
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Check TTS configuration
print("🔧 TTS Configuration:")
print(f"   Fish Audio API Key present: {bool(os.getenv('FISH_API_KEY'))}")
print(f"   Fish Model ID: {os.getenv('FISH_MODEL_ID', 'Not set (will use default)')}")
print(f"   OpenAI API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")
print("" + "=" * 50)

# OpenAI Voice Options (used as fallback if Fish Audio not available)
OPENAI_VOICE = "onyx"  # Options: alloy, echo, fable, onyx, nova, shimmer

async def fetch_and_create_briefing():
    """
    Fetch articles, create text file, and generate audio
    """
    
    # 1. Fetch articles from Finlight
    print("📰 Fetching articles from Finlight...")
    
    api_key = os.getenv("FINLIGHT_API_KEY")
    if not api_key:
        print("❌ FINLIGHT_API_KEY not found in .env")
        return
    
    # Fetch articles
    articles_data = []
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
                "pageSize": 100  # Maximum allowed by Finlight API
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            all_articles = data.get('articles', [])
            
            # Prioritize finance-related articles
            finance_keywords = ['stock', 'market', 'invest', 'finance', 'earnings', 'economy', 
                               'fed', 'inflation', 'gdp', 'trading', 'ipo', 'merger', 'acquisition',
                               'revenue', 'profit', 'nasdaq', 'dow', 's&p', 'crypto', 'bitcoin',
                               'bank', 'fund', 'equity', 'bond', 'yield', 'rate', 'fiscal']
            
            finance_articles = []
            other_articles = []
            
            for article in all_articles:
                title = article.get('title', '').lower()
                content = article.get('content', '')[:500].lower()
                
                # Check if article is finance-related
                is_finance = any(kw in title or kw in content for kw in finance_keywords)
                
                if is_finance:
                    finance_articles.append(article)
                else:
                    other_articles.append(article)
            
            # Combine: mix finance articles with important general news
            # Take more articles for a comprehensive 5-minute briefing
            articles_data = finance_articles[:50] + other_articles[:25]  # Up to 75 articles for better selection
            
            print(f"✅ Fetched {len(all_articles)} total articles")
            print(f"   📊 {len(finance_articles)} finance-related")
            print(f"   📰 {len(other_articles)} general news")
            print(f"   ✨ Using {len(articles_data)} for briefing")
        else:
            print(f"❌ Error fetching articles: {response.status_code}")
            return
    
    # 2. Use Gemini to create AI-summarized briefing
    print("\n🤖 Creating AI-summarized briefing with Gemini...")
    
    # Prepare articles for Gemini - use more content for better summaries
    article_texts = []
    for article in articles_data[:50]:  # Use top 50 articles
        title = article.get('title', 'No title')
        content = article.get('content', '')[:2000]  # Use more content for better context
        source = article.get('source', 'Unknown')
        publish_date = article.get('publishDate', '')
        
        if content and len(content) > 100:  # Only include substantial articles
            article_texts.append(f"Title: {title}\nSource: {source}\nDate: {publish_date}\nContent: {content}\n---")
    
    combined_articles = "\n".join(article_texts)
    
    # Create prompt for Gemini - FORCE 800 WORDS
    prompt = f"""
    MANDATORY: Write EXACTLY 800 words. This is non-negotiable. Count the words.
    
    Create a detailed market news briefing for text-to-speech.
    
    Current time of day: {get_time_greeting()}
    Date: {datetime.now().strftime('%B %d, %Y')}
    
    Articles to summarize:
    {combined_articles}
    
    Create a natural, conversational audio script following these STRICT rules:
    
    CRITICAL CONTENT RULES:
    - AVOID REPETITION: If multiple articles mention the same company/event, discuss it ONLY ONCE
    - NO REDUNDANCY: Don't say "C3AI dropped 31%" multiple times
    - DIVERSE COVERAGE: Cover as many different companies as possible
    - Each ticker should appear only once in the entire briefing
    
    STRUCTURE:
    1. Opening (20 words): "Good {get_time_greeting()}. Here's your comprehensive market briefing for {datetime.now().strftime('%B %d')}. Let's begin with today's major market movements."
    2. Cover 8-10 stories with FULL DETAIL (each 75-100 words):
       - Major market movements (150 words total)
       - Company earnings and business news (200 words)
       - Economic indicators and Federal Reserve (150 words)
       - Tech sector updates (100 words)
       - Energy and commodities (100 words)
       - International markets (50 words)
    3. Use smooth transitions between topics
    4. Closing (20 words): "That concludes today's comprehensive briefing. Stay informed and have a successful trading day."
    
    CRITICAL PRONUNCIATION RULES:
    - Stock tickers: ALWAYS write as "ticker [spell out letters] --" with double dash for pause. 
      Example: "ticker A-A-P-L --" not "AAPL"
      The double dash creates a natural pause after the ticker.
    - Percentages: Write "percent" not "%". Example: "down eight percent"
    - Currency: Write "dollars", "euros", "pounds". Example: "twenty billion dollars"
    - Large numbers: Spell out completely:
      * 1,000 = "one thousand"
      * 25,000 = "twenty-five thousand"
      * 1,000,000 = "one million"
      * 2,700,000 = "two point seven million"
      * 5,000,000,000 = "five billion"
    - Dates: Write out months. Example: "February tenth" not "Feb 10"
    - Common abbreviations spelled out:
      * CEO = "C-E-O"
      * IPO = "I-P-O"
      * GDP = "G-D-P"
      * Fed = "Federal Reserve" or "the Fed"
      * S&P = "S and P"
      * AI = "A-I"
    
    PACING AND CLARITY:
    - Use short, clear sentences (max 20 words)
    - Add periods for natural pauses between topics
    - Use transitions: "In corporate news...", "Turning to the markets...", "Meanwhile in Asia..."
    - Avoid run-on sentences
    - Each story should be 3-5 sentences
    
    MANDATORY WORD COUNTS:
    - Introduction: 50 words
    - Story 1 (Market Overview): 120 words - Discuss indices, major movers, volume
    - Story 2 (Top Stock News): 120 words - Cover the biggest company story with full context
    - Story 3 (Earnings/Business): 120 words - Detailed earnings or merger news
    - Story 4 (Economic Data): 100 words - Fed, inflation, jobs, or GDP news
    - Story 5 (Tech Sector): 100 words - Major tech developments
    - Story 6 (Energy/Commodities): 80 words - Oil, gold, or commodity moves
    - Story 7 (International): 80 words - Global market developments  
    - Conclusion/Outlook: 30 words
    
    TOTAL: EXACTLY 800 WORDS. This is MANDATORY. Do not write less.
    
    FORBIDDEN:
    - No markdown formatting (*, **, #, etc.)
    - No parentheses or brackets
    - No URLs or web addresses
    - No abbreviations without spelling out
    - No special characters or symbols
    
    Remember: Every single word must be pronounceable by text-to-speech. When in doubt, spell it out.
    
    YOU MUST WRITE 800 WORDS. If you write less than 800 words, you have failed.
    Count the words. Write detailed analysis. Include numbers, context, implications.
    This is a professional 5-minute radio segment. WRITE 800 WORDS.
    """
    
    try:
        # Configure generation for longer output
        generation_config = {
            "temperature": 0.9,  # More creative for longer content
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,  # Allow longer output
            "candidate_count": 1
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        briefing_text = response.text.strip()
        
        # Verify length for 5-minute briefing
        word_count = len(briefing_text.split())
        print(f"✅ AI summary generated successfully")
        print(f"   Word count: {word_count} words")
        print(f"   Estimated duration: {word_count / 150:.1f} minutes")
        
        if word_count < 700:
            print(f"⚠️  Warning: Briefing is too short ({word_count} words). Target is 750-850 words.")
        elif word_count > 900:
            print(f"⚠️  Warning: Briefing is too long ({word_count} words). Target is 750-850 words.")
    except Exception as e:
        print(f"❌ Error with Gemini: {str(e)}")
        # Fallback to simple concatenation
        briefing_text = f"Good {get_time_greeting()}! Here's your news briefing. "
        for article in articles_data[:3]:
            content = article.get('content', '')[:200]
            briefing_text += f"{content} "
        briefing_text += "That's all for now."
    
    # Save to text file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"briefing_{timestamp}.txt"
    
    # Save to text file
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write(briefing_text)
    
    print(f"✅ Text briefing saved to: {text_filename}")
    print(f"   File size: {len(briefing_text)} characters")
    
    # 3. Generate audio using Fish Audio (primary) or OpenAI (fallback)
    print("\n🎵 Generating audio file...")
    
    # Use the same text from the file for audio
    audio_script = briefing_text
    audio_filename = f"briefing_{timestamp}.mp3"
    
    print(f"📏 Text length: {len(audio_script)} characters")
    
    # Try Fish Audio first (no character limit!)
    fish_api_key = os.getenv("FISH_API_KEY")
    if fish_api_key:
        print("🐟 Using Fish Audio TTS (no character limit!)...")
        try:
            from fish_audio_sdk import Session, TTSRequest
            import io
            
            # Initialize Fish Audio session
            session = Session(fish_api_key)
            
            # Create TTS request with consistent voice model
            fish_model_id = os.getenv("FISH_MODEL_ID")
            if fish_model_id:
                print(f"   Using specific voice model: {fish_model_id}")
                request = TTSRequest(
                    text=audio_script,
                    reference_id=fish_model_id  # Use consistent voice
                )
            else:
                print("   Using default Fish Audio voice")
                print("   Tip: Set FISH_MODEL_ID in .env for consistent voice")
                
                # Optionally list available models
                try:
                    models = list(session.list_models())
                    if models:
                        print(f"   Available models: {len(models)}")
                        for i, model in enumerate(models[:3]):
                            print(f"     - {model.id}: {model.title}")
                except:
                    pass
                
                request = TTSRequest(text=audio_script)
            
            # Collect audio chunks
            audio_data = io.BytesIO()
            chunk_count = 0
            
            # Generate audio
            print("   Generating audio...")
            async for chunk in session.tts.awaitable(request):
                audio_data.write(chunk)
                chunk_count += 1
                if chunk_count % 10 == 0:
                    print(f"   Received {chunk_count} chunks...")
            
            # Save audio file
            with open(audio_filename, 'wb') as f:
                f.write(audio_data.getvalue())
            
            print(f"✅ Audio file generated with Fish Audio: {audio_filename}")
            print(f"   File size: {len(audio_data.getvalue()) / 1024:.1f} KB")
            print(f"   Total chunks: {chunk_count}")
            
        except Exception as e:
            print(f"❌ Fish Audio TTS failed: {str(e)}")
            print("   Falling back to OpenAI...")
            fish_api_key = None  # Mark as failed to try OpenAI
    
    # Fallback to OpenAI if Fish Audio not available or failed
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not fish_api_key and openai_api_key:
        print("🎯 Using OpenAI TTS HD...")
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_api_key)
            
            # If text is too long, split into chunks
            if len(audio_script) > 4096:
                print(f"⚠️  Text exceeds OpenAI's 4096 char limit")
                print("   Splitting into chunks...")
                
                # Split text into chunks at sentence boundaries
                chunks = []
                current_chunk = ""
                sentences = audio_script.replace(". ", ".\n").split("\n")
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 < 4000:  # Leave some buffer
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                print(f"   Created {len(chunks)} chunks")
                
                # Generate audio for each chunk
                audio_parts = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"   Generating chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
                    response = openai_client.audio.speech.create(
                        model="tts-1-hd",
                        voice=OPENAI_VOICE,
                        input=chunk,
                        response_format="mp3",
                        speed=1.0
                    )
                    audio_parts.append(response.content)
                
                # Combine audio chunks (simple concatenation for MP3)
                print("   Combining audio chunks...")
                combined_audio = b''.join(audio_parts)
                
                # Save combined audio
                with open(audio_filename, 'wb') as f:
                    f.write(combined_audio)
                
                print(f"✅ Audio file generated with OpenAI (chunked): {audio_filename}")
                print(f"   File size: {len(combined_audio) / 1024:.1f} KB")
                
            else:
                # Text is short enough for single request
                print("   Model: tts-1-hd")
                print(f"   Voice: {OPENAI_VOICE}")
                
                response = openai_client.audio.speech.create(
                    model="tts-1-hd",
                    voice=OPENAI_VOICE,
                    input=audio_script,
                    response_format="mp3",
                    speed=1.0
                )
                
                # Save audio file
                with open(audio_filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Audio file generated with OpenAI: {audio_filename}")
                print(f"   File size: {len(response.content) / 1024:.1f} KB")
                
        except Exception as e:
            print(f"❌ OpenAI TTS failed: {str(e)}")
            print("   Please check your OPENAI_API_KEY in .env")
            
    else:
        print("❌ No OPENAI_API_KEY found in .env")
        print("   Please add your OpenAI API key to use TTS")
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ Briefing generation complete!")
    print(f"📄 Text file: {text_filename}")
    print(f"🎵 Audio file: {audio_filename}")
    print("=" * 50)

def get_time_greeting():
    """Get appropriate time-based greeting"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"

if __name__ == "__main__":
    print("🚀 Market Brief Generator")
    print("=" * 50)
    asyncio.run(fetch_and_create_briefing())