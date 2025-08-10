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
                "pageSize": 100
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
            # Take more finance articles but ensure we have some general news too
            articles_data = finance_articles[:35] + other_articles[:15]  # Up to 50 articles
            
            print(f"✅ Fetched {len(all_articles)} total articles")
            print(f"   📊 {len(finance_articles)} finance-related")
            print(f"   📰 {len(other_articles)} general news")
            print(f"   ✨ Using {len(articles_data)} for briefing")
        else:
            print(f"❌ Error fetching articles: {response.status_code}")
            return
    
    # 2. Use Gemini to create AI-summarized briefing
    print("\n🤖 Creating AI-summarized briefing with Gemini...")
    
    # Prepare articles for Gemini
    article_texts = []
    for article in articles_data:
        title = article.get('title', 'No title')
        content = article.get('content', '')[:1000]  # Use more content for AI
        source = article.get('source', 'Unknown')
        
        if content:
            article_texts.append(f"Title: {title}\nSource: {source}\nContent: {content}\n---")
    
    combined_articles = "\n".join(article_texts)
    
    # Create prompt for Gemini
    prompt = f"""
    You are creating a 10-minute audio news briefing that covers both financial markets AND important world events.
    
    Current time of day: {get_time_greeting()}
    
    Articles to summarize:
    {combined_articles}
    
    Create a natural, conversational audio script that:
    1. Starts with "Good {get_time_greeting()}! Here's your comprehensive briefing for {datetime.now().strftime('%B %d')}."
    2. Structure: 70% finance/markets/crypto, 30% important world events
    3. Cover 12-15 stories total:
       - Start with major market moves (stocks, crypto, economy)
       - Include company earnings and significant business news
       - Cover Federal Reserve, inflation, or economic policy updates
       - Then transition to important non-financial news (geopolitics, tech breakthroughs, major events)
    4. Group related stories together
    5. Explain WHY each story matters and its potential impact
    6. Use smooth transitions like "Turning to..." or "Meanwhile in..."
    7. End with key takeaways covering both markets and world events
    
    Important formatting rules for audio:
    - Write "percent" not "%"
    - Write "dollars" not "$"
    - Write out numbers (ten thousand, not 10,000)
    - Keep sentences short and conversational
    - Total length should be 1400-1600 words (10 minutes when spoken at 150 words/minute)
    
    Do not include any markdown, asterisks, or formatting. Just plain conversational text.
    """
    
    try:
        response = model.generate_content(prompt)
        briefing_text = response.text.strip()
        print("✅ AI summary generated successfully")
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
    
    # 3. Generate audio using Kokoro TTS
    print("\n🎵 Generating audio file...")
    
    # Use the same text from the file for audio
    audio_script = briefing_text
    
    # Call Kokoro TTS
    audio_filename = f"briefing_{timestamp}.mp3"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8880/v1/audio/speech",
                json={
                    "input": audio_script,
                    "voice": "af_sky"  # or "af" for different voice
                }
            )
            
            if response.status_code == 200:
                # Save audio file
                with open(audio_filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Audio file generated: {audio_filename}")
                print(f"   File size: {len(response.content) / 1024:.1f} KB")
            else:
                print(f"❌ Error generating audio: {response.status_code}")
                
    except httpx.ConnectError:
        print("❌ Could not connect to Kokoro TTS.")
        print("   Make sure it's running: docker ps")
        print("   Or start it with: ./run.sh")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
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