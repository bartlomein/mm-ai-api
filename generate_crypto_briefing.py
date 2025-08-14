#!/usr/bin/env python3
"""
Generate a crypto market briefing using FMP data
Example: "How is crypto doing overall?"
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from src.services.fmp_service import FMPService
from src.services.audio_service import AudioService

load_dotenv()

async def main():
    print("🪙 Generating Crypto Market Briefing...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Initialize services
    fmp_service = FMPService()
    audio_service = AudioService()
    
    # Get crypto overview
    print("Fetching crypto market data...")
    crypto_data = await fmp_service.get_crypto_overview()
    
    if not crypto_data:
        print("❌ Failed to fetch crypto data")
        return
    
    # Create briefing script
    script = f"""Good {datetime.now().strftime('%p').lower()}! Here's your cryptocurrency market update.

The crypto market is currently {crypto_data.get('market_sentiment', 'mixed')}. {crypto_data.get('summary', '')}

Let me break down the major cryptocurrencies for you:

"""
    
    # Add details for top cryptos
    for crypto in crypto_data.get('cryptos', [])[:6]:
        if crypto.get('symbol'):
            name = crypto['symbol'].replace('USD', '')
            price = crypto.get('price', 0)
            change = crypto.get('changePercent', 0)
            direction = "up" if change > 0 else "down"
            
            if name == "BTC":
                name = "Bitcoin"
            elif name == "ETH":
                name = "Ethereum"
            elif name == "BNB":
                name = "Binance Coin"
            elif name == "SOL":
                name = "Solana"
            elif name == "ADA":
                name = "Cardano"
            elif name == "XRP":
                name = "Ripple"
            
            script += f"{name} is trading at ${price:,.2f}, {direction} {abs(change):.1f} percent. "
    
    script += f"""

Overall market sentiment appears to be {crypto_data.get('market_sentiment', 'mixed')}, with {sum(1 for c in crypto_data.get('cryptos', []) if c.get('changePercent', 0) > 0)} out of {len(crypto_data.get('cryptos', []))} major cryptocurrencies showing positive movement.

This reflects current investor sentiment and market dynamics in the digital asset space.
"""
    
    print("\nGenerated Script:")
    print("-" * 50)
    print(script)
    print("-" * 50)
    
    # Save text version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"crypto_briefing_{timestamp}.txt"
    with open(text_filename, 'w') as f:
        f.write(script)
    print(f"\n✅ Text saved to: {text_filename}")
    
    # Generate audio
    print("\nGenerating audio (this may take a minute)...")
    audio_bytes = await audio_service.generate_audio(script)
    
    if audio_bytes:
        audio_filename = f"crypto_briefing_{timestamp}.mp3"
        with open(audio_filename, 'wb') as f:
            f.write(audio_bytes)
        print(f"✅ Audio saved to: {audio_filename}")
        print(f"   Size: {len(audio_bytes) / 1024:.1f} KB")
        print(f"   Duration: ~{audio_service.estimate_duration(script)} seconds")
    else:
        print("❌ Failed to generate audio")

if __name__ == "__main__":
    asyncio.run(main())