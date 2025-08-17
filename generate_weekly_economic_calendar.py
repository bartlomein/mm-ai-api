#!/usr/bin/env python3
"""
Generate this week's upcoming high impact economic calendar items
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.fmp_service import FMPService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_calendar_dates():
    """Get dates for economic calendar based on current day of week
    - Always show current week (Monday to Sunday)
    - If Wednesday or later, also include next week
    """
    today = datetime.now()
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # Get Monday of current week
    monday_this_week = today - timedelta(days=current_weekday)
    
    # Get Sunday of current week
    sunday_this_week = monday_this_week + timedelta(days=6)
    
    # If it's Wednesday (2) or later, extend to next Sunday
    if current_weekday >= 2:  # Wednesday = 2
        # Include next week too (extend to next Sunday)
        end_date = sunday_this_week + timedelta(days=7)
    else:
        # Just this week
        end_date = sunday_this_week
    
    return monday_this_week.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), current_weekday >= 2

def format_event(event: Dict[str, Any]) -> str:
    """Format a single economic event for display"""
    lines = []
    
    # Event header
    lines.append(f"📅 {event.get('date', 'N/A')} - {event.get('event', 'Unknown Event')}")
    lines.append(f"   Country: {event.get('country', 'N/A')}")
    
    # Show actual vs estimate if available
    actual = event.get('actual')
    estimate = event.get('estimate')
    previous = event.get('previous')
    
    if actual or estimate or previous:
        values = []
        if actual:
            values.append(f"Actual: {actual}")
        if estimate:
            values.append(f"Estimate: {estimate}")
        if previous:
            values.append(f"Previous: {previous}")
        lines.append(f"   {' | '.join(values)}")
    
    return "\n".join(lines)

def group_events_by_date(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group events by date"""
    grouped = {}
    for event in events:
        date = event.get('date', 'Unknown')
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(event)
    return grouped

async def generate_weekly_calendar():
    """Generate economic calendar for important events"""
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    # Get calendar dates
    start_date, end_date, includes_next_week = get_calendar_dates()
    
    # Determine title based on period
    if includes_next_week:
        title = "THIS WEEK + NEXT WEEK ECONOMIC CALENDAR"
        period_desc = f"{start_date} to {end_date} (This Week + Next Week)"
    else:
        title = "THIS WEEK'S ECONOMIC CALENDAR"
        period_desc = f"{start_date} to {end_date} (This Week)"
    
    # Get current day name
    today = datetime.now()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day = day_names[today.weekday()]
    
    print("=" * 60)
    print(f"📊 {title}")
    print("=" * 60)
    print(f"Today: {current_day}, {today.strftime('%B %d, %Y')}")
    print(f"Period: {period_desc}")
    print("-" * 60)
    
    try:
        # Fetch economic calendar for the week
        logger.info(f"Fetching economic calendar from {start_date} to {end_date}")
        calendar = await fmp_service.get_economic_calendar(
            from_date=start_date,
            to_date=end_date
        )
        
        if not calendar:
            print("❌ No calendar data available")
            return
        
        # Get high impact events and filter out past events
        high_impact_events = calendar.get("high_impact", [])
        
        # Filter out events that have already occurred (only keep future events)
        now = datetime.now()
        future_events = []
        for event in high_impact_events:
            event_date_str = event.get('date', '')
            try:
                # Parse the event date
                if ' ' in event_date_str:
                    event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S")
                else:
                    # If no time, assume end of day
                    event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d")
                    event_datetime = event_datetime.replace(hour=23, minute=59)
                
                # Only include future events
                if event_datetime >= now:
                    future_events.append(event)
            except:
                # If date parsing fails, include the event
                future_events.append(event)
        
        high_impact_events = future_events
        
        if not high_impact_events:
            print("ℹ️ No upcoming economic events remaining this period")
            
            # Show all upcoming events if no high impact ones
            all_events = calendar.get("events", [])
            # Filter past events from all events too
            future_all_events = []
            for event in all_events:
                event_date_str = event.get('date', '')
                try:
                    if ' ' in event_date_str:
                        event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d")
                        event_datetime = event_datetime.replace(hour=23, minute=59)
                    
                    if event_datetime >= now:
                        future_all_events.append(event)
                except:
                    future_all_events.append(event)
            
            all_events = future_all_events
            if all_events:
                print(f"\nFound {len(all_events)} total events this week")
                print("\nShowing first 10 events:")
                print("-" * 60)
                for event in all_events[:10]:
                    print(format_event(event))
                    print()
        else:
            print(f"🎯 Found {len(high_impact_events)} upcoming events")
            print("=" * 60)
            
            # Group by date
            grouped = group_events_by_date(high_impact_events)
            
            # Sort dates
            sorted_dates = sorted(grouped.keys())
            
            # Get Sunday of this week for separation
            today = datetime.now()
            monday_this_week = today - timedelta(days=today.weekday())
            sunday_this_week = monday_this_week + timedelta(days=6)
            
            # Separate this week and next week events
            this_week_shown = False
            next_week_shown = False
            
            for date in sorted_dates:
                # Parse and format date nicely
                try:
                    # Handle both date and datetime formats
                    if ' ' in date:
                        date_obj = datetime.strptime(date.split(' ')[0], "%Y-%m-%d")
                    else:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                    day_name = date_obj.strftime("%A")
                    formatted_date = date_obj.strftime("%B %d, %Y")
                except ValueError:
                    # Fallback if date parsing fails
                    date_obj = None
                    day_name = ""
                    formatted_date = date
                
                # Check if we need to show week separator
                if date_obj:
                    if date_obj <= sunday_this_week and not this_week_shown:
                        print("\n" + "=" * 60)
                        print("📅 THIS WEEK")
                        print("=" * 60)
                        this_week_shown = True
                    elif date_obj > sunday_this_week and not next_week_shown:
                        print("\n" + "=" * 60)
                        print("📅 NEXT WEEK")
                        print("=" * 60)
                        next_week_shown = True
                
                print(f"\n📆 {day_name}, {formatted_date}")
                print("-" * 40)
                
                for event in grouped[date]:
                    print(format_event(event))
                    print()
        
        # Summary statistics
        print("=" * 60)
        print("📈 SUMMARY STATISTICS")
        print("-" * 60)
        
        all_events = calendar.get("events", [])
        
        # Count by country
        country_counts = {}
        for event in all_events:
            country = event.get('country', 'Unknown')
            country_counts[country] = country_counts.get(country, 0) + 1
        
        print(f"Total Events: {len(all_events)}")
        print(f"High Impact Events: {len(high_impact_events)}")
        print(f"\nEvents by Country:")
        for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {country}: {count} events")
        
        # Count by impact level
        impact_counts = {}
        for event in all_events:
            impact = event.get('impact', 'Unknown')
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
        
        print(f"\nEvents by Impact Level:")
        for impact, count in sorted(impact_counts.items()):
            print(f"  • {impact}: {count} events")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error generating calendar: {e}")
        print(f"❌ Error: {e}")

async def generate_us_only_calendar():
    """Generate calendar for US economic events"""
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    # Get calendar dates
    start_date, end_date, includes_next_week = get_calendar_dates()
    
    # Determine title based on period
    if includes_next_week:
        period_desc = f"{start_date} to {end_date} (This Week + Next Week)"
    else:
        period_desc = f"{start_date} to {end_date} (This Week)"
    
    print("\n" + "=" * 60)
    print("🇺🇸 US ECONOMIC CALENDAR")
    print("=" * 60)
    print(f"Period: {period_desc}")
    print("-" * 60)
    
    try:
        # Fetch economic calendar for the week with US filter
        logger.info(f"Fetching US economic calendar from {start_date} to {end_date}")
        calendar = await fmp_service.get_economic_calendar(
            from_date=start_date,
            to_date=end_date,
            country="US"
        )
        
        if not calendar:
            print("❌ No calendar data available")
            return
        
        # Get high impact events and filter out past events
        high_impact_events = calendar.get("high_impact", [])
        
        # Filter out events that have already occurred
        now = datetime.now()
        future_events = []
        for event in high_impact_events:
            event_date_str = event.get('date', '')
            try:
                if ' ' in event_date_str:
                    event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d %H:%M:%S")
                else:
                    event_datetime = datetime.strptime(event_date_str, "%Y-%m-%d")
                    event_datetime = event_datetime.replace(hour=23, minute=59)
                
                if event_datetime >= now:
                    future_events.append(event)
            except:
                future_events.append(event)
        
        high_impact_events = future_events
        
        if high_impact_events:
            print(f"🎯 Found {len(high_impact_events)} upcoming US events")
            print("=" * 60)
            
            # Group by date for week separation
            grouped = group_events_by_date(high_impact_events)
            sorted_dates = sorted(grouped.keys())
            
            # Get Sunday of this week for separation
            today = datetime.now()
            monday_this_week = today - timedelta(days=today.weekday())
            sunday_this_week = monday_this_week + timedelta(days=6)
            
            this_week_shown = False
            next_week_shown = False
            
            for date in sorted_dates:
                # Parse date
                try:
                    if ' ' in date:
                        date_obj = datetime.strptime(date.split(' ')[0], "%Y-%m-%d")
                    else:
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                    day_name = date_obj.strftime("%A")
                    formatted_date = date_obj.strftime("%B %d, %Y")
                except ValueError:
                    date_obj = None
                    day_name = ""
                    formatted_date = date
                
                # Check if we need to show week separator
                if date_obj:
                    if date_obj <= sunday_this_week and not this_week_shown:
                        print("\n" + "=" * 60)
                        print("📅 THIS WEEK")
                        print("=" * 60)
                        this_week_shown = True
                    elif date_obj > sunday_this_week and not next_week_shown:
                        print("\n" + "=" * 60)
                        print("📅 NEXT WEEK")
                        print("=" * 60)
                        next_week_shown = True
                
                print(f"\n📆 {day_name}, {formatted_date}")
                print("-" * 40)
                
                for event in grouped[date]:
                    print(format_event(event))
                    print()
        else:
            print("ℹ️ No upcoming US events scheduled")
        
    except Exception as e:
        logger.error(f"Error generating US calendar: {e}")
        print(f"❌ Error: {e}")

async def main():
    """Main execution"""
    
    # Generate full weekly calendar
    await generate_weekly_calendar()
    
    # Also generate US-only high impact events
    await generate_us_only_calendar()

if __name__ == "__main__":
    asyncio.run(main())