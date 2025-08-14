# CryptoAnalyzer Module

## Overview

The `CryptoAnalyzer` module provides comprehensive cryptocurrency price analysis for Bitcoin (BTC), Ethereum (ETH), and Solana (SOL). It fetches real-time data from the Financial Modeling Prep (FMP) API and provides structured analysis with text-to-speech (TTS) formatted output for integration with market briefings.

## Features

- **Real-time Data**: Fetches 5-minute price data from FMP API
- **Hourly Aggregation**: Converts 5-minute data into hourly OHLCV (Open, High, Low, Close, Volume) analysis
- **8-Hour Analysis**: Provides comprehensive analysis over the last 8 hours
- **TTS-Formatted Output**: All text output is properly formatted for text-to-speech systems
- **Professional Analysis**: Includes price changes, trend direction, momentum, and volume analysis
- **Error Handling**: Graceful fallbacks when data is unavailable

## Supported Cryptocurrencies

| Symbol | Name     | API Symbol |
|--------|----------|------------|
| BTC    | Bitcoin  | BTCUSD     |
| ETH    | Ethereum | ETHUSD     |
| SOL    | Solana   | SOLUSD     |

## Installation & Setup

1. The module is already included in the project at `/Users/bart/dev/mm-ai-be/crypto_analysis.py`
2. No additional API keys required (uses embedded FMP API key)
3. Requires the following Python packages (already in requirements.txt):
   - `httpx` - for API requests
   - `asyncio` - for async operations

## Basic Usage

### Simple Crypto Summary for Briefings

```python
from crypto_analysis import CryptoAnalyzer

async def get_crypto_for_briefing():
    analyzer = CryptoAnalyzer()
    summary = await analyzer.get_crypto_summary_for_briefing(8)
    print(summary)
    # Output: "In cryptocurrency markets, Bitcoin is trading at..."
```

### Individual Crypto Analysis

```python
async def analyze_bitcoin():
    analyzer = CryptoAnalyzer()
    btc_analysis = await analyzer.get_individual_crypto_analysis('BTC', 8)
    
    print(f"Price: {btc_analysis['current_price']}")
    print(f"Change: {btc_analysis['percentage_change']}")
    print(f"Trend: {btc_analysis['trend_direction']}")
```

### All Cryptocurrencies Analysis

```python
async def analyze_all_cryptos():
    analyzer = CryptoAnalyzer()
    all_analysis = await analyzer.get_all_crypto_analysis(8)
    
    for crypto, analysis in all_analysis.items():
        print(f"{crypto}: {analysis['current_price']}")
```

## Analysis Output Structure

Each crypto analysis returns a dictionary with the following fields:

```python
{
    'crypto_name': 'Bitcoin',                           # Human-readable name
    'current_price': '124 thousand dollars',            # TTS-formatted price
    'current_price_raw': 123597.48,                     # Raw price for calculations
    'price_change': 'up 2.1 thousand dollars',          # TTS-formatted change
    'percentage_change': 'up 1.77 percent',             # TTS-formatted percentage
    'percentage_change_raw': 1.77,                      # Raw percentage for calculations
    'high_price': '124 thousand dollars',               # 8-hour high (TTS)
    'low_price': '121 thousand dollars',                # 8-hour low (TTS)
    'volume_analysis': '3.4 billion in average hourly volume',  # TTS-formatted volume
    'trend_direction': 'up',                            # 'up', 'down', or 'sideways'
    'momentum': 'positive',                             # 'positive', 'negative', 'neutral', etc.
    'period_hours': 8,                                  # Number of data points analyzed
    'timestamp': 'August 13, 2025 at 07:42 PM'         # Analysis timestamp
}
```

## TTS Formatting Features

The module automatically formats all output for optimal text-to-speech pronunciation:

### Price Formatting
- `$123,597.48` → `"124 thousand dollars"`
- `$4,768.05` → `"4.8 thousand dollars"`
- `$202.85` → `"203 dollars"`

### Percentage Formatting
- `+1.77%` → `"up 1.77 percent"`
- `-3.21%` → `"down 3.21 percent"`
- `0.0%` → `"unchanged"`

### Volume Formatting
- `3,400,000,000` → `"3.4 billion in average hourly volume"`
- `45,000,000` → `"45.0 million in average hourly volume"`

## Integration with Existing Briefing System

### Simple Integration

Add to existing briefing generation scripts:

```python
from crypto_analysis import CryptoAnalyzer

async def generate_briefing():
    # Existing briefing code...
    
    # Add crypto section
    analyzer = CryptoAnalyzer()
    crypto_section = await analyzer.get_crypto_summary_for_briefing(8)
    
    # Include in briefing
    briefing_parts.append(crypto_section)
```

### Advanced Integration

For detailed control, use individual analysis:

```python
async def generate_detailed_crypto_section():
    analyzer = CryptoAnalyzer()
    all_analysis = await analyzer.get_all_crypto_analysis(8)
    
    crypto_parts = ["Moving to cryptocurrency markets."]
    
    for crypto_symbol in ['BTC', 'ETH', 'SOL']:
        if crypto_symbol in all_analysis:
            analysis = all_analysis[crypto_symbol]
            if analysis['current_price_raw'] > 0:  # Valid data
                section = f"{analysis['crypto_name']} is trading at {analysis['current_price']}, {analysis['percentage_change']} with {analysis['momentum']} momentum."
                crypto_parts.append(section)
    
    return " ".join(crypto_parts)
```

## Testing

### Run All Tests
```bash
python test_crypto_analysis.py
```

### Run Integration Example
```bash
python example_crypto_integration.py
```

### Test Enhanced Briefing
```bash
python generate_briefing_with_crypto.py
```

## API Details

### Data Source
- **API**: Financial Modeling Prep (FMP)
- **Endpoint**: `https://financialmodelingprep.com/api/v3/historical-chart/5min/{symbol}`
- **Update Frequency**: 5-minute intervals
- **Historical Depth**: Typically 24+ hours of data available

### Data Processing
1. Fetches 5-minute OHLCV data
2. Groups data by hour
3. Aggregates into hourly OHLCV bars
4. Calculates trend and momentum indicators
5. Formats for TTS compatibility

## Performance

- **Typical Response Time**: 2-3 seconds for all three cryptocurrencies
- **Data Points**: ~2,800 5-minute data points aggregated into 8 hourly periods
- **Concurrent Requests**: Handles multiple crypto symbols concurrently
- **Error Resilience**: Graceful degradation if data unavailable

## Error Handling

The module handles various error conditions:

- **API Unavailable**: Returns fallback text indicating data unavailability
- **Insufficient Data**: Uses available data with appropriate warnings
- **Network Timeouts**: 30-second timeout with error messages
- **Invalid Symbols**: Validates crypto symbols before API calls

## Example Output

### Successful Analysis
```
In cryptocurrency markets, Bitcoin is trading at 124 thousand dollars, up 1.77 percent over the past 8 hours with an up trend. Ethereum is trading at 4.8 thousand dollars, up 1.40 percent over the past 8 hours with an up trend. Solana is trading at 203 dollars, up 2.43 percent over the past 8 hours with an up trend. The crypto market is showing broad strength across major coins.
```

### Data Unavailable
```
Cryptocurrency data is currently unavailable. Moving on to other market news.
```

## Future Enhancements

Potential improvements for future versions:

1. **Additional Cryptocurrencies**: Add support for more coins (ADA, DOT, MATIC, etc.)
2. **Technical Indicators**: RSI, MACD, moving averages
3. **News Integration**: Combine price data with crypto news
4. **Market Cap Analysis**: Include market capitalization changes
5. **Correlation Analysis**: Compare crypto movements with traditional markets

## Troubleshooting

### Common Issues

**No data returned**
- Check internet connection
- Verify FMP API is accessible
- Ensure crypto symbols are supported

**Incomplete analysis**
- May occur during market hours with limited data
- Module will use available data and note limitations

**Slow performance**
- Normal for first run as it fetches large datasets
- Subsequent calls may be faster due to API caching

### Debug Mode

Enable verbose logging by checking the console output:
- `[CryptoAnalyzer]` prefixed messages show detailed processing steps
- Error messages include specific failure reasons
- Data point counts help verify successful processing

## License & Credits

- Part of the MarketMotion project
- Uses Financial Modeling Prep API for data
- Follows existing project TTS formatting standards
- Compatible with Fish Audio and OpenAI TTS systems