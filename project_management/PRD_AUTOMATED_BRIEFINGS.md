# Product Requirements Document: Automated Market Briefings System

## Executive Summary

MarketMotion will deliver automated, AI-powered audio market briefings every 3 hours for general market updates and specialized sector analysis. The system leverages existing NewsAPI.ai, FMP, and Finlight services to create comprehensive, timely market intelligence delivered as 5-minute audio briefings.

## Project Overview

### Vision
Become the primary source for automated, professional-quality market audio briefings, serving both retail investors and financial professionals with timely, actionable market intelligence.

### Goals
1. **Automated General Briefings**: Deliver market updates every 3 hours during trading hours
2. **Sector-Specific Intelligence**: Provide deep-dive sector analysis for targeted investment strategies
3. **Zero Manual Intervention**: Fully automated pipeline from data collection to audio delivery
4. **Scalable Architecture**: Support thousands of concurrent users with personalized briefings

### Success Metrics
- Briefing generation success rate: >99.5%
- Audio generation time: <5 minutes per briefing
- User engagement: >70% listen completion rate
- System uptime: 99.9%
- Cost per briefing: <$0.05

## Product Requirements

### 1. General Market Briefings (10 Minutes Each)

#### Daily Schedule (3 Comprehensive Briefings)
- **5:00 AM EST - Morning Market Brief**: Pre-market comprehensive analysis
- **1:00 PM EST - Midday Market Update**: Mid-trading day comprehensive review
- **7:00 PM EST - Evening Market Wrap**: Full day comprehensive analysis

#### Content Structure for 10-Minute Comprehensive Briefings

**5:00 AM - Morning Market Brief (10 minutes)**
1. **Global Market Overview** (2 minutes)
   - Asian markets closing recap
   - European markets opening
   - U.S. futures analysis
   - Currency and commodity movements
   - Global news impact

2. **Pre-Market Analysis** (2 minutes)
   - Pre-market movers and volume
   - Key support/resistance levels
   - Earnings releases before open
   - Analyst upgrades/downgrades
   - Economic data preview

3. **Sector Preparation** (2 minutes)
   - All 11 S&P sectors futures
   - Sector rotation expectations
   - Industry-specific news
   - ETF flows analysis

4. **Trading Day Strategy** (2 minutes)
   - Opening bell expectations
   - Key stocks to watch
   - Options flow insights
   - Technical setups

5. **News & Catalysts** (2 minutes)
   - Breaking overnight news
   - Corporate developments
   - Economic calendar
   - Geopolitical updates

**1:00 PM - Midday Market Update (10 minutes)**
1. **Morning Session Recap** (2 minutes)
   - Opening moves analysis
   - Morning highs and lows
   - Volume and breadth
   - Trend establishment

2. **Current Market State** (2 minutes)
   - Real-time index levels
   - Intraday movers
   - Sector performance
   - Market internals

3. **News Impact Assessment** (2 minutes)
   - Morning news reactions
   - Economic data results
   - Corporate announcements
   - Fed speaker highlights

4. **Technical Analysis** (2 minutes)
   - Key levels holding/breaking
   - Chart patterns developing
   - Momentum indicators
   - Volume analysis

5. **Afternoon Outlook** (2 minutes)
   - Afternoon catalysts
   - Power hour expectations
   - After-hours earnings preview
   - Risk factors

**7:00 PM - Evening Market Wrap (10 minutes)**
1. **Complete Market Recap** (2 minutes)
   - Open, high, low, close for all indices
   - Volume analysis
   - Market breadth
   - Volatility assessment

2. **Winners & Losers Analysis** (2 minutes)
   - Top gainers with catalysts
   - Top losers with reasons
   - Unusual volume stocks
   - After-hours movers

3. **Comprehensive News Digest** (2 minutes)
   - All major market news
   - Economic data impact
   - Corporate earnings
   - M&A activity

4. **All Sectors Performance** (2 minutes)
   - 11 S&P sectors analysis
   - Sector rotation patterns
   - Industry group movements
   - Thematic trends

5. **Tomorrow's Preparation** (2 minutes)
   - Pre-market earnings
   - Economic calendar
   - Global market setup
   - Key levels to watch


#### Data Sources
- **Real-time Market Data**: FMP API
  - Quotes, movers, volume
  - Sector performance
  - Economic calendar
  
- **News Aggregation**: 
  - NewsAPI.ai: Breaking news, trending topics
  - Finlight: Financial-specific news
  
- **Technical Analysis**: FMP intraday data

### 2. Sector-Specific Briefings

#### Supported Sectors (Phase 1)
1. **Technology** (XLK)
2. **Healthcare** (XLV)
3. **Financials** (XLF)
4. **Energy** (XLE)
5. **Consumer Discretionary** (XLY)

#### Supported Sectors (Phase 2)
6. **Industrials** (XLI)
7. **Materials** (XLB)
8. **Real Estate** (XLRE)
9. **Utilities** (XLU)
10. **Consumer Staples** (XLP)
11. **Communications** (XLC)

#### Content Structure (5 minutes each)
1. **Sector Overview** (45 seconds)
   - Sector ETF performance
   - Relative strength vs SPY
   - Volume and momentum

2. **Top Performers** (1 minute)
   - Leading stocks in sector
   - Key catalysts and news
   - Technical breakouts

3. **Sector News Deep Dive** (2 minutes)
   - Industry-specific developments
   - Regulatory updates
   - Analyst actions
   - M&A activity

4. **Subsector Analysis** (1 minute)
   - Performance breakdown
   - Emerging trends
   - Rotation patterns

5. **Outlook & Opportunities** (15 seconds)
   - Trade ideas
   - Risk factors
   - Upcoming catalysts

#### Update Frequency
- **Daily**: 7:00 AM EST (pre-market prep)
- **Weekly Deep Dive**: Sunday 6:00 PM EST

## Technical Architecture

### Core Components

#### 1. Scheduler Service
- **Technology**: Python AsyncIO + APScheduler
- **Responsibilities**:
  - Trigger briefing generation
  - Handle timezone conversions
  - Manage retry logic
  - Monitor job completion

#### 2. Data Aggregation Layer
- **News Service Orchestrator**:
  ```python
  - Parallel fetch from NewsAPI.ai, Finlight
  - Deduplication algorithm
  - Relevance scoring
  - Time-based filtering
  ```

- **Market Data Service**:
  ```python
  - Real-time quotes from FMP
  - Calculate performance metrics
  - Identify movers and shakers
  - Sector rotation analysis
  ```

#### 3. Content Generation Pipeline
- **AI Summarization**:
  - Gemini 2.0 Flash for speed
  - Sector-specific prompts
  - Consistent formatting rules
  - Word count enforcement (750-850)

#### 4. Audio Generation
- **Primary**: Fish Audio API
- **Fallback**: OpenAI TTS
- **Voice Consistency**: Dedicated voice IDs per briefing type

#### 5. Distribution System
- **Storage**: Supabase
- **CDN**: CloudFlare for global distribution
- **API**: FastAPI endpoints for client access

### Database Schema

```sql
-- Briefings table
CREATE TABLE briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL, -- 'morning', 'midday', 'evening', 'full_day', 'tech_sector', etc.
    scheduled_time TIMESTAMP NOT NULL,
    generation_started_at TIMESTAMP,
    generation_completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- 'pending', 'generating', 'completed', 'failed'
    content_text TEXT,
    content_hash VARCHAR(64), -- For deduplication
    audio_url TEXT,
    audio_duration_seconds INTEGER,
    metadata JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sector configurations
CREATE TABLE sector_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sector_code VARCHAR(10) NOT NULL UNIQUE, -- 'XLK', 'XLV', etc.
    sector_name VARCHAR(100) NOT NULL,
    etf_symbol VARCHAR(10),
    top_holdings JSONB, -- Array of top stock symbols
    keywords TEXT[], -- For news filtering
    schedule_cron VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    custom_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User subscriptions
CREATE TABLE user_briefing_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    briefing_type VARCHAR(50) NOT NULL,
    sector_code VARCHAR(10),
    delivery_method VARCHAR(20), -- 'push', 'email', 'in_app'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics
CREATE TABLE briefing_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_id UUID REFERENCES briefings(id),
    user_id UUID REFERENCES users(id),
    started_listening_at TIMESTAMP,
    stopped_listening_at TIMESTAMP,
    completion_percentage DECIMAL(5,2),
    user_rating INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation Phases

### Phase 1: Core Automation (Week 1-2)
- General market briefings every 3 hours
- Basic scheduler implementation
- Single voice for all briefings
- File-based storage

### Phase 2: Sector Briefings (Week 3-4)
- Top 5 sectors (Tech, Healthcare, Financials, Energy, Consumer)
- Sector-specific news filtering
- Custom prompts per sector
- Database integration

### Phase 3: Scale & Optimize (Week 5-6)
- All 11 sectors
- CDN integration
- Performance optimization
- Monitoring and alerting

### Phase 4: Personalization (Week 7-8)
- User subscriptions
- Custom briefing schedules
- Push notifications
- Analytics dashboard

## API Endpoints

### Briefing Generation
```
POST /api/briefings/generate
{
    "type": "general" | "sector",
    "sector_code": "XLK", // Optional for sector
    "force": boolean // Override schedule
}

GET /api/briefings/latest
?type=general&sector_code=XLK

GET /api/briefings/schedule
Returns upcoming briefing schedule

GET /api/briefings/{id}
Get specific briefing details

GET /api/briefings/{id}/audio
Stream audio file
```

### Subscription Management
```
POST /api/subscriptions
{
    "briefing_types": ["general", "tech_sector"],
    "delivery_method": "push"
}

GET /api/subscriptions/my
List user's subscriptions

DELETE /api/subscriptions/{id}
Unsubscribe from briefing
```

### Analytics
```
POST /api/analytics/listening
{
    "briefing_id": "uuid",
    "event": "start" | "stop" | "complete",
    "timestamp": "2025-01-15T10:00:00Z",
    "position_seconds": 145
}

GET /api/analytics/briefings/{id}
Get briefing performance metrics
```

## Error Handling & Reliability

### Retry Strategy
1. **Data Fetch Failures**:
   - Retry 3 times with exponential backoff
   - Fall back to cached data if available
   - Generate with partial data if critical sources fail

2. **AI Generation Failures**:
   - Retry with different prompt
   - Fall back to template-based generation
   - Use previous successful briefing as template

3. **Audio Generation Failures**:
   - Try Fish Audio first
   - Fall back to OpenAI TTS
   - Fall back to local TTS if both fail

### Monitoring & Alerts
- **Critical Alerts**:
  - Briefing generation failure rate >5%
  - Audio generation time >10 minutes
  - Data source unavailable >5 minutes
  
- **Warning Alerts**:
  - Retry rate >10%
  - Generation time >7 minutes
  - Low completion rates <50%

## Cost Analysis

### Per Briefing Costs (10-minute format)
- **NewsAPI.ai**: $0.02 (200 articles for comprehensive coverage)
- **FMP API**: $0.01 (extensive market data)
- **Finlight**: $0.002 (financial news)
- **Gemini AI**: $0.005 (1500-1700 words)
- **Fish Audio**: $0.04 (10-minute audio)
- **Storage/CDN**: $0.002
- **Total**: ~$0.08 per 10-minute briefing

### Monthly Projections (1000 users)
- General briefings: 3/day × 30 days = 90 × $0.08 = $7.20/user (10-min comprehensive)
- Sector briefings: 2/day × 30 days = 60 × $0.04 = $2.40/user (5-min each)
- Total: ~$9.60/user/month in costs
- Suggested pricing: $29.99/month (68% margin) or $34.99/month (72% margin)

## Security & Compliance

### Data Security
- API keys in environment variables
- Encrypted storage for sensitive data
- Rate limiting on all endpoints
- Input sanitization for prompts

### Compliance
- No personal financial advice disclaimer
- Market data attribution
- News source citations
- Audio content moderation

## Testing Strategy

### Unit Tests
- Data fetching services
- Content generation logic
- Audio generation pipeline
- Scheduling logic

### Integration Tests
- End-to-end briefing generation
- Multi-service orchestration
- Error handling scenarios
- Database operations

### Load Testing
- Concurrent briefing generation
- API endpoint stress testing
- Audio streaming performance
- Database query optimization

## Success Criteria

### Launch Metrics (Month 1)
- [ ] 100% schedule adherence
- [ ] <5% generation failure rate
- [ ] <5 minute generation time
- [ ] >80% audio quality score

### Growth Metrics (Month 3)
- [ ] 1,000+ active users
- [ ] >70% completion rate
- [ ] <$0.05 cost per briefing
- [ ] >4.5/5 user rating

## Risks & Mitigation

### Technical Risks
1. **API Rate Limits**
   - Mitigation: Implement caching, use multiple API keys
   
2. **AI Hallucination**
   - Mitigation: Fact-checking layer, source attribution

3. **Audio Generation Delays**
   - Mitigation: Pre-generate during low-traffic periods

### Business Risks
1. **Low User Adoption**
   - Mitigation: Free tier, referral program
   
2. **High Operational Costs**
   - Mitigation: Optimize API usage, negotiate bulk pricing

3. **Competition**
   - Mitigation: Unique sector insights, superior audio quality

## Appendix

### A. Sector Keywords Mapping
```python
SECTOR_KEYWORDS = {
    "XLK": ["technology", "software", "semiconductor", "AI", "cloud"],
    "XLV": ["healthcare", "pharma", "biotech", "medical", "FDA"],
    "XLF": ["banking", "financial", "insurance", "fintech", "rates"],
    "XLE": ["energy", "oil", "gas", "renewable", "crude"],
    "XLY": ["consumer", "retail", "e-commerce", "discretionary"]
}
```

### B. Voice Configuration
```python
VOICE_CONFIG = {
    "general": "802e3bc2b27e49c2995d23ef70e6ac89",  # Professional news
    "tech_sector": "03397b4c4be74759b72533b663fbd001",  # Tech-focused
    "financial_sector": "5196af35f6ff4a0dbf541793fc9f2157"  # Business tone
}
```

### C. Schedule Configuration
```python
BRIEFING_SCHEDULE = {
    "general": ["06:00", "09:30", "12:30", "15:30", "18:30", "21:30"],
    "sectors": {
        "daily": "07:00",
        "weekly": "Sunday 18:00"
    }
}
```

---

*Document Version: 1.0*
*Last Updated: August 2025*
*Author: MarketMotion Product Team*