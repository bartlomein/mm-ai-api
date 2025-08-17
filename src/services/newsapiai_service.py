import httpx
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NewsAPIAIService:
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_AI_KEY")
        self.base_url = "https://eventregistry.org/api/v1"
        
        if not self.api_key:
            print("[NewsAPIAIService] WARNING: NEWSAPI_AI_KEY not found in environment variables")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
        """Make HTTP request with consistent error handling"""
        if not self.api_key:
            print("[NewsAPIAIService] ERROR: API key not configured")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to data payload if using POST
        if data:
            data["apiKey"] = self.api_key
        
        # Add API key to params if using GET
        if params:
            params["apiKey"] = self.api_key
        elif not data:
            params = {"apiKey": self.api_key}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if data:
                    # POST request with JSON data
                    response = await client.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json=data
                    )
                else:
                    # GET request with query params
                    response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"[NewsAPIAIService] Error {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"[NewsAPIAIService] Request error: {str(e)}")
            return None
    
    async def search_articles(
        self,
        keyword: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        sort_by: str = "date",
        max_articles: int = 50,
        category: Optional[str] = None,
        ignore_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search articles with date filtering and English language
        
        Args:
            keyword: Search terms/phrases
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            sort_by: Sort method (date, rel, cosSim)
            max_articles: Maximum number of articles to return
            category: News category (business, economy, etc.)
            ignore_sources: List of source URIs to exclude (e.g., ["timesofindia.com"])
        
        Returns:
            Dict with articles, summary, and metadata
        """
        try:
            # Build query parameters
            query_data = {
                "action": "getArticles",
                "resultType": "articles",
                "articlesSortBy": sort_by,
                "articlesCount": max_articles,
                "lang": "eng",  # Always English
                "dataType": "news"  # Only news articles, not blogs or PR
            }
            
            # Add keyword search if provided
            if keyword:
                query_data["keyword"] = keyword
                query_data["keywordsLoc"] = "body,title"  # Search in both title and body
            
            # Add date filtering if provided
            if date_start:
                query_data["dateStart"] = date_start
            if date_end:
                query_data["dateEnd"] = date_end
            
            # Add category filtering for financial news
            if category:
                # Map common categories to NewsAPI.ai category URIs
                category_map = {
                    "business": "dmoz/Business",
                    "finance": "dmoz/Business/Financial_Services",
                    "economy": "dmoz/Business/Economics_and_Trade",
                    "markets": "dmoz/Business/Investing"
                }
                if category.lower() in category_map:
                    query_data["categoryUri"] = category_map[category.lower()]
            
            # Add source exclusion - default to excluding Times of India
            default_ignore = ["timesofindia.com", "timesofindia.indiatimes.com"]
            
            if ignore_sources is None:
                ignore_sources = default_ignore
            else:
                # Combine user-specified sources with defaults
                ignore_sources = list(set(ignore_sources + default_ignore))
            
            # Add to query if we have sources to exclude
            if ignore_sources:
                if len(ignore_sources) == 1:
                    query_data["ignoreSourceUri"] = ignore_sources[0]
                else:
                    # For multiple sources, pass as list
                    query_data["ignoreSourceUri"] = ignore_sources
            
            # Log the search parameters including excluded sources
            if ignore_sources:
                print(f"[NewsAPIAIService] Searching articles with keyword: {keyword}, dates: {date_start} to {date_end}, excluding: {ignore_sources}")
            else:
                print(f"[NewsAPIAIService] Searching articles with keyword: {keyword}, dates: {date_start} to {date_end}")
            
            response = await self._make_request("article/getArticles", data=query_data)
            
            if not response:
                return {"articles": [], "summary": "No articles found", "metadata": {}}
            
            # Extract articles from response
            articles_data = response.get("articles", {})
            raw_articles = articles_data.get("results", [])
            
            # Normalize article format to match existing services
            normalized_articles = []
            for article in raw_articles:
                normalized_article = {
                    "title": article.get("title", ""),
                    "content": article.get("body", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("dateTime", ""),
                    "source": article.get("source", {}).get("title", "Unknown"),
                    "author": self._extract_authors(article.get("authors", [])),
                    "language": article.get("lang", "eng"),
                    "sentiment": article.get("sentiment", 0),
                    "relevance": article.get("relevance", 0),
                    "concepts": [c.get("label", "") for c in article.get("concepts", [])[:5]],  # Top 5 concepts
                    "categories": [c.get("label", "") for c in article.get("categories", [])[:3]],  # Top 3 categories
                    "location": article.get("location", {}).get("label", ""),
                    "image": article.get("image", ""),
                    "social_score": article.get("socialScore", {})
                }
                normalized_articles.append(normalized_article)
            
            # Generate summary for LLM consumption
            summary = self._generate_summary(normalized_articles, keyword, date_start, date_end)
            
            # Prepare metadata
            metadata = {
                "total_results": articles_data.get("totalResults", 0),
                "articles_returned": len(normalized_articles),
                "search_keyword": keyword,
                "date_start": date_start,
                "date_end": date_end,
                "sort_by": sort_by,
                "language": "eng",
                "query_timestamp": datetime.now().isoformat()
            }
            
            print(f"[NewsAPIAIService] Found {len(normalized_articles)} articles")
            
            return {
                "articles": normalized_articles,
                "summary": summary,
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"[NewsAPIAIService] Error in search_articles: {str(e)}")
            return {"articles": [], "summary": "Search failed", "metadata": {}}
    
    async def fetch_financial_news(
        self,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        max_articles: int = 30,
        ignore_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch financial and business news specifically
        """
        # Use business/finance keywords for better targeting
        financial_keywords = "stock market OR trading OR investment OR finance OR economy OR earnings OR IPO OR cryptocurrency OR forex"
        
        return await self.search_articles(
            keyword=financial_keywords,
            date_start=date_start,
            date_end=date_end,
            max_articles=max_articles,
            category="finance",
            ignore_sources=ignore_sources
        )
    
    async def fetch_for_date_range(
        self,
        days_back: int = 1,
        keyword: Optional[str] = None,
        max_articles: int = 50,
        ignore_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch articles from the last N days
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        date_start = start_date.strftime("%Y-%m-%d")
        date_end = end_date.strftime("%Y-%m-%d")
        
        return await self.search_articles(
            keyword=keyword,
            date_start=date_start,
            date_end=date_end,
            max_articles=max_articles,
            ignore_sources=ignore_sources
        )
    
    async def get_recent_headlines(
        self,
        hours_back: int = 24,
        keyword: Optional[str] = None,
        max_articles: int = 20,
        ignore_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get recent headlines from the last N hours
        """
        # Convert hours to days for date filtering
        days_back = max(1, hours_back // 24)
        
        result = await self.fetch_for_date_range(
            days_back=days_back,
            keyword=keyword,
            max_articles=max_articles,
            ignore_sources=ignore_sources
        )
        
        # Filter to articles within the hour range if we have precise timestamps
        if result.get("articles"):
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            filtered_articles = []
            
            for article in result["articles"]:
                try:
                    # Try to parse the article timestamp
                    if article.get("published_at"):
                        article_time = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
                        if article_time >= cutoff_time:
                            filtered_articles.append(article)
                except:
                    # If timestamp parsing fails, include the article
                    filtered_articles.append(article)
            
            result["articles"] = filtered_articles[:max_articles]
            result["metadata"]["filtered_by_hours"] = hours_back
            result["summary"] = self._generate_summary(filtered_articles, keyword, None, None)
        
        return result
    
    async def search_articles_by_time(
        self,
        keyword: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        sort_by: str = "date",
        max_articles: int = 50,
        category: Optional[str] = None,
        ignore_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search articles with precise datetime filtering
        
        Args:
            keyword: Search terms/phrases
            start_datetime: Start datetime (timezone-aware or naive)
            end_datetime: End datetime (timezone-aware or naive)
            sort_by: Sort method (date, rel, cosSim)
            max_articles: Maximum number of articles to return
            category: News category (business, economy, etc.)
        
        Returns:
            Dict with articles, summary, and metadata
        """
        try:
            # Convert datetime to date strings for the API
            date_start = None
            date_end = None
            
            if start_datetime:
                date_start = start_datetime.strftime("%Y-%m-%d")
            if end_datetime:
                date_end = end_datetime.strftime("%Y-%m-%d")
            
            print(f"[NewsAPIAIService] Searching articles with datetime filter: {start_datetime} to {end_datetime}")
            
            # Get articles for the date range first
            result = await self.search_articles(
                keyword=keyword,
                date_start=date_start,
                date_end=date_end,
                sort_by=sort_by,
                max_articles=max_articles * 2,  # Get more to account for time filtering
                category=category,
                ignore_sources=ignore_sources
            )
            
            articles = result.get("articles", [])
            
            # Filter by precise time if datetime parameters provided
            if (start_datetime or end_datetime) and articles:
                filtered_articles = []
                
                for article in articles:
                    try:
                        # Parse article timestamp
                        article_time_str = article.get("published_at", "")
                        if not article_time_str:
                            continue
                            
                        # Handle different timestamp formats
                        if article_time_str.endswith('Z'):
                            article_time = datetime.fromisoformat(article_time_str.replace('Z', '+00:00'))
                        elif '+' in article_time_str or article_time_str.endswith('UTC'):
                            article_time = datetime.fromisoformat(article_time_str.replace('UTC', '+00:00'))
                        else:
                            # Assume UTC if no timezone info
                            article_time = datetime.fromisoformat(article_time_str)
                        
                        # Convert to naive datetime for comparison if input datetimes are naive
                        if start_datetime and start_datetime.tzinfo is None and article_time.tzinfo is not None:
                            article_time = article_time.replace(tzinfo=None)
                        elif end_datetime and end_datetime.tzinfo is None and article_time.tzinfo is not None:
                            article_time = article_time.replace(tzinfo=None)
                        
                        # Apply time filters
                        if start_datetime and article_time < start_datetime:
                            continue
                        if end_datetime and article_time > end_datetime:
                            continue
                            
                        filtered_articles.append(article)
                        
                        # Stop if we have enough articles
                        if len(filtered_articles) >= max_articles:
                            break
                            
                    except Exception as e:
                        # If timestamp parsing fails, include article to be safe
                        print(f"[NewsAPIAIService] Warning: Could not parse timestamp for article: {e}")
                        filtered_articles.append(article)
                        continue
                
                result["articles"] = filtered_articles[:max_articles]
                result["metadata"]["filtered_by_datetime"] = True
                result["metadata"]["start_datetime"] = start_datetime.isoformat() if start_datetime else None
                result["metadata"]["end_datetime"] = end_datetime.isoformat() if end_datetime else None
                result["metadata"]["articles_after_time_filter"] = len(filtered_articles)
                
                # Update summary
                result["summary"] = self._generate_summary_with_time(
                    filtered_articles, keyword, start_datetime, end_datetime
                )
                
                print(f"[NewsAPIAIService] Time filter applied: {len(articles)} -> {len(filtered_articles)} articles")
            
            return result
            
        except Exception as e:
            print(f"[NewsAPIAIService] Error in search_articles_by_time: {str(e)}")
            return {"articles": [], "summary": "Time-based search failed", "metadata": {}}

    async def get_trending_topics(self, max_topics: int = 10) -> Dict[str, Any]:
        """
        Get trending topics/concepts in financial news
        """
        try:
            # Get recent financial news to analyze trending topics
            recent_news = await self.fetch_financial_news(max_articles=100)
            
            if not recent_news.get("articles"):
                return {"topics": [], "summary": "No trending topics available", "metadata": {}}
            
            # Extract and count concepts from articles
            concept_counts = {}
            category_counts = {}
            
            for article in recent_news["articles"]:
                # Count concepts (entities, topics)
                for concept in article.get("concepts", []):
                    if concept and len(concept) > 2:  # Filter out very short concepts
                        concept_counts[concept] = concept_counts.get(concept, 0) + 1
                
                # Count categories
                for category in article.get("categories", []):
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1
            
            # Get top trending concepts
            trending_concepts = sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:max_topics]
            trending_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate summary
            top_concepts = [concept for concept, count in trending_concepts[:5]]
            summary = f"Trending topics in financial news: {', '.join(top_concepts)}"
            
            return {
                "topics": {
                    "concepts": trending_concepts,
                    "categories": trending_categories
                },
                "summary": summary,
                "metadata": {
                    "articles_analyzed": len(recent_news["articles"]),
                    "unique_concepts": len(concept_counts),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"[NewsAPIAIService] Error in get_trending_topics: {str(e)}")
            return {"topics": [], "summary": "Trending analysis failed", "metadata": {}}
    
    def _extract_authors(self, authors_list: List[Dict]) -> str:
        """Extract author names from authors list"""
        if not authors_list:
            return "Unknown"
        
        author_names = [author.get("name", "") for author in authors_list if author.get("name")]
        if author_names:
            return ", ".join(author_names[:2])  # Return up to 2 authors
        return "Unknown"
    
    def _generate_summary(
        self,
        articles: List[Dict],
        keyword: Optional[str],
        date_start: Optional[str],
        date_end: Optional[str]
    ) -> str:
        """Generate human-readable summary for LLM consumption"""
        if not articles:
            return "No articles found for the specified criteria."
        
        # Extract key information
        sources = list(set([article.get("source", "Unknown") for article in articles[:10]]))
        top_sources = sources[:5]
        
        # Get date range of articles
        dates = []
        for article in articles:
            if article.get("published_at"):
                try:
                    date_str = article["published_at"][:10]  # Extract YYYY-MM-DD
                    dates.append(date_str)
                except:
                    pass
        
        date_range = ""
        if dates:
            unique_dates = sorted(set(dates))
            if len(unique_dates) == 1:
                date_range = f" from {unique_dates[0]}"
            elif len(unique_dates) > 1:
                date_range = f" from {unique_dates[0]} to {unique_dates[-1]}"
        
        # Build summary
        summary_parts = []
        summary_parts.append(f"Found {len(articles)} articles{date_range}")
        
        if keyword:
            summary_parts.append(f"searching for '{keyword}'")
        
        if top_sources:
            summary_parts.append(f"from sources including {', '.join(top_sources[:3])}")
        
        # Add trending topics if available
        trending_concepts = []
        for article in articles[:10]:
            trending_concepts.extend(article.get("concepts", [])[:2])
        
        if trending_concepts:
            unique_concepts = list(set(trending_concepts))[:5]
            summary_parts.append(f"covering topics like {', '.join(unique_concepts)}")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_summary_with_time(
        self,
        articles: List[Dict],
        keyword: Optional[str],
        start_datetime: Optional[datetime],
        end_datetime: Optional[datetime]
    ) -> str:
        """Generate human-readable summary for time-filtered LLM consumption"""
        if not articles:
            return "No articles found for the specified time criteria."
        
        # Extract key information
        sources = list(set([article.get("source", "Unknown") for article in articles[:10]]))
        top_sources = sources[:5]
        
        # Build time range string
        time_range = ""
        if start_datetime and end_datetime:
            time_range = f" from {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}"
        elif start_datetime:
            time_range = f" since {start_datetime.strftime('%Y-%m-%d %H:%M')}"
        elif end_datetime:
            time_range = f" before {end_datetime.strftime('%Y-%m-%d %H:%M')}"
        
        # Build summary
        summary_parts = []
        summary_parts.append(f"Found {len(articles)} articles{time_range}")
        
        if keyword:
            summary_parts.append(f"searching for '{keyword}'")
        
        if top_sources:
            summary_parts.append(f"from sources including {', '.join(top_sources[:3])}")
        
        # Add trending topics if available
        trending_concepts = []
        for article in articles[:10]:
            trending_concepts.extend(article.get("concepts", [])[:2])
        
        if trending_concepts:
            unique_concepts = list(set(trending_concepts))[:5]
            summary_parts.append(f"covering topics like {', '.join(unique_concepts)}")
        
        return ". ".join(summary_parts) + "."