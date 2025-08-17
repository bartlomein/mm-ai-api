#!/usr/bin/env python3
"""
Debug Economic Calendar - Premium Briefing Issue
Diagnoses exactly why the economic calendar is failing in premium briefing
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.fmp_service import FMPService

def get_date_range_like_premium_briefing():
    """Replicate the EXACT date logic from premium briefing v2"""
    now = datetime.now()
    current_weekday = now.weekday()  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    
    print(f"Current time: {now}")
    print(f"Current weekday: {current_weekday} ({now.strftime('%A')})")
    
    if current_weekday == 6:  # Sunday
        # Get Monday-Friday of upcoming week
        days_until_monday = 1
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        logic = "Sunday: Monday-Friday of upcoming week"
        
    elif current_weekday == 5:  # Saturday  
        # Get Monday-Friday of upcoming week
        days_until_monday = 2
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # Friday
        logic = "Saturday: Monday-Friday of upcoming week"
        
    elif current_weekday == 4:  # Friday
        # Get Friday of current week through Friday of next week
        start_date = now  # Start with today (Friday)
        end_date = now + timedelta(days=7)  # Next Friday (7 days later)
        logic = "Friday: Current Friday through next Friday"
        
    else:  # Monday (0) through Thursday (3)
        # Get remaining days of current week (including today)
        start_date = now
        days_until_friday = 4 - current_weekday
        end_date = now + timedelta(days=days_until_friday)
        logic = f"{now.strftime('%A')}: Remaining days of current week"
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    print(f"Logic applied: {logic}")
    print(f"Date range: {start_date_str} to {end_date_str}")
    
    return start_date_str, end_date_str

async def test_fmp_service_call():
    """Test the exact FMP service call from premium briefing"""
    print("=" * 80)
    print("🔍 DEBUGGING PREMIUM BRIEFING ECONOMIC CALENDAR")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    if not os.getenv('FMP_API_KEY'):
        print("❌ FMP_API_KEY not found in environment")
        return False
    
    # Get date range using premium briefing logic
    start_date_str, end_date_str = get_date_range_like_premium_briefing()
    
    # Initialize FMP service (same as premium briefing)
    fmp_service = FMPService()
    
    print(f"\n🔧 Testing FMP Service Call...")
    print(f"   Using positional arguments: get_economic_calendar('{start_date_str}', '{end_date_str}')")
    
    try:
        # Call exactly like premium briefing (positional arguments)
        calendar_data = await fmp_service.get_economic_calendar(
            start_date_str,  # Use positional arguments
            end_date_str     # Use positional arguments
        )
        
        print(f"✅ FMP API call successful")
        print(f"   Raw response type: {type(calendar_data)}")
        
        if calendar_data:
            print(f"   Response keys: {list(calendar_data.keys()) if isinstance(calendar_data, dict) else 'Not a dict'}")
            
            if isinstance(calendar_data, dict) and "events" in calendar_data:
                all_events = calendar_data["events"]
                print(f"   Total events found: {len(all_events)}")
                
                # Filter exactly like premium briefing
                high_impact_events = []
                for event in all_events:
                    if event.get("impact") == "High":
                        high_impact_events.append(event)
                
                print(f"   High impact events: {len(high_impact_events)}")
                
                if high_impact_events:
                    print(f"\n📈 First 5 High Impact Events:")
                    for i, event in enumerate(high_impact_events[:5]):
                        date = event.get('date', 'Unknown')
                        event_name = event.get('event', 'Unknown Event')
                        country = event.get('country', 'Unknown')
                        impact = event.get('impact', 'Unknown')
                        print(f"   {i+1}. {date} - {country} - {event_name} ({impact})")
                
                # Test the premium briefing logic exactly
                events_by_day = {}
                for event in all_events:
                    if event.get("impact") == "High":
                        event_date_str = event.get("date", "").split("T")[0]
                        
                        try:
                            event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                            day_name = event_date.strftime("%A")
                            
                            if event_date_str not in events_by_day:
                                events_by_day[event_date_str] = {
                                    "day_name": day_name,
                                    "date": event_date_str,
                                    "events": []
                                }
                            
                            events_by_day[event_date_str]["events"].append(event)
                        except Exception as e:
                            print(f"   ⚠️ Date parsing error: {e}")
                
                # Create summary exactly like premium briefing
                if high_impact_events:
                    summary = f"Found {len(high_impact_events)} major economic events"
                    print(f"\n📊 Premium Briefing Summary: {summary}")
                else:
                    summary = "No major economic events scheduled"
                    print(f"\n❌ Premium Briefing Summary: {summary}")
                
                # Show what premium briefing would return
                result = {
                    "events_by_day": events_by_day,
                    "high_impact_events": high_impact_events,
                    "date_range": f"{start_date_str} to {end_date_str}",
                    "summary": summary
                }
                
                print(f"\n📦 Premium Briefing Return Object:")
                print(f"   events_by_day: {len(result['events_by_day'])} days")
                print(f"   high_impact_events: {len(result['high_impact_events'])} events")
                print(f"   summary: {result['summary']}")
                
                return result
                
            else:
                print(f"❌ No 'events' key in response")
                print(f"   Full response: {calendar_data}")
                return None
        else:
            print(f"❌ Empty response from FMP")
            return None
        
    except Exception as e:
        print(f"❌ Error calling FMP service: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def compare_with_working_script():
    """Compare with our working show_economic_calendar.py script"""
    print(f"\n" + "=" * 80)
    print("🆚 COMPARING WITH WORKING SCRIPT")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Use the working script's date logic
    now = datetime.now()
    current_weekday = now.weekday()
    
    if current_weekday == 6:  # Sunday
        days_until_monday = 1
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)
    elif current_weekday == 5:  # Saturday  
        days_until_monday = 2
        start_date = now + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)
    elif current_weekday == 4:  # Friday
        start_date = now
        end_date = now + timedelta(days=7)
    else:  # Monday-Thursday
        start_date = now
        days_until_friday = 4 - current_weekday
        end_date = now + timedelta(days=days_until_friday)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"Working script date range: {start_date_str} to {end_date_str}")
    
    # Initialize FMP service
    fmp_service = FMPService()
    
    try:
        # Call exactly like working script
        result = await fmp_service.get_economic_calendar(
            start_date_str,
            end_date_str
        )
        
        events = result.get('events', []) if isinstance(result, dict) else result
        high_impact = [e for e in events if e.get('impact') == 'High']
        
        print(f"Working script results:")
        print(f"   Total events: {len(events)}")
        print(f"   High impact: {len(high_impact)}")
        
        return len(high_impact) > 0
        
    except Exception as e:
        print(f"❌ Working script test failed: {str(e)}")
        return False

async def main():
    """Main diagnostic function"""
    print("🚀 Starting Economic Calendar Diagnostics...\n")
    
    # Test 1: Premium briefing approach
    premium_result = await test_fmp_service_call()
    
    # Test 2: Working script approach
    working_result = await compare_with_working_script()
    
    print(f"\n" + "=" * 80)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    if premium_result and len(premium_result.get('high_impact_events', [])) > 0:
        print("✅ Premium briefing approach WORKS")
        print(f"   Found {len(premium_result['high_impact_events'])} high impact events")
        print("   The issue is NOT in the FMP service call")
        print("   Check how the briefing text is generated from this data")
    else:
        print("❌ Premium briefing approach FAILS")
        print("   Issue is in the FMP service call or data processing")
    
    if working_result:
        print("✅ Working script approach WORKS")
    else:
        print("❌ Working script approach FAILS")
    
    if premium_result and working_result:
        print("\n💡 BOTH methods work - the issue is in briefing text generation")
    elif working_result and not premium_result:
        print("\n💡 Working script works but premium fails - different API calls")
    else:
        print("\n💡 Both methods fail - API or environment issue")

if __name__ == "__main__":
    asyncio.run(main())