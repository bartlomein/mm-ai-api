# MarketMotion - Project Documentation

## Project Overview
MarketMotion is an automated financial news briefing system that generates premium audio market updates using AI. It provides comprehensive morning, midday, and evening briefings plus free-tier options, fetching multi-source financial news and creating intelligent summaries with advanced TTS services.

## Key Features
- **Multi-Source News Aggregation**: Fetches financial news from Finlight API and NewsAPI.ai
- **Real-Time Market Data**: Integrates Financial Modeling Prep (FMP) for live market quotes, crypto, and indices
- **AI-Powered Summarization**: Uses Google Gemini to create professional market briefings
- **Text-to-Speech**: Converts briefings to audio using Fish Audio (primary) or OpenAI TTS (fallback)
- **Multiple Briefing Types**: Morning (12-15 min), Midday (live trading), Evening (10-15 min), and Free tier
- **EST Timezone Support**: All briefings use consistent Eastern Time for US market alignment
- **Smart Deduplication**: Avoids repeating similar news stories
- **Professional Formatting**: Properly formats stock tickers, numbers, and financial terms for TTS
- **Weekend Detection**: Automatically adjusts messaging based on market hours

## Architecture

### Services Structure
```
src/
├── services/
│   ├── audio_service.py      # TTS generation (Fish Audio, OpenAI)
│   ├── news_service.py        # Finlight API integration for news articles
│   ├── newsapiai_service.py   # NewsAPI.ai integration for comprehensive news coverage
│   ├── fmp_service.py         # Financial Modeling Prep API for market data
│   ├── summary_service.py     # Gemini AI summarization and script generation
│   ├── pipeline_service.py    # Orchestrates the full pipeline
│   └── supabase_service.py    # Database integration (if configured)
├── utils/
│   └── timezone_utils.py     # EST timezone utilities for consistent market time
└── main.py                    # FastAPI application
```

### Service Descriptions

#### **audio_service.py**
- Handles text-to-speech conversion
- Primary: Fish Audio API (unlimited length, high quality)
- Fallback: OpenAI TTS (4096 character limit)
- Automatically selects best available service
- Formats text for optimal TTS pronunciation
- Estimates audio duration based on word count

#### **news_service.py**
- Integrates with Finlight API for financial news
- Fetches general market news or ticker-specific articles
- Returns structured article data with title, content, source, and date
- Handles API errors gracefully with empty list fallbacks

#### **newsapiai_service.py**
- Integrates with NewsAPI.ai (Event Registry) for comprehensive news coverage
- **Key Methods:**
  - `search_articles()` - Advanced search with date filtering and English language
  - `search_articles_by_time()` - Precise datetime filtering for specific time ranges
  - `fetch_financial_news()` - Specialized financial and business news search
  - `fetch_for_date_range()` - Date-specific queries (last N days)
  - `get_recent_headlines()` - Recent news from last N hours
  - `get_trending_topics()` - Trending concepts and topics analysis
- **Features:**
  - Advanced date/time filtering (dateStart, dateEnd, precise datetime)
  - Keyword search with boolean operators (AND, OR, NOT)
  - Article sorting by date, relevance, or social score
  - Always returns English articles with normalized data structure
  - Sentiment analysis (-1 to 1 scale) for each article
  - Concept extraction (entities, topics, categories)
  - Source diversity tracking
  - Deduplication of similar articles
- **Data Returned:**
  - Title, content, source, URL
  - Published date/time with timezone
  - Sentiment score
  - Related concepts and entities
  - Categories and topics
- Enables multi-source news aggregation with Finlight

#### **fmp_service.py**
- Real-time market data from Financial Modeling Prep API
- **Key Methods:**
  - `get_market_indices()` - SPY, QQQ, DIA, IWM, VTI quotes
  - `get_premarket_data()` - Pre-market trading activity
  - `get_crypto_overview()` - Bitcoin, Ethereum, major crypto performance
  - `get_market_movers()` - Top gainers, losers, most active stocks
  - `get_sector_performance()` - Sector rotation analysis
  - `get_intraday_performance()` - Historical price action (5min/1min intervals)
  - `get_economic_calendar()` - Upcoming economic events
  - `generate_market_briefing()` - Combined market narrative
- Normalizes data for LLM consumption with summaries
- Handles market sentiment analysis

#### **summary_service.py**
- Uses Google Gemini 2.0 Flash for AI summarization
- Creates professional market briefings from news and data
- **Key Methods:**
  - `create_general_script()` - Free tier general market summary
  - `create_personalized_script()` - Premium tier with specific tickers
  - `create_market_data_script()` - Combines FMP data with news context
- Enforces 750-850 word count for 5-minute audio
- Applies TTS formatting rules automatically
- Includes retry logic for proper word count

#### **pipeline_service.py**
- Orchestrates multi-service workflows
- **Key Methods:**
  - `generate_general_briefing()` - News-based briefing for free tier
  - `generate_personalized_briefing()` - Ticker-specific for premium tier
  - `generate_market_data_briefing()` - FMP data + news combination
  - `generate_intraday_update()` - Symbol-specific performance updates
  - `generate_multi_source_briefing()` - Combines Finlight + NewsAPI.ai sources
  - `generate_date_filtered_briefing()` - Date-specific briefings using NewsAPI.ai
  - `generate_trending_briefing()` - Briefings based on trending topics analysis
- Handles file storage and audio generation
- Returns structured responses with metadata
- Supports multi-source news aggregation and date-filtered content

#### **supabase_service.py** (if configured)
- Database operations for user data and briefings
- Stores generated audio files
- Manages user preferences and subscription tiers

#### **timezone_utils.py** (NEW)
- **EST Timezone Support**: Ensures all briefings use Eastern Time consistently
- **Key Functions**:
  - `get_est_time()` - Current time in EST/EDT
  - `is_weekend_est()` - Weekend detection based on US market hours
  - `get_est_weekday_name()` - Day name in Eastern Time
  - `format_est_timestamp()` - EST timestamps for file naming
  - `format_est_display()` - EST display formatting
- **Critical for US Markets**: Proper market hours detection regardless of server location

### Scripts

#### Premium Briefing Generators (MAIN)
- `generate_premium_morning_briefing.py` - **Morning briefing** (12-15 min): Economic calendar, premarket data, comprehensive news
- `generate_premium_midday_briefing.py` - **Midday briefing** (live trading): Real-time market data, trading activity, sector performance  
- `generate_premium_evening_briefing.py` - **Evening briefing** (10-15 min): Full day recap, comprehensive market analysis
- `generate_free_briefing.py` - **Free tier briefing**: Shorter briefings for non-premium users

#### Market Data & Analysis Scripts
- `generate_spy_premarket.py` - SPY premarket activity briefing
- `generate_weekly_economic_calendar.py` - Generate economic calendar briefings

#### NewsAPI.ai Scripts
- `search_news_topic.py` - Search for news on any topic with flexible time filtering
- `search_recent_hours.py` - Get news from the last N hours
- `generate_newsapiai_demo.py` - Demonstrates NewsAPI.ai capabilities and multi-source briefings
- `generate_weekly_economic_calendar.py` - Generate economic calendar briefings
- `test_newsapiai_service.py` - Tests NewsAPI.ai service methods and pipeline integration

#### Testing Scripts
- `test_pipeline.py` - Tests the full pipeline
- `test_fmp_service.py` - Tests all FMP service methods
- `list_fish_models.py` - Lists available Fish Audio voice models
- `test_fish_voices.py` - Tests different TTS voices

## Configuration

### Environment Variables (.env)
```bash
# News & Market Data
FINLIGHT_API_KEY=xxx           # Required: Financial news API
NEWSAPI_AI_KEY=xxx             # Required: NewsAPI.ai for comprehensive news coverage
FMP_API_KEY=xxx                # Required: Financial Modeling Prep for market data

# AI/LLM
GEMINI_API_KEY=xxx             # Required: Google Gemini for summarization
DEEPSEEK_API_KEY=xxx           # Optional: Fallback LLM

# Text-to-Speech (in priority order)
FISH_API_KEY=xxx               # Primary: Best quality, no char limit
FISH_MODEL_ID=xxx              # Optional: Specific voice model ID
OPENAI_API_KEY=xxx             # Fallback: 4096 char limit

# Database (Future)
SUPABASE_URL=xxx
SUPABASE_ANON_KEY=xxx
```

### Recommended Fish Audio Voice Models
- **Energetic Male**: `802e3bc2b27e49c2995d23ef70e6ac89` (Professional news voice)
- **Elon Musk**: `03397b4c4be74759b72533b663fbd001` (Tech-focused)
- **Donald Trump**: `5196af35f6ff4a0dbf541793fc9f2157` (Business tone)

## Usage

### Generate Premium Briefings

#### Morning Briefing (12-15 minutes)
```bash
# Generate premium morning briefing with economic calendar
./generate_premium_morning_briefing.py

# Features:
# - Economic calendar (today + upcoming)
# - Premarket data and futures
# - Comprehensive news from multiple sources
# - Crypto overnight moves
# - International markets (Asian close, European open)
```

#### Midday Briefing (Live Trading Focus)
```bash
# Generate real-time market update during trading hours
./generate_premium_midday_briefing.py

# Features:
# - Live market data and indices
# - Market movers and sector performance
# - Real-time trading activity
# - Breaking news and developments
```

#### Evening Briefing (10-15 minutes)
```bash
# Generate comprehensive end-of-day market recap
./generate_premium_evening_briefing.py

# Features:
# - Full day trading recap
# - Daily market performance analysis
# - Comprehensive news from last 18 hours
# - Sector analysis and market highlights
```

#### Free Tier Briefing
```bash
# Generate shorter briefing for free tier users
./generate_free_briefing.py

# Features:
# - Shorter format
# - Essential market updates
# - Basic news coverage
```

#### Specific Market Queries
```bash
# SPY premarket analysis
./generate_spy_premarket.py

# Weekly economic calendar
./generate_weekly_economic_calendar.py
```

#### NewsAPI.ai Topic Search
```bash
# Search any topic (returns title and full content)
./search_news_topic.py "artificial intelligence"
./search_news_topic.py "Tesla" 3  # Last 3 days
./search_news_topic.py "Bitcoin" 7 25  # Last 7 days, max 25 articles

# Time-based search (precise datetime filtering)
./search_news_topic.py "Apple earnings" --time "2025-08-16 09:00" "2025-08-16 17:00"
./search_news_topic.py "Fed meeting" --time "2025-08-15 14:00" "2025-08-16 10:00" 20

# Output format:
# - Clear article boundaries (ARTICLE N / END OF ARTICLE N)
# - Full title and complete content (no truncation)
# - Supports any topic: stocks, crypto, economics, technology, etc.
```

#### Recent News Search
```bash
# Get news from the last N hours
./search_recent_hours.py 2  # Last 2 hours
./search_recent_hours.py 24  # Last 24 hours
./search_recent_hours.py 1 20  # Last hour, max 20 articles
```

### Start the API Server
```bash
# Development
uvicorn src.main:app --reload --port 8000

# Or use the run script
./run.sh
```

### API Endpoints
- `GET /api/health` - Check service status and TTS configuration
- `POST /api/test/generate` - Generate general market briefing
- `POST /api/test/generate-personalized` - Generate personalized briefing for specific tickers

## Text-to-Speech Formatting Rules

### Critical TTS Formatting
The system automatically formats text for proper TTS pronunciation:

1. **Stock Tickers**: `AAPL` → `"ticker A-A-P-L --"` (spelled out with pause)
2. **Percentages**: `25%` → `"twenty-five percent"`
3. **Currency**: `$1.5B` → `"one point five billion dollars"`
4. **Large Numbers**: 
   - `1,000` → `"one thousand"`
   - `2,500,000` → `"two point five million"`
   - `3,700,000,000` → `"three point seven billion"`
5. **Abbreviations**:
   - `CEO` → `"C-E-O"`
   - `IPO` → `"I-P-O"`
   - `GDP` → `"G-D-P"`
   - `S&P` → `"S and P"`

## Briefing Structure (5 Minutes)

The system generates briefings with this structure:
1. **Opening** (20 words): Greeting and date
2. **Market Overview** (150 words): Indices, volume, sentiment
3. **Stock News** (150 words): Individual company movements
4. **Economic Data** (120 words): Fed, inflation, employment
5. **Tech Sector** (100 words): Technology developments
6. **Energy/Commodities** (100 words): Oil, gold, resources
7. **International** (80 words): Global markets
8. **Closing** (30 words): Wrap-up and outlook

**Total**: 750-850 words = 5 minutes at 150 wpm

## Common Issues and Solutions

### Issue: Briefings Too Short
**Solution**: Use `generate_briefing_v2.py` which generates sections separately and enforces word counts.

### Issue: Duplicate News Stories
**Solution**: The system now includes deduplication logic that:
- Tracks mentioned companies
- Filters similar articles
- Ensures each ticker appears only once

### Issue: TTS Pronunciation Problems
**Solution**: All prompts include strict formatting rules for numbers, tickers, and abbreviations.

### Issue: Fish Audio Takes Too Long
**Solution**: Fish Audio may take 3-4 minutes for 800-word texts. This is normal. The text file is created immediately if you need it sooner.

## Development Commands

### Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests
```bash
# Test Finlight API
python test_finlight.py

# Test FMP Service (market data)
python test_fmp_service.py

# Test full pipeline
python test_pipeline.py

# Check briefing length
python test_briefing_length.py

# Test Fish Audio voices
python test_fish_voices.py
```

### Run the Server
```bash
# Simple start
./run.sh

# Or manually
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

## Code Quality

### Linting and Type Checking
```bash
# If configured in package.json or directly:
npm run lint        # or: ruff check .
npm run typecheck   # or: mypy .
```

### Before Committing
Always run linting and type checking to ensure code quality. The project may have pre-commit hooks configured.

## Future Enhancements

### Planned Features
- User authentication and personalization
- Scheduled briefing generation (cron jobs)
- Multiple briefing types (crypto, commodities, sectors)
- Supabase integration for audio storage
- Mobile app integration
- Subscription tiers with Stripe

### Database Schema (Future)
- Users table (auth, preferences)
- Briefings table (generated content)
- Audio files (Supabase storage)
- User preferences (tickers, schedule)

## Troubleshooting

### Debug TTS Configuration
```bash
# Check which TTS service is configured
curl http://localhost:8000/api/health
```

### View Logs
The system provides detailed logging:
- `[AudioService]` - TTS service selection and generation
- `[SummaryService]` - AI summarization process
- `[NewsService]` - API data fetching
- `[FMPService]` - Market data retrieval and normalization
- `[PipelineService]` - Orchestration and workflow execution
- `[Main]` - Application startup and configuration

### Common Error Messages
- `"FINLIGHT_API_KEY not found"` - Set the API key in .env
- `"FMP_API_KEY not found"` - Set the Financial Modeling Prep API key in .env
- `"Text too long for OpenAI TTS"` - Text exceeds 4096 chars, will use Fish Audio
- `"No TTS service configured"` - Set at least one TTS API key
- `"Generated only X words"` - Gemini didn't follow word count, will retry
- `"No premarket data available"` - Markets are likely open, premarket data not available

## Best Practices

1. **Use the appropriate premium briefing generator**:
   - Morning: `./generate_premium_morning_briefing.py` (pre-market prep)
   - Midday: `./generate_premium_midday_briefing.py` (live trading)
   - Evening: `./generate_premium_evening_briefing.py` (day recap)
   - Free: `./generate_free_briefing.py` (basic tier)

2. **Set `FISH_MODEL_ID`** in .env for consistent voice across all briefings

3. **All scripts automatically use EST timezone** - no manual timezone handling needed

4. **NewsAPI.ai limits**: Stay within 100 articles per request (automatically handled)

5. **Monitor word counts** in output to ensure proper briefing length

6. **Weekend detection**: Scripts automatically detect weekends and adjust messaging

## Support and Resources

- **Fish Audio Docs**: https://docs.fish.audio
- **Finlight API**: https://finlight.me
- **NewsAPI.ai (Event Registry)**: https://eventregistry.org/documentation
- **Financial Modeling Prep API**: https://site.financialmodelingprep.com/developer/docs
- **Google Gemini**: https://ai.google.dev
- **OpenAI TTS**: https://platform.openai.com/docs/guides/text-to-speech

## EST Timezone Support

All briefing generators now use **consistent Eastern Time (EST/EDT)** for:
- **Weekend Detection**: Proper market hours recognition
- **Date Calculations**: News search ranges and time filtering
- **Timestamps**: File naming and briefing headers
- **Market Context**: Weekday vs weekend messaging

### Timezone Utilities (`src/utils/timezone_utils.py`)
```python
get_est_time()          # Current EST time
is_weekend_est()        # Weekend detection in EST
get_est_weekday_name()  # Day name in EST
format_est_timestamp()  # EST timestamps for files
format_est_display()    # EST display formatting
```

This ensures all briefings are **aligned with US financial markets** regardless of server location.

## Version History

### Current Version: 3.0 (August 2025)
- **🚀 MAJOR REFACTORING**: Cleaned up codebase from 12 → 4 briefing generators
- **🕐 EST Timezone Support**: All briefings use consistent Eastern Time
- **📱 Premium Briefing Types**: Morning (12-15min), Midday (live), Evening (10-15min), Free tier
- **🔧 Fixed NewsAPI.ai Integration**: Resolved 100-article API limit issue
- **🧹 Clean Repository**: Added comprehensive .gitignore for generated files
- **✅ Weekend Detection**: Smart messaging that avoids "trading day" on weekends
- Enhanced NewsAPI.ai integration with comprehensive documentation
- Topic search script with full content retrieval (no truncation)
- Precise datetime filtering for time-based searches
- Financial Modeling Prep (FMP) integration for real-time market data
- Multi-source news aggregation (Finlight + NewsAPI.ai)
- Professional TTS formatting and section-by-section generation

### Previous Issues (Now Fixed)
- ✅ Briefings were too short (45 seconds instead of 5 minutes)
- ✅ Duplicate news stories appeared multiple times
- ✅ Stock tickers weren't pronounced correctly
- ✅ Numbers and percentages formatted incorrectly
- ✅ Voice changed between generations
- ✅ Evening briefing getting 0 articles (NewsAPI.ai 100-article limit exceeded)
- ✅ Inconsistent timezone usage across briefing generators
- ✅ "Wrapping up trading day" said on weekends
- ✅ Repository cluttered with 12 different briefing scripts

---

*Last Updated: August 2025*
*Project: MarketMotion - Automated Financial News & Market Data Briefings*