from django import template
from django import template

register = template.Library()

@register.filter
def get_range(value):
    return range(value)



@register.filter
def round_number(value):
    return round(value)

