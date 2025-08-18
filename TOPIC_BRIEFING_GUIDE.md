# Daily Topic Briefing Generator

A comprehensive system for generating topic-specific news briefings using AI-powered summarization and multi-source news aggregation.

## Overview

The Topic Briefing Generator creates professional 10-15 minute audio briefings on any topic by:
- Fetching relevant articles from multiple news sources 
- Using AI to analyze and summarize content
- Generating TTS-optimized audio with professional narration
- Providing both text and audio outputs

## Features

### Multi-Source News Aggregation
- **Primary**: NewsAPI.ai with advanced keyword search and boolean operators
- **Secondary**: Finlight API for financial topics  
- **Smart Fallbacks**: Automatic time range expansion and related keyword search
- **Quality Filtering**: Deduplication, source diversity, and relevance scoring

### Intelligent Topic Classification
- **Volume Categories**: High/Medium/Low volume topics with adaptive time ranges
- **Subject Categories**: Technology, Healthcare, Energy, Financial, Policy
- **Search Optimization**: Custom keyword expansion for better article discovery
- **Edge Case Handling**: Graceful degradation for niche or low-volume topics

### AI-Powered Content Generation  
- **15-Minute Structure**: Topic overview → Latest developments → Market impact → Company highlights → Future outlook → Conclusion
- **10-Minute Option**: Condensed version with proportional sections
- **TTS Optimization**: Professional pronunciation, natural transitions, broadcast style
- **Anti-Duplication**: Ensures each company/event appears only once

### Audio Generation
- **Fish Audio Integration**: Premium TTS with unlimited length
- **Intro Stitching**: Automatic intro audio addition
- **Professional Quality**: Broadcast-ready audio output
- **Duration Estimation**: Accurate timing based on word count

## Usage

### Basic Usage
```bash
# Generate 15-minute briefing on biotechnology
python daily_topic_briefing.py "biotechnology"

# 10-minute briefing looking back 3 days  
python daily_topic_briefing.py "artificial intelligence" --days=3 --length=10

# Text-only output (no audio)
python daily_topic_briefing.py "renewable energy" --no-audio
```

### Command Line Options
- `topic` (required): Topic name (e.g., "biotechnology", "cryptocurrency")
- `--days`: Days to look back for articles (default: 2)
- `--length`: Briefing length in minutes - 10 or 15 (default: 15)
- `--no-audio`: Skip audio generation, text only

### Example Topics

**High Volume (1-day search)**:
- "cryptocurrency" 
- "federal reserve"
- "stock market"
- "inflation"

**Medium Volume (2-day search)**:
- "artificial intelligence"
- "biotechnology" 
- "electric vehicles"
- "renewable energy"

**Low Volume (7-day search)**:
- "quantum computing"
- "space tourism" 
- "gene therapy"
- "nuclear fusion"

## Output Files

Each generation creates three files:

1. **Briefing Text**: `topic_briefing_[topic]_[timestamp].txt`
   - Clean, TTS-ready script
   - 1500-2250 words depending on length
   - Professional broadcast style

2. **Raw Data**: `topic_briefing_raw_[topic]_[timestamp].txt`  
   - All source articles with metadata
   - Search parameters and classification
   - Useful for debugging and analysis

3. **Audio File**: `topic_briefing_audio_[topic]_[timestamp].mp3` (if enabled)
   - Professional narration with intro
   - 10-15 minute duration
   - Broadcast quality

## System Architecture

### Topic Classification System
```python
# Volume categories determine search strategy
{
    "high_volume": 1 day lookback,      # Breaking news topics
    "medium_volume": 2 days lookback,   # Standard topics  
    "low_volume": 7 days lookback      # Niche/research topics
}

# Subject categories enable targeted search
{
    "technology": ["AI", "blockchain", "quantum computing"],
    "healthcare": ["biotechnology", "pharmaceuticals"], 
    "energy": ["renewable energy", "oil", "electric vehicles"],
    "financial": ["crypto", "fed", "markets", "banking"]
}
```

### Search Strategy Flow
1. **Topic Analysis**: Classify volume and subject category
2. **Keyword Generation**: Create boolean search terms with OR operators
3. **Multi-Source Fetch**: NewsAPI.ai primary, Finlight for financial topics
4. **Adaptive Expansion**: Extend time range if low article count
5. **Quality Control**: Deduplication and relevance filtering

### AI Content Generation
- **Google Gemini 2.0 Flash**: High-performance model with 2048 token output
- **Structured Prompts**: Section-specific word targets and formatting rules
- **Content Rules**: No hallucination, source attribution, anti-duplication
- **TTS Formatting**: Optimized for professional audio generation

## Technical Requirements

### Environment Variables
```bash
NEWSAPI_AI_KEY=xxx          # Required: NewsAPI.ai for comprehensive search
FINLIGHT_API_KEY=xxx        # Optional: Financial news (for financial topics)
GEMINI_API_KEY=xxx          # Required: Google Gemini for AI summarization
FISH_API_KEY=xxx            # Required: Fish Audio for TTS generation
OPENAI_API_KEY=xxx          # Optional: OpenAI TTS fallback
```

### Dependencies
- Python 3.10+
- asyncio support
- pydub (optional, for audio stitching)
- All existing project dependencies

## Error Handling

### Common Scenarios
- **No Articles Found**: Extends time range automatically, graceful failure if still no results
- **API Failures**: Multi-source fallbacks, detailed error logging
- **Low Volume Topics**: Smart expansion with related keywords
- **Rate Limiting**: Respectful API usage with proper timeouts

### Debugging
- **Verbose Logging**: Detailed search parameters and results
- **Raw Data Files**: Complete article metadata for analysis  
- **Classification Info**: Topic categorization and search strategy used

## Integration with Existing System

### Follows Established Patterns
- Same service architecture (NewsAPI.ai, Finlight, Summary, Audio)
- Consistent file naming conventions
- Identical TTS formatting and pronunciation rules  
- Standard error handling and logging patterns

### Extends Current Capabilities  
- Topic-specific search (vs. general market news)
- Adaptive time ranges (vs. fixed periods)
- Subject categorization (vs. one-size-fits-all)
- Customizable briefing lengths

## Best Practices

### Topic Selection
- Use broad, well-covered topics for reliable results
- Consider topic volume when setting expectations
- Financial topics benefit from dual-source coverage
- Technology topics have rich keyword expansion

### Time Range Guidelines
- Breaking news: 1-2 days
- Industry analysis: 3-7 days  
- Research topics: 7-30 days
- Let the system auto-adjust for optimal results

### Content Quality
- System prevents duplicate coverage across sections
- Source diversity ensures comprehensive coverage
- Professional formatting ready for broadcast
- Accurate pronunciation for technical terms

## Future Enhancements

### Planned Features
- Custom keyword injection for specialized topics
- Multiple output formats (bullet points, executive summary)
- Industry-specific briefing templates
- User preference learning for topic classification

### Potential Integrations
- Slack/Teams bot for automated briefings
- Email digest delivery
- Podcast RSS feed generation  
- Integration with calendar systems for scheduled briefings

---

*For technical support or feature requests, see the main project documentation.*