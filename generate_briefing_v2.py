#!/usr/bin/env python3
"""
Enhanced briefing generator that ensures 5-minute length by generating sections separately
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
            all_articles = data.get('articles', [])
            
            # Prioritize finance articles
            finance_keywords = ['stock', 'market', 'invest', 'finance', 'earnings', 'economy', 
                               'fed', 'inflation', 'gdp', 'trading', 'ipo', 'merger', 'acquisition',
                               'revenue', 'profit', 'nasdaq', 'dow', 's&p', 'crypto', 'bitcoin']
            
            finance_articles = []
            other_articles = []
            
            for article in all_articles:
                title = article.get('title', '').lower()
                content = article.get('content', '')[:500].lower()
                
                is_finance = any(kw in title or kw in content for kw in finance_keywords)
                
                if is_finance:
                    finance_articles.append(article)
                else:
                    other_articles.append(article)
            
            articles_data = finance_articles[:50] + other_articles[:25]
            
            print(f"✅ Fetched {len(all_articles)} total articles")
            print(f"   Using {len(articles_data)} for briefing")
            
            return articles_data
        else:
            print(f"❌ Error fetching articles: {response.status_code}")
            return []

def deduplicate_articles(articles):
    """Remove duplicate or very similar articles"""
    seen_topics = set()
    unique_articles = []
    
    for article in articles:
        title = article.get('title', '').lower()
        # Extract key identifiers (company names, tickers, main keywords)
        key_words = set()
        
        # Extract stock tickers (uppercase sequences)
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', article.get('title', ''))
        key_words.update(tickers)
        
        # Extract main topic words
        for word in title.split():
            if len(word) > 4:  # Focus on meaningful words
                key_words.add(word.strip('.,!?()[]{}'))
        
        # Create a topic signature
        topic_signature = tuple(sorted(key_words))
        
        # Skip if we've seen a very similar article
        if topic_signature not in seen_topics or len(topic_signature) < 2:
            seen_topics.add(topic_signature)
            unique_articles.append(article)
    
    return unique_articles

def generate_section(articles, section_name, word_count, focus_keywords=None):
    """Generate a specific section of the briefing"""
    
    # Deduplicate articles first
    unique_articles = deduplicate_articles(articles[:40])
    
    # Filter articles for this section
    relevant_articles = []
    seen_companies = set()  # Track companies already mentioned
    
    for article in unique_articles:
        title = article.get('title', '')
        title_lower = title.lower()
        content = article.get('content', '')[:1500]
        
        # Extract company/ticker from title
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', title)
        company_key = tickers[0] if tickers else title[:30]
        
        # Skip if we already have news about this company
        if company_key in seen_companies:
            continue
            
        if focus_keywords:
            if any(kw in title_lower or kw in content.lower() for kw in focus_keywords):
                relevant_articles.append(f"Title: {title}\nContent: {content[:500]}")
                seen_companies.add(company_key)
        else:
            relevant_articles.append(f"Title: {title}\nContent: {content[:500]}")
            seen_companies.add(company_key)
    
    if not relevant_articles:
        relevant_articles = [f"Title: {a.get('title')}\nContent: {a.get('content', '')[:500]}" for a in unique_articles[:10]]
    
    articles_text = "\n---\n".join(relevant_articles[:10])
    
    prompt = f"""
    Write EXACTLY {word_count} words about {section_name}.
    
    Use these articles:
    {articles_text}
    
    CRITICAL RULES:
    1. AVOID REPETITION: If multiple articles mention the same company/event, mention it ONLY ONCE
    2. NO REDUNDANCY: Don't repeat the same information in different words
    3. DIVERSE COVERAGE: Cover as many different companies/topics as possible
    4. Write EXACTLY {word_count} words. Count them.
    
    FORMATTING:
    - Stock tickers: Write as "ticker A-A-P-L --" (spell letters with dashes, add pause)
    - Percentages: "five percent" not "5%"
    - Money: "billion dollars" not "$B"
    - Numbers: "two point five million" not "2.5M"
    - No markdown, no asterisks
    
    Write detailed analysis covering DIFFERENT stories. Each company should be mentioned only once.
    If you see similar news (like "C3AI drops 31%" in multiple articles), mention it ONCE.
    Focus on variety and comprehensive market coverage.
    
    YOU MUST WRITE EXACTLY {word_count} WORDS.
    """
    
    try:
        generation_config = {
            "temperature": 0.8,
            "max_output_tokens": 1024,
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        text = response.text.strip()
        
        # Verify word count
        actual_count = len(text.split())
        if actual_count < word_count * 0.8:
            print(f"   ⚠️  {section_name}: Only {actual_count} words (target: {word_count})")
        else:
            print(f"   ✅ {section_name}: {actual_count} words")
        
        return text
    except Exception as e:
        print(f"   ❌ Error generating {section_name}: {e}")
        return ""

def get_time_greeting():
    """Get appropriate time-based greeting"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    else:
        return "evening"

async def create_comprehensive_briefing():
    """Create a 5-minute briefing by generating sections separately"""
    
    # Fetch articles
    articles = await fetch_articles()
    if not articles:
        print("❌ No articles to process")
        return
    
    print("\n🤖 Generating comprehensive 5-minute briefing...")
    
    # Generate each section with specific word counts
    sections = []
    
    # Opening
    opening = f"Good {get_time_greeting()}. Here's your comprehensive market briefing for {datetime.now().strftime('%B %d')}."
    sections.append(opening)
    print(f"   ✅ Opening: {len(opening.split())} words")
    
    # Market Overview (150 words)
    print("   Generating market overview...")
    market_section = generate_section(
        articles, 
        "market overview including major indices, volume, and overall sentiment",
        150,
        ['market', 'index', 'dow', 'nasdaq', 's&p', 'volume', 'trading']
    )
    if market_section:
        sections.append("Let's begin with today's market overview. " + market_section)
    
    # Top Stock News (150 words)
    print("   Generating top stock news...")
    stock_section = generate_section(
        articles,
        "major individual stock movements and company news",
        150,
        ['stock', 'share', 'company', 'earnings', 'revenue']
    )
    if stock_section:
        sections.append("Turning to individual stocks. " + stock_section)
    
    # Economic Data (120 words)
    print("   Generating economic data section...")
    econ_section = generate_section(
        articles,
        "economic indicators, Federal Reserve, inflation, and employment",
        120,
        ['fed', 'inflation', 'gdp', 'employment', 'economic', 'rate']
    )
    if econ_section:
        sections.append("In economic news. " + econ_section)
    
    # Tech Sector (100 words)
    print("   Generating tech sector update...")
    tech_section = generate_section(
        articles,
        "technology sector developments",
        100,
        ['tech', 'software', 'ai', 'chip', 'semiconductor', 'cloud']
    )
    if tech_section:
        sections.append("In the technology sector. " + tech_section)
    
    # Energy/Commodities (100 words)
    print("   Generating energy and commodities...")
    energy_section = generate_section(
        articles,
        "energy and commodity markets including oil, gold, and other resources",
        100,
        ['oil', 'energy', 'gold', 'commodity', 'crude', 'gas']
    )
    if energy_section:
        sections.append("Looking at energy and commodities. " + energy_section)
    
    # International Markets (80 words)
    print("   Generating international markets...")
    intl_section = generate_section(
        articles,
        "international market developments",
        80,
        ['asia', 'europe', 'china', 'japan', 'global', 'international']
    )
    if intl_section:
        sections.append("In international markets. " + intl_section)
    
    # Closing
    closing = "That concludes today's comprehensive market briefing. Stay informed and have a successful trading day."
    sections.append(closing)
    print(f"   ✅ Closing: {len(closing.split())} words")
    
    # Combine all sections
    briefing_text = " ".join(sections)
    
    # Final word count
    total_words = len(briefing_text.split())
    print(f"\n✅ Total briefing: {total_words} words")
    print(f"   Estimated duration: {total_words / 150:.1f} minutes")
    
    if total_words < 700:
        print("   ⚠️  Still too short! Adding market outlook...")
        # Add an outlook section if still too short
        outlook = generate_section(
            articles,
            "market outlook and what to watch for tomorrow",
            150,
            ['outlook', 'forecast', 'expect', 'tomorrow', 'week ahead']
        )
        if outlook:
            briefing_text = briefing_text.replace(
                "That concludes today's comprehensive market briefing.",
                f"Finally, looking ahead. {outlook} That concludes today's comprehensive market briefing."
            )
            total_words = len(briefing_text.split())
            print(f"   Final word count: {total_words} words")
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"briefing_{timestamp}.txt"
    
    with open(text_filename, 'w', encoding='utf-8') as f:
        f.write(briefing_text)
    
    print(f"\n✅ Text briefing saved to: {text_filename}")
    print(f"   File size: {len(briefing_text)} characters")
    print(f"   Word count: {total_words} words")
    print(f"   Duration: {total_words / 150:.1f} minutes")
    
    # Generate audio using Fish Audio
    await generate_audio(briefing_text, timestamp)

async def generate_audio(text, timestamp):
    """Generate audio using Fish Audio"""
    print("\n🎵 Generating audio file...")
    
    audio_filename = f"briefing_{timestamp}.mp3"
    
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
            
            audio_data = io.BytesIO()
            chunk_count = 0
            
            print("   Generating audio...")
            async for chunk in session.tts.awaitable(request):
                audio_data.write(chunk)
                chunk_count += 1
                if chunk_count % 50 == 0:  # Print less frequently
                    print(f"   Received {chunk_count} chunks...")
            
            with open(audio_filename, 'wb') as f:
                f.write(audio_data.getvalue())
            
            print(f"✅ Audio file generated: {audio_filename}")
            print(f"   File size: {len(audio_data.getvalue()) / 1024:.1f} KB")
            
        except Exception as e:
            print(f"❌ Fish Audio TTS failed: {str(e)}")
    else:
        print("❌ No FISH_API_KEY found")
    
    print("\n" + "=" * 50)
    print("✅ Briefing generation complete!")
    print(f"📄 Text file: briefing_{timestamp}.txt")
    print(f"🎵 Audio file: {audio_filename}")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Market Brief Generator V2 - Comprehensive 5-Minute Briefings")
    print("=" * 50)
    asyncio.run(create_comprehensive_briefing())