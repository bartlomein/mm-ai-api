#!/usr/bin/env python3
"""
Test script to verify FMP API integration and all service methods
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

async def test_fmp_api():
    """Test the FMP API endpoint directly"""
    import httpx
    
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        print("❌ FMP_API_KEY not found in .env")
        return False
    
    print("Testing FMP API connection...")
    
    # Test basic quote endpoint
    url = f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={api_key}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    print(f"✅ FMP API connected! AAPL price: ${data[0].get('price', 'N/A')}")
                    return True
                else:
                    print("❌ FMP API returned empty data")
                    return False
            else:
                print(f"❌ FMP API error: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error connecting to FMP API: {str(e)}")
        return False

async def test_fmp_service():
    """Test our FMPService class and all its methods"""
    from src.services.fmp_service import FMPService
    
    service = FMPService()
    
    if not service.api_key:
        print("❌ FMPService: API key not configured")
        return
    
    print("\n" + "="*50)
    print("Testing FMPService Methods")
    print("="*50)
    
    # Test 1: Market Indices
    print("\n1. Testing Market Indices (SPY, QQQ, DIA)...")
    indices = await service.get_market_indices()
    if indices and indices.get("summary"):
        print(f"✅ Indices: {indices['summary']}")
        for idx in indices.get("indices", [])[:3]:
            if idx.get("symbol"):
                print(f"   - {idx['symbol']}: ${idx.get('price', 0):.2f} ({idx.get('changePercent', 0):.2f}%)")
    else:
        print("❌ Failed to fetch market indices")
    
    # Test 2: Premarket Data
    print("\n2. Testing Premarket Data...")
    premarket = await service.get_premarket_data()
    if premarket and premarket.get("summary"):
        print(f"✅ Premarket: {premarket['summary']}")
    else:
        print("⚠️  No premarket data (markets may be open)")
    
    # Test 3: Crypto Overview
    print("\n3. Testing Crypto Overview...")
    crypto = await service.get_crypto_overview()
    if crypto and crypto.get("summary"):
        print(f"✅ Crypto: {crypto['summary']}")
        print(f"   Market Sentiment: {crypto.get('market_sentiment', 'unknown')}")
        for c in crypto.get("cryptos", [])[:3]:
            if c.get("symbol"):
                print(f"   - {c['symbol']}: ${c.get('price', 0):,.2f} ({c.get('changePercent', 0):.2f}%)")
    else:
        print("❌ Failed to fetch crypto data")
    
    # Test 4: Market Movers
    print("\n4. Testing Market Movers...")
    movers = await service.get_market_movers()
    if movers and movers.get("summary"):
        print(f"✅ Movers: {movers['summary']}")
        
        if movers.get("gainers"):
            print("   Top Gainers:")
            for g in movers["gainers"][:3]:
                print(f"     - {g.get('symbol', 'N/A')}: +{g.get('changePercent', 0):.1f}%")
        
        if movers.get("losers"):
            print("   Top Losers:")
            for l in movers["losers"][:3]:
                print(f"     - {l.get('symbol', 'N/A')}: {l.get('changePercent', 0):.1f}%")
    else:
        print("❌ Failed to fetch market movers")
    
    # Test 5: Sector Performance
    print("\n5. Testing Sector Performance...")
    sectors = await service.get_sector_performance()
    if sectors and sectors.get("summary"):
        print(f"✅ Sectors: {sectors['summary']}")
        for sector in sectors.get("sectors", [])[:5]:
            if sector.get("sector"):
                print(f"   - {sector['sector']}: {sector.get('changePercent', 0)}%")
    else:
        print("❌ Failed to fetch sector performance")
    
    # Test 6: Intraday Performance (SPY last 8 hours)
    print("\n6. Testing Intraday Performance (SPY - Last 8 Hours)...")
    intraday = await service.get_intraday_performance("SPY")
    if intraday and intraday.get("summary"):
        print(f"✅ SPY 8-hour: {intraday['summary']}")
        print(f"   Data points: {intraday.get('data_points', 0)}")
        print(f"   Volume: {intraday.get('volume_total', 0):,.0f}")
    else:
        print("❌ Failed to fetch intraday data")
    
    # Test 7: Economic Calendar
    print("\n7. Testing Economic Calendar...")
    calendar = await service.get_economic_calendar()
    if calendar and calendar.get("summary"):
        print(f"✅ Calendar: {calendar['summary']}")
        if calendar.get("high_impact"):
            print("   High Impact Events:")
            for event in calendar["high_impact"][:3]:
                print(f"     - {event.get('event', 'N/A')} ({event.get('country', 'N/A')})")
    else:
        print("⚠️  No economic events or failed to fetch")
    
    # Test 8: Generate Market Briefing
    print("\n8. Testing Market Briefing Generation...")
    briefing = await service.generate_market_briefing()
    if briefing:
        print("✅ Market Briefing Generated:")
        print("-" * 40)
        print(briefing[:500] + "..." if len(briefing) > 500 else briefing)
        print("-" * 40)
        print(f"   Total length: {len(briefing)} characters")
    else:
        print("❌ Failed to generate market briefing")
    
    # Test 9: Past 8 Hours Summary
    print("\n9. Testing Past 8 Hours Summary...")
    past_8h = await service.get_past_8_hours_summary(["SPY", "QQQ", "BTCUSD"])
    if past_8h:
        print(f"✅ 8-Hour Summary: {past_8h}")
    else:
        print("❌ Failed to generate 8-hour summary")

async def test_specific_use_cases():
    """Test specific investor/trader use cases"""
    from src.services.fmp_service import FMPService
    
    service = FMPService()
    
    print("\n" + "="*50)
    print("Testing Specific Use Cases")
    print("="*50)
    
    # Use Case 1: Morning Premarket Check
    print("\n📊 Use Case 1: Morning Premarket Check")
    print("What an investor wants to hear before market open...")
    
    # Get premarket for major indices and popular stocks
    premarket = await service.get_premarket_data(["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "MSFT"])
    indices = await service.get_market_indices()
    
    morning_brief = []
    morning_brief.append(f"Good morning! It's {datetime.now().strftime('%A, %B %d')}.")
    
    if premarket.get("summary"):
        morning_brief.append(f"In premarket trading: {premarket['summary']}")
    
    if indices.get("summary"):
        morning_brief.append(f"Yesterday's close: {indices['summary']}")
    
    print("\n".join(morning_brief))
    
    # Use Case 2: Crypto Check
    print("\n📊 Use Case 2: How is Crypto Doing?")
    crypto = await service.get_crypto_overview()
    
    if crypto:
        print(f"The crypto market is {crypto.get('market_sentiment', 'mixed')} today.")
        print(crypto.get("summary", ""))
    
    # Use Case 3: SPY Intraday Performance
    print("\n📊 Use Case 3: How is SPY Doing Today?")
    spy_intraday = await service.get_intraday_performance("SPY", "5min")
    
    if spy_intraday.get("summary"):
        print(spy_intraday["summary"])
    
    # Use Case 4: Market Movers Alert
    print("\n📊 Use Case 4: What's Moving in the Market?")
    movers = await service.get_market_movers()
    
    if movers:
        print(movers.get("summary", ""))
        if movers.get("most_active"):
            active_symbols = [s.get("symbol") for s in movers["most_active"][:3]]
            print(f"Most actively traded: {', '.join(active_symbols)}")

async def main():
    """Run all tests"""
    print("🚀 Starting FMP Service Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test API connection first
    api_ok = await test_fmp_api()
    
    if api_ok:
        # Test all service methods
        await test_fmp_service()
        
        # Test specific use cases
        await test_specific_use_cases()
    
    print("\n✅ FMP Service tests completed!")

if __name__ == "__main__":
    asyncio.run(main())