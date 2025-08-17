"""
Timezone utilities for consistent EST/EDT handling across all briefing scripts
"""
from datetime import datetime
from zoneinfo import ZoneInfo


def get_est_time() -> datetime:
    """Get current time in Eastern Time (EST/EDT)"""
    return datetime.now(ZoneInfo('US/Eastern'))


def is_weekend_est() -> bool:
    """Check if it's weekend in Eastern Time (Saturday = 5, Sunday = 6)"""
    est_time = get_est_time()
    return est_time.weekday() in [5, 6]


def is_weekday_est() -> bool:
    """Check if it's weekday in Eastern Time (Monday = 0, Friday = 4)"""
    return not is_weekend_est()


def get_est_weekday_name() -> str:
    """Get the current weekday name in EST"""
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    est_time = get_est_time()
    return day_names[est_time.weekday()]


def format_est_timestamp() -> str:
    """Format current EST time for briefing timestamps"""
    est_time = get_est_time()
    return est_time.strftime("%Y%m%d_%H%M%S")


def format_est_display() -> str:
    """Format current EST time for display in briefings"""
    est_time = get_est_time()
    return est_time.strftime('%B %d, %Y at %I:%M %p ET')