#!/usr/bin/env python3
"""
Daily Topic Briefing Generator
Generates comprehensive 15-minute briefings on specific topics using multi-source news aggregation.

Usage:
    python daily_topic_briefing.py "artificial intelligence"
    python daily_topic_briefing.py "biotechnology" --days=3
    python daily_topic_briefing.py "renewable energy" --length=10
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Fix for Python 3.13+ compatibility with pydub
try:
    import audioop
    from pydub import AudioSegment
    AUDIO_STITCHING_AVAILABLE = True
except ModuleNotFoundError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
        from pydub import AudioSegment
        AUDIO_STITCHING_AVAILABLE = True
    except ModuleNotFoundError:
        print("⚠️ Warning: pydub/audioop not available. Audio stitching disabled.")
        AUDIO_STITCHING_AVAILABLE = False

# CRITICAL: Load environment variables BEFORE any imports that use them
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.newsapiai_service import NewsAPIAIService
from src.services.news_service import NewsService
from src.services.summary_service import SummaryService
from src.services.audio_service import AudioService
from src.utils.timezone_utils import get_est_time, format_est_timestamp, format_est_display

class TopicBriefingGenerator:
    """Generates comprehensive topic-specific news briefings."""
    
    def __init__(self):
        """Initialize all required services."""
        self.newsapiai_service = NewsAPIAIService()
        self.news_service = NewsService()  # Finlight
        self.summary_service = SummaryService()
        self.audio_service = AudioService()
        
        # Topic classification and search strategies
        self.topic_categories = {
            "high_volume": ["stock market", "cryptocurrency", "federal reserve", "inflation", "earnings"],
            "medium_volume": ["biotechnology", "renewable energy", "electric vehicles", "artificial intelligence", "5g technology"],
            "low_volume": ["quantum computing", "space tourism", "lab grown meat", "nuclear fusion", "gene therapy"],
            "financial": ["stock market", "cryptocurrency", "federal reserve", "inflation", "earnings", "ipo", "merger", "banking"],
            "technology": ["artificial intelligence", "machine learning", "blockchain", "5g", "quantum computing", "cybersecurity"],
            "healthcare": ["biotechnology", "pharmaceutical", "medical devices", "gene therapy", "clinical trials"],
            "energy": ["renewable energy", "oil prices", "electric vehicles", "nuclear energy", "solar power", "wind power"],
            "policy": ["federal reserve", "regulation", "trade war", "sanctions", "monetary policy", "fiscal policy"]
        }
    
    def classify_topic(self, topic: str) -> Dict[str, Any]:
        """Classify topic and determine search strategy."""
        topic_lower = topic.lower()
        
        # Determine volume category
        volume_category = "medium_volume"  # default
        for category, topics in self.topic_categories.items():
            if category.endswith("_volume") and any(t in topic_lower for t in topics):
                volume_category = category
                break
        
        # Determine subject category
        subject_categories = []
        for category, topics in self.topic_categories.items():
            if not category.endswith("_volume") and any(t in topic_lower for t in topics):
                subject_categories.append(category)
        
        if not subject_categories:
            subject_categories = ["general"]
        
        return {
            "volume_category": volume_category,
            "subject_categories": subject_categories,
            "primary_category": subject_categories[0] if subject_categories else "general"
        }
    
    def generate_search_keywords(self, topic: str, classification: Dict[str, Any]) -> str:
        """Generate optimized search keywords based on topic and classification."""
        base_topic = topic.lower()
        
        # Keyword expansions based on topic
        keyword_expansions = {
            "artificial intelligence": "artificial intelligence OR AI OR machine learning OR deep learning OR neural networks",
            "biotechnology": "biotechnology OR biotech OR pharmaceutical OR drug development OR clinical trials OR FDA approval",
            "renewable energy": "renewable energy OR solar power OR wind power OR clean energy OR green energy OR sustainable energy",
            "electric vehicles": "electric vehicles OR EV OR Tesla OR battery technology OR charging infrastructure OR autonomous vehicles",
            "cryptocurrency": "cryptocurrency OR bitcoin OR ethereum OR blockchain OR crypto OR digital currency OR DeFi",
            "quantum computing": "quantum computing OR quantum technology OR quantum supremacy OR quantum research OR quantum processors",
            "space tourism": "space tourism OR commercial space OR SpaceX OR Blue Origin OR space economy OR satellite industry",
            "gene therapy": "gene therapy OR genetic engineering OR CRISPR OR gene editing OR genetic medicine OR personalized medicine",
            "nuclear fusion": "nuclear fusion OR fusion energy OR fusion power OR fusion reactor OR clean energy OR fusion breakthrough",
            "cybersecurity": "cybersecurity OR cyber security OR hacking OR data breach OR ransomware OR information security"
        }
        
        # Use expansion if available, otherwise create basic expansion
        if base_topic in keyword_expansions:
            return keyword_expansions[base_topic]
        else:
            # Create basic expansion by splitting topic and adding OR
            words = base_topic.split()
            if len(words) > 1:
                return f"{base_topic} OR {' OR '.join(words)}"
            else:
                return base_topic
    
    def get_optimal_time_range(self, classification: Dict[str, Any]) -> int:
        """Always return 1 day (24 hours) - no adaptive time ranges."""
        return 1
    
    async def fetch_topic_articles(self, topic: str, days_back: int = 1, max_total_articles: int = 50) -> Dict[str, Any]:
        """Fetch articles for the specific topic from multiple sources."""
        
        # Check if it's Monday - if so, use 72 hours to cover the weekend
        current_time = get_est_time()
        is_monday = current_time.weekday() == 0  # Monday = 0
        
        if is_monday and days_back == 1:
            actual_days_back = 3  # 72 hours to cover weekend
            print(f"\n📰 Fetching articles for topic: '{topic}'")
            print(f"   📅 Monday detected - looking back 72 hours (covering weekend)")
        else:
            actual_days_back = days_back
            print(f"\n📰 Fetching articles for topic: '{topic}'")
            print(f"   🕒 Looking back {actual_days_back} days")
        
        classification = self.classify_topic(topic)
        keywords = self.generate_search_keywords(topic, classification)
        
        print(f"   🔍 Search keywords: {keywords}")
        print(f"   📊 Topic classification: {classification['primary_category']} ({classification['volume_category']})")
        
        # Calculate date range - use actual_days_back (which accounts for Monday logic)
        end_date = get_est_time()
        start_date = end_date - timedelta(days=actual_days_back)
        
        all_articles = []
        sources_used = []
        
        # Primary: NewsAPI.ai search using concept URI method
        try:
            print("   📡 Searching NewsAPI.ai with concept URI...")
            newsapi_result = await self.newsapiai_service.search_articles_by_topic(
                topic=topic,
                date_start=start_date.strftime("%Y-%m-%d"),
                date_end=end_date.strftime("%Y-%m-%d"),
                max_articles=40
            )
            
            if newsapi_result and newsapi_result.get("articles"):
                newsapi_articles = newsapi_result["articles"]
                print(f"   ✅ NewsAPI.ai: {len(newsapi_articles)} articles")
                all_articles.extend(newsapi_articles)
                sources_used.append("NewsAPI.ai")
            else:
                print("   ❌ NewsAPI.ai: No articles found")
                
        except Exception as e:
            print(f"   ❌ NewsAPI.ai error: {str(e)}")
        
        # Secondary: Finlight (always try for any topic since they have broad coverage)
        try:
            print("   📡 Searching Finlight...")
            finlight_articles = await self.news_service.fetch_for_topic(topic, max_articles=25)
            
            if finlight_articles:
                print(f"   ✅ Finlight: {len(finlight_articles)} articles")
                all_articles.extend(finlight_articles)
                sources_used.append("Finlight")
            else:
                print("   ❌ Finlight: No articles found")
                
        except Exception as e:
            print(f"   ❌ Finlight error: {str(e)}")
        
        # Remove duplicates but don't expand time range
        seen_titles = set()
        unique_articles = []
        
        for article in all_articles:
            title = article.get("title", "").lower()
            if title not in seen_titles and title:
                seen_titles.add(title)
                unique_articles.append(article)
        
        final_articles = unique_articles[:max_total_articles]
        
        print(f"\n✅ Article collection complete:")
        print(f"   📊 Total articles: {len(final_articles)}")
        print(f"   🔗 Sources: {', '.join(sources_used) if sources_used else 'No articles found'}")
        print(f"   📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        return {
            "articles": final_articles,
            "topic": topic,
            "classification": classification,
            "sources_used": sources_used,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days_back": actual_days_back,
                "is_monday": is_monday
            },
            "metadata": {
                "total_articles": len(final_articles),
                "search_keywords": keywords,
                "fetch_time": get_est_time().isoformat()
            }
        }
    
    async def generate_topic_briefing(self, articles_data: Dict[str, Any], target_length: int = 15) -> str:
        """Generate AI-powered topic briefing with adaptive content based on article count."""
        articles = articles_data["articles"]
        topic = articles_data["topic"]
        classification = articles_data["classification"]
        
        if not articles:
            return f"Unable to generate briefing for '{topic}' - no articles found in the past 24 hours. Try a broader topic or check back when more news is available."
        
        # Adaptive briefing strategy based on article count
        article_count = len(articles)
        print(f"\n🤖 Generating briefing with {article_count} articles...")
        
        if article_count >= 15:
            # Plenty of articles - generate full target length
            actual_length = target_length
            content_strategy = "comprehensive"
            print(f"   📊 Strategy: Comprehensive {target_length}-minute briefing")
        elif article_count >= 8:
            # Moderate articles - slightly shorter but detailed
            actual_length = max(target_length - 3, 8)  # 3 minutes shorter, minimum 8 minutes
            content_strategy = "detailed"
            print(f"   📊 Strategy: Detailed {actual_length}-minute briefing (reduced from {target_length})")
        else:
            # Few articles - focus on deep analysis
            actual_length = max(target_length - 5, 5)  # 5 minutes shorter, minimum 5 minutes
            content_strategy = "deep_analysis"
            print(f"   📊 Strategy: Deep analysis {actual_length}-minute briefing (reduced from {target_length})")
        
        # Calculate adaptive word count
        target_words = actual_length * 150
        
        # Prepare articles for AI processing with full content for deep analysis
        articles_text = ""
        max_articles_to_process = min(article_count, 30)
        
        for i, article in enumerate(articles[:max_articles_to_process], 1):
            title = article.get('title', 'No title')
            content = article.get('content', 'No content available')
            source = article.get('source', 'Unknown source')
            published_date = article.get('published_at', '')
            
            # For deep analysis with few articles, use more content per article
            if content_strategy == "deep_analysis":
                content_preview = content[:3000] if len(content) > 3000 else content  # More content
            elif content_strategy == "detailed":
                content_preview = content[:2000] if len(content) > 2000 else content
            else:
                content_preview = content[:1500] if len(content) > 1500 else content
            
            articles_text += f"\n[ARTICLE {i}]\n"
            articles_text += f"Title: {title}\n"
            articles_text += f"Source: {source}\n"
            articles_text += f"Date: {published_date}\n"
            articles_text += f"Content: {content_preview}\n"
            articles_text += "-" * 50 + "\n"
        
        # Create adaptive section targets
        current_date = get_est_time()
        primary_category = classification["primary_category"]
        
        if content_strategy == "comprehensive":
            # Full briefing structure (15+ articles) - NO TOPIC OVERVIEW
            if actual_length >= 14:
                section_targets = {
                    "developments": 600,     # +100 from removing overview
                    "impact": 500,           # +100 from removing overview  
                    "highlights": 500,       # +100 from removing overview
                    "outlook": 400,          # +50 from removing overview
                    "conclusion": 250        # -50 to balance
                }
            else:  # 10-13 minute comprehensive
                section_targets = {
                    "developments": 500,     # +300 from removing overview
                    "impact": 400,           # +50 from removing overview
                    "highlights": 400,       # +50 from removing overview
                    "outlook": 350,          # +50 from removing overview
                    "conclusion": 200       # Same
                }
        elif content_strategy == "detailed":
            # Detailed analysis of moderate article count (8-14 articles)
            section_targets = {
                "developments": 500,        # +250 from removing overview
                "impact": 350,             # +50 from removing overview
                "highlights": 350,         # +50 from removing overview
                "outlook": 300,            # +50 from removing overview
                "conclusion": 200          # Same
            }
        else:  # deep_analysis
            # Deep dive into few articles (1-7 articles)
            section_targets = {
                "developments": 450,       # +250 from removing overview
                "impact": 300,             # +50 from removing overview
                "highlights": 300,         # +50 from removing overview
                "outlook": 250,            # +50 from removing overview
                "conclusion": 150          # Same
            }
        
        prompt = f"""
        You are a senior news editor creating a comprehensive {target_length}-minute briefing on {topic}.
        
        TASK: Analyze the following {len(articles)} articles about {topic} and create a professional {actual_length}-minute briefing.
        
        Current Date: {current_date.strftime('%B %d, %Y')}
        Topic: {topic}
        Primary Category: {primary_category}
        Articles Available: {len(articles)} articles (past 24 hours)
        Content Strategy: {content_strategy}
        
        ARTICLES TO ANALYZE:
        {articles_text}
        
        YOUR MISSION:
        1. ANALYZE all articles thoroughly - use ONLY information from the provided articles, NEVER make up details
        2. CREATE a {content_strategy} {target_words}-word briefing that educates listeners about this topic
        
        CONTENT STRATEGY GUIDELINES:
        - COMPREHENSIVE ({article_count} >= 15 articles): Cover broad range of developments with standard depth
        - DETAILED ({article_count} = 8-14 articles): Focus on thorough analysis of available stories  
        - DEEP ANALYSIS ({article_count} < 8 articles): Provide in-depth exploration of each story with extensive context and implications
        
        3. STRUCTURE your briefing with this EXACT format:
        
           START WITH: "Welcome to your MarketMotion Topic briefing on {topic}. It's {current_date.strftime('%B %d')}, and we're covering the latest news and developments."
           
           Then say "Latest developments." and cover the most important recent news ({section_targets["developments"]} words)
           - 4-5 major recent developments
           - Timeline of recent events
           - Breaking news and updates
           
           Then say "Market and business impact." and analyze economic implications ({section_targets["impact"]} words)
           - Financial impact and market reactions
           - Investment trends and funding
           - Stock movements and company performance (if applicable)
           
           Then say "Company and sector highlights." and focus on key organizations ({section_targets["highlights"]} words)
           - Leading companies and their strategies
           - Competitive landscape
           - Partnerships and collaborations
           
           Then say "Looking ahead." and discuss future implications ({section_targets["outlook"]} words)
           - Future trends and predictions
           - Upcoming events and milestones
           - Potential challenges and opportunities
           
           End with "Conclusion." and wrap up the briefing ({section_targets["conclusion"]} words)
           - Summary of key points
           - Why this topic matters for listeners
           - "That concludes your MarketMotion briefing on {topic}. Thank you for listening."
        
        CRITICAL WORD COUNT REQUIREMENTS:
        - TARGET: EXACTLY {target_words} words total ({target_length} minutes at 150 wpm)
        - Each section MUST hit its word count target - no exceptions
        - If you write significantly less than {target_words} words, you FAILED the assignment
        - Better to be comprehensive and detailed than brief
        
        CRITICAL FORMATTING RULES:
        - NO ASTERISKS anywhere in the text
        - NO BOLD formatting (no ** or *)
        - NO section headers in brackets or capitals
        - Use periods (.) for section transitions: "Topic overview." not "Topic Overview:"
        - Write everything as clean, flowing text ready for TTS
        
        ACCURACY RULES:
        - Use ONLY information from the provided articles
        - NO HALLUCINATION: Never invent facts, numbers, or quotes
        - If an article lacks detail, say "reports indicate" or "according to sources"
        - Include source attribution naturally in the text
        - Write in professional broadcast style
        - Use present tense for current events
        
        ANTI-DUPLICATION RULES:
        - NEVER repeat the same story, company, or development across different sections
        - Each company, person, or event should only appear ONCE in the entire briefing
        - Ensure each section covers DIFFERENT aspects of the topic
        
        FORMAT FOR TTS:
        - Company names: spell out abbreviations on first mention
        - Percentages: "five percent" not "5%"  
        - Large numbers: "two point five billion" not "2.5B"
        - Dates: "January fifteenth" not "Jan 15"
        - NEVER use pipe characters (|) - use periods or commas for natural pauses
        - Section transitions need clear pauses: "Topic overview.\\n\\nContent starts here"
        
        Generate the comprehensive {target_length}-minute briefing now:
        """
        
        # Call Gemini for briefing generation
        try:
            print(f"   🧠 Processing {len(articles)} articles with Gemini...")
            print(f"   🎯 Target: {target_words} words ({target_length} minutes)")
            
            response = self.summary_service.model.generate_content(prompt)
            briefing_text = response.text.strip()
            
            # Check word count
            actual_words = len(briefing_text.split())
            print(f"   ✅ Generated briefing: {actual_words} words")
            
            if actual_words < target_words * 0.8:  # Less than 80% of target
                print(f"   ⚠️ Briefing shorter than expected, but proceeding...")
            
            return briefing_text
            
        except Exception as e:
            print(f"   ❌ Gemini error: {str(e)}")
            return f"Error generating briefing for '{topic}'. Please check AI service configuration."
    
    def stitch_audio_with_intro(self, main_audio_file: str, intro_file: str = "intro1.mp3") -> str:
        """Stitch an intro audio file to the beginning of the main audio file."""
        if not AUDIO_STITCHING_AVAILABLE:
            print(f"⚠️ Audio stitching not available (missing pydub/audioop). Skipping intro...")
            return main_audio_file
            
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
            intro_duration = len(intro_audio) / 1000
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
    
    async def generate_briefing(self, topic: str, days_back: int = 1, target_length: int = 15, create_audio: bool = True) -> Dict[str, Any]:
        """Generate the complete topic briefing."""
        print("\n" + "=" * 80)
        print(f"📰 TOPIC BRIEFING GENERATOR")
        print(f"Topic: {topic}")
        print(f"Length: {target_length} minutes")
        print("=" * 80)
        
        # Step 1: Fetch articles
        articles_data = await self.fetch_topic_articles(topic, days_back)
        
        if not articles_data["articles"]:
            return {
                "success": False,
                "error": f"No articles found for topic '{topic}'",
                "topic": topic
            }
        
        # Step 2: Generate briefing
        briefing_text = await self.generate_topic_briefing(articles_data, target_length)
        
        # Step 3: Save files
        timestamp = format_est_timestamp()
        topic_filename = topic.lower().replace(" ", "_").replace("/", "_")
        
        # Save raw data file
        raw_filename = f"topic_briefing_raw_{topic_filename}_{timestamp}.txt"
        raw_data_text = self.format_raw_data(articles_data)
        with open(raw_filename, "w", encoding="utf-8") as f:
            f.write(raw_data_text)
        print(f"\n📊 Raw data saved to: {raw_filename}")
        
        # Save briefing file
        briefing_filename = f"topic_briefing_{topic_filename}_{timestamp}.txt"
        with open(briefing_filename, "w", encoding="utf-8") as f:
            f.write(briefing_text)
        print(f"✅ Briefing saved to: {briefing_filename}")
        print(f"📄 Briefing length: {len(briefing_text.split())} words")
        
        # Step 4: Generate audio if requested
        audio_file = None
        if create_audio and briefing_text:
            print(f"\n🎙️ Generating {target_length}-minute audio briefing...")
            print(f"   📝 Text length: {len(briefing_text.split())} words")
            print(f"   ⏱️ Estimated duration: ~{target_length} minutes")
            print("   🐟 Using Fish Audio service (this may take 3-4 minutes)...")
            
            try:
                # Generate audio
                audio_bytes = await self.audio_service.generate_audio(
                    text=briefing_text,
                    tier="premium"
                )
                
                # Save audio file
                audio_file = f"topic_briefing_audio_{topic_filename}_{timestamp}.mp3"
                with open(audio_file, 'wb') as f:
                    f.write(audio_bytes)
                
                # Calculate metrics
                file_size_mb = len(audio_bytes) / (1024 * 1024)
                estimated_duration = len(briefing_text.split()) / 150
                
                print(f"\n✅ Audio successfully generated!")
                print(f"   🎵 File: {audio_file}")
                print(f"   ⏱️ Estimated duration: {estimated_duration:.1f} minutes")
                print(f"   📁 Size: {file_size_mb:.1f} MB")
                
                # Add intro if available
                final_audio_file = self.stitch_audio_with_intro(audio_file)
                if final_audio_file != audio_file:
                    audio_file = final_audio_file
                
            except Exception as e:
                print(f"❌ Audio generation failed: {str(e)}")
                audio_file = None
        
        return {
            "success": True,
            "topic": topic,
            "briefing_file": briefing_filename,
            "raw_data_file": raw_filename,
            "audio_file": audio_file,
            "word_count": len(briefing_text.split()),
            "target_length_minutes": target_length,
            "articles_analyzed": len(articles_data["articles"]),
            "sources_used": articles_data["sources_used"],
            "timestamp": timestamp
        }
    
    def format_raw_data(self, articles_data: Dict[str, Any]) -> str:
        """Format raw article data for file output."""
        lines = []
        lines.append(f"TOPIC BRIEFING RAW DATA")
        lines.append(f"Generated: {format_est_display()}")
        lines.append("=" * 80)
        
        lines.append(f"\nTopic: {articles_data['topic']}")
        lines.append(f"Classification: {articles_data['classification']}")
        lines.append(f"Sources Used: {', '.join(articles_data['sources_used'])}")
        lines.append(f"Date Range: {articles_data['date_range']}")
        lines.append(f"Total Articles: {articles_data['metadata']['total_articles']}")
        lines.append(f"Search Keywords: {articles_data['metadata']['search_keywords']}")
        
        lines.append(f"\n📰 ARTICLES ({len(articles_data['articles'])} total)")
        lines.append("-" * 60)
        
        for i, article in enumerate(articles_data['articles'], 1):
            lines.append(f"\n{i}. {article.get('title', 'No title')}")
            lines.append(f"   Source: {article.get('source', 'Unknown')}")
            lines.append(f"   Date: {article.get('published_at', 'Unknown')}")
            lines.append(f"   URL: {article.get('url', 'N/A')}")
            
            content = article.get('content', 'No content available')
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"   Content: {content}")
        
        lines.append("\n" + "=" * 80)
        lines.append("END OF RAW DATA")
        
        return "\n".join(lines)


async def main():
    """Main execution function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate topic-specific news briefings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python daily_topic_briefing.py "artificial intelligence"
  python daily_topic_briefing.py "biotechnology" --days=3
  python daily_topic_briefing.py "renewable energy" --length=10 --no-audio
  python daily_topic_briefing.py "cryptocurrency" --days=1 --length=15
        """
    )
    
    parser.add_argument("topic", help="Topic to generate briefing for (e.g., 'biotechnology', 'artificial intelligence')")
    parser.add_argument("--days", type=int, default=1, help="Days to look back for articles (default: 1 = 24 hours)")
    parser.add_argument("--length", type=int, choices=[10, 15], default=15, help="Briefing length in minutes (default: 15)")
    parser.add_argument("--no-audio", action="store_true", help="Skip audio generation")
    
    args = parser.parse_args()
    
    # Validate topic
    if not args.topic or len(args.topic.strip()) < 3:
        print("❌ Error: Topic must be at least 3 characters long")
        sys.exit(1)
    
    topic = args.topic.strip()
    create_audio = not args.no_audio
    
    try:
        generator = TopicBriefingGenerator()
        result = await generator.generate_briefing(
            topic=topic,
            days_back=args.days,
            target_length=args.length,
            create_audio=create_audio
        )
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 GENERATION SUMMARY")
        print("=" * 80)
        
        if result["success"]:
            print(f"✅ Topic: {result['topic']}")
            print(f"📄 Briefing file: {result['briefing_file']}")
            print(f"📊 Raw data file: {result['raw_data_file']}")
            if result.get('audio_file'):
                print(f"🎵 Audio file: {result['audio_file']}")
            print(f"📝 Word count: {result['word_count']} words ({result['target_length_minutes']}-minute target)")
            print(f"📰 Articles analyzed: {result['articles_analyzed']}")
            print(f"🔗 Sources: {', '.join(result['sources_used'])}")
            
            if result.get('audio_file'):
                print(f"\n🎧 Audio briefing ready: {result['audio_file']}")
            else:
                print(f"\n💡 Audio generation was skipped or failed")
        else:
            print(f"❌ Failed to generate briefing: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Generation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())