#!/usr/bin/env python3
"""
Premium Morning Market Briefing Generator (12-15 minutes)
Generates comprehensive morning market briefings with economic calendar integration
Target: 1800-2250 words for 12-15 minute audio at 150 wpm
"""

import os
import sys
import json
import requests
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.summary_service import SummaryService
from services.audio_service import AudioService
from crypto_analysis import CryptoAnalyzer

# Load environment variables
load_dotenv()

class EconomicCalendarService:
    """Service for fetching and processing economic calendar data"""
    
    def __init__(self):
        self.api_key = "af382a3ee3dca2917ac1d80c284dec2f"  # FMP API key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    def fetch_economic_events(self, date: Optional[str] = None) -> List[Dict]:
        """Fetch economic calendar events for a specific date"""
        if not date:
            # Use today's date in YYYY-MM-DD format
            date = datetime.now().strftime("%Y-%m-%d")
            
        url = f"{self.base_url}/economic_calendar"
        params = {
            "from": date,
            "to": date,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            events = response.json()
            
            # Filter and sort events
            return self._process_events(events)
        except Exception as e:
            print(f"Error fetching economic calendar: {e}")
            return []
    
    def _process_events(self, events: List[Dict]) -> List[Dict]:
        """Process and categorize economic events"""
        processed = []
        
        for event in events:
            # Extract and normalize event data
            processed_event = {
                "date": event.get("date", ""),
                "time": event.get("date", "").split(" ")[1] if " " in event.get("date", "") else "",
                "country": event.get("country", ""),
                "event": event.get("event", ""),
                "currency": event.get("currency", ""),
                "previous": event.get("previous"),
                "estimate": event.get("estimate"),
                "actual": event.get("actual"),
                "change": event.get("change"),
                "impact": event.get("impact", "").lower(),
                "changePercentage": event.get("changePercentage"),
                "unit": event.get("unit", "")
            }
            
            # Determine impact level if not provided
            if not processed_event["impact"]:
                processed_event["impact"] = self._determine_impact(processed_event["event"])
            
            processed.append(processed_event)
        
        # Sort by impact (high first) and then by time
        processed.sort(key=lambda x: (
            0 if x["impact"] == "high" else (1 if x["impact"] == "medium" else 2),
            x["time"]
        ))
        
        return processed
    
    def _determine_impact(self, event_name: str) -> str:
        """Determine impact level based on event name"""
        high_impact_keywords = [
            "GDP", "CPI", "Inflation", "Employment", "Jobless", "NFP", "Non-Farm",
            "Interest Rate", "FOMC", "ECB", "Fed", "Retail Sales", "PMI"
        ]
        
        medium_impact_keywords = [
            "Housing", "Consumer", "Manufacturing", "Trade", "Confidence",
            "Sentiment", "Production", "Orders"
        ]
        
        event_upper = event_name.upper()
        
        for keyword in high_impact_keywords:
            if keyword.upper() in event_upper:
                return "high"
        
        for keyword in medium_impact_keywords:
            if keyword.upper() in event_upper:
                return "medium"
        
        return "low"
    
    def get_high_impact_events(self, events: List[Dict]) -> List[Dict]:
        """Filter only high impact events"""
        return [e for e in events if e["impact"] == "high"]
    
    def format_event_for_speech(self, event: Dict) -> str:
        """Format economic event for TTS pronunciation"""
        parts = []
        
        # Event name
        parts.append(event["event"])
        
        # Previous vs Estimate vs Actual
        if event["actual"] is not None:
            parts.append(f"came in at {self._format_number(event['actual'], event['unit'])}")
            if event["estimate"] is not None:
                parts.append(f"versus an estimate of {self._format_number(event['estimate'], event['unit'])}")
            if event["previous"] is not None:
                parts.append(f"and previous reading of {self._format_number(event['previous'], event['unit'])}")
        elif event["estimate"] is not None:
            parts.append(f"expected at {self._format_number(event['estimate'], event['unit'])}")
            if event["previous"] is not None:
                parts.append(f"compared to previous {self._format_number(event['previous'], event['unit'])}")
        
        return ", ".join(parts)
    
    def _format_number(self, value: Any, unit: str) -> str:
        """Format numbers for speech"""
        if value is None:
            return "no data"
        
        try:
            num = float(value)
            
            # Handle percentages
            if unit == "%":
                if num == int(num):
                    return f"{int(num)} percent"
                else:
                    return f"{num} percent"
            
            # Handle millions/billions
            if abs(num) >= 1000000:
                return f"{num/1000000:.1f} million"
            elif abs(num) >= 1000:
                return f"{num/1000:.1f} thousand"
            else:
                if num == int(num):
                    return str(int(num))
                else:
                    return str(num)
        except:
            return str(value)


class MorningPremiumBriefingGenerator:
    """Generate premium morning market briefings (12-15 minutes)"""
    
    def __init__(self):
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        self.calendar_service = EconomicCalendarService()
        self.finlight_api_key = os.getenv("FINLIGHT_API_KEY")
        
        # Morning briefing structure (12-15 minutes = 1800-2250 words)
        self.sections = [
            ("opening", 30),           # Morning greeting with date and overview
            ("economic_calendar", 200), # Today's economic events analysis
            ("futures_premarket", 180), # Futures and pre-market activity
            ("market_overview", 200),   # Yesterday's close and overnight moves
            ("earnings_today", 180),     # Today's earnings releases
            ("sector_focus", 200),       # 2-3 sectors to watch today
            ("tech_innovation", 150),    # Technology sector updates
            ("financials", 150),         # Banking and financial sector
            ("energy_commodities", 150), # Energy, oil, gold, commodities
            ("crypto_digital", 120),     # Overnight crypto movements
            ("international", 150),      # Asian close, European open
            ("watchlist", 120),          # Key levels and stocks to watch
            ("day_ahead", 120),          # Trading day outlook
            ("closing", 40)              # Morning wrap-up
        ]
        
        self.total_target_words = sum(words for _, words in self.sections)
        print(f"Target total words: {self.total_target_words} (for 12-15 minute morning briefing)")
        
        self.mentioned_companies = set()
        self.used_articles = set()
        
    async def generate_morning_briefing(self) -> Tuple[str, str]:
        """Generate complete morning premium briefing"""
        print("\n" + "="*60)
        print("PREMIUM MORNING MARKET BRIEFING GENERATOR")
        print("Target: 12-15 minutes of professional morning analysis")
        print("="*60 + "\n")
        
        # Fetch news articles
        print("📰 Fetching latest financial news...")
        articles = self._fetch_and_process_news()
        
        # Fetch economic calendar
        print("📅 Fetching today's economic calendar...")
        economic_events = self.calendar_service.fetch_economic_events()
        high_impact_events = self.calendar_service.get_high_impact_events(economic_events)
        
        print(f"Found {len(economic_events)} total events, {len(high_impact_events)} high-impact")
        
        # Fetch real crypto data for crypto section
        print("📊 Fetching cryptocurrency market data...")
        crypto_analyzer = CryptoAnalyzer()
        crypto_data = None
        try:
            crypto_data = await crypto_analyzer.get_all_crypto_analysis(hours=8)
            crypto_summary = await crypto_analyzer.get_crypto_summary_for_briefing(hours=8)
            print(f"   ✓ Got crypto data for BTC, ETH, SOL")
        except Exception as e:
            print(f"   ⚠️ Could not fetch crypto data: {e}")
            crypto_summary = None
        
        # Generate each section
        briefing_sections = []
        total_words = 0
        
        for i, (section_name, target_words) in enumerate(self.sections):
            print(f"\n📝 Generating {section_name} section ({target_words} words)...")
            
            # Gemini 2.0 Flash has better rate limits (60 RPM on free tier)
            # But let's still be conservative to avoid any issues
            try:
                if section_name == "economic_calendar":
                    section_content = self._generate_economic_section(
                        high_impact_events, economic_events, target_words
                    )
                elif section_name == "crypto_digital":
                    # Use real crypto data for crypto section
                    section_content = self._generate_crypto_section(
                        crypto_summary, crypto_data, articles, target_words
                    )
                else:
                    section_content = self._generate_section(
                        section_name, articles, target_words
                    )
                
                word_count = len(section_content.split())
                total_words += word_count
                briefing_sections.append(section_content)
                
                print(f"   ✓ Generated {word_count} words (target: {target_words})")
                
                # Small delay between requests (2 seconds for Gemini 2.0 Flash)
                # 60 RPM limit means we can do 1 per second, but let's be safe
                time.sleep(2)
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(f"   ⚠️ Rate limit hit, waiting 60 seconds...")
                    time.sleep(60)
                    # Retry once
                    try:
                        if section_name == "economic_calendar":
                            section_content = self._generate_economic_section(
                                high_impact_events, economic_events, target_words
                            )
                        else:
                            section_content = self._generate_section(
                                section_name, articles, target_words
                            )
                        
                        word_count = len(section_content.split())
                        total_words += word_count
                        briefing_sections.append(section_content)
                        
                        print(f"   ✓ Generated {word_count} words (target: {target_words}) after retry")
                    except:
                        print(f"   ❌ Failed to generate {section_name} section, using placeholder")
                        section_content = f"[{section_name} section unavailable due to API limits]"
                        briefing_sections.append(section_content)
                else:
                    raise
        
        # Combine all sections
        full_briefing = "\n\n".join(briefing_sections)
        
        print(f"\n📊 MORNING BRIEFING COMPLETE:")
        print(f"   Total words: {total_words}")
        print(f"   Target words: {self.total_target_words}")
        print(f"   Estimated duration: {total_words/150:.1f} minutes at 150 wpm")
        
        # Save text version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_filename = f"morning_premium_briefing_{timestamp}.txt"
        
        with open(text_filename, 'w') as f:
            f.write(full_briefing)
            f.write(f"\n\n---\nGenerated: {datetime.now()}\n")
            f.write(f"Total words: {total_words}\n")
            f.write(f"High-impact events today: {len(high_impact_events)}\n")
        
        print(f"\n💾 Text saved to: {text_filename}")
        
        # Generate audio
        print("\n🎙️ Generating premium audio (this may take 5-7 minutes)...")
        audio_filename = f"morning_premium_briefing_{timestamp}.mp3"
        
        # Run async audio generation
        try:
            import asyncio
            # generate_audio returns bytes, not a filename
            audio_bytes = asyncio.run(self.audio_service.generate_audio(
                full_briefing,
                tier="premium"  # Use premium voice
            ))
            
            if audio_bytes:
                # Save the audio bytes to file
                with open(audio_filename, 'wb') as f:
                    f.write(audio_bytes)
                print(f"✅ Audio saved to: {audio_filename}")
                print(f"📍 Full path: {os.path.abspath(audio_filename)}")
            else:
                print("❌ Audio generation failed")
                audio_filename = None
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            audio_filename = None
        
        return text_filename, audio_filename
    
    def _fetch_and_process_news(self) -> List[Dict]:
        """Fetch and process news articles directly from Finlight API"""
        
        if not self.finlight_api_key:
            print("Warning: No FINLIGHT_API_KEY found")
            return []
            
        url = "https://api.finlight.me/v2/articles"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-API-KEY": self.finlight_api_key
        }
        
        # Fetch more articles for premium briefing
        payload = {
            "includeContent": True,
            "includeEntities": False,
            "excludeEmptyContent": True,
            "pageSize": 100  # Max supported by API
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                print(f"Fetched {len(articles)} articles from Finlight")
            else:
                print(f"Error fetching articles: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
        
        if not articles:
            print("Warning: No articles fetched")
            return []
        
        # Prioritize finance-related content
        finance_keywords = [
            'stock', 'market', 'trading', 'earnings', 'revenue', 'profit',
            'shares', 'investor', 'nasdaq', 'dow', 's&p', 'fed', 'inflation',
            'gdp', 'economy', 'ipo', 'merger', 'acquisition', 'dividend',
            'bitcoin', 'crypto', 'oil', 'gold', 'commodity', 'treasury',
            'yield', 'bond', 'etf', 'hedge fund', 'private equity', 'futures',
            'premarket', 'pre-market', 'after-hours'
        ]
        
        scored_articles = []
        for article in articles:
            content = (article.get('content', '') + ' ' + 
                      article.get('title', '') + ' ' + 
                      article.get('summary', '')).lower()
            
            score = sum(1 for keyword in finance_keywords if keyword in content)
            article['relevance_score'] = score
            scored_articles.append(article)
        
        # Sort by relevance
        scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_articles
    
    def _generate_crypto_section(self, crypto_summary: str, crypto_data: Dict, 
                                articles: List[Dict], target_words: int) -> str:
        """Generate crypto section with REAL price data"""
        
        # Get any crypto-related articles
        relevant_articles = self._get_relevant_articles("crypto_digital", articles)
        
        articles_text = ""
        if relevant_articles:
            for i, article in enumerate(relevant_articles[:5], 1):
                content = article.get('content', '')[:1000]
                title = article.get('title', 'N/A')
                if content and len(content) > 100:
                    articles_text += f"\nArticle {i}:\n"
                    articles_text += f"Title: {title}\n"
                    articles_text += f"Content: {content}\n---\n"
        
        # Build crypto data text with real prices
        crypto_text = ""
        if crypto_summary:
            crypto_text = f"REAL CRYPTO DATA (last 8 hours):\n{crypto_summary}\n\n"
            
            if crypto_data:
                # Add specific details
                for symbol, data in crypto_data.items():
                    if data and 'analysis' in data:
                        analysis = data['analysis']
                        crypto_text += f"\n{symbol}:\n"
                        crypto_text += f"- Current: {analysis['current_price_formatted']}\n"
                        crypto_text += f"- Change: {analysis['price_change_formatted']}\n"
                        crypto_text += f"- Trend: {analysis['trend']}\n"
        
        prompt = f"""Generate EXACTLY {target_words} words for the cryptocurrency section.

DO NOT say 'Good morning'. Start with 'Cryptocurrency markets...' or 'Overnight crypto trading...'

USE THIS REAL CRYPTO DATA (DO NOT MAKE UP PRICES):
{crypto_text}

Additional crypto news (if any):
{articles_text if articles_text else "No crypto-specific news articles available."}

Requirements:
1. Use the EXACT prices and percentages provided above
2. DO NOT invent any prices - use only what's given
3. If no data is available, say "Crypto data unavailable at this time"
4. Focus on the 8-hour overnight movements
5. MUST be EXACTLY {target_words} words
6. Professional tone, factual reporting

Write the section now using ONLY the real data provided:"""
        
        section = self.summary_service.model.generate_content(prompt).text
        return self._format_for_tts(section)
    
    def _generate_economic_section(self, high_impact_events: List[Dict], 
                                  all_events: List[Dict], 
                                  target_words: int) -> str:
        """Generate economic calendar section for morning briefing"""
        
        # Format events for the prompt
        events_text = ""
        
        if high_impact_events:
            events_text += "High-impact events scheduled for today:\n"
            for event in high_impact_events[:5]:  # Limit to top 5
                formatted = self.calendar_service.format_event_for_speech(event)
                events_text += f"- {event['time']} {event['country']}: {formatted}\n"
        
        if len(all_events) > len(high_impact_events):
            medium_events = [e for e in all_events if e["impact"] == "medium"][:3]
            if medium_events:
                events_text += "\nMedium-impact events to monitor:\n"
                for event in medium_events:
                    events_text += f"- {event['time']} {event['country']}: {event['event']}\n"
        
        prompt = f"""Generate EXACTLY {target_words} words for the economic calendar section of a premium MORNING market briefing.

IMPORTANT: Use ONLY the data provided below. DO NOT make up any numbers or events.

Today's ACTUAL economic data releases and events (USE ONLY THESE):
{events_text}

Requirements:
1. Start with "Looking at today's economic calendar"
2. ONLY discuss the events listed above - don't add any others
3. Use the EXACT numbers provided (previous, estimate, actual)
4. If no events are listed, say "Limited economic releases scheduled today"
5. Explain what each event means for markets
6. MUST be EXACTLY {target_words} words

Format the PROVIDED numbers for speech:
- "eight thirty A-M Eastern" not "8:30 AM ET"
- "two point five percent" not "2.5%" (only if data shows 2.5)
- Use the exact figures from the events above

DO NOT HALLUCINATE: Only discuss the events and numbers explicitly listed above.
"""
        
        section = self.summary_service.model.generate_content(prompt).text
        return self._format_for_tts(section)
    
    def _generate_section(self, section_name: str, articles: List[Dict], 
                         target_words: int) -> str:
        """Generate a specific section of the morning briefing"""
        
        # Get relevant articles for this section
        relevant_articles = self._get_relevant_articles(section_name, articles)
        
        # Create articles text for prompt - provide MORE content for accurate summaries
        articles_text = ""
        if not relevant_articles:
            articles_text = "No relevant articles found for this section."
        else:
            for i, article in enumerate(relevant_articles[:10], 1):  # Use up to 10 articles
                # Use more content to ensure we have real data to summarize
                content = article.get('content', '')[:2500]  # Increased from 2000
                title = article.get('title', 'N/A')
                
                # Only include if there's actual content
                if content and len(content) > 100:  # Ensure meaningful content
                    articles_text += f"\nArticle {i}:\n"
                    articles_text += f"Title: {title}\n"
                    articles_text += f"Content: {content}\n"
                    articles_text += "---\n"
        
        # If we have no good articles for this section, note that
        if not articles_text or articles_text == "No relevant articles found for this section.":
            articles_text = f"No specific articles found for {section_name}. Use general market articles if applicable."
        
        # Get today's date correctly
        from datetime import datetime
        today_date = datetime.now().strftime("%B %d, %Y")
        
        # Morning-specific section prompts - NO "Good morning" except in opening!
        section_prompts = {
            "opening": f"Generate EXACTLY {target_words} words for the MORNING opening. Start with 'Good morning' and include today's date ({today_date}), brief preview of market conditions and what's ahead today.",
            
            "futures_premarket": f"Generate EXACTLY {target_words} words on futures and pre-market activity. DO NOT say 'Good morning'. Start with 'Futures indicate...' or 'Pre-market activity shows...'. Include: S&P, Nasdaq, Dow futures, notable pre-market movers, volume, implied open, overseas influence on futures.",
            
            "market_overview": f"Generate EXACTLY {target_words} words analyzing yesterday's close and overnight developments. DO NOT say 'Good morning'. Start with 'Yesterday's session...' or 'Markets closed...'. Include: how markets closed yesterday, overnight news, Asian market close, European market status, key levels broken overnight.",
            
            "earnings_today": f"Generate EXACTLY {target_words} words on today's earnings releases. DO NOT say 'Good morning'. Start with 'Today's earnings calendar...' or 'Companies reporting today...'. Include: companies reporting before the bell, after the close today, key metrics to watch, analyst expectations, potential market impact.",
            
            "sector_focus": f"Generate EXACTLY {target_words} words on 2-3 sectors to watch today. DO NOT say 'Good morning'. Start with 'Sector rotation shows...' or 'Energy and financials are...'. Include: sectors showing pre-market strength/weakness, rotation signals, key catalysts, leading stocks in each sector.",
            
            "tech_innovation": f"Generate EXACTLY {target_words} words on technology sector for the morning. DO NOT say 'Good morning'. Start with 'Technology futures...' or 'The tech sector...'. Include: tech futures, major tech pre-market moves, AI/semiconductor updates, software sector outlook for today.",
            
            "financials": f"Generate EXACTLY {target_words} words on financial sector morning outlook. DO NOT say 'Good morning'. Start with 'Financial stocks...' or 'Banks are showing...'. Include: bank pre-market activity, yield curve, interest rate expectations, any financial earnings today.",
            
            "energy_commodities": f"Generate EXACTLY {target_words} words on energy and commodities. DO NOT say 'Good morning'. Start with 'Oil prices...' or 'Commodities are...'. Include: overnight oil moves, gold in Asian/European trading, dollar strength impact, commodity futures for the day.",
            
            "crypto_digital": f"Generate EXACTLY {target_words} words on overnight cryptocurrency action. DO NOT say 'Good morning'. Start with 'Bitcoin traded...' or 'Cryptocurrency markets...'. Include: Bitcoin and Ethereum overnight moves, altcoin activity, any crypto news impacting traditional markets.",
            
            "international": f"Generate EXACTLY {target_words} words on international markets. DO NOT say 'Good morning'. Start with 'Asian markets closed...' or 'Global markets show...'. Include: how Asia closed, European market status, emerging markets, currency moves affecting US trading.",
            
            "watchlist": f"Generate EXACTLY {target_words} words on key levels and stocks to watch. DO NOT say 'Good morning'. Start with 'Key support levels...' or 'Watch these levels...'. Include: support/resistance for major indices, stocks with unusual pre-market volume, key technical levels, volatility expectations.",
            
            "day_ahead": f"Generate EXACTLY {target_words} words on trading day outlook. DO NOT say 'Good morning'. Start with 'Today's trading...' or 'Market expectations...'. Include: expected market themes, potential catalysts, risk factors, trading ranges, volume expectations.",
            
            "closing": f"Generate EXACTLY {target_words} words for morning closing. DO NOT say 'Good morning' again. Start with 'To wrap up...' or 'In summary...'. Include: top 3 things to watch today, reminder of economic releases, wish for successful trading day, premium subscriber appreciation."
        }
        
        base_prompt = section_prompts.get(section_name, f"Generate EXACTLY {target_words} words for {section_name}.")
        
        prompt = f"""{base_prompt}

CRITICAL: You MUST use ONLY the information from these articles. DO NOT make up any prices, percentages, or data that isn't in the articles.

Articles to summarize (USE ONLY THESE):
{articles_text}

STRICT RULES - YOU MUST FOLLOW:
1. ONLY use information from the articles above - NEVER invent data
2. If articles don't mention specific prices (like Bitcoin at $27,000), DON'T make them up
3. If there's no relevant content for this section in the articles, say "Limited coverage in current news flow" and discuss what IS available
4. MUST be EXACTLY {target_words} words - count carefully
5. AVOID REPETITION: Don't mention these companies again: {', '.join(self.mentioned_companies) if self.mentioned_companies else 'none yet'}
6. Format ONLY the numbers that appear IN THE ARTICLES for speech:
   - "five percent" not "5%" (only if article mentions 5%)
   - "ticker A-A-P-L --" not "AAPL"
   - Numbers must come from articles, not your knowledge
7. Professional tone but NEVER add data not in the articles

DO NOT HALLUCINATE: If the articles don't mention crypto prices, don't say "Bitcoin at twenty-seven thousand". If they don't mention specific percentages, don't add them. ONLY summarize what's actually written in the articles above.

Write the section now using ONLY facts from the articles:"""
        
        # Generate with Gemini
        section = self.summary_service.model.generate_content(prompt).text
        
        # Track mentioned companies
        self._track_mentioned_companies(section)
        
        # Format for TTS
        return self._format_for_tts(section)
    
    def _get_relevant_articles(self, section_name: str, articles: List[Dict]) -> List[Dict]:
        """Get articles relevant to specific section - morning focus"""
        
        # Morning-specific section keywords
        section_keywords = {
            "futures_premarket": ["futures", "pre-market", "premarket", "implied open", "overnight", "before bell"],
            "market_overview": ["close", "yesterday", "overnight", "asia", "europe", "session"],
            "earnings_today": ["earnings", "reports today", "before bell", "after close", "guidance", "expects"],
            "sector_focus": ["sector", "rotation", "strength", "weakness", "outperform", "underperform"],
            "tech_innovation": ["tech", "technology", "ai", "software", "semiconductor", "apple", "microsoft"],
            "financials": ["bank", "financial", "yield", "rates", "jpmorgan", "goldman", "lending"],
            "energy_commodities": ["oil", "gas", "gold", "commodity", "copper", "crude", "wti", "brent"],
            "crypto_digital": ["bitcoin", "ethereum", "crypto", "blockchain", "overnight", "24-hour"],
            "international": ["china", "europe", "japan", "asia", "emerging", "currency", "global"],
            "watchlist": ["watch", "level", "support", "resistance", "breakout", "volume", "unusual"],
            "day_ahead": ["today", "expect", "outlook", "forecast", "catalyst", "scheduled"]
        }
        
        keywords = section_keywords.get(section_name, [])
        
        if not keywords:
            return articles[:10]
        
        # Score and filter articles
        relevant = []
        for article in articles:
            if article.get('url', '') in self.used_articles:
                continue
                
            content = (article.get('content', '') + ' ' + 
                      article.get('title', '') + ' ' + 
                      article.get('summary', '')).lower()
            
            score = sum(1 for kw in keywords if kw in content)
            
            if score > 0:
                article['section_score'] = score
                relevant.append(article)
        
        # Sort by relevance
        relevant.sort(key=lambda x: x.get('section_score', 0), reverse=True)
        
        # Mark articles as used
        for article in relevant[:8]:
            self.used_articles.add(article.get('url', ''))
        
        return relevant
    
    def _track_mentioned_companies(self, text: str):
        """Track companies mentioned to avoid repetition"""
        # Common company names to track
        companies = [
            'apple', 'microsoft', 'google', 'amazon', 'meta', 'tesla', 'nvidia',
            'jpmorgan', 'goldman', 'berkshire', 'johnson', 'walmart', 'exxon',
            'pfizer', 'disney', 'netflix', 'adobe', 'salesforce', 'oracle'
        ]
        
        text_lower = text.lower()
        for company in companies:
            if company in text_lower:
                self.mentioned_companies.add(company)
    
    def _format_for_tts(self, text: str) -> str:
        """Format text for optimal TTS pronunciation"""
        import re
        
        # Format stock tickers (AAPL -> ticker A-A-P-L --)
        text = re.sub(r'\b([A-Z]{2,5})\b(?!\w)', 
                     lambda m: f"ticker {'-'.join(m.group(1))} --", text)
        
        # Format percentages (5% -> five percent)
        text = re.sub(r'(\d+\.?\d*)%', r'\1 percent', text)
        
        # Format currency (more comprehensive)
        text = re.sub(r'\$(\d+\.?\d*)T', r'\1 trillion dollars', text)
        text = re.sub(r'\$(\d+\.?\d*)B', r'\1 billion dollars', text)
        text = re.sub(r'\$(\d+\.?\d*)M', r'\1 million dollars', text)
        text = re.sub(r'\$(\d+\.?\d*)K', r'\1 thousand dollars', text)
        
        # Format times for morning briefing
        text = re.sub(r'(\d{1,2}):(\d{2})\s*([AP]M)', 
                     lambda m: f"{m.group(1)} {m.group(2)} {m.group(3).replace('AM', 'A-M').replace('PM', 'P-M')}", 
                     text)
        
        # Format common abbreviations
        abbreviations = {
            'CEO': 'C-E-O', 'CFO': 'C-F-O', 'COO': 'C-O-O', 'CTO': 'C-T-O',
            'IPO': 'I-P-O', 'GDP': 'G-D-P', 'AI': 'A-I', 'EV': 'E-V',
            'ETF': 'E-T-F', 'SEC': 'S-E-C', 'FDA': 'F-D-A', 'EU': 'E-U',
            'UK': 'U-K', 'US': 'U-S', 'Q1': 'first quarter', 'Q2': 'second quarter',
            'Q3': 'third quarter', 'Q4': 'fourth quarter', 'YoY': 'year over year',
            'MoM': 'month over month', 'P/E': 'price to earnings', 'ET': 'Eastern',
            'EST': 'Eastern', 'PST': 'Pacific', 'CPI': 'C-P-I', 'PPI': 'P-P-I',
            'PMI': 'P-M-I', 'ISM': 'I-S-M', 'FOMC': 'F-O-M-C'
        }
        
        for abbr, replacement in abbreviations.items():
            text = text.replace(abbr, replacement)
        
        return text


async def main():
    """Main execution function"""
    generator = MorningPremiumBriefingGenerator()
    
    try:
        text_file, audio_file = await generator.generate_morning_briefing()
        
        print("\n" + "="*60)
        print("✅ PREMIUM MORNING BRIEFING GENERATION COMPLETE!")
        print("="*60)
        print(f"📄 Text file: {text_file}")
        if audio_file:
            print(f"🎵 Audio file: {audio_file}")
        print("\nYour premium 12-15 minute morning market briefing is ready!")
        
    except Exception as e:
        print(f"\n❌ Error generating morning briefing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())