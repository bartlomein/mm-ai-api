#!/usr/bin/env python3
"""
Enhanced briefing generator that includes cryptocurrency analysis.
Based on generate_briefing_v2.py with added crypto section.
"""

import asyncio
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Import our crypto analyzer
from crypto_analysis import CryptoAnalyzer

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Check TTS configuration
print("🔧 TTS Configuration:")
print(f"   Fish Audio API Key present: {bool(os.getenv('FISH_API_KEY'))}")
print(f"   Fish Model ID: {os.getenv('FISH_MODEL_ID', 'Not set (will use default)')}")
print(f"   OpenAI API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")
print("=" * 50)

async def fetch_articles():
    """Fetch articles from Finlight"""
    print("📰 Fetching articles from Finlight...")
    
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
                "pageSize": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            print(f"✅ Fetched {len(articles)} articles")
            return articles[:20]  # Return top 20
        else:
            print(f"❌ Failed to fetch articles: {response.status_code}")
            return []

async def fetch_crypto_analysis():
    """Fetch cryptocurrency analysis"""
    print("🔍 Analyzing cryptocurrency markets...")
    
    try:
        analyzer = CryptoAnalyzer()
        crypto_summary = await analyzer.get_crypto_summary_for_briefing(8)
        print("✅ Crypto analysis complete")
        return crypto_summary
    except Exception as e:
        print(f"❌ Crypto analysis failed: {str(e)}")
        return "Cryptocurrency data is currently unavailable."

def get_time_greeting():
    """Get appropriate time-based greeting"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"

async def generate_briefing_section(section_name, word_target, articles, crypto_data=None):
    """Generate a specific section of the briefing"""
    print(f"🔄 Generating {section_name} section ({word_target} words)...")
    
    # Prepare article text
    article_texts = []
    for article in articles[:10]:  # Use top 10 articles per section
        title = article.get('title', 'No title')
        content = article.get('content', '')[:1000]  # Limit content per article
        source = article.get('source', 'Unknown')
        
        if content:
            article_texts.append(f"Title: {title}\nSource: {source}\nContent: {content}\n---")
    
    combined_articles = "\n".join(article_texts)
    
    # Create section-specific prompts
    section_prompts = {
        "Market Overview": f"""
        Create a market overview section focusing on major indices, market sentiment, and overall trends.
        Target: exactly {word_target} words.
        
        Articles:
        {combined_articles}
        
        Focus on: S&P 500, Dow Jones, NASDAQ, market sentiment, volume, sector performance.
        """,
        
        "Stock News": f"""
        Create a stock news section covering individual company movements and earnings.
        Target: exactly {word_target} words.
        
        Articles:
        {combined_articles}
        
        Focus on: Individual stock movements, earnings reports, analyst upgrades/downgrades, company news.
        """,
        
        "Economic Data": f"""
        Create an economic data section covering Fed policy, inflation, employment, and economic indicators.
        Target: exactly {word_target} words.
        
        Articles:
        {combined_articles}
        
        Focus on: Federal Reserve, inflation data, employment reports, GDP, economic indicators.
        """,
        
        "Cryptocurrency": f"""
        Create a cryptocurrency section using the provided analysis.
        Target: exactly {word_target} words.
        
        Crypto Analysis:
        {crypto_data or "Cryptocurrency data unavailable."}
        
        Expand on the crypto analysis with market context, institutional adoption news, and regulatory developments.
        Use the provided price data and add relevant commentary about the broader crypto market.
        """,
        
        "International": f"""
        Create an international markets section covering global markets and geopolitical news.
        Target: exactly {word_target} words.
        
        Articles:
        {combined_articles}
        
        Focus on: European markets, Asian markets, currency movements, geopolitical events affecting markets.
        """
    }
    
    base_prompt = section_prompts.get(section_name, f"""
    Create a {section_name} section for a market briefing.
    Target: exactly {word_target} words.
    
    Articles:
    {combined_articles}
    """)
    
    full_prompt = f"""
    {base_prompt}
    
    CRITICAL PRONUNCIATION RULES FOR TEXT-TO-SPEECH:
    - Stock tickers: ALWAYS write as "ticker [spell out letters] --" with double dash for pause.
      Example: "ticker A-A-P-L --" not "AAPL"
    - Percentages: Write "percent" not "%". Example: "up five percent"
    - Currency: Write "dollars", "euros", "pounds". Example: "fifty billion dollars"
    - Large numbers: Spell out completely:
      * 1,000 = "one thousand"
      * 1,500,000 = "one point five million"
      * 2,300,000,000 = "two point three billion"
    - Abbreviations: Spell out:
      * CEO = "C-E-O"
      * GDP = "G-D-P"
      * AI = "A-I"
    
    OUTPUT REQUIREMENTS:
    - EXACTLY {word_target} words (no more, no less)
    - Natural, conversational tone
    - No markdown formatting
    - No parentheses or special characters
    - Professional financial news style
    """
    
    try:
        response = model.generate_content(full_prompt)
        section_text = response.text.strip()
        
        word_count = len(section_text.split())
        print(f"   Generated {word_count} words for {section_name}")
        
        return section_text
    except Exception as e:
        print(f"❌ Error generating {section_name}: {str(e)}")
        return f"Error generating {section_name} section."

async def generate_audio(text, filename):
    """Generate audio using the existing audio service pattern"""
    print(f"🔊 Generating audio: {filename}")
    
    try:
        # Import the audio service
        import sys
        sys.path.append('./src')
        from services.audio_service import AudioService
        
        audio_service = AudioService()
        audio_bytes = await audio_service.generate_audio(text, tier="free")
        
        with open(filename, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"✅ Audio saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Audio generation failed: {str(e)}")
        return False

async def main():
    """Main briefing generation function"""
    print("🎯 Starting Enhanced Market Briefing Generation (with Crypto)")
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"⏰ Time: {datetime.now().strftime('%I:%M %p')}")
    print("=" * 60)
    
    # Step 1: Fetch data
    articles_task = fetch_articles()
    crypto_task = fetch_crypto_analysis()
    
    articles, crypto_data = await asyncio.gather(articles_task, crypto_task)
    
    if not articles:
        print("❌ No articles available. Exiting.")
        return
    
    # Step 2: Generate sections
    greeting = get_time_greeting()
    date_str = datetime.now().strftime('%B %d')
    
    # Define section structure for 5-minute briefing (800 words total)
    sections = [
        ("Opening", 20),
        ("Market Overview", 150),
        ("Stock News", 150),
        ("Economic Data", 120),
        ("Cryptocurrency", 100),  # New crypto section
        ("International", 80),
        ("Closing", 30)
    ]
    
    # Generate opening
    opening = f"Good {greeting}. Here's your enhanced market briefing for {date_str}, including cryptocurrency analysis. Let's begin with today's major developments."
    
    briefing_parts = [opening]
    
    # Generate each section
    for section_name, word_target in sections[1:-1]:  # Skip opening and closing
        if section_name == "Cryptocurrency":
            section_text = await generate_briefing_section(section_name, word_target, articles, crypto_data)
        else:
            section_text = await generate_briefing_section(section_name, word_target, articles)
        briefing_parts.append(section_text)
    
    # Add closing
    closing = "That concludes your enhanced market briefing with cryptocurrency analysis. Have a successful trading day."
    briefing_parts.append(closing)
    
    # Combine all sections
    full_briefing = " ".join(briefing_parts)
    
    # Step 3: Save text file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"briefing_with_crypto_{timestamp}.txt"
    
    with open(text_filename, 'w') as f:
        f.write(full_briefing)
    
    # Step 4: Generate audio
    audio_filename = f"briefing_with_crypto_{timestamp}.mp3"
    audio_success = await generate_audio(full_briefing, audio_filename)
    
    # Step 5: Report results
    word_count = len(full_briefing.split())
    estimated_duration = word_count / 150  # 150 words per minute
    
    print("\n" + "=" * 60)
    print("📊 BRIEFING GENERATION COMPLETE")
    print("=" * 60)
    print(f"📄 Text file: {text_filename}")
    if audio_success:
        print(f"🔊 Audio file: {audio_filename}")
    print(f"📈 Word count: {word_count}")
    print(f"⏱️  Estimated duration: {estimated_duration:.1f} minutes")
    print(f"🎯 Target achieved: {'Yes' if 750 <= word_count <= 850 else 'No'}")
    
    # Show section breakdown
    print(f"\n📋 Section Structure:")
    for section_name, word_target in sections:
        print(f"   {section_name}: {word_target} words")
    
    print(f"\n💰 Crypto Analysis Included: Yes")
    print(f"📊 Crypto Data Quality: {'Good' if 'unavailable' not in crypto_data.lower() else 'Limited'}")

if __name__ == "__main__":
    asyncio.run(main())