#!/usr/bin/env python3
"""
Test script for economic calendar date logic.
Tests the proper weekday range calculation for economic calendar.

Logic:
- Sunday: Monday-Friday of upcoming week
- Monday: Monday-Friday of current week (including today)  
- Tuesday: Tuesday-Friday of current week (including today)
- Wednesday: Wednesday-Friday of current week (including today)
- Thursday: Thursday-Friday of current week (including today)
- Friday: Friday of current week through Friday of next week
- Saturday: Monday-Friday of upcoming week
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
    
    print(f"Today is: {now.strftime('%A, %Y-%m-%d')} (weekday={current_weekday})")
    
    if current_weekday == 6:  # Sunday
        # Get Monday-Friday of upcoming week
        days_until_monday = 1
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        print("📅 Sunday logic: Getting Monday-Friday of upcoming week")
        
    elif current_weekday == 5:  # Saturday  
        # Get Monday-Friday of upcoming week
        days_until_monday = 2
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        print("📅 Saturday logic: Getting Monday-Friday of upcoming week")
        
    elif current_weekday == 4:  # Friday
        # Get Friday of current week through Friday of next week
        start_date = now  # Start with today (Friday)
        end_date = now + timedelta(days=7)  # Next Friday (7 days later)
        print("📅 Friday logic: Getting Friday of current week through Friday of next week")
        
    else:  # Monday (0) through Thursday (3)
        # Get remaining days of current week (including today)
        start_date = now
        days_until_friday = 4 - current_weekday
        end_date = now + timedelta(days=days_until_friday)
        print(f"📅 Weekday logic: Getting {now.strftime('%A')}-Friday of current week")
    
    return start_date, end_date

def test_date_logic():
    """Test the date logic for different days of the week."""
    print("=" * 60)
    print("🗓️  ECONOMIC CALENDAR DATE LOGIC TEST")
    print("=" * 60)
    
    # Test current day
    start_date, end_date = get_economic_calendar_date_range()
    
    print(f"\n📊 Date Range Calculated:")
    print(f"   Start: {start_date.strftime('%A, %Y-%m-%d')}")
    print(f"   End:   {end_date.strftime('%A, %Y-%m-%d')}")
    print(f"   Days:  {(end_date - start_date).days + 1} business days")
    
    # Show what days this covers
    current_date = start_date
    days_covered = []
    while current_date <= end_date:
        days_covered.append(current_date.strftime('%A %m/%d'))
        current_date += timedelta(days=1)
    
    print(f"\n📋 Days Covered: {', '.join(days_covered)}")
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

async def test_economic_calendar_api():
    """Test the FMP economic calendar API with the calculated dates."""
    print("\n" + "=" * 60)
    print("🏛️  TESTING FMP ECONOMIC CALENDAR API")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    if not os.getenv('FMP_API_KEY'):
        print("❌ FMP_API_KEY not found in environment")
        return False
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    # Get date range
    start_date_str, end_date_str = test_date_logic()
    
    print(f"\n🔍 Fetching economic calendar from {start_date_str} to {end_date_str}...")
    
    try:
        # Test the economic calendar method (now with await)
        result = await fmp_service.get_economic_calendar(start_date_str, end_date_str)
        events = result.get('events', []) if isinstance(result, dict) else result
        
        print(f"✅ Successfully fetched {len(events)} economic events")
        
        if events:
            print(f"\n📈 Sample Events (first 5):")
            for i, event in enumerate(events[:5]):
                date = event.get('date', 'Unknown')
                event_name = event.get('event', 'Unknown Event')
                country = event.get('country', 'Unknown')
                impact = event.get('impact', 'Unknown')
                print(f"   {i+1}. {date} - {country} - {event_name} ({impact} impact)")
        else:
            print("⚠️  No economic events found for this date range")
            print("   This could be normal if there are no major releases scheduled")
        
    except Exception as e:
        print(f"❌ Error fetching economic calendar: {str(e)}")
        return False
    
    return True

def test_different_weekdays():
    """Test the logic for different days of the week by simulating different dates."""
    print("\n" + "=" * 60)
    print("🧪 TESTING LOGIC FOR ALL WEEKDAYS")
    print("=" * 60)
    
    # Test dates for each day of the week
    test_dates = [
        datetime(2025, 8, 18),  # Monday
        datetime(2025, 8, 19),  # Tuesday  
        datetime(2025, 8, 20),  # Wednesday
        datetime(2025, 8, 21),  # Thursday
        datetime(2025, 8, 22),  # Friday
        datetime(2025, 8, 23),  # Saturday
        datetime(2025, 8, 17),  # Sunday (today)
    ]
    
    for test_date in test_dates:
        weekday = test_date.weekday()
        weekday_name = test_date.strftime('%A')
        
        print(f"\n🗓️  Testing: {weekday_name} {test_date.strftime('%Y-%m-%d')}")
        
        # Simulate logic for this day
        if weekday == 6:  # Sunday
            days_until_monday = 1
            start = test_date + timedelta(days=days_until_monday)
            end = start + timedelta(days=4)
            logic = "Monday-Friday of upcoming week"
        elif weekday == 5:  # Saturday
            days_until_monday = 2
            start = test_date + timedelta(days=days_until_monday)
            end = start + timedelta(days=4)
            logic = "Monday-Friday of upcoming week"
        elif weekday == 4:  # Friday
            start = test_date  # Start with Friday
            end = test_date + timedelta(days=7)  # Next Friday (7 days later)
            logic = "Friday of current week through Friday of next week"
        else:  # Monday-Thursday
            start = test_date
            days_until_friday = 4 - weekday
            end = test_date + timedelta(days=days_until_friday)
            logic = f"{weekday_name}-Friday of current week"
        
        print(f"   Logic: {logic}")
        print(f"   Range: {start.strftime('%A %m/%d')} to {end.strftime('%A %m/%d')}")

async def main():
    """Main async function to run all tests."""
    print("🚀 Starting Economic Calendar Date Logic Tests...\n")
    
    # Test 1: Current day logic
    test_date_logic()
    
    # Test 2: All weekdays simulation
    test_different_weekdays()
    
    # Test 3: API call with real data
    success = await test_economic_calendar_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed - check the output above")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())