from datetime import datetime

PREDICATES = {
    "contains": lambda field, value: value.lower() in (field or "").lower(),
    "does_not_contain": lambda field, value: value.lower() not in (field or "").lower(),
    "equals": lambda field, value: (field or "").lower() == value.lower(),
    "does_not_equal": lambda field, value: (field or "").lower() != value.lower(),
    "starts_with": lambda field, value: (field or "").lower().startswith(value.lower()),
    "ends_with": lambda field, value: (field or "").lower().endswith(value.lower()),
    "less_than_days": lambda field, value: _is_less_than_days(field, value),
    "greater_than_days": lambda field, value: _is_greater_than_days(field, value)
}

def _is_less_than_days(field, value):
    """Check if email was received less than X days ago"""
    if not field:
        return False
    try:
        date_obj = datetime.strptime(field, "%a, %d %b %Y %H:%M:%S %z")
        today = datetime.now(date_obj.tzinfo)
        days_diff = (today - date_obj).days
        return days_diff < int(value)
    except (ValueError, TypeError):
        return False

def _is_greater_than_days(field, value):
    """Check if email was received more than X days ago"""
    if not field:
        return False
    try:
        date_obj = datetime.strptime(field, "%a, %d %b %Y %H:%M:%S %z")
        today = datetime.now(date_obj.tzinfo)
        days_diff = (today - date_obj).days
        return days_diff > int(value)
    except (ValueError, TypeError):
        return False
