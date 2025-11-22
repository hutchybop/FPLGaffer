from datetime import datetime


def format_date_with_ordinal():
    current_date = datetime.now()
    day = current_date.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    return current_date.strftime(f"%a {day}{suffix} %b")
