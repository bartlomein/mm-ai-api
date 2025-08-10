# Backend Architecture - AI Financial News Audio Platform

## Overview
Fetch news on-demand → AI summarization → Generate personalized audio briefings → Store audio files for playback history

## Tech Stack
- **Database**: Supabase (PostgreSQL + Auth + Storage)
- **Backend**: FastAPI (Python) or Node.js
- **AI/LLM**: Gemini 1.5 Flash (free) → DeepSeek (overflow)
- **TTS**: Kokoro (self-hosted) → Cartesia (premium)
- **News Source**: Finlight API (on-demand fetching)
- **CDN**: Supabase Storage → Cloudflare R2 (scale)

---

## Phase 1: Supabase Setup

### 1.1 Database Schema

```sql
-- Users table (extends Supabase auth.users)
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  subscription_tier TEXT DEFAULT 'free', -- 'free', 'premium', 'pro'
  preferred_voice TEXT DEFAULT 'bella', -- TTS voice preference
  brief_length TEXT DEFAULT 'medium', -- 'short' (2min), 'medium' (5min), 'long' (10min)
  notification_settings JSONB DEFAULT '{"daily": true, "breaking": false}',
  preferred_brief_time TIME DEFAULT '07:00:00',
  timezone TEXT DEFAULT 'America/New_York',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User's stock watchlist/portfolio
CREATE TABLE user_stocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  company_name TEXT,
  shares DECIMAL(10,2), -- NULL for watchlist, number for portfolio
  average_cost DECIMAL(10,2), -- For P&L calculations
  priority INTEGER DEFAULT 5, -- 1-10, for ranking importance
  added_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, ticker)
);

-- Generated audio briefings
CREATE TABLE audio_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL, -- "Morning Brief - March 15, 2024"
  description TEXT, -- Brief summary of what's included
  transcript TEXT NOT NULL, -- Full text that was spoken
  audio_url TEXT NOT NULL, -- Supabase storage URL
  duration_seconds INTEGER,
  file_size_bytes INTEGER,
  
  -- Metadata
  tickers_covered TEXT[], -- Which stocks were discussed
  news_sources INTEGER DEFAULT 0, -- How many articles were summarized
  brief_type TEXT DEFAULT 'on_demand', -- 'daily', 'on_demand', 'breaking'
  voice_model TEXT DEFAULT 'kokoro_bella', -- Track which TTS voice
  llm_model TEXT, -- Which AI model was used
  
  -- Cost tracking
  generation_cost_llm DECIMAL(10,6) DEFAULT 0,
  generation_cost_tts DECIMAL(10,6) DEFAULT 0,
  
  -- User engagement
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_played_at TIMESTAMPTZ,
  play_count INTEGER DEFAULT 0,
  play_duration_seconds INTEGER, -- How much they actually listened
  user_rating INTEGER, -- 1-5 stars
  
  -- Indexing for quick lookups
  INDEX idx_user_created (user_id, created_at DESC),
  INDEX idx_tickers (tickers_covered) USING GIN
);

-- Track generation requests (for rate limiting & debugging)
CREATE TABLE generation_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  request_type TEXT, -- 'full_brief', 'single_stock', 'market_summary'
  tickers_requested TEXT[],
  status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
  error_message TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  briefing_id UUID REFERENCES audio_briefings(id) -- Link to generated audio
);

-- Usage tracking for billing/analytics
CREATE TABLE usage_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  date DATE DEFAULT CURRENT_DATE,
  briefs_generated INTEGER DEFAULT 0,
  minutes_generated INTEGER DEFAULT 0,
  llm_tokens_used INTEGER DEFAULT 0,
  tts_characters_used INTEGER DEFAULT 0,
  cost_total DECIMAL(10,6) DEFAULT 0,
  UNIQUE(user_id, date) -- One row per user per day
);

-- User preferences and feedback
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE UNIQUE,
  
  -- Content preferences
  include_pre_market BOOLEAN DEFAULT true,
  include_after_hours BOOLEAN DEFAULT false,
  include_crypto BOOLEAN DEFAULT false,
  include_international BOOLEAN DEFAULT false,
  news_depth TEXT DEFAULT 'balanced', -- 'headlines', 'balanced', 'detailed'
  
  -- Audio preferences  
  speaking_speed DECIMAL(3,2) DEFAULT 1.0, -- 0.75 to 1.5
  include_music BOOLEAN DEFAULT false,
  
  -- Personalization
  investor_type TEXT DEFAULT 'moderate', -- 'conservative', 'moderate', 'aggressive'
  focus_areas TEXT[], -- ['earnings', 'technical', 'macro', 'company_news']
  
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_briefings_user_date ON audio_briefings(user_id, created_at DESC);
CREATE INDEX idx_stocks_user ON user_stocks(user_id);
CREATE INDEX idx_requests_user_status ON generation_requests(user_id, status);
CREATE INDEX idx_metrics_user_date ON usage_metrics(user_id, date DESC);
```

### 1.2 Row Level Security (RLS)
```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE audio_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can manage own profile" 
  ON user_profiles FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can manage own stocks" 
  ON user_stocks FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own briefings" 
  ON audio_briefings FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own preferences" 
  ON user_preferences FOR ALL USING (auth.uid() = user_id);
```

### 1.3 Supabase Storage Setup
```sql
-- Storage buckets (create in dashboard)
1. audio-briefings (public) - Store generated audio files
   Structure: /{user_id}/{year}/{month}/{briefing_id}.mp3
   
2. audio-cache (private) - Cache common segments
   Structure: /common/{hash}.mp3 (market intro, disclaimers, etc.)
```

## Phase 2: News Fetching & Summarization Pipeline

### 2.1 Core Audio Generation Service
```python
# services/audio_generator.py
from typing import List, Optional
import asyncio
import httpx
from datetime import datetime, timedelta
import hashlib
import json

class AudioBriefingGenerator:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        self.finlight_api = os.getenv("FINLIGHT_API_KEY")
        self.gemini_count = 0
        self.gemini_daily_limit = 375
        
    async def generate_briefing(
        self, 
        user_id: str, 
        tickers: Optional[List[str]] = None,
        brief_type: str = "on_demand"
    ):
        """Main entry point for generating audio briefing"""
        
        # 1. Create request record
        request = await self._create_request(user_id, tickers, brief_type)
        
        try:
            # 2. Get user preferences and stocks
            user_data = await self._get_user_data(user_id)
            
            # 3. Fetch relevant news
            if tickers:
                # Specific stocks requested
                news_content = await self._fetch_ticker_news(tickers)
            else:
                # Use user's portfolio
                user_tickers = [s['ticker'] for s in user_data['stocks']]
                if user_tickers:
                    news_content = await self._fetch_ticker_news(user_tickers)
                else:
                    # General market news
                    news_content = await self._fetch_general_news()
            
            # 4. Generate AI summary
            summary_data = await self._generate_summary(
                news_content, 
                user_data,
                brief_type
            )
            
            # 5. Create audio script
            audio_script = await self._create_audio_script(
                summary_data,
                user_data,
                brief_type
            )
            
            # 6. Generate audio with TTS
            audio_file = await self._generate_audio(
                audio_script,
                user_data['profile']['subscription_tier'],
                user_data['profile']['preferred_voice']
            )
            
            # 7. Upload to storage
            audio_url = await self._upload_audio(audio_file, user_id)
            
            # 8. Create briefing record
            briefing = await self._create_briefing_record(
                user_id=user_id,
                title=self._generate_title(brief_type),
                transcript=audio_script,
                audio_url=audio_url,
                audio_file=audio_file,
                tickers=tickers or user_tickers,
                summary_data=summary_data
            )
            
            # 9. Update request status
            await self._update_request(request['id'], 'completed', briefing['id'])
            
            # 10. Track usage
            await self._track_usage(user_id, summary_data, audio_file)
            
            return briefing
            
        except Exception as e:
            await self._update_request(request['id'], 'failed', error=str(e))
            raise
    
    async def _fetch_ticker_news(self, tickers: List[str]):
        """Fetch news for specific tickers from Finlight"""
        async with httpx.AsyncClient() as client:
            all_articles = []
            
            for ticker in tickers[:10]:  # Limit to 10 tickers
                response = await client.get(
                    f"https://api.finlight.me/v2/news",
                    headers={"Authorization": f"Bearer {self.finlight_api}"},
                    params={
                        "tickers": ticker,
                        "limit": 5,  # 5 articles per ticker
                        "from": (datetime.now() - timedelta(hours=24)).isoformat()
                    }
                )
                
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    all_articles.extend(articles)
            
            # Deduplicate by title
            seen = set()
            unique_articles = []
            for article in all_articles:
                if article['title'] not in seen:
                    seen.add(article['title'])
                    unique_articles.append(article)
            
            return unique_articles[:20]  # Max 20 articles total
    
    async def _fetch_general_news(self):
        """Fetch general market news"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.finlight.me/v2/news",
                headers={"Authorization": f"Bearer {self.finlight_api}"},
                params={
                    "limit": 15,
                    "from": (datetime.now() - timedelta(hours=12)).isoformat()
                }
            )
            
            if response.status_code == 200:
                return response.json().get('articles', [])
            return []
    
    async def _generate_summary(self, articles, user_data, brief_type):
        """Generate AI summary of articles"""
        
        # Prepare context
        portfolio_context = self._create_portfolio_context(user_data)
        
        # Combine article content
        article_texts = []
        for article in articles[:10]:  # Limit to 10 most relevant
            article_texts.append(
                f"Title: {article['title']}\n"
                f"Source: {article.get('source', 'Unknown')}\n"
                f"Content: {article['content'][:1000]}\n"  # First 1000 chars
                f"---"
            )
        
        combined_articles = "\n".join(article_texts)
        
        # Create prompt based on brief type
        prompt = self._create_summary_prompt(
            combined_articles,
            portfolio_context,
            brief_type,
            user_data['preferences']
        )
        
        # Generate summary (try free tier first)
        if self.gemini_count < self.gemini_daily_limit:
            summary = await self._summarize_with_gemini(prompt)
            model_used = "gemini-1.5-flash"
            cost = 0
        else:
            summary = await self._summarize_with_deepseek(prompt)
            model_used = "deepseek-v3"
            cost = len(prompt) * 0.00000014  # $0.14/M tokens
        
        return {
            'summary': summary,
            'articles_processed': len(articles),
            'model': model_used,
            'cost': cost
        }
    
    def _create_summary_prompt(self, articles, portfolio, brief_type, preferences):
        """Create the summarization prompt"""
        
        base_prompt = f"""
        You are creating a personalized audio news briefing for an investor.
        
        User Portfolio: {portfolio}
        Brief Type: {brief_type}
        User Preferences: {preferences}
        
        Articles to summarize:
        {articles}
        
        Create a {brief_type} audio briefing that:
        1. Starts with most important news affecting the user's stocks
        2. Includes market overview if relevant
        3. Mentions specific price movements and percentages
        4. Explains WHY things happened in simple terms
        5. Ends with what to watch for next
        
        Format for audio:
        - Conversational, like a knowledgeable friend
        - Say "percent" not "%", "dollars" not "$"
        - Use company names, then ticker in parentheses
        - Natural transitions between topics
        - Total length: {'2-3 minutes' if brief_type == 'short' else '5-7 minutes'}
        
        Start with: "Good {self._get_time_greeting()}! Here's your market update..."
        """
        
        return base_prompt
    
    def _create_audio_script(self, summary_data, user_data, brief_type):
        """Convert summary into final audio script"""
        
        script_parts = []
        
        # Opening
        greeting = self._get_personalized_greeting(user_data['profile']['full_name'])
        script_parts.append(greeting)
        
        # Main content
        script_parts.append(summary_data['summary'])
        
        # Closing
        closing = self._get_closing(brief_type)
        script_parts.append(closing)
        
        return " ".join(script_parts)
    
    async def _generate_audio(self, script, subscription_tier, voice_preference):
        """Generate audio using TTS service"""
        
        if subscription_tier == 'premium':
            # Use Cartesia for premium
            audio_data = await self._generate_cartesia(script, voice_preference)
        else:
            # Use Kokoro for free tier
            audio_data = await self._generate_kokoro(script, voice_preference)
        
        return audio_data
    
    async def _generate_kokoro(self, text, voice="bella"):
        """Generate with self-hosted Kokoro"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.getenv('KOKORO_URL', 'http://localhost:8880')}/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": text,
                    "voice": f"af_{voice}",
                    "response_format": "mp3"
                },
                timeout=60.0
            )
            return response.content
    
    async def _upload_audio(self, audio_data, user_id):
        """Upload audio to Supabase Storage"""
        
        # Generate filename
        now = datetime.now()
        filename = f"{user_id}/{now.year}/{now.month}/{now.day}_{now.hour}{now.minute}.mp3"
        
        # Upload to storage
        response = self.supabase.storage.from_("audio-briefings").upload(
            filename,
            audio_data,
            file_options={"content-type": "audio/mpeg"}
        )
        
        # Get public URL
        url = self.supabase.storage.from_("audio-briefings").get_public_url(filename)
        
        return url
    
    async def _create_briefing_record(self, **kwargs):
        """Create database record for briefing"""
        
        briefing = self.supabase.table("audio_briefings").insert({
            "user_id": kwargs['user_id'],
            "title": kwargs['title'],
            "description": f"Covering {len(kwargs['tickers'])} stocks",
            "transcript": kwargs['transcript'],
            "audio_url": kwargs['audio_url'],
            "duration_seconds": self._estimate_duration(kwargs['transcript']),
            "file_size_bytes": len(kwargs['audio_file']),
            "tickers_covered": kwargs['tickers'],
            "news_sources": kwargs['summary_data']['articles_processed'],
            "brief_type": kwargs.get('brief_type', 'on_demand'),
            "voice_model": kwargs.get('voice_model', 'kokoro_bella'),
            "llm_model": kwargs['summary_data']['model'],
            "generation_cost_llm": kwargs['summary_data']['cost'],
            "generation_cost_tts": 0  # Kokoro is free
        }).execute()
        
        return briefing.data[0]
    
    def _estimate_duration(self, text):
        """Estimate audio duration (150 words per minute)"""
        word_count = len(text.split())
        return int((word_count / 150) * 60)
    
    def _get_time_greeting(self):
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
```

### 2.2 FastAPI Endpoints
```python
# main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import jwt

app = FastAPI(title="Market Audio Brief API")
security = HTTPBearer()

# Initialize services
audio_generator = AudioBriefingGenerator()

# Request models
class GenerateBriefingRequest(BaseModel):
    tickers: Optional[List[str]] = None
    brief_type: str = "on_demand"

class AddStockRequest(BaseModel):
    ticker: str
    shares: Optional[float] = None
    average_cost: Optional[float] = None

# Auth dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload["sub"]  # user_id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/briefings/generate")
async def generate_briefing(
    request: GenerateBriefingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Generate a new audio briefing"""
    
    # Check rate limiting (e.g., 10 per day for free users)
    today_count = supabase.table("audio_briefings").select(
        "count", count="exact"
    ).eq("user_id", user_id).gte(
        "created_at", datetime.now().date().isoformat()
    ).execute().count
    
    user = supabase.table("user_profiles").select("subscription_tier").eq(
        "id", user_id
    ).single().execute().data
    
    if user['subscription_tier'] == 'free' and today_count >= 3:
        raise HTTPException(status_code=429, detail="Daily limit reached")
    
    # Generate in background
    background_tasks.add_task(
        audio_generator.generate_briefing,
        user_id,
        request.tickers,
        request.brief_type
    )
    
    return {
        "status": "generating",
        "message": "Your briefing is being generated. Check back in 30-60 seconds."
    }

@app.get("/api/briefings")
async def get_briefings(
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get user's briefing history"""
    
    briefings = supabase.table("audio_briefings").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    
    return {
        "briefings": briefings.data,
        "total": len(briefings.data),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/briefings/{briefing_id}")
async def get_briefing(
    briefing_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get specific briefing and mark as played"""
    
    briefing = supabase.table("audio_briefings").select("*").eq(
        "id", briefing_id
    ).eq("user_id", user_id).single().execute()
    
    if not briefing.data:
        raise HTTPException(status_code=404, detail="Briefing not found")
    
    # Update play count
    supabase.table("audio_briefings").update({
        "last_played_at": datetime.now().isoformat(),
        "play_count": briefing.data["play_count"] + 1
    }).eq("id", briefing_id).execute()
    
    return briefing.data

@app.post("/api/briefings/{briefing_id}/rate")
async def rate_briefing(
    briefing_id: str,
    rating: int,
    user_id: str = Depends(get_current_user)
):
    """Rate a briefing"""
    
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    supabase.table("audio_briefings").update({
        "user_rating": rating
    }).eq("id", briefing_id).eq("user_id", user_id).execute()
    
    return {"status": "rated"}

@app.get("/api/stocks")
async def get_stocks(user_id: str = Depends(get_current_user)):
    """Get user's stock watchlist"""
    
    stocks = supabase.table("user_stocks").select("*").eq(
        "user_id", user_id
    ).order("priority", desc=True).execute()
    
    return stocks.data

@app.post("/api/stocks")
async def add_stock(
    stock: AddStockRequest,
    user_id: str = Depends(get_current_user)
):
    """Add stock to watchlist"""
    
    # Check if already exists
    existing = supabase.table("user_stocks").select("id").eq(
        "user_id", user_id
    ).eq("ticker", stock.ticker.upper()).execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")
    
    # Add stock
    result = supabase.table("user_stocks").insert({
        "user_id": user_id,
        "ticker": stock.ticker.upper(),
        "shares": stock.shares,
        "average_cost": stock.average_cost
    }).execute()
    
    return result.data[0]

@app.delete("/api/stocks/{ticker}")
async def remove_stock(
    ticker: str,
    user_id: str = Depends(get_current_user)
):
    """Remove stock from watchlist"""
    
    supabase.table("user_stocks").delete().eq(
        "user_id", user_id
    ).eq("ticker", ticker.upper()).execute()
    
    return {"status": "removed"}

@app.get("/api/profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get user profile and preferences"""
    
    profile = supabase.table("user_profiles").select(
        "*, user_preferences(*)"
    ).eq("id", user_id).single().execute()
    
    return profile.data

@app.patch("/api/profile")
async def update_profile(
    updates: dict,
    user_id: str = Depends(get_current_user)
):
    """Update user profile"""
    
    allowed_fields = [
        'full_name', 'preferred_voice', 'brief_length',
        'preferred_brief_time', 'timezone'
    ]
    
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    result = supabase.table("user_profiles").update(
        filtered_updates
    ).eq("id", user_id).execute()
    
    return result.data[0]

@app.get("/api/usage")
async def get_usage(user_id: str = Depends(get_current_user)):
    """Get usage statistics"""
    
    # Today's usage
    today = datetime.now().date().isoformat()
    
    usage = supabase.table("usage_metrics").select("*").eq(
        "user_id", user_id
    ).eq("date", today).single().execute()
    
    # This month's totals
    month_start = datetime.now().replace(day=1).date().isoformat()
    
    monthly = supabase.table("usage_metrics").select(
        "briefs_generated, minutes_generated, cost_total"
    ).eq("user_id", user_id).gte("date", month_start).execute()
    
    monthly_totals = {
        "briefs": sum(d["briefs_generated"] for d in monthly.data),
        "minutes": sum(d["minutes_generated"] for d in monthly.data),
        "cost": sum(d["cost_total"] for d in monthly.data)
    }
    
    return {
        "today": usage.data if usage.data else {"briefs_generated": 0},
        "month": monthly_totals
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

### 2.3 Background Jobs (Optional - for scheduled briefs)
```python
# workers/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class BriefingScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.audio_generator = AudioBriefingGenerator()
        
    def start(self):
        # Morning briefs
        self.scheduler.add_job(
            self.generate_morning_briefs,
            'cron',
            hour=6,
            minute=0,
            id='morning_briefs'
        )
        
        # Market close summary
        self.scheduler.add_job(
            self.generate_close_briefs,
            'cron',
            hour=16,
            minute=30,
            day_of_week='mon-fri',
            id='close_briefs'
        )
        
        self.scheduler.start()
    
    async def generate_morning_briefs(self):
        """Generate morning briefs for subscribed users"""
        
        # Get users who want morning briefs
        users = supabase.table("user_profiles").select(
            "id, user_stocks(ticker)"
        ).eq("notification_settings->daily", True).execute().data
        
        for user in users:
            tickers = [s['ticker'] for s in user['user_stocks']]
            await self.audio_generator.generate_briefing(
                user['id'],
                tickers,
                'daily'
            )
```

## Phase 3: Deployment

### 3.1 Docker Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
      - FINLIGHT_API_KEY=${FINLIGHT_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - CARTESIA_API_KEY=${CARTESIA_API_KEY}
      - KOKORO_URL=http://kokoro:8880
    depends_on:
      - kokoro

  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
    ports:
      - "8880:8880"
    volumes:
      - ./models:/app/models
```

### 3.2 Environment Variables
```env
# .env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
SUPABASE_JWT_SECRET=xxx
FINLIGHT_API_KEY=xxx
GEMINI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx
CARTESIA_API_KEY=xxx  # Optional for premium
KOKORO_URL=http://localhost:8880
```

## Implementation Timeline

### Week 1: Core Pipeline
- [ ] Set up Supabase (schema, auth, storage)
- [ ] Deploy Kokoro TTS locally
- [ ] Build Finlight integration
- [ ] Test news fetching with tickers

### Week 2: AI & Audio
- [ ] Implement summarization (Gemini + DeepSeek)
- [ ] Create audio generation pipeline
- [ ] Test end-to-end flow
- [ ] Set up storage and CDN

### Week 3: API & Features
- [ ] Build FastAPI endpoints
- [ ] Add authentication
- [ ] Implement rate limiting
- [ ] Add user preferences

### Week 4: Polish & Deploy
- [ ] Error handling
- [ ] Performance optimization
- [ ] Deploy to production
- [ ] Monitor and iterate

## Cost Analysis

### Per User Per Day
| Component | Free Tier | Premium Tier |
|-----------|-----------|--------------|
| News API | $0.001 (shared) | $0.001 |
| LLM Summary | $0.001 (Gemini free) | $0.005 (better model) |
| TTS | $0 (Kokoro) | $0.01 (Cartesia) |
| Storage | $0.001 | $0.001 |
| **Total** | **$0.002** | **$0.017** |

### At Scale (1000 users, 30% daily active)
| Component | Monthly Cost |
|-----------|-------------|
| Hosting (API + Kokoro) | $20 |
| Finlight API | $50-100 |
| LLM (300 briefs/day) | $15 |
| Storage (Supabase) | $25 |
| **Total** | **$110-160/month** |

## Key Optimizations

### Smart Caching
- Cache news fetches for 15 minutes
- Reuse summaries for similar portfolios
- Store common audio segments

### Batch Processing
- Group API calls to Finlight
- Batch LLM requests when possible

### Progressive Enhancement
- Start with basic summaries
- Add features based on usage

### Cost Controls
- Daily limits for free users
- Gemini free tier first, then DeepSeek
- Self-hosted Kokoro for all free users

## Security Best Practices

### API Security
- Rate limiting per user
- JWT validation on all endpoints
- Input sanitization

### Data Privacy
- Audio files use signed URLs
- No storage of raw article content
- User data isolation with RLS

### Cost Protection
- Daily generation limits
- Request queuing
- Monitoring alerts

## Monitoring & Analytics

Track these metrics:
- Briefings generated per day
- Average generation time
- Cost per briefing
- User retention (daily actives)
- Audio completion rates
- User ratings
- Popular tickers
- Peak usage times

This streamlined architecture focuses on the core loop: fetch news → summarize → generate audio → store. Much simpler than storing articles, and you can iterate quickly on the summarization quality without worrying about data management.