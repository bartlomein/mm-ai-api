#!/usr/bin/env python3
"""
Show Economic Calendar Script
Displays what the economic calendar would look like with the new Friday logic.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.fmp_service import FMPService

def get_economic_calendar_date_range():
    """Calculate the correct date range for economic calendar based on current day."""
    now = datetime.now()
    current_weekday = now.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    
    if current_weekday == 6:  # Sunday
        # Get Monday-Friday of upcoming week
        days_until_monday = 1
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        period_desc = "Monday-Friday of upcoming week"
        
    elif current_weekday == 5:  # Saturday  
        # Get Monday-Friday of upcoming week
        days_until_monday = 2
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        period_desc = "Monday-Friday of upcoming week"
        
    elif current_weekday == 4:  # Friday
        # Get Friday of current week through Friday of next week
        start_date = now  # Start with today (Friday)
        end_date = now + timedelta(days=7)  # Next Friday (7 days later)
        period_desc = "Friday of current week through Friday of next week"
        
    else:  # Monday (0) through Thursday (3)
        # Get remaining days of current week (including today)
        start_date = now
        days_until_friday = 4 - current_weekday
        end_date = now + timedelta(days=days_until_friday)
        period_desc = f"{now.strftime('%A')}-Friday of current week"
    
    return start_date, end_date, period_desc

def format_event_for_display(event):
    """Format an economic event for nice display."""
    date = event.get('date', 'Unknown')
    time = event.get('time', '')
    country = event.get('country', 'Unknown')
    event_name = event.get('event', 'Unknown Event')
    impact = event.get('impact', 'Unknown')
    actual = event.get('actual', '')
    forecast = event.get('forecast', '')
    previous = event.get('previous', '')
    
    # Format date nicely
    try:
        if 'T' in date:
            dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = dt.strftime('%A, %B %d')
        if time:
            formatted_date += f" at {time}"
    except:
        formatted_date = date
    
    # Format impact with emoji
    impact_emoji = {
        'High': '🔴',
        'Medium': '🟡', 
        'Low': '🟢'
    }.get(impact, '⚪')
    
    # Build the display string
    display = f"{impact_emoji} {formatted_date} - {country} - {event_name}"
    
    # Add data if available
    data_parts = []
    if actual:
        data_parts.append(f"Actual: {actual}")
    if forecast:
        data_parts.append(f"Forecast: {forecast}")
    if previous:
        data_parts.append(f"Previous: {previous}")
    
    if data_parts:
        display += f" ({', '.join(data_parts)})"
    
    return display

async def show_economic_calendar():
    """Show the economic calendar with the new logic."""
    print("=" * 80)
    print("📅 ECONOMIC CALENDAR PREVIEW")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    if not os.getenv('FMP_API_KEY'):
        print("❌ FMP_API_KEY not found in environment")
        return
    
    # Get current date info
    now = datetime.now()
    print(f"Current Date: {now.strftime('%A, %B %d, %Y')}")
    print(f"Current Time: {now.strftime('%I:%M %p')}")
    
    # Calculate date range
    start_date, end_date, period_desc = get_economic_calendar_date_range()
    
    print(f"\n📊 Calendar Period: {period_desc}")
    print(f"Date Range: {start_date.strftime('%A, %B %d')} to {end_date.strftime('%A, %B %d, %Y')}")
    print(f"Total Days: {(end_date - start_date).days + 1}")
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    print(f"\n🔍 Fetching economic events...")
    
    try:
        # Fetch economic calendar
        result = await fmp_service.get_economic_calendar(
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        events = result.get('events', []) if isinstance(result, dict) else result
        
        if not events:
            print("⚠️  No economic events found for this period")
            return
        
        print(f"✅ Found {len(events)} total events")
        
        # Filter for high impact events only
        high_impact = [e for e in events if e.get('impact') == 'High']
        
        print(f"\n📈 Economic Events Found: {len(high_impact)} events")
        
        # Show high impact events in detail
        print(f"\n🔴 MAJOR ECONOMIC EVENTS:")
        print("-" * 80)
        if high_impact:
            for event in high_impact:
                print(f"   {format_event_for_display(event)}")
        else:
            print("   No major economic events scheduled")
        
        # Show what would go in briefing
        print(f"\n📝 WHAT WOULD APPEAR IN BRIEFING:")
        print("=" * 80)
        
        if high_impact:
            print("Economic calendar for the week ahead...")
            print()
            briefing_events = []
            
            # Add high impact events only
            for event in high_impact[:5]:  # Top 5 high impact
                event_name = event.get('event', 'Unknown Event')
                country = event.get('country', 'Unknown')
                date = event.get('date', '')
                
                try:
                    if 'T' in date:
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(date, '%Y-%m-%d')
                    day_name = dt.strftime('%A')
                except:
                    day_name = "this week"
                
                briefing_events.append(f"{country} releases {event_name} on {day_name}")
            
            # Format for TTS
            if briefing_events:
                briefing_text = "Key economic releases include " + ", ".join(briefing_events[:3])
                if len(briefing_events) > 3:
                    briefing_text += f", and {len(briefing_events) - 3} other major indicators"
                briefing_text += "."
                
                print(briefing_text)
            
        else:
            print("Economic calendar for the week ahead...")
            print()
            print("No major economic releases scheduled for the period ahead.")
        
    except Exception as e:
        print(f"❌ Error fetching economic calendar: {str(e)}")

if __name__ == "__main__":
    asyncio.run(show_economic_calendar())