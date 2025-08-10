# Backend Pipeline PRD - Mobile-First Audio Briefing API

## Overview
API-first backend development for a React Native app that delivers both general market briefings (free) and personalized financial news audio briefings (paid tiers). Includes payment processing, subscription management, and tiered content delivery.

## Mobile App Requirements Context
- **Platform**: React Native (iOS & Android)
- **Audio Playback**: Streaming MP3 files
- **Auth**: Supabase Auth SDK
- **Payments**: Stripe integration (via Supabase)
- **Content Tiers**: Free (general news) / Premium ($4.99) / Pro ($14.99)
- **Real-time**: Push notifications for completed briefings
- **Offline**: Download capability (premium feature)

---

## Subscription Tiers & Features

### Free Tier
- **Daily Limit**: 1 general market briefing
- **Content**: Top market news (not personalized)
- **Audio Length**: 2-3 minutes
- **Voice**: Basic Kokoro voice
- **History**: Last 7 days only
- **Ads**: Audio ads at start/end

### Premium Tier ($4.99/month)
- **Daily Limit**: 5 personalized briefings
- **Content**: Personalized to 10 stocks
- **Audio Length**: 5 minutes
- **Voice**: Premium Kokoro voices
- **History**: 30 days
- **Features**: Download for offline, no ads
- **Priority**: Faster generation

### Pro Tier ($14.99/month)
- **Daily Limit**: Unlimited briefings
- **Content**: Unlimited stocks + sectors
- **Audio Length**: Up to 10 minutes
- **Voice**: Premium voices + Cartesia option
- **History**: Unlimited
- **Features**: Real-time alerts, API access
- **Priority**: Highest priority queue

---

## News Content Strategy

### General Market Feed (Free)
- **Sources**: Market indices, top movers, major headlines
- **Update Frequency**: Every 4 hours
- **Caching**: Aggressive (same for all free users)
- **Personalization**: None (same content for everyone)

### Personalized Feed (Paid)
- **Sources**: User's portfolio, watchlist, sectors
- **Update Frequency**: On-demand + scheduled
- **Caching**: Per-user basis
- **Personalization**: Based on holdings, preferences, behavior

---

## Phase 1: Minimal Pipeline MVP (Days 1-3)
*Get both free and paid pipelines working*

### 1.1 Dual Pipeline System

#### Quick Setup Script
```bash
# Initial project structure
mkdir -p src/{services,api,utils,config}
touch src/main.py
touch .env
```

#### Core Services to Build

**NewsService** (`src/services/news.py`)
```python
class NewsService:
    async def fetch_general_market(self):
        """Free tier: SPY, QQQ, DIA, top movers"""
        # Cached for all free users
        
    async def fetch_for_tickers(self, tickers: List[str], tier: str):
        """Paid tiers: personalized news"""
        # Check tier limits
        # Premium: max 10 tickers
        # Pro: unlimited
```

**SummaryService** (`src/services/summary.py`)
```python
class SummaryService:
    async def create_general_script(self, articles):
        """Free tier: generic market summary"""
        # 2-3 minute script
        # Include ad slots
        
    async def create_personalized_script(self, articles, user_profile):
        """Paid tiers: personalized narrative"""
        # 5-10 minute script based on tier
        # User's positions, P&L context
```

**AudioService** (`src/services/audio.py`)
```python
class AudioService:
    async def generate_mp3(self, text: str, tier: str):
        """Generate based on tier"""
        # Free: basic voice, with ads
        # Premium: better voices, no ads
        # Pro: best voices + Cartesia option
```

**PipelineService** (`src/services/pipeline.py`)
```python
class PipelineService:
    async def generate_general_briefing(self):
        """Batch generate for all free users"""
        # Run every 4 hours
        # Store single copy
        
    async def generate_personalized_briefing(self, user_id):
        """On-demand for paid users"""
        # Check subscription status
        # Apply tier limits
```

### 1.2 Minimal API Endpoints

```python
# Free tier endpoints
GET /api/briefings/general/latest
  response: { 
    audio_url,  # Same for all free users
    generated_at,
    duration,
    title: "Market Update - 3PM"
  }

# Paid tier endpoints  
POST /api/briefings/personalized
  body: { tickers?: ["AAPL", "TSLA"] }
  response: { 
    briefing_id: "uuid",
    status: "queued",
    tier: "premium|pro"
  }

# Subscription endpoints
GET /api/subscription/status
  response: {
    tier: "free|premium|pro",
    expires_at?: date,
    usage: {
      briefings_today: 1,
      briefings_limit: 5
    }
  }

POST /api/subscription/checkout
  body: { tier: "premium|pro" }
  response: { checkout_url: "stripe_url" }
```

### 1.3 Local Testing Setup
```yaml
# docker-compose.yml - Just the essentials
services:
  api:
    build: .
    ports: ["8000:8000"]
  
  kokoro:
    image: kokoro-tts
    ports: ["8880:8880"]
```

### Deliverable: Working Demo
- Can generate audio for 2-3 stocks
- Returns playable MP3 URL
- Mobile app can play the audio

---

## Phase 2: Mobile-Optimized API (Days 4-6)
*Make it work well with React Native*

### 2.1 Supabase Integration

#### Database Tables (With Subscriptions)
```sql
-- User subscription management
CREATE TABLE user_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users UNIQUE,
  tier TEXT DEFAULT 'free', -- 'free', 'premium', 'pro'
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  status TEXT DEFAULT 'active', -- 'active', 'canceled', 'past_due'
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Track daily usage for limits
CREATE TABLE usage_tracking (
  user_id UUID REFERENCES auth.users,
  date DATE DEFAULT CURRENT_DATE,
  briefings_generated INT DEFAULT 0,
  api_calls INT DEFAULT 0,
  PRIMARY KEY (user_id, date)
);

-- General briefings (shared by all free users)
CREATE TABLE general_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT, -- "Morning Market Update"
  audio_url TEXT,
  transcript TEXT,
  duration_seconds INT,
  market_summary JSONB, -- Indices, top movers, etc
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ -- When to regenerate
);

-- Personalized briefings (paid users)
CREATE TABLE personalized_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  tier TEXT NOT NULL, -- Track which tier generated this
  audio_url TEXT,
  transcript TEXT,
  duration_seconds INT,
  tickers TEXT[],
  personalization_context JSONB, -- User's positions, P&L, etc
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User's stock watchlist (paid feature)
CREATE TABLE user_tickers (
  user_id UUID REFERENCES auth.users,
  ticker TEXT,
  shares DECIMAL(10,2), -- For P&L calculation (pro feature)
  avg_cost DECIMAL(10,2),
  priority INT DEFAULT 5, -- Which stocks to focus on
  PRIMARY KEY (user_id, ticker)
);

-- Payment history
CREATE TABLE payment_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  amount INT, -- In cents
  currency TEXT DEFAULT 'usd',
  tier TEXT,
  stripe_payment_intent TEXT,
  status TEXT, -- 'succeeded', 'failed'
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Storage Setup
- Single bucket: `audio-files`
- Public access for signed URLs
- 7-day expiration

### 2.2 Authentication Middleware

```python
# Verify Supabase JWT from React Native
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if token:
        user = verify_supabase_token(token)
        request.state.user = user
    return await call_next(request)
```

### 2.3 Mobile-Friendly Endpoints

```python
# Free Tier Endpoints
GET /api/briefings/general/latest
  response: {
    id, audio_url, title, duration,
    generated_at,
    next_update_at,  # When new one will be available
    ad_markers: [  # For ad insertion
      { position: 0, duration: 15 },
      { position: 180, duration: 15 }
    ]
  }

GET /api/briefings/general/history
  query: { limit: 7 }  # Free users get 7 days
  response: {
    briefings: [{
      id, title, duration, generated_at, audio_url
    }]
  }

# Paid Tier Endpoints
POST /api/briefings/personalized
  headers: { Authorization: "Bearer {token}" }
  body: { 
    tickers?: string[],  # Optional, uses saved
    length?: "short|medium|long",
    focus?: "holdings|watchlist|sectors"
  }
  response: {
    briefing_id: string,
    status: "queued|limited|upgrade_required",
    queue_position?: number,
    estimated_seconds: 15  # Faster for paid
  }

GET /api/briefings/personalized/history
  query: { limit: 30, offset: 0 }
  response: {
    briefings: [{
      id, title, duration, created_at,
      audio_url,
      tickers_covered,
      tier_generated,  # Which tier was used
      downloadable: boolean  # Premium/Pro only
    }],
    has_more: boolean
  }

# Portfolio Management (Paid Feature)
GET /api/portfolio
  response: {
    tier: "free|premium|pro",
    tickers: tier === "free" ? null : [{
      ticker, company_name,
      shares?, avg_cost?,  # Pro only
      current_price, change_percent,
      p_l?: number  # Pro only
    }],
    portfolio_value?: number,  # Pro only
    daily_change?: number  # Pro only
  }

POST /api/portfolio/add
  body: { 
    ticker: string,
    shares?: number,  # Pro only
    avg_cost?: number  # Pro only
  }
  response: {
    success: boolean,
    error?: "tier_limit|invalid_ticker",
    upgrade_url?: string
  }

# Subscription Management
GET /api/subscription/status
  response: {
    tier: "free|premium|pro",
    status: "active|canceled|past_due",
    expires_at?: date,
    cancel_at_period_end: boolean,
    usage: {
      briefings_today: 1,
      briefings_limit: 5,
      stocks_used: 3,
      stocks_limit: 10
    },
    features: {
      personalized_news: boolean,
      portfolio_tracking: boolean,
      unlimited_history: boolean,
      api_access: boolean,
      priority_generation: boolean
    }
  }

POST /api/subscription/create-checkout
  body: { 
    tier: "premium|pro",
    period: "monthly|yearly"  # Yearly gets discount
  }
  response: {
    checkout_url: string,  # Stripe hosted checkout
    session_id: string
  }

POST /api/subscription/manage
  response: {
    portal_url: string  # Stripe customer portal
  }

# Webhook for Stripe (backend only)
POST /api/webhooks/stripe
  # Handles subscription updates
```

### 2.4 Push Notification Support
```python
# When briefing is ready
async def notify_briefing_ready(user_id, briefing_id):
    await supabase.rpc('notify_user', {
        'user_id': user_id,
        'title': 'Your briefing is ready!',
        'body': 'Tap to listen',
        'data': {'briefing_id': briefing_id}
    })
```

---

## Phase 3: Production Pipeline (Days 7-9)
*Scale and optimize*

### 3.1 Background Processing with Tiers

```python
# Priority queues based on subscription tier
from asyncio import PriorityQueue

class BriefingQueue:
    def __init__(self):
        self.queue = PriorityQueue()
        
    async def add_job(self, user_id: str, tier: str):
        priority = {
            "pro": 1,      # Highest priority
            "premium": 2,  # Medium priority  
            "free": 3      # Lowest priority
        }[tier]
        
        await self.queue.put((priority, user_id))

# Scheduled job for general briefings
@app.on_event("startup")
async def schedule_general_briefings():
    # Generate new general briefing every 4 hours
    scheduler.add_job(
        generate_general_briefing,
        'cron',
        hour='*/4',  # 12am, 4am, 8am, 12pm, 4pm, 8pm
        id='general_briefing'
    )

async def generate_general_briefing():
    """Generate one briefing for all free users"""
    # Fetch general market news
    news = await news_service.fetch_general_market()
    
    # Create generic summary
    script = await summary_service.create_general_script(news)
    
    # Add ad slots
    script_with_ads = add_audio_ads(script)
    
    # Generate audio once
    audio = await audio_service.generate_mp3(script_with_ads, "free")
    
    # Store in general_briefings table
    await store_general_briefing(audio)
```

### 3.2 Caching Layer

```python
# Simple in-memory cache to start
from cachetools import TTLCache

news_cache = TTLCache(maxsize=100, ttl=900)  # 15 min
summary_cache = TTLCache(maxsize=50, ttl=3600)  # 1 hour

def get_cached_news(tickers_key):
    return news_cache.get(tickers_key)
```

### 3.3 Error Handling & Retries

```python
# Graceful degradation for mobile experience
class BriefingError(Exception):
    def to_mobile_response(self):
        return {
            "error": self.message,
            "retry_after": self.retry_seconds,
            "fallback_action": self.fallback  # e.g., "try_fewer_tickers"
        }
```

### 3.4 Rate Limiting by Tier

```python
# Dynamic limits based on subscription
from slowapi import Limiter

def get_rate_limit(request: Request):
    user = request.state.user
    tier = user.subscription_tier
    
    limits = {
        "free": "1/day",
        "premium": "5/day",
        "pro": "100/day"  # Essentially unlimited
    }
    return limits[tier]

limiter = Limiter(key_func=get_user_id)

@app.post("/api/briefings/personalized")
@limiter.limit(get_rate_limit)
async def create_personalized_briefing():
    pass

# Also check database limits
async def check_usage_limits(user_id: str, tier: str):
    today = datetime.now().date()
    usage = await db.fetch_one(
        "SELECT briefings_generated FROM usage_tracking WHERE user_id = ? AND date = ?",
        user_id, today
    )
    
    limits = {"free": 1, "premium": 5, "pro": 100}
    
    if usage and usage['briefings_generated'] >= limits[tier]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Daily limit reached",
                "limit": limits[tier],
                "upgrade_url": "/subscription/upgrade"
            }
        )
```

---

## Payment Integration (Stripe + Supabase)

### Stripe Setup
```python
# services/payments.py
import stripe
from typing import Optional

class PaymentService:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.price_ids = {
            "premium_monthly": "price_xxx",  # $4.99/mo
            "premium_yearly": "price_yyy",   # $49.99/yr (2 months free)
            "pro_monthly": "price_zzz",      # $14.99/mo
            "pro_yearly": "price_aaa"        # $149.99/yr (2 months free)
        }
    
    async def create_checkout_session(
        self,
        user_id: str,
        email: str,
        tier: str,
        period: str
    ):
        """Create Stripe checkout session"""
        
        price_id = self.price_ids[f"{tier}_{period}"]
        
        session = stripe.checkout.Session.create(
            customer_email=email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=f"{APP_URL}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/subscription/cancel",
            metadata={
                'user_id': user_id,
                'tier': tier
            },
            allow_promotion_codes=True,
            billing_address_collection='auto'
        )
        
        return session
    
    async def handle_webhook(self, payload: dict, signature: str):
        """Process Stripe webhook events"""
        
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            os.getenv("STRIPE_WEBHOOK_SECRET")
        )
        
        if event.type == 'checkout.session.completed':
            session = event.data.object
            await self.activate_subscription(
                session.metadata.user_id,
                session.subscription,
                session.metadata.tier
            )
            
        elif event.type == 'customer.subscription.updated':
            sub = event.data.object
            await self.update_subscription(sub)
            
        elif event.type == 'customer.subscription.deleted':
            sub = event.data.object
            await self.cancel_subscription(sub)
    
    async def activate_subscription(
        self,
        user_id: str,
        stripe_sub_id: str,
        tier: str
    ):
        """Activate user's subscription"""
        
        subscription = stripe.Subscription.retrieve(stripe_sub_id)
        
        await db.execute("""
            INSERT INTO user_subscriptions 
            (user_id, tier, stripe_subscription_id, status,
             current_period_start, current_period_end)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                tier = $2,
                stripe_subscription_id = $3,
                status = $4,
                current_period_start = $5,
                current_period_end = $6,
                updated_at = NOW()
        """, user_id, tier, stripe_sub_id, subscription.status,
            datetime.fromtimestamp(subscription.current_period_start),
            datetime.fromtimestamp(subscription.current_period_end))
```

### Trial Period Support
```python
# 7-day free trial for new users
async def create_trial_checkout(user_id: str, tier: str):
    session = stripe.checkout.Session.create(
        # ... other params
        subscription_data={
            'trial_period_days': 7,
            'trial_settings': {
                'end_behavior': {
                    'missing_payment_method': 'cancel'
                }
            }
        }
    )
```

### In-App Purchase Support (iOS/Android)
```python
# Validate IAP receipts
@app.post("/api/subscription/validate-iap")
async def validate_iap(
    platform: str,  # 'ios' or 'android'
    receipt: str,
    product_id: str
):
    if platform == 'ios':
        # Validate with Apple
        is_valid = await validate_apple_receipt(receipt)
    else:
        # Validate with Google
        is_valid = await validate_google_receipt(receipt)
    
    if is_valid:
        # Activate subscription
        await activate_iap_subscription(user_id, product_id)
```

---

## Phase 4: Mobile Experience Optimization (Days 10-12)
*Make it fast and reliable for mobile*

### 4.1 Response Optimization

```python
# Pagination for large responses
class PaginatedResponse:
    items: List[Any]
    next_cursor: Optional[str]
    has_more: bool

# Partial responses for quick loading
@app.get("/api/briefings/{id}/quick")
async def get_briefing_quick(id: str):
    # Return just what's needed for playback
    return {
        "audio_url": url,
        "duration": seconds
    }
```

### 4.2 Audio Streaming Optimization

```python
# Support range requests for audio streaming
@app.get("/api/audio/{file_id}")
async def stream_audio(
    file_id: str,
    range: Optional[str] = Header(None)
):
    if range:
        # Handle byte-range requests for smooth streaming
        start, end = parse_range_header(range)
        return StreamingResponse(
            audio_chunks(start, end),
            status_code=206,
            headers={"Accept-Ranges": "bytes"}
        )
```

### 4.3 Offline Support Endpoints

```python
# Help React Native cache effectively
@app.get("/api/briefings/{id}/download")
async def get_download_info(id: str):
    return {
        "audio_url": signed_url,  # 24-hour signed URL
        "expires_at": timestamp,
        "file_size": bytes,
        "checksum": md5  # For integrity
    }
```

### 4.4 WebSocket for Real-time Updates

```python
# Real-time generation progress
@app.websocket("/ws/briefings/{briefing_id}")
async def briefing_progress(websocket: WebSocket, briefing_id: str):
    await websocket.accept()
    
    while generating:
        progress = get_generation_progress(briefing_id)
        await websocket.send_json({
            "status": progress.status,
            "percent": progress.percent,
            "message": progress.message
        })
        await asyncio.sleep(1)
```

---

## Phase 5: Analytics & Monitoring (Days 13-14)
*Track mobile app usage*

### 5.1 Mobile Analytics Endpoints

```python
# Track listening behavior
POST /api/analytics/playback
  body: {
    briefing_id: string,
    event: "started|paused|completed|skipped",
    position: number,
    session_id: string
  }

# App performance metrics
POST /api/analytics/performance
  body: {
    metric: "audio_load_time|api_response_time",
    value: number,
    context: {}
  }
```

### 5.2 User Engagement Tracking

```python
# Metrics that matter for mobile
- Daily active users
- Audio completion rate
- Time to first play
- Network errors
- Offline playback usage
```

---

## Mobile-Specific Considerations

### API Response Format
```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "version": "1.0",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Error Responses for React Native
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after": 60,
    "upgrade_url": "app://upgrade"
  }
}
```

### Health Check for App
```python
@app.get("/api/health/mobile")
async def mobile_health():
    return {
        "api": "healthy",
        "kokoro": check_kokoro(),
        "news_api": check_finlight(),
        "min_app_version": "1.0.0",
        "features": {
            "audio_generation": True,
            "push_notifications": True
        }
    }
```

---

## Development Priorities

### Week 1 Focus
1. ✅ Get basic pipeline working
2. ✅ Generate first audio file
3. ✅ Serve it to React Native app
4. ✅ Add Supabase auth
5. ✅ Store briefings in database

### Week 2 Focus
1. ✅ Background processing
2. ✅ User ticker management
3. ✅ Caching for performance
4. ✅ Mobile-optimized responses
5. ✅ Error handling

### Testing with React Native
```javascript
// Quick test from React Native
const testAPI = async () => {
  const response = await fetch('http://localhost:8000/api/briefings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${supabaseToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tickers: ['AAPL', 'GOOGL']
    })
  });
  
  const data = await response.json();
  console.log('Briefing ID:', data.briefing_id);
  
  // Poll for completion
  setTimeout(async () => {
    const briefing = await fetch(
      `http://localhost:8000/api/briefings/${data.briefing_id}`
    );
    const audio = await briefing.json();
    
    // Play audio
    await TrackPlayer.add({
      id: audio.id,
      url: audio.audio_url,
      title: 'Market Briefing',
      duration: audio.duration
    });
    await TrackPlayer.play();
  }, 30000);
};
```

---

## Environment Variables
```env
# Backend (.env)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx  # Public key for client
SUPABASE_SERVICE_KEY=xxx  # Secret for backend
FINLIGHT_API_KEY=xxx
GEMINI_API_KEY=xxx
DEEPSEEK_API_KEY=xxx  # Fallback when Gemini quota exceeded
KOKORO_URL=http://localhost:8880
CARTESIA_API_KEY=xxx  # For Pro tier premium voices

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_PREMIUM_MONTHLY=price_xxx
STRIPE_PRICE_PREMIUM_YEARLY=price_yyy
STRIPE_PRICE_PRO_MONTHLY=price_zzz
STRIPE_PRICE_PRO_YEARLY=price_aaa

# React Native (.env)
API_URL=http://localhost:8000  # or production URL
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# In-App Purchase Product IDs
IAP_PREMIUM_MONTHLY=com.yourapp.premium.monthly
IAP_PREMIUM_YEARLY=com.yourapp.premium.yearly
IAP_PRO_MONTHLY=com.yourapp.pro.monthly
IAP_PRO_YEARLY=com.yourapp.pro.yearly
```

---

## Quick Start Commands

```bash
# 1. Setup Python environment
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx supabase python-dotenv

# 2. Start Kokoro TTS
docker run -p 8880:8880 kokoro-tts

# 3. Run the API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 4. Test from React Native
# Update API_URL in your app to your machine's IP
# e.g., http://192.168.1.100:8000
```

---

## Success Metrics for Mobile Backend

### Performance
- API response time: <200ms (p95)
- Audio generation: <30 seconds
- Audio URL availability: <100ms
- Streaming start time: <2 seconds

### Reliability  
- API uptime: >99.5%
- Audio generation success: >95%
- Mobile client compatibility: 100%

### User Experience
- Time to first audio: <45 seconds
- Playback interruptions: <1%
- Offline playback success: >90%

This backend is specifically designed to work seamlessly with your React Native app, focusing on mobile-first API design, efficient audio delivery, and smooth user experience.