from django.contrib.staticfiles.finders import find
from django.template.loader import get_template
from weasyprint import HTML, CSS

from . import models


def generate_receipt_pdf(pk, target, force_html=False):

    pdf = models.ReceiptPDF.objects.select_related(
        'receipt',
        'receipt__receipt_type',
        'receipt__document_type',
        'receipt__validation',
        'receipt__point_of_sales',
        'receipt__point_of_sales__owner',
    ).prefetch_related(
        'receipt__entries',
    ).get(
        receipt__pk=pk
    )

    html = get_template('django_afip/invoice.html').render(dict(
        pdf=pdf,
        taxpayer=pdf.receipt.point_of_sales.owner,
    ))

    css = CSS(
        find('django_afip/invoice.css')
    )

    if force_html:
        return html
    else:
        return HTML(
            string=html,
            # url_fetcher=url_fetcher,
        ).write_pdf(
            target=target,
            stylesheets=(css,),
        )
