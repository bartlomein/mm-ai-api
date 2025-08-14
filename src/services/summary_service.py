import os
from typing import List, Dict, Optional
import google.generativeai as genai
from datetime import datetime

class SummaryService:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # Use Gemini 2.0 Flash for better performance and higher rate limits
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def _get_time_greeting(self) -> str:
        """Get appropriate time-based greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    async def create_general_script(self, articles: List[Dict]) -> str:
        """
        Create a 5-minute general market summary for free tier
        """
        if not articles:
            return self._create_fallback_script()
        
        # Prepare article summaries using full content
        article_texts = []
        for article in articles[:15]:  # Use more articles for 5-minute briefing
            title = article.get('title', 'No title')
            # Use full content field, limiting to first 1500 chars per article
            content = article.get('content', '')[:1500]
            source = article.get('source', 'Unknown')
            publish_date = article.get('publishDate', '')
            
            # Only include if there's actual content
            if content:
                article_texts.append(f"Title: {title}\nSource: {source}\nDate: {publish_date}\nContent: {content}\n---")
        
        combined_articles = "\n".join(article_texts)
        
        prompt = f"""
        You are creating a 5-minute audio news briefing from today's top financial and market stories.
        This will be fed into a text-to-speech system, so formatting for pronunciation is CRITICAL.
        
        Current time of day: {self._get_time_greeting()}
        Date: {datetime.now().strftime('%B %d, %Y')}
        
        Articles to summarize:
        {combined_articles}
        
        Create a natural, conversational audio script following these STRICT rules:
        
        STRUCTURE:
        1. Opening (20 words): "Good {self._get_time_greeting()}. Here's your market briefing for {datetime.now().strftime('%B %d')}. Let's begin with today's major developments."
        2. Cover 8-10 stories with FULL DETAIL (each 75-100 words)
        3. Group related stories together (e.g., tech stocks, energy sector, economic indicators)
        4. Provide context and explain market impact
        5. End with: "That concludes your market briefing. Have a successful trading day."
        
        CRITICAL CONTENT RULES:
        - AVOID REPETITION: If multiple articles mention the same company/event, discuss it ONLY ONCE
        - NO REDUNDANCY: Don't repeat "C3AI dropped 31%" in different sections
        - DIVERSE COVERAGE: Cover as many different companies as possible
        - Each ticker should appear only once in the entire briefing
        - If you see duplicate news, pick the most detailed version and ignore others
        
        CRITICAL PRONUNCIATION RULES:
        - Stock tickers: ALWAYS write as "ticker [spell out letters] --" with double dash for pause.
          Example: "ticker A-A-P-L --" not "AAPL"
          The double dash creates a natural pause after the ticker.
        - Percentages: Write "percent" not "%". Example: "up five percent"
        - Currency: Write "dollars", "euros", "pounds". Example: "fifty billion dollars"
        - Large numbers: Spell out completely. Examples:
          * 1,000 = "one thousand"
          * 10,000 = "ten thousand" 
          * 1,000,000 = "one million"
          * 1,500,000 = "one point five million"
          * 2,300,000,000 = "two point three billion"
        - Dates: Write out months. Example: "January fifteenth" not "Jan 15"
        - Abbreviations: Spell out completely:
          * CEO = "C-E-O" or "chief executive officer"
          * IPO = "I-P-O" or "initial public offering"
          * GDP = "G-D-P" or "gross domestic product"
          * AI = "A-I" or "artificial intelligence"
          * EV = "E-V" or "electric vehicle"
        
        PACING AND CLARITY:
        - Use short, clear sentences (max 20 words)
        - Add natural pauses with periods between topics
        - Use transition phrases: "Moving to tech news...", "In the energy sector...", "Turning to economic data..."
        - Avoid run-on sentences
        - Each story should be 3-5 sentences
        
        CONTENT REQUIREMENTS:
        - YOU MUST WRITE EXACTLY 800 WORDS. NOT 200. NOT 400. EXACTLY 800 WORDS.
        - Each story gets 100+ words. No quick summaries. Full detailed coverage.
        - Be specific with company names and numbers
        - Explain WHY each story matters to investors
        - Include both positive and negative market news for balance
        
        FORBIDDEN:
        - No markdown formatting (*, **, #, etc.)
        - No parentheses or brackets
        - No URLs or email addresses
        - No abbreviations without spelling them out
        - No special characters
        
        Remember: Every word must be pronounceable by TTS. When in doubt, spell it out phonetically.
        
        IMPORTANT: This MUST be a FULL 5-minute briefing (750-850 words). Don't rush through headlines.
        Provide detailed coverage with context, background, analysis, and market implications for each story.
        Think of this as a professional Bloomberg Radio or CNBC segment, not a quick summary.
        """
        
        try:
            # Configure for longer output
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
                "candidate_count": 1
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            result = response.text.strip()
            
            # Check word count
            word_count = len(result.split())
            if word_count < 700:
                print(f"[SummaryService] WARNING: Generated only {word_count} words, retrying...")
                # Try again with even more explicit instructions
                retry_prompt = prompt + f"\n\nYOU ONLY WROTE {word_count} WORDS. THIS IS TOO SHORT. WRITE EXACTLY 800 WORDS."
                response = self.model.generate_content(retry_prompt, generation_config=generation_config)
                result = response.text.strip()
            
            return result
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return self._create_fallback_script()
    
    async def create_personalized_script(self, articles: List[Dict], tickers: List[str]) -> str:
        """
        Create a 5-minute personalized summary for premium tier
        """
        if not articles:
            return self._create_fallback_script(tickers)
        
        # Group articles by ticker
        ticker_articles = {}
        for article in articles:
            ticker = article.get('primary_ticker', 'GENERAL')
            if ticker not in ticker_articles:
                ticker_articles[ticker] = []
            ticker_articles[ticker].append(article)
        
        # Prepare detailed summaries using full content
        article_texts = []
        for ticker in tickers[:10]:
            if ticker in ticker_articles:
                ticker_news = ticker_articles[ticker][:3]  # Top 3 per ticker
                for article in ticker_news:
                    title = article.get('title', 'No title')
                    # Use the full content field, with more chars for personalized
                    content = article.get('content', '')[:1500]  # More content for premium
                    source = article.get('source', 'Unknown')
                    publish_date = article.get('publishDate', '')
                    
                    if content:
                        article_texts.append(f"[{ticker}] Title: {title}\nSource: {source}\nDate: {publish_date}\nContent: {content}\n---")
        
        # If no ticker-specific articles, use general ones
        if not article_texts and articles:
            for article in articles[:5]:
                title = article.get('title', 'No title')
                content = article.get('content', '')[:1500]
                source = article.get('source', 'Unknown')
                if content:
                    article_texts.append(f"Title: {title}\nSource: {source}\nContent: {content}\n---")
        
        combined_articles = "\n".join(article_texts)
        tickers_str = ", ".join(tickers[:10])
        
        # Format tickers for TTS with pauses
        formatted_tickers = []
        for ticker in tickers[:10]:
            formatted_ticker = "ticker " + "-".join(list(ticker.upper())) + " --"  # Add pause after ticker
            formatted_tickers.append(formatted_ticker)
        tickers_tts = ", ".join(formatted_tickers)
        
        prompt = f"""
        You are creating a 5-minute personalized audio briefing focused on these stocks: {tickers_tts}
        This will be fed into a text-to-speech system, so formatting for pronunciation is CRITICAL.
        
        Current time of day: {self._get_time_greeting()}
        Date: {datetime.now().strftime('%B %d, %Y')}
        
        Articles to summarize:
        {combined_articles}
        
        Create a natural, conversational audio script following these STRICT rules:
        
        STRUCTURE:
        1. Opening: "Good {self._get_time_greeting()}. Here's your personalized briefing for {datetime.now().strftime('%B %d')}, focusing on your portfolio."
        2. Cover news about the specified tickers first
        3. Then cover relevant sector and market news
        4. Provide analysis on how news affects these specific stocks
        5. End with: "That's your personalized market update. Stay informed and trade wisely."
        
        CRITICAL CONTENT RULES:
        - AVOID REPETITION: Each company/ticker should be discussed ONLY ONCE
        - NO REDUNDANCY: If multiple articles cover the same event, synthesize into one mention
        - FOCUS ON YOUR STOCKS: Prioritize news about {tickers_tts}
        - DIVERSE COVERAGE: After covering tracked stocks, add variety with different market news
        
        CRITICAL PRONUNCIATION RULES:
        - Stock tickers: ALWAYS write as "ticker [spell out letters] --" with double dash for pause.
          Examples: "{tickers[0] if tickers else 'AAPL'}" becomes "ticker {'-'.join(list(tickers[0])) if tickers else 'A-A-P-L'} --"
        - When mentioning the companies, use full names when possible
        - Percentages: Write "percent" not "%". Example: "up twelve percent"
        - Currency: Write "dollars", "euros", "pounds". Example: "thirty million dollars"
        - Large numbers: Spell out completely:
          * 1,000 = "one thousand"
          * 50,000 = "fifty thousand" 
          * 1,200,000 = "one point two million"
          * 3,500,000,000 = "three point five billion"
        - Dates: Write out months. Example: "March twenty-first"
        - Financial terms spelled out:
          * P/E = "P-E ratio" or "price to earnings ratio"
          * EPS = "E-P-S" or "earnings per share"
          * YoY = "year over year"
          * QoQ = "quarter over quarter"
          * M&A = "M and A" or "mergers and acquisitions"
        
        PACING AND CLARITY:
        - Use short, clear sentences (max 20 words)
        - Pause between different stocks/topics with periods
        - Use transitions: "Regarding {formatted_tickers[0]}...", "Moving to your tech holdings..."
        - Each stock should get 30-60 seconds of coverage
        
        CONTENT REQUIREMENTS:
        - YOU MUST WRITE EXACTLY 800 WORDS. NOT 200. NOT 400. EXACTLY 800 WORDS.
        - Each story gets 100+ words. No quick summaries. Full detailed coverage.
        - Prioritize news about the specified tickers
        - Explain how broader market trends affect these specific stocks
        - Include price movements if mentioned in articles
        - Provide actionable insights
        
        FORBIDDEN:
        - No markdown formatting (*, **, #, etc.)
        - No parentheses or brackets  
        - No URLs or email addresses
        - No abbreviations without spelling them out
        - No special characters or symbols
        
        Remember: Every word must be perfectly pronounceable. The user is tracking {tickers_tts}.
        
        IMPORTANT: This MUST be a FULL 5-minute personalized briefing (750-850 words). Don't rush.
        Provide in-depth analysis of how each news item affects the tracked stocks. Include price targets,
        analyst opinions, and strategic implications. This is a premium briefing - make it comprehensive.
        """
        
        try:
            # Configure for longer output
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
                "candidate_count": 1
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            result = response.text.strip()
            
            # Check word count
            word_count = len(result.split())
            if word_count < 700:
                print(f"[SummaryService] WARNING: Generated only {word_count} words, retrying...")
                # Try again with even more explicit instructions
                retry_prompt = prompt + f"\n\nYOU ONLY WROTE {word_count} WORDS. THIS IS TOO SHORT. WRITE EXACTLY 800 WORDS."
                response = self.model.generate_content(retry_prompt, generation_config=generation_config)
                result = response.text.strip()
            
            return result
        except Exception as e:
            print(f"Error generating personalized summary: {str(e)}")
            return self._create_fallback_script(tickers)
    
    def _create_fallback_script(self, tickers: Optional[List[str]] = None) -> str:
        """Create a fallback script if API fails"""
        greeting = f"Good {self._get_time_greeting()}! "
        
        if tickers:
            tickers_str = ", ".join(tickers[:5])
            return f"{greeting}We're having trouble fetching the latest news for {tickers_str}. Please try again in a few moments."
        else:
            return f"{greeting}We're having trouble fetching the latest market news. Please try again in a few moments."
    
    async def create_market_data_script(self, articles: List[Dict], enhanced_prompt: str) -> str:
        """
        Create a script combining real-time market data with news context
        Used with FMP service data
        """
        try:
            # Prepare article context if available
            article_context = ""
            if articles:
                article_summaries = []
                for article in articles[:10]:
                    title = article.get('title', 'No title')
                    content = article.get('content', '')[:500]
                    if content:
                        article_summaries.append(f"- {title}: {content[:200]}...")
                
                article_context = "\n".join(article_summaries)
            
            # Combine enhanced prompt with article context
            full_prompt = enhanced_prompt
            if article_context:
                full_prompt += f"\n\nRECENT NEWS HEADLINES:\n{article_context}"
            
            # Add TTS formatting rules
            full_prompt += """
            
            CRITICAL FORMATTING RULES FOR TEXT-TO-SPEECH:
            1. Stock tickers MUST be formatted as: "ticker A-A-P-L --" (spell out each letter with dashes, then pause)
            2. Percentages: Write out as "twenty-five percent" not "25%"
            3. Currency: "$1.5B" becomes "one point five billion dollars"
            4. Large numbers: "2,500,000" becomes "two point five million"
            5. Abbreviations: "CEO" becomes "C-E-O", "IPO" becomes "I-P-O", "S&P" becomes "S and P"
            
            Structure:
            - Opening greeting with date (20 words)
            - Market indices overview (150 words)
            - Individual stock movements (150 words)
            - Sector performance (120 words)
            - Crypto market update (100 words)
            - Economic events/outlook (100 words)
            - Market sentiment and closing (110 words)
            
            TOTAL: 750-850 words for 5-minute audio at 150 words per minute
            """
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 2048,
            }
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            result = response.text.strip()
            
            # Check word count
            word_count = len(result.split())
            if word_count < 700:
                print(f"[SummaryService] WARNING: Generated only {word_count} words for market data script")
            
            return result
            
        except Exception as e:
            print(f"Error generating market data script: {str(e)}")
            # Return the enhanced prompt as fallback
            return enhanced_prompt