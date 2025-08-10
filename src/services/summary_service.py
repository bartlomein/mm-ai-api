import os
from typing import List, Dict, Optional
import google.generativeai as genai
from datetime import datetime

class SummaryService:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        Create a 2-3 minute general market summary for free tier
        """
        if not articles:
            return self._create_fallback_script()
        
        # Prepare article summaries using full content
        article_texts = []
        for article in articles[:10]:  # Use top 10 articles
            title = article.get('title', 'No title')
            # Use full content field, limiting to first 1000 chars per article
            content = article.get('content', '')[:1000]
            source = article.get('source', 'Unknown')
            publish_date = article.get('publishDate', '')
            
            # Only include if there's actual content
            if content:
                article_texts.append(f"Title: {title}\nSource: {source}\nDate: {publish_date}\nContent: {content}\n---")
        
        combined_articles = "\n".join(article_texts)
        
        prompt = f"""
        You are creating a 2-3 minute audio news briefing from today's top stories.
        
        Current time of day: {self._get_time_greeting()}
        
        Articles to summarize:
        {combined_articles}
        
        Create a natural, conversational audio script that:
        1. Starts with "Good {self._get_time_greeting()}! Here's your news briefing for {datetime.now().strftime('%B %d')}."
        2. Covers the 3-4 most important or interesting stories
        3. Provides context and explains why these stories matter
        4. Transitions smoothly between topics
        5. Ends with a brief wrap-up
        
        Important formatting rules for audio:
        - Write "percent" not "%"
        - Write "dollars" not "$"
        - Write out numbers (ten thousand, not 10,000)
        - Keep sentences short and conversational
        - Total length should be 300-400 words (2-3 minutes when spoken)
        
        Do not include any markdown, asterisks, or formatting. Just plain conversational text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return self._create_fallback_script()
    
    async def create_personalized_script(self, articles: List[Dict], tickers: List[str]) -> str:
        """
        Create a 5-7 minute personalized summary for premium tier
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
        
        prompt = f"""
        You are creating a 5-7 minute personalized audio briefing focused on these stocks: {tickers_str}
        
        Current time of day: {self._get_time_greeting()}
        
        Articles to summarize:
        {combined_articles}
        
        Create a natural, conversational audio script that:
        1. Starts with "Good {self._get_time_greeting()}! Here's your personalized briefing for {datetime.now().strftime('%B %d')}."
        2. Focus on news that relates to or would interest someone following {tickers_str}
        3. If there's specific news about those companies/stocks, prioritize that
        4. Otherwise, discuss relevant industry news, market trends, or economic news that could affect those stocks
        5. Provide analysis and context
        6. End with key takeaways
        
        Important formatting rules for audio:
        - Write "percent" not "%"
        - Write "dollars" not "$"
        - Write out numbers (ten thousand, not 10,000)
        - Keep sentences short and conversational
        - Total length should be 700-900 words (5-7 minutes when spoken)
        
        Do not include any markdown, asterisks, or formatting. Just plain conversational text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
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