# Market Brief AI - Project Documentation

## Project Overview
Market Brief AI is an automated financial news briefing system that generates 5-minute audio market updates using AI. It fetches financial news, creates intelligent summaries, and converts them to speech using advanced TTS services.

## Key Features
- **Automated News Aggregation**: Fetches latest financial news from Finlight API
- **AI-Powered Summarization**: Uses Google Gemini to create professional market briefings
- **Text-to-Speech**: Converts briefings to audio using Fish Audio (primary), OpenAI TTS, or Kokoro
- **5-Minute Format**: Generates exactly 750-850 words for consistent 5-minute audio briefings
- **Smart Deduplication**: Avoids repeating similar news stories
- **Professional Formatting**: Properly formats stock tickers, numbers, and financial terms for TTS

## Architecture

### Services Structure
```
src/
├── services/
│   ├── audio_service.py      # TTS generation (Fish Audio, OpenAI, Kokoro)
│   ├── news_service.py        # Finlight API integration
│   ├── summary_service.py     # Gemini AI summarization
│   └── pipeline_service.py    # Orchestrates the full pipeline
└── main.py                    # FastAPI application
```

### Scripts
- `generate_briefing_v2.py` - Main script for generating 5-minute briefings (RECOMMENDED)
- `generate_briefing.py` - Original briefing generator
- `test_pipeline.py` - Tests the full pipeline
- `list_fish_models.py` - Lists available Fish Audio voice models
- `test_fish_voices.py` - Tests different TTS voices

## Configuration

### Environment Variables (.env)
```bash
# News Data
FINLIGHT_API_KEY=xxx           # Required: Financial news API

# AI/LLM
GEMINI_API_KEY=xxx             # Required: Google Gemini for summarization
DEEPSEEK_API_KEY=xxx           # Optional: Fallback LLM

# Text-to-Speech (in priority order)
FISH_API_KEY=xxx               # Primary: Best quality, no char limit
FISH_MODEL_ID=xxx              # Optional: Specific voice model ID
OPENAI_API_KEY=xxx             # Secondary: 4096 char limit
KOKORO_URL=http://localhost:8880  # Tertiary: Self-hosted fallback

# Database (Future)
SUPABASE_URL=xxx
SUPABASE_ANON_KEY=xxx
```

### Recommended Fish Audio Voice Models
- **Energetic Male**: `802e3bc2b27e49c2995d23ef70e6ac89` (Professional news voice)
- **Elon Musk**: `03397b4c4be74759b72533b663fbd001` (Tech-focused)
- **Donald Trump**: `5196af35f6ff4a0dbf541793fc9f2157` (Business tone)

## Usage

### Generate a 5-Minute Market Briefing
```bash
# Recommended: Use v2 for proper 5-minute briefings
./generate_briefing_v2.py

# This will:
# 1. Fetch 100+ articles from Finlight
# 2. Generate 800-word briefing in sections
# 3. Create audio file using Fish Audio
# 4. Save both text and audio files
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

# Test full pipeline
python test_pipeline.py

# Check briefing length
python test_briefing_length.py

# Test Fish Audio voices
python test_fish_voices.py
```

### Docker Commands
```bash
# Start Kokoro TTS (if using)
docker-compose up -d kokoro

# Start all services
docker-compose up -d
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
- `[Main]` - Application startup and configuration

### Common Error Messages
- `"FINLIGHT_API_KEY not found"` - Set the API key in .env
- `"Text too long for OpenAI TTS"` - Text exceeds 4096 chars, will use Fish Audio
- `"No TTS service configured"` - Set at least one TTS API key
- `"Generated only X words"` - Gemini didn't follow word count, will retry

## Best Practices

1. **Always use `generate_briefing_v2.py`** for consistent 5-minute briefings
2. **Set `FISH_MODEL_ID`** in .env for consistent voice
3. **Monitor word counts** in output to ensure proper length
4. **Check for duplicate content** in generated briefings
5. **Verify TTS formatting** in text files before audio generation

## Support and Resources

- **Fish Audio Docs**: https://docs.fish.audio
- **Finlight API**: https://finlight.me
- **Google Gemini**: https://ai.google.dev
- **OpenAI TTS**: https://platform.openai.com/docs/guides/text-to-speech

## Version History

### Current Version: 2.0
- Generates proper 5-minute briefings (750-850 words)
- Includes article deduplication
- Supports Fish Audio as primary TTS
- Professional TTS formatting
- Section-by-section generation for consistency

### Previous Issues (Now Fixed)
- ✅ Briefings were too short (45 seconds instead of 5 minutes)
- ✅ Duplicate news stories appeared multiple times
- ✅ Stock tickers weren't pronounced correctly
- ✅ Numbers and percentages formatted incorrectly
- ✅ Voice changed between generations

---

*Last Updated: August 2024*
*Project: Market Brief AI - Automated Financial News Briefings*