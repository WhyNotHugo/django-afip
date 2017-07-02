import re
import warnings

from django import template

register = template.Library()


@register.filter
def receiptnumber(receipt):
    warnings.warn(
        'Use receipt.formatted_number instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return receipt.formatted_number


@register.filter
def format_cuit(cuit):
    numbers = re.sub('[^\\d]', '', str(cuit))
    if len(numbers) != 11:
        return cuit
    return '{}-{}-{}'.format(
        numbers[0:2],
        numbers[2:10],
        numbers[10:11]
    )
