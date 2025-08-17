# MarketMotion API - Backend

AI-powered financial news audio briefings for mobile.

## Quick Start

### One-Command Start 🚀

```bash
# Start everything (Kokoro TTS + API server)
./run.sh

# Stop everything
./stop.sh
```

That's it! The `run.sh` script will:
- ✅ Start Kokoro TTS container
- ✅ Set up Python environment
- ✅ Install dependencies
- ✅ Start the API server
- ✅ Handle shutdown gracefully

### First Time Setup

1. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. **Required API Keys:**
- `FINLIGHT_API_KEY` - For financial news data (get from finlight.me)
- `NEWSAPI_AI_KEY` - For comprehensive news coverage (get from eventregistry.org)
- `FMP_API_KEY` - For real-time market data (get from financialmodelingprep.com)
- `GEMINI_API_KEY` - For AI summaries (get from Google AI Studio)
- `FISH_API_KEY` - For high-quality TTS (optional, get from fish.audio)
- `OPENAI_API_KEY` - For fallback TTS (optional)

3. **Make sure Docker is running**, then:
```bash
./run.sh
```

## Test the Pipeline

### Generate General Market Briefing (Free Tier)
```bash
curl -X POST http://localhost:8000/api/test/generate
```

### Generate Personalized Briefing (Premium Tier)
```bash
curl -X POST http://localhost:8000/api/test/generate-personalized \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "GOOGL", "TSLA"]}'
```

### Play Generated Audio
Open the audio_url from the response in your browser or:
```bash
# Get the file_id from the response
curl http://localhost:8000/api/test/audio/{file_id} -o briefing.mp3
```

## News Search Scripts

### Search Any Topic
```bash
# Basic search (last 24 hours)
./search_news_topic.py "artificial intelligence"

# Search last N days
./search_news_topic.py "Tesla" 3  # Last 3 days
./search_news_topic.py "Bitcoin" 7 25  # Last 7 days, max 25 articles

# Precise time search
./search_news_topic.py "Apple earnings" --time "2025-08-16 09:00" "2025-08-16 17:00"
./search_news_topic.py "Fed meeting" --time "2025-08-15 14:00" "2025-08-16 10:00" 20
```

### Recent Hours Search
```bash
# Get news from the last N hours
./search_recent_hours.py 2  # Last 2 hours
./search_recent_hours.py 24  # Last 24 hours
```

### Generate Briefings
```bash
# Market data briefing with real-time data
./generate_market_data_briefing.py

# Crypto market analysis
./generate_crypto_briefing.py

# SPY premarket analysis
./generate_spy_premarket.py
```

## API Endpoints

### Core Pipeline (Testing)
- `POST /api/test/generate` - Generate general briefing
- `POST /api/test/generate-personalized` - Generate personalized briefing
- `GET /api/test/audio/{file_id}` - Get audio file

### Health Check
- `GET /` - API info
- `GET /api/health` - Health status

## Project Structure
```
src/
├── main.py                    # FastAPI app
├── services/
│   ├── news_service.py        # Finlight API integration
│   ├── newsapiai_service.py   # NewsAPI.ai integration
│   ├── fmp_service.py         # Financial Modeling Prep API
│   ├── summary_service.py     # Gemini AI summaries
│   ├── audio_service.py       # Fish Audio / OpenAI TTS
│   └── pipeline_service.py    # Orchestration
└── models/                    # Data models (coming soon)
```

## Next Steps

1. **Day 2-3**: Add Supabase for storage and auth
2. **Day 4-5**: Implement scheduled daily briefings
3. **Week 2**: Add Stripe payments and premium features

## Environment Variables

See `.env.example` for all required variables.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.main:app --reload
```

## Kokoro TTS

Kokoro is a high-quality, zero-shot text-to-speech model that runs locally:
- **Cost**: FREE (self-hosted)
- **Quality**: Excellent, natural sounding voices
- **Voices**: 10+ voices (American/British, Male/Female)
- **Speed**: ~2-5 seconds for a paragraph on CPU
- **No API limits**: Generate unlimited audio

### Managing Kokoro

```bash
./kokoro.sh start    # Start container
./kokoro.sh stop     # Stop container
./kokoro.sh logs     # View logs
./kokoro.sh test     # Generate test audio
./kokoro.sh voices   # List available voices
```

## Cost Estimates

- News API: ~$0.001 per briefing
- Gemini AI: Free tier (1500 requests/day)
- Kokoro TTS: FREE (self-hosted)
- **Total**: ~$0.002 per briefing (99% cheaper!)