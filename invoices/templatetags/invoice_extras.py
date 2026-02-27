from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def smart_number(value):
    """Format number to remove trailing zeros (60.0 -> 60, 60.5 -> 60.5)"""
    try:
        num = Decimal(str(value))
        # If it's a whole number, return as int
        if num == num.to_integral_value():
            return int(num)
        # Otherwise return with decimal places
        return float(num)
    except (ValueError, TypeError, AttributeError):
        return value
