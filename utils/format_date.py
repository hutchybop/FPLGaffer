from datetime import datetime
from zoneinfo import ZoneInfo


def format_date_with_ordinal():
    """
    Format current date with ordinal suffix.
    Args:
        None
    Returns:
        str: formatted date string (e.g., "Mon 25th Nov")
    """
    current_date = datetime.now()
    day = current_date.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return current_date.strftime(f"%a {day}{suffix} %b")


def format_uk_deadline(deadline_time):
    """
    Format FPL API deadline time into UK local time.
    Args:
        deadline_time: ISO datetime string from FPL API (UTC, e.g. ...Z)
    Returns:
        str: formatted UK datetime string (e.g., "Fri 10 Apr 2026, 18:30 BST")
    """
    if not deadline_time:
        return ""

    dt_utc = datetime.fromisoformat(deadline_time.replace("Z", "+00:00"))
    dt_uk = dt_utc.astimezone(ZoneInfo("Europe/London"))
    return dt_uk.strftime("%a %d %b %Y, %H:%M %Z")
