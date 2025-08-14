#!/usr/bin/env python3
"""
Generate a quick market summary to a text file
Just to see what the FMP data looks like in a readable format
"""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from src.services.fmp_service import FMPService

load_dotenv()

async def main():
    print("📊 Generating Quick Market Summary...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}")
    print("-" * 50)
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    if not fmp_service.api_key:
        print("❌ FMP_API_KEY not found in .env file")
        return
    
    # Start building the summary
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("MARKET SUMMARY")
    summary_lines.append(f"{datetime.now().strftime('%A, %B %d, %Y - %I:%M %p ET')}")
    summary_lines.append("=" * 60)
    summary_lines.append("")
    
    # 1. Market Indices
    print("Fetching market indices...")
    indices = await fmp_service.get_market_indices()
    if indices.get("indices"):
        summary_lines.append("📈 MAJOR INDICES")
        summary_lines.append("-" * 40)
        for idx in indices["indices"]:
            if idx.get("symbol"):
                direction = "↑" if idx.get("change", 0) > 0 else "↓"
                summary_lines.append(
                    f"{idx['symbol']:5} ${idx.get('price', 0):>8.2f}  "
                    f"{direction} {idx.get('change', 0):>7.2f} ({idx.get('changePercent', 0):>6.2f}%)"
                )
                summary_lines.append(f"      Range: ${idx.get('dayLow', 0):.2f} - ${idx.get('dayHigh', 0):.2f}")
                summary_lines.append(f"      Volume: {idx.get('volume', 0):,}")
                summary_lines.append("")
    
    # 2. Crypto Overview
    print("Fetching crypto data...")
    crypto = await fmp_service.get_crypto_overview()
    if crypto.get("cryptos"):
        summary_lines.append("🪙 CRYPTOCURRENCY")
        summary_lines.append("-" * 40)
        summary_lines.append(f"Market Sentiment: {crypto.get('market_sentiment', 'Unknown').upper()}")
        summary_lines.append("")
        for c in crypto["cryptos"][:4]:  # Top 4 cryptos
            if c.get("symbol"):
                name = c["symbol"].replace("USD", "")
                direction = "↑" if c.get("change", 0) > 0 else "↓"
                summary_lines.append(
                    f"{name:6} ${c.get('price', 0):>10,.2f}  "
                    f"{direction} {c.get('changePercent', 0):>6.2f}%"
                )
        summary_lines.append("")
    
    # 3. Market Movers
    print("Fetching market movers...")
    movers = await fmp_service.get_market_movers()
    if movers:
        summary_lines.append("🔥 MARKET MOVERS")
        summary_lines.append("-" * 40)
        
        if movers.get("gainers"):
            summary_lines.append("Top Gainers:")
            for g in movers["gainers"][:3]:
                summary_lines.append(
                    f"  {g.get('symbol', 'N/A'):6} +{g.get('changePercent', 0):.1f}%  "
                    f"${g.get('price', 0):.2f}"
                )
            summary_lines.append("")
        
        if movers.get("losers"):
            summary_lines.append("Top Losers:")
            for l in movers["losers"][:3]:
                summary_lines.append(
                    f"  {l.get('symbol', 'N/A'):6} {l.get('changePercent', 0):.1f}%  "
                    f"${l.get('price', 0):.2f}"
                )
            summary_lines.append("")
        
        if movers.get("most_active"):
            summary_lines.append("Most Active:")
            for a in movers["most_active"][:3]:
                volume = a.get('volume')
                if volume:
                    vol_millions = volume / 1_000_000
                    vol_str = f"Vol: {vol_millions:.1f}M"
                else:
                    vol_str = "Vol: N/A"
                summary_lines.append(
                    f"  {a.get('symbol', 'N/A'):6} ${a.get('price', 0):.2f}  {vol_str}"
                )
            summary_lines.append("")
    
    # 4. Sector Performance
    print("Fetching sector performance...")
    sectors = await fmp_service.get_sector_performance()
    if sectors.get("sectors"):
        summary_lines.append("📊 SECTOR PERFORMANCE")
        summary_lines.append("-" * 40)
        
        # Sort sectors by performance
        sorted_sectors = sorted(
            sectors["sectors"], 
            key=lambda x: float(x.get("changePercent", 0)) if x.get("changePercent") else 0,
            reverse=True
        )
        
        for sector in sorted_sectors[:10]:  # Top 10 sectors
            if sector.get("sector"):
                change = float(sector.get("changePercent", 0)) if sector.get("changePercent") else 0
                bar_length = int(abs(change) * 5)  # Scale for visual
                bar = "█" * min(bar_length, 20)  # Cap at 20 chars
                
                if change > 0:
                    summary_lines.append(f"  {sector['sector'][:20]:20} +{change:.2f}% {bar}")
                else:
                    summary_lines.append(f"  {sector['sector'][:20]:20} {change:.2f}% {bar}")
        summary_lines.append("")
    
    # 5. Economic Calendar
    print("Fetching economic calendar...")
    calendar = await fmp_service.get_economic_calendar()
    if calendar.get("high_impact"):
        summary_lines.append("📅 HIGH IMPACT EVENTS (Today/Tomorrow)")
        summary_lines.append("-" * 40)
        for event in calendar["high_impact"][:5]:
            summary_lines.append(
                f"• {event.get('event', 'N/A')} ({event.get('country', 'N/A')})"
            )
            if event.get('actual') and event.get('estimate'):
                summary_lines.append(
                    f"  Actual: {event['actual']} | "
                    f"Est: {event['estimate']} | "
                    f"Prev: {event.get('previous', 'N/A')}"
                )
        summary_lines.append("")
    
    # 6. 8-Hour Performance Summary
    print("Fetching 8-hour performance...")
    past_8h = await fmp_service.get_past_8_hours_summary(["SPY", "QQQ", "BTCUSD"])
    if past_8h:
        summary_lines.append("⏰ PAST 8 HOURS")
        summary_lines.append("-" * 40)
        # Split the summary into individual lines
        for line in past_8h.split(" | "):
            summary_lines.append(line)
        summary_lines.append("")
    
    # Add footer
    summary_lines.append("=" * 60)
    summary_lines.append("Generated by MarketMotion - FMP Service")
    summary_lines.append("Data provided by Financial Modeling Prep")
    summary_lines.append("=" * 60)
    
    # Join all lines
    full_summary = "\n".join(summary_lines)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_summary_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(full_summary)
    
    print(f"\n✅ Market summary saved to: {filename}")
    print(f"   Lines: {len(summary_lines)}")
    print(f"   Size: {len(full_summary)} characters")
    
    # Also print to console
    print("\n" + "=" * 60)
    print("PREVIEW (First 50 lines):")
    print("=" * 60)
    for line in summary_lines[:50]:
        print(line)
    
    if len(summary_lines) > 50:
        print("\n... (See full file for complete summary)")

if __name__ == "__main__":
    asyncio.run(main())