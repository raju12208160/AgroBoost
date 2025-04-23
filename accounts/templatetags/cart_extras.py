from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0  # In case of invalid values
