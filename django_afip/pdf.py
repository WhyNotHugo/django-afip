import logging
import mimetypes

from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.loader import get_template
from weasyprint import default_url_fetcher, HTML

from . import models

logger = logging.getLogger(__name__)


def staticfile_url_fetcher(url):
    """
    Returns files when the staticfiles app does not returns a relative path to
    a file.
    """
    if url.startswith('/'):
        base_url = staticfiles_storage.base_url
        filename = url.replace(base_url, '', 1)

        filepath = find(filename)
        with open(filepath, 'rb') as file_:
            data = file_.read()
        return dict(
            string=data,
            mime_type=mimetypes.guess_type(url)[0],
        )
    else:
        return default_url_fetcher(url)


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

    html = get_template('receipts/code_{}.html'.format(
        pdf.receipt.receipt_type.code,
    )).render(dict(
        pdf=pdf,
        taxpayer=pdf.receipt.point_of_sales.owner,
    ))

    if force_html:
        return html
    else:
        return HTML(
            string=html,
            base_url='not-used://',
            url_fetcher=staticfile_url_fetcher,
        ).write_pdf(
            target=target,
        )
