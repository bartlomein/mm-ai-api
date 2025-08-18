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
        
        # Topic to Wikipedia concept URI mapping
        self.topic_concepts = {
            "artificial intelligence": "http://en.wikipedia.org/wiki/Artificial_intelligence",
            "biotechnology": "http://en.wikipedia.org/wiki/Biotechnology", 
            "cryptocurrency": "http://en.wikipedia.org/wiki/Cryptocurrency",
            "renewable energy": "http://en.wikipedia.org/wiki/Renewable_energy",
            "electric vehicles": "http://en.wikipedia.org/wiki/Electric_vehicle",
            "quantum computing": "http://en.wikipedia.org/wiki/Quantum_computing",
            "gene therapy": "http://en.wikipedia.org/wiki/Gene_therapy",
            "nuclear fusion": "http://en.wikipedia.org/wiki/Nuclear_fusion",
            "space tourism": "http://en.wikipedia.org/wiki/Space_tourism",
            "cybersecurity": "http://en.wikipedia.org/wiki/Computer_security",
            "blockchain": "http://en.wikipedia.org/wiki/Blockchain",
            "machine learning": "http://en.wikipedia.org/wiki/Machine_learning",
            "climate change": "http://en.wikipedia.org/wiki/Climate_change",
            "federal reserve": "http://en.wikipedia.org/wiki/Federal_Reserve",
            "pharmaceutical": "http://en.wikipedia.org/wiki/Pharmaceutical_industry"
        }
    
    def get_concept_uri(self, topic: str) -> Optional[str]:
        """Get Wikipedia concept URI for a topic."""
        topic_lower = topic.lower().strip()
        
        # Direct match
        if topic_lower in self.topic_concepts:
            return self.topic_concepts[topic_lower]
        
        # Partial match for compound topics
        for known_topic, uri in self.topic_concepts.items():
            if known_topic in topic_lower or any(word in topic_lower for word in known_topic.split()):
                return uri
        
        # Generate URI for unknown topics
        formatted_topic = topic.replace(" ", "_").title()
        return f"http://en.wikipedia.org/wiki/{formatted_topic}"
    
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
        Search articles using proper NewsAPI.ai query structure
        
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
            # Build proper NewsAPI.ai query structure following sandbox example
            query_conditions = []
            
            # Try to use concept URI first for better results
            concept_uri = None
            if keyword:
                concept_uri = self.get_concept_uri(keyword)
                if concept_uri:
                    query_conditions.append({"conceptUri": concept_uri})
                    print(f"[NewsAPIAIService] Using concept URI: {concept_uri}")
                else:
                    # Fallback to keyword search
                    query_conditions.append({"keyword": keyword, "keywordsLoc": "body,title"})
                    print(f"[NewsAPIAIService] Using keyword search: {keyword}")
            
            # Add date and language filtering
            date_lang_condition = {"lang": "eng"}
            if date_start:
                date_lang_condition["dateStart"] = date_start
            if date_end:
                date_lang_condition["dateEnd"] = date_end
            query_conditions.append(date_lang_condition)
            
            # Add category filtering if provided
            if category:
                category_map = {
                    "business": "dmoz/Business",
                    "finance": "dmoz/Business/Financial_Services", 
                    "economy": "dmoz/Business/Economics_and_Trade",
                    "markets": "dmoz/Business/Investing"
                }
                if category.lower() in category_map:
                    query_conditions.append({"categoryUri": category_map[category.lower()]})
            
            # Build the complete query structure exactly like the sandbox
            query_data = {
                "$query": {
                    "$and": query_conditions
                },
                "$filter": {
                    "startSourceRankPercentile": 0,
                    "endSourceRankPercentile": 40  # Top 40% sources as requested
                }
            }
            
            # Add source exclusion to filter
            default_ignore = ["timesofindia.com", "timesofindia.indiatimes.com"]
            if ignore_sources is None:
                ignore_sources = default_ignore
            else:
                ignore_sources = list(set(ignore_sources + default_ignore))
            
            if ignore_sources:
                if len(ignore_sources) == 1:
                    query_data["$filter"]["ignoreSourceUri"] = ignore_sources[0]
                else:
                    query_data["$filter"]["ignoreSourceUri"] = ignore_sources
            
            # Prepare the complete request data
            request_data = {
                "query": query_data,
                "resultType": "articles",
                "articlesSortBy": sort_by,
                "articlesCount": max_articles
            }
            
            # Log the search parameters
            print(f"[NewsAPIAIService] Searching: {keyword or concept_uri}, dates: {date_start} to {date_end}, top 40% sources")
            
            response = await self._make_request("article/getArticles", data=request_data)
            
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
    
    async def search_articles_by_topic(
        self,
        topic: str,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        max_articles: int = 50
    ) -> Dict[str, Any]:
        """
        Search articles by topic using concept URI (better for specific topics)
        """
        try:
            concept_uri = self.get_concept_uri(topic)
            
            # Build query conditions
            query_conditions = [
                {"conceptUri": concept_uri}
            ]
            
            # Add date and language filtering
            date_lang_condition = {"lang": "eng"}
            if date_start:
                date_lang_condition["dateStart"] = date_start
            if date_end:
                date_lang_condition["dateEnd"] = date_end
            query_conditions.append(date_lang_condition)
            
            # Build complete query following sandbox structure
            request_data = {
                "query": {
                    "$query": {
                        "$and": query_conditions
                    },
                    "$filter": {
                        "startSourceRankPercentile": 0,
                        "endSourceRankPercentile": 40,  # Top 40% sources
                        "ignoreSourceUri": ["timesofindia.com", "timesofindia.indiatimes.com"]
                    }
                },
                "resultType": "articles",
                "articlesSortBy": "date",
                "articlesCount": max_articles
            }
            
            print(f"[NewsAPIAIService] Topic search using concept URI: {concept_uri}")
            print(f"[NewsAPIAIService] Date range: {date_start} to {date_end}, max articles: {max_articles}")
            
            response = await self._make_request("article/getArticles", data=request_data)
            
            if not response:
                return {"articles": [], "summary": "No articles found", "metadata": {}}
            
            # Extract articles from response
            articles_data = response.get("articles", {})
            raw_articles = articles_data.get("results", [])
            
            # Normalize article format
            normalized_articles = []
            for article in raw_articles:
                normalized_article = {
                    "title": article.get("title", ""),
                    "content": article.get("body", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("dateTime", ""),
                    "source": article.get("source", {}).get("title", "Unknown"),
                    "author": self._extract_authors(article.get("authors", [])),
                    "language": article.get("lang", ""),
                    "sentiment": article.get("sentiment"),
                    "relevance": article.get("relevance"),
                    "concepts": self._extract_concepts(article.get("concepts", [])),
                    "categories": self._extract_categories(article.get("categories", [])),
                    "location": self._extract_location(article.get("location")),
                    "image": article.get("image"),
                    "social_score": article.get("socialScore", {})
                }
                normalized_articles.append(normalized_article)
            
            # Create summary
            summary = f"Found {len(normalized_articles)} articles on {topic}"
            if date_start and date_end:
                summary += f" from {date_start} to {date_end}"
            
            # Create metadata
            metadata = {
                "total_results": articles_data.get("totalResults", len(normalized_articles)),
                "articles_returned": len(normalized_articles),
                "search_topic": topic,
                "concept_uri": concept_uri,
                "date_start": date_start,
                "date_end": date_end,
                "source_quality": "top_40_percent",
                "query_timestamp": datetime.now().isoformat()
            }
            
            print(f"[NewsAPIAIService] Found {len(normalized_articles)} articles using concept URI")
            
            return {
                "articles": normalized_articles,
                "summary": summary,
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"[NewsAPIAIService] Error in search_articles_by_topic: {str(e)}")
            return {"articles": [], "summary": "Topic search failed", "metadata": {}}
    
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
    
    def _extract_concepts(self, concepts_list: List[Dict]) -> List[str]:
        """Extract concept labels from concepts list"""
        if not concepts_list:
            return []
        
        concepts = [concept.get("label", {}).get("eng", "") for concept in concepts_list if concept.get("label")]
        return [c for c in concepts if c][:5]  # Return up to 5 concepts
    
    def _extract_categories(self, categories_list: List[Dict]) -> List[str]:
        """Extract category labels from categories list"""
        if not categories_list:
            return []
        
        categories = [cat.get("label", {}).get("eng", "") for cat in categories_list if cat.get("label")]
        return [c for c in categories if c][:3]  # Return up to 3 categories
    
    def _extract_location(self, location_data: Optional[Dict]) -> str:
        """Extract location from location data"""
        if not location_data:
            return ""
        
        if isinstance(location_data, dict):
            return location_data.get("label", {}).get("eng", "")
        return str(location_data)
    
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