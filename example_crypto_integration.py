#!/usr/bin/env python3
"""
Example integration of CryptoAnalyzer with the existing briefing system.
This shows how to incorporate crypto analysis into market briefings.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_analysis import CryptoAnalyzer

async def generate_crypto_briefing_section():
    """
    Generate a complete crypto section for inclusion in market briefings.
    This follows the same TTS formatting rules as the existing summary service.
    """
    print("=" * 60)
    print("CRYPTO BRIEFING SECTION GENERATION")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    try:
        # Get comprehensive analysis
        all_analysis = await analyzer.get_all_crypto_analysis(8)
        
        # Generate briefing text following TTS formatting rules
        briefing_parts = []
        
        # Opening
        briefing_parts.append("Moving to cryptocurrency markets.")
        
        # Individual coin analysis
        for crypto_symbol in ['BTC', 'ETH', 'SOL']:
            if crypto_symbol in all_analysis:
                analysis = all_analysis[crypto_symbol]
                
                if analysis['current_price_raw'] > 0:  # Valid data
                    crypto_name = analysis['crypto_name']
                    current_price = analysis['current_price']
                    percentage_change = analysis['percentage_change']
                    high_price = analysis['high_price']
                    low_price = analysis['low_price']
                    trend = analysis['trend_direction']
                    momentum = analysis['momentum']
                    
                    # Create detailed analysis following briefing format
                    coin_section = (
                        f"{crypto_name} is currently trading at {current_price}, "
                        f"{percentage_change} over the past eight hours. "
                        f"The cryptocurrency hit a high of {high_price} and a low of {low_price} "
                        f"during this period, showing {momentum} momentum with an overall {trend} trend. "
                    )
                    
                    briefing_parts.append(coin_section)
        
        # Market context
        valid_analyses = [a for a in all_analysis.values() if a['current_price_raw'] > 0]
        if len(valid_analyses) >= 2:
            positive_moves = sum(1 for a in valid_analyses if a['percentage_change_raw'] > 0)
            total_coins = len(valid_analyses)
            
            if positive_moves == total_coins:
                context = "The cryptocurrency market is displaying broad-based strength across all major digital assets, suggesting positive investor sentiment and potential institutional buying interest."
            elif positive_moves > total_coins / 2:
                context = "Cryptocurrency markets are showing mixed but generally positive performance, with most major coins advancing despite some sector rotation."
            elif positive_moves == 0:
                context = "Digital asset markets are facing widespread selling pressure, with all major cryptocurrencies declining amid risk-off sentiment."
            else:
                context = "Cryptocurrency markets are showing mixed performance with divergent price action across major digital assets."
            
            briefing_parts.append(context)
        
        # Transition
        briefing_parts.append("That concludes our cryptocurrency market update.")
        
        # Combine all parts
        full_briefing = " ".join(briefing_parts)
        
        print(f"Generated Crypto Briefing Section:")
        print("-" * 50)
        print(full_briefing)
        print("-" * 50)
        
        # Analysis
        word_count = len(full_briefing.split())
        estimated_time = word_count / 150  # 150 words per minute
        
        print(f"\nSection Analysis:")
        print(f"Word count: {word_count}")
        print(f"Estimated speaking time: {estimated_time:.1f} minutes")
        print(f"Suitable for briefing: {'Yes' if 50 <= word_count <= 200 else 'No'}")
        
        return full_briefing
        
    except Exception as e:
        print(f"Error generating crypto briefing: {str(e)}")
        return "Cryptocurrency market data is currently unavailable."

async def show_detailed_crypto_data():
    """
    Show detailed crypto data for analysis and debugging.
    """
    print("\n" + "=" * 60)
    print("DETAILED CRYPTO DATA ANALYSIS")
    print("=" * 60)
    
    analyzer = CryptoAnalyzer()
    
    for crypto in ['BTC', 'ETH', 'SOL']:
        print(f"\n--- Detailed {crypto} Analysis ---")
        
        try:
            analysis = await analyzer.get_individual_crypto_analysis(crypto, 8)
            
            # Show raw and formatted data
            print(f"Raw price: ${analysis['current_price_raw']:,.2f}")
            print(f"TTS price: {analysis['current_price']}")
            print(f"Raw change: {analysis['percentage_change_raw']:+.2f}%")
            print(f"TTS change: {analysis['percentage_change']}")
            print(f"Volume: {analysis['volume_analysis']}")
            print(f"Trend: {analysis['trend_direction']}")
            print(f"Momentum: {analysis['momentum']}")
            print(f"Data quality: {analysis['period_hours']} hourly periods")
            
        except Exception as e:
            print(f"Error analyzing {crypto}: {str(e)}")

async def main():
    """
    Main function demonstrating crypto analysis integration.
    """
    print("Crypto Analysis Integration Example")
    print(f"Generated at: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    
    # Generate briefing section
    await generate_crypto_briefing_section()
    
    # Show detailed data
    await show_detailed_crypto_data()
    
    print(f"\n" + "=" * 60)
    print("INTEGRATION COMPLETE")
    print("=" * 60)
    print("\nTo integrate with existing briefing system:")
    print("1. Import CryptoAnalyzer in your briefing generation script")
    print("2. Call analyzer.get_crypto_summary_for_briefing(8) in your briefing logic")
    print("3. Include the returned text in your briefing sections")
    print("4. The text is already formatted for TTS compatibility")

if __name__ == "__main__":
    asyncio.run(main())