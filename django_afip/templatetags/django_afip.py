import re

from django import template

register = template.Library()


@register.filter
def format_cuit(cuit):
    numbers = re.sub("[^\\d]", "", str(cuit))
    if len(numbers) != 11:
        return cuit
    return f"{numbers[0:2]}-{numbers[2:10]}-{numbers[10:11]}"
