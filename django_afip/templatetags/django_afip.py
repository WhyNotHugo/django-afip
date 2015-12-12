from django import template

register = template.Library()


@register.filter
def receiptnumber(receipt):
    return "{:04d}-{:08d}".format(
        receipt.point_of_sales.number,
        receipt.receipt_number,
    )
