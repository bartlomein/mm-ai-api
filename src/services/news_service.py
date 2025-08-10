import httpx
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class NewsService:
    def __init__(self):
        self.api_key = os.getenv("FINLIGHT_API_KEY")
        self.base_url = "https://api.finlight.me/v2"
        
    async def fetch_general_market(self) -> List[Dict]:
        """
        Fetch general news using /v2/articles endpoint
        Returns articles with full content for summarization
        """
        async with httpx.AsyncClient() as client:
            try:
                # Use the articles endpoint with proper payload
                response = await client.post(
                    f"{self.base_url}/articles",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "X-API-KEY": self.api_key
                    },
                    json={
                        "includeContent": True,  # Get full article content
                        "includeEntities": False,
                        "excludeEmptyContent": True,
                        "pageSize": 100 
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    print(f"Fetched {len(articles)} articles from Finlight")
                    
                    # Return all articles, no filtering
                    return articles[:20]  # Return top 20 articles
                    
                else:
                    print(f"Error fetching articles: {response.status_code}")
                    print(f"Response: {response.text}")
                    return []
                    
            except Exception as e:
                print(f"Error in fetch_general_market: {str(e)}")
                return []
    
    async def fetch_for_tickers(self, tickers: List[str]) -> List[Dict]:
        """
        For now, just fetch all articles and let AI figure out relevance
        In future, could filter by ticker mentions if needed
        """
        # For MVP, just return same articles as general fetch
        # The AI will handle making it relevant to the requested tickers
        articles = await self.fetch_general_market()
        
        # Tag them with the requested tickers for context
        for article in articles:
            article['requested_tickers'] = tickers
        
        print(f"Returning {len(articles)} articles for personalized briefing about: {tickers}")
        
        return articles