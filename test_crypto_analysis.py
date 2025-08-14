#!/usr/bin/env python3
"""
Test script for the CryptoAnalyzer module.
This script tests all functionality and provides sample output.
"""

import asyncio
import sys
import os

# Add the current directory to Python path so we can import our module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_analysis import CryptoAnalyzer

async def test_individual_crypto():
    """Test individual crypto analysis"""
    print("=" * 60)
    print("TESTING INDIVIDUAL CRYPTO ANALYSIS")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    for crypto in ['BTC', 'ETH', 'SOL']:
        print(f"\n--- {crypto} Analysis ---")
        try:
            analysis = await analyzer.get_individual_crypto_analysis(crypto, 8)
            
            print(f"Crypto: {analysis['crypto_name']}")
            print(f"Current Price: {analysis['current_price']}")
            print(f"Price Change: {analysis['price_change']}")
            print(f"Percentage Change: {analysis['percentage_change']}")
            print(f"High: {analysis['high_price']}")
            print(f"Low: {analysis['low_price']}")
            print(f"Volume: {analysis['volume_analysis']}")
            print(f"Trend: {analysis['trend_direction']}")
            print(f"Momentum: {analysis['momentum']}")
            print(f"Data Points: {analysis['period_hours']}")
            print(f"Timestamp: {analysis['timestamp']}")
            
        except Exception as e:
            print(f"ERROR analyzing {crypto}: {str(e)}")

async def test_all_crypto_analysis():
    """Test getting analysis for all cryptos at once"""
    print("\n" + "=" * 60)
    print("TESTING ALL CRYPTO ANALYSIS")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    try:
        all_analysis = await analyzer.get_all_crypto_analysis(8)
        
        for crypto_symbol, analysis in all_analysis.items():
            print(f"\n{crypto_symbol} ({analysis['crypto_name']}):")
            print(f"  Price: {analysis['current_price']}")
            print(f"  Change: {analysis['percentage_change']}")
            print(f"  Trend: {analysis['trend_direction']}")
            print(f"  Momentum: {analysis['momentum']}")
            
    except Exception as e:
        print(f"ERROR in all crypto analysis: {str(e)}")

async def test_briefing_summary():
    """Test generating a briefing summary"""
    print("\n" + "=" * 60)
    print("TESTING BRIEFING SUMMARY")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    try:
        summary = await analyzer.get_crypto_summary_for_briefing(8)
        print(f"\nGenerated Briefing Summary:")
        print("-" * 40)
        print(summary)
        print("-" * 40)
        
        # Check word count
        word_count = len(summary.split())
        print(f"\nSummary word count: {word_count}")
        print(f"Estimated speaking time: {word_count / 150:.1f} minutes")
        
    except Exception as e:
        print(f"ERROR generating briefing summary: {str(e)}")

async def test_tts_formatting():
    """Test TTS formatting functions"""
    print("\n" + "=" * 60)
    print("TESTING TTS FORMATTING")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    # Test price formatting
    test_prices = [45123.45, 1234.56, 56.78, 0.0345, 1500000]
    print("\nPrice Formatting:")
    for price in test_prices:
        formatted = analyzer._format_price_for_tts(price)
        print(f"  ${price:,.2f} -> {formatted}")
    
    # Test percentage formatting
    test_percentages = [5.67, -3.21, 12.5, -0.45, 0.0]
    print("\nPercentage Formatting:")
    for pct in test_percentages:
        formatted = analyzer._format_percentage_for_tts(pct)
        print(f"  {pct}% -> {formatted}")
    
    # Test volume formatting
    test_volumes = [1500000000, 45000000, 123000, 500]
    print("\nVolume Formatting:")
    for volume in test_volumes:
        formatted = analyzer._format_volume_for_tts(volume)
        print(f"  {volume:,} -> {formatted}")

async def main():
    """Run all tests"""
    print("Starting CryptoAnalyzer Tests...")
    print(f"Testing with FMP API endpoint")
    
    try:
        await test_tts_formatting()
        await test_individual_crypto()
        await test_all_crypto_analysis()
        await test_briefing_summary()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())