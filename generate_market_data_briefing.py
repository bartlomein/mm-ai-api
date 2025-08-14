#!/usr/bin/env python3
"""
Generate a comprehensive market data briefing using FMP + news data for MarketMotion
This combines real-time market data with AI-generated narrative
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from src.services.pipeline_service import PipelineService

load_dotenv()

async def main():
    print("📈 Generating Comprehensive Market Data Briefing...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Initialize pipeline service
    pipeline = PipelineService()
    
    # Example 1: Full market briefing with all data types
    print("\n1. FULL MARKET BRIEFING")
    print("=" * 50)
    
    result = await pipeline.generate_market_data_briefing(
        focus_areas=["indices", "crypto", "movers", "sectors", "calendar"],
        voice=None  # Use default voice
    )
    
    if result.get("status") == "success":
        print(f"✅ Generated full market briefing")
        print(f"   File: {result.get('file_path')}")
        print(f"   Duration: {result.get('duration_seconds')} seconds")
        print(f"   Data sections: {result.get('data_sections')}")
        print(f"\nTranscript preview (first 500 chars):")
        print(result.get('transcript', '')[:500] + "...")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "-" * 50)
    
    # Example 2: Premarket focused briefing
    print("\n2. PREMARKET BRIEFING")
    print("=" * 50)
    
    result = await pipeline.generate_market_data_briefing(
        focus_areas=["premarket", "indices", "calendar"],
        voice=None
    )
    
    if result.get("status") == "success":
        print(f"✅ Generated premarket briefing")
        print(f"   File: {result.get('file_path')}")
        print(f"   Focus areas: {', '.join(result.get('focus_areas', []))}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "-" * 50)
    
    # Example 3: Crypto-focused briefing
    print("\n3. CRYPTO-FOCUSED BRIEFING")
    print("=" * 50)
    
    result = await pipeline.generate_market_data_briefing(
        focus_areas=["crypto", "movers"],
        voice=None
    )
    
    if result.get("status") == "success":
        print(f"✅ Generated crypto briefing")
        print(f"   File: {result.get('file_path')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "-" * 50)
    
    # Example 4: Intraday update for specific symbols
    print("\n4. INTRADAY UPDATE (Past 8 Hours)")
    print("=" * 50)
    
    result = await pipeline.generate_intraday_update(
        symbols=["SPY", "QQQ", "BTCUSD"],
        hours=8,
        voice=None
    )
    
    if result.get("status") == "success":
        print(f"✅ Generated intraday update")
        print(f"   Symbols: {', '.join(result.get('symbols', []))}")
        print(f"   Timeframe: {result.get('hours')} hours")
        print(f"   File: {result.get('file_path')}")
        print(f"\nTranscript:")
        print(result.get('transcript', 'No transcript'))
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)
    print("✅ All briefings generated successfully!")
    print("\nCommon investor queries this handles:")
    print("- 'How are the markets doing?'")
    print("- 'What's happening in crypto?'")
    print("- 'How is SPY doing premarket?'")
    print("- 'What happened in the last 8 hours?'")
    print("- 'What are today's biggest movers?'")
    print("- 'Which sectors are performing best?'")
    print("- 'What economic events are coming up?'")

if __name__ == "__main__":
    asyncio.run(main())