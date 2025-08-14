#!/usr/bin/env python3
"""
Generate SPY premarket briefing using FMP data
Example: "How is SPY doing premarket?"
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from src.services.fmp_service import FMPService
from src.services.audio_service import AudioService

load_dotenv()

async def main():
    print("📊 Generating SPY Premarket Briefing...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Initialize services
    fmp_service = FMPService()
    audio_service = AudioService()
    
    # Get premarket data for SPY and related ETFs
    print("Fetching premarket data...")
    symbols = ["SPY", "QQQ", "IWM", "DIA"]
    premarket_data = await fmp_service.get_premarket_data(symbols)
    
    # Also get yesterday's close for context
    print("Fetching yesterday's close data...")
    indices_data = await fmp_service.get_market_indices()
    
    if not premarket_data:
        print("⚠️  No premarket data available (markets may be open)")
        # Try intraday instead
        print("Fetching intraday data as fallback...")
        intraday = await fmp_service.get_intraday_performance("SPY", "5min")
        
        if intraday:
            script = f"""Good {datetime.now().strftime('%p').lower()}! The market is currently open.

{intraday.get('summary', 'SPY trading data unavailable.')}

"""
        else:
            script = "Market data is currently unavailable. Please try again later."
    else:
        # Create briefing script
        script = f"""Good {datetime.now().strftime('%p').lower()}! Here's your premarket update for the S and P 500.

"""
        
        # Find SPY specifically
        spy_data = None
        for stock in premarket_data.get('premarket', []):
            if stock.get('symbol') == 'SPY':
                spy_data = stock
                break
        
        if spy_data and spy_data.get('preMarketPrice'):
            price = spy_data['preMarketPrice']
            change = spy_data.get('preMarketChange', 0)
            change_pct = spy_data.get('preMarketChangePercent', 0)
            last_close = spy_data.get('lastClose', 0)
            
            direction = "higher" if change > 0 else "lower"
            
            script += f"""The S P Y E T F is trading at ${price:.2f} in premarket, {direction} by ${abs(change):.2f} or {abs(change_pct):.2f} percent from yesterday's close of ${last_close:.2f}.

"""
        
        # Add context from other major indices
        script += "Other major index E T Fs in premarket: "
        
        for stock in premarket_data.get('premarket', []):
            if stock.get('symbol') != 'SPY' and stock.get('preMarketPrice'):
                symbol = stock['symbol']
                change_pct = stock.get('preMarketChangePercent', 0)
                direction = "up" if change_pct > 0 else "down"
                
                # Spell out ETF names for TTS
                if symbol == "QQQ":
                    name = "Q Q Q"
                elif symbol == "IWM":
                    name = "I W M"
                elif symbol == "DIA":
                    name = "D I A"
                else:
                    name = symbol
                
                script += f"{name} is {direction} {abs(change_pct):.2f} percent. "
        
        # Add market context
        script += """

This premarket activity suggests """
        
        # Determine overall sentiment
        positive_count = sum(1 for s in premarket_data.get('premarket', []) 
                           if s.get('preMarketChangePercent', 0) > 0)
        total_count = len([s for s in premarket_data.get('premarket', []) 
                          if s.get('preMarketPrice')])
        
        if total_count > 0:
            if positive_count > total_count * 0.6:
                script += "a positive opening for the broader market, with risk-on sentiment prevailing."
            elif positive_count < total_count * 0.4:
                script += "a cautious start to trading, with defensive positioning evident."
            else:
                script += "mixed sentiment heading into the regular session."
        
        script += """

Remember that premarket trading typically has lower volume and can be more volatile than regular hours trading. These levels may change significantly at market open."""
    
    print("\nGenerated Script:")
    print("-" * 50)
    print(script)
    print("-" * 50)
    
    # Save text version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"spy_premarket_{timestamp}.txt"
    with open(text_filename, 'w') as f:
        f.write(script)
    print(f"\n✅ Text saved to: {text_filename}")
    
    # Generate audio
    print("\nGenerating audio (this may take a minute)...")
    audio_bytes = await audio_service.generate_audio(script)
    
    if audio_bytes:
        audio_filename = f"spy_premarket_{timestamp}.mp3"
        with open(audio_filename, 'wb') as f:
            f.write(audio_bytes)
        print(f"✅ Audio saved to: {audio_filename}")
        print(f"   Size: {len(audio_bytes) / 1024:.1f} KB")
        print(f"   Duration: ~{audio_service.estimate_duration(script)} seconds")
    else:
        print("❌ Failed to generate audio")

if __name__ == "__main__":
    asyncio.run(main())