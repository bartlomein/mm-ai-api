# MVP Roadmap - AI Financial News Audio Platform

## Project Vision
Build a mobile app that delivers AI-generated audio briefings of financial news. Start with general market updates for everyone, then add personalized premium tiers.

## MVP Scope (2 Weeks)
- ✅ General market briefings (1/day free, no ads)
- ✅ Personalization by ticker selection ($9.99/month)
- ✅ Stripe payments for subscriptions
- ✅ React Native app with audio playback
- ❌ Portfolio tracking (post-MVP)
- ❌ Real-time alerts (post-MVP)
- ❌ Social features (post-MVP)

## Subscription Tiers

### Free Tier
- **1 general market briefing per day**
- **No ads** (clean experience)
- 2-3 minute market overview
- Last 7 days history

### Premium Tier ($9.99/month)
- **3 briefings per day**
- **Personalized by ticker selection**
- 5-7 minute detailed audio
- 30 day history
- Priority generation

---

# Week 1: Core Pipeline & Free Tier

## Day 1-2: Basic Pipeline Setup
*Get the simplest possible news → audio pipeline working*

### Goal
Generate a single audio file from market news that can be played in the app.

### Tasks
```python
1. Project Setup (2 hours)
   - Initialize FastAPI project
   - Set up Docker for Kokoro TTS
   - Create basic folder structure
   - Configure environment variables

2. News Fetching (3 hours)
   - Integrate Finlight API
   - Fetch general market news (SPY, QQQ, major indices)
   - Return top 10 articles
   - Simple JSON response

3. AI Summarization (3 hours)
   - Connect to Gemini API
   - Create basic prompt for market summary
   - Generate 2-minute script
   - Format for audio (no symbols, natural speech)

4. Audio Generation (2 hours)
   - Setup Kokoro TTS locally
   - Convert script to MP3
   - Save to local filesystem
   - Return file path
```

### Deliverable
```bash
# Test endpoint
curl -X POST http://localhost:8000/api/test/generate
# Returns: { "audio_file": "/tmp/market_brief.mp3" }
```

### Success Metrics
- Can generate audio file in <30 seconds
- Audio is clear and coherent
- 2-3 minute duration

---

## Day 3-4: Daily General Briefings
*Create the free tier experience*

### Goal
Generate one market briefing per day (morning) that all free users share.

### Database Schema (Minimal)
```sql
-- Just one table to start
CREATE TABLE general_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  audio_url TEXT,
  transcript TEXT,
  duration_seconds INT,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  is_latest BOOLEAN DEFAULT false
);
```

### Tasks
```python
1. Supabase Setup (2 hours)
   - Create project
   - Set up storage bucket for audio
   - Configure public access
   - Get credentials

2. Storage Integration (2 hours)
   - Upload MP3 to Supabase Storage
   - Generate public URLs
   - Set expiration policies

3. Scheduled Generation (3 hours)
   - Create cron job (once daily at 6 AM EST)
   - Generate morning market briefing
   - Upload to storage
   - Update database
   - Mark as "today's briefing"

4. API Endpoints (2 hours)
   GET /api/briefings/general/today
     → Returns today's briefing
   
   GET /api/briefings/general/history
     → Returns last 7 briefings
```

### Deliverable
```json
// GET /api/briefings/general/today
{
  "id": "uuid",
  "title": "Morning Market Update - January 1",
  "audio_url": "https://storage.url/audio.mp3",
  "duration": 180,
  "generated_at": "2024-01-01T06:00:00Z",
  "is_today": true,
  "date": "2024-01-01"
}
```

### Success Metrics
- Briefing generates automatically at 6 AM EST daily
- Free users get one briefing per day
- Audio URLs work from mobile app

---

## Day 5: Authentication & User Accounts
*Set up Supabase Auth for the app*

### Goal
Users can create accounts and sign in via the mobile app.

### Tasks
```python
1. Supabase Auth Setup (2 hours)
   - Enable email/password auth
   - Configure JWT settings
   - Set up auth policies

2. User Profile Table (1 hour)
   CREATE TABLE user_profiles (
     id UUID REFERENCES auth.users PRIMARY KEY,
     email TEXT,
     full_name TEXT,
     tier TEXT DEFAULT 'free',
     created_at TIMESTAMPTZ DEFAULT NOW()
   );

3. Auth Middleware (2 hours)
   - JWT validation
   - User context injection
   - Protected endpoints

4. Basic Endpoints (2 hours)
   POST /api/auth/register
   POST /api/auth/login
   GET /api/auth/profile
   POST /api/auth/logout
```

### Deliverable
- Users can sign up/login from React Native
- JWT tokens work for API calls
- User profile accessible

---

# Week 2: Paid Tiers & Personalization

## Day 6-7: Stripe Payment Integration
*Add subscription management*

### Goal
Users can upgrade to Premium ($9.99/month) tier.

### Database Additions
```sql
CREATE TABLE user_subscriptions (
  user_id UUID REFERENCES auth.users PRIMARY KEY,
  tier TEXT DEFAULT 'free',
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  status TEXT DEFAULT 'active',
  current_period_end TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tasks
```python
1. Stripe Setup (2 hours)
   - Create single product: Premium @ $9.99/mo
   - Set up webhook endpoint
   - Configure test mode

2. Checkout Flow (3 hours)
   POST /api/subscription/create-checkout
     → Returns Stripe checkout URL for $9.99 plan
   
   POST /api/subscription/cancel
     → Cancels subscription

3. Webhook Handler (3 hours)
   POST /api/webhooks/stripe
   - Handle checkout.completed
   - Handle subscription.updated
   - Handle subscription.deleted
   - Update user tier in database

4. Subscription Status (2 hours)
   GET /api/subscription/status
     → Current tier & daily usage (0/1 or 0/3)
```

### Deliverable
- Users can upgrade via Stripe Checkout
- Subscriptions sync to database
- Tier changes reflect immediately

---

## Day 8-9: Personalized Briefings (Simple)
*Let premium users select tickers for personalized news*

### Goal
Premium users can generate up to 3 briefings per day with selected tickers.

### Database Additions
```sql
CREATE TABLE personalized_briefings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users,
  audio_url TEXT,
  transcript TEXT,
  duration_seconds INT,
  tickers TEXT[], -- Simple array, no tracking
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE usage_tracking (
  user_id UUID,
  date DATE,
  briefings_count INT DEFAULT 0,
  PRIMARY KEY (user_id, date)
);
```

### Tasks
```python
1. Ticker Selection (3 hours)
   POST /api/briefings/personalized
   {
     "tickers": ["AAPL", "GOOGL", "TSLA"]
   }
   
   - Validate tier (must be premium)
   - Check daily limit (3 per day)
   - Queue generation

2. Personalized Pipeline (4 hours)
   - Fetch news for specific tickers
   - Create personalized summary
   - 5-7 minute detailed scripts
   - Better voice quality

3. History & Playback (2 hours)
   GET /api/briefings/personalized/history
   GET /api/briefings/personalized/{id}
```

### Deliverable
```json
// POST /api/briefings/personalized
{
  "briefing_id": "uuid",
  "status": "processing",
  "estimated_seconds": 20
}

// After processing
{
  "id": "uuid",
  "audio_url": "https://...",
  "duration": 300,
  "tickers": ["AAPL", "GOOGL"],
  "created_at": "2024-01-01T10:00:00Z"
}
```

---

## Day 10-11: Priority & Quality Improvements
*Make premium tier worth it*

### Goal
Clear quality difference between free and premium.

### Improvements by Tier

#### Free Tier
- 1 general briefing per day (morning)
- Basic voice quality
- 2-3 minute duration
- 7-day history limit
- Standard generation

#### Premium Tier ($9.99)
- 3 briefings per day
- Personalized ticker selection
- Better voice quality
- 5-7 minute detailed audio
- 30-day history
- Priority queue (faster generation)
- Download for offline listening

### Tasks
```python
1. Voice Quality (3 hours)
   - Basic voice for free tier
   - Premium voices for paid tier
   - Voice selection in profile

2. Priority Queue (3 hours)
   - Implement priority based on tier
   - Premium → Free order
   - Show queue position

3. Rate Limiting (3 hours)
   - Enforce daily limits (1 for free, 3 for premium)
   - Clear error messages
   - Upgrade prompts when limit reached

4. Download Feature (2 hours)
   - Generate signed URLs for premium users
   - Enable offline playback in app
```

---

## Day 12-13: Mobile App Integration
*Ensure smooth React Native experience*

### Goal
Complete integration with React Native app.

### Key Features
```javascript
// Free User Flow
1. Open app → See today's general briefing
2. Play audio immediately
3. See history (last 7 days)
4. Upgrade prompt when trying to generate more

// Premium User Flow  
1. Open app → See generate button
2. Select tickers (simple picker)
3. Generate personalized briefing
4. See generation progress
5. Play when ready
6. Access full history (30 days)
7. Download for offline
```

### API Optimizations
```python
1. Streaming Support (2 hours)
   - Byte-range requests for audio
   - Smooth playback on mobile

2. Offline URLs (2 hours)
   - 24-hour signed URLs for premium
   - Download tracking

3. Push Notifications (3 hours)
   - "Your briefing is ready"
   - Morning notification for free tier
   - Generation complete for premium

4. Error Handling (2 hours)
   - Network-aware responses
   - Retry mechanisms
   - Graceful degradation
```

---

## Day 14: Testing & Launch Prep
*Final polish and testing*

### Testing Checklist
- [ ] Free tier: Can play daily general briefing
- [ ] Auth: Sign up/login works
- [ ] Payments: Can upgrade to $9.99 premium
- [ ] Premium: Can generate 3 personalized briefings per day
- [ ] Audio: Plays smoothly on iOS/Android
- [ ] Downloads: Premium users can save offline
- [ ] Errors: All edge cases handled

### Launch Checklist
- [ ] Production API deployed
- [ ] Stripe in production mode
- [ ] Supabase configured
- [ ] Monitoring set up
- [ ] Error tracking enabled
- [ ] Analytics configured

---

# Post-MVP Roadmap

## Month 2 Enhancements
- **Portfolio Tracking**: Add position tracking for P&L
- **Smart Summaries**: Include user's gains/losses
- **Categories**: Tech, Healthcare, Energy sectors
- **Scheduled Briefs**: Daily morning briefings
- **Web App**: Simple web player

## Month 3 Growth Features
- **Social**: Share briefings
- **Alerts**: Breaking news notifications
- **Watchlists**: Save ticker groups
- **Export**: Download transcripts
- **API Access**: Pro tier developer API

## Month 4 Advanced
- **AI Chat**: Ask questions about briefings
- **Multi-language**: Spanish, Chinese
- **Earnings Mode**: Special earnings reports
- **Team Plans**: Business subscriptions
- **White Label**: Custom branding

---

# Technical Architecture

## Core Stack
```yaml
Backend:
  - FastAPI (Python 3.11)
  - Supabase (Auth + DB + Storage)
  - Stripe (Payments)
  
AI/ML:
  - Gemini 1.5 Flash (Free quota)
  - DeepSeek (Overflow)
  
TTS:
  - Kokoro (Self-hosted)
  - Cartesia (Pro tier)
  
News:
  - Finlight API
  
Mobile:
  - React Native
  - Expo (optional)
```

## Cost Projections

### Per User Costs
| Component | Free | Premium ($9.99) |
|-----------|------|-----------------|
| News API | $0.001 | $0.015 |
| AI Summary | $0.001 | $0.015 |
| TTS | $0 | $0.01 |
| Storage | $0.001 | $0.005 |
| **Total** | $0.003 | $0.045 |

### Revenue Projections (100 users)
- 70 Free users: $0
- 30 Premium users: $299.70/mo
- **Total Revenue**: $299.70/mo
- **Total Costs**: ~$30/mo
- **Profit**: ~$270/mo

### Unit Economics
- Premium user generates: $9.99/mo
- Premium user costs: ~$1.35/mo (3 briefings/day × 30 days × $0.015)
- **Margin per premium user**: ~$8.64 (86%)

---

# Implementation Order

## Week 1 Priority
1. ✅ Basic pipeline (news → summary → audio)
2. ✅ Daily general briefing at 6 AM EST
3. ✅ Supabase storage
4. ✅ Public API for free tier
5. ✅ User authentication

## Week 2 Priority
1. ✅ Stripe payment ($9.99/mo)
2. ✅ Premium tier management
3. ✅ Personalized briefings (ticker selection)
4. ✅ Daily limits (1 free, 3 premium)
5. ✅ Mobile optimization

## Success Criteria
- Free users get 1 general briefing daily
- Premium users can create 3 personalized briefings
- Payments process successfully at $9.99/mo
- Audio plays smoothly on mobile
- System handles 100+ concurrent users

## Key Differentiators
- **No ads** - Clean experience for all users
- **Simple pricing** - Just free or $9.99
- **Quality content** - AI-powered summaries
- **Mobile-first** - Built for on-the-go listening
- **Personalization** - Choose your stocks (premium)

This MVP focuses on proving the core value proposition: **AI-generated audio briefings that save time and deliver personalized financial news**.