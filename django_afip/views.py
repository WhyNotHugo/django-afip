from __future__ import annotations

import warnings

from django.utils.functional import cached_property
from django_renderpdf.views import PDFView

from django_afip import models
from django_afip.pdf import PdfBuilder


class ReceiptPDFView(PDFView):
    #: The PDF Builder class to use for generating PDF files.
    #:
    #: Set this to a custom subclass if you need custom behaviour for your PDF files.
    builder_class = PdfBuilder

    @cached_property
    def receipt(self) -> models.Receipt:
        """Returns the receipt.

        Returns the same in-memory instance during the whole request."""

        return models.Receipt.objects.select_related(
            "receipt_type",
            "point_of_sales",
        ).get(
            pk=self.kwargs["pk"],
        )

    @cached_property
    def builder(self) -> PdfBuilder:
        """Returns the pdf builder.

        Returns the same in-memory instance during the whole request."""

        return self.builder_class(self.receipt)

    @property
    def download_name(self) -> str:
        """Return the filename to be used when downloading this receipt."""
        return f"{self.receipt.formatted_number}.pdf"

    def get_template_names(self) -> list[str]:
        """Return the templates use to render the Receipt PDF.

        See :meth:`~.PdfBuilder.get_template_names` for exact implementation details.
        """
        return self.builder.get_template_names()

    @staticmethod
    def get_context_for_pk(pk: int, *args, **kwargs) -> dict:
        """Returns the context for a receipt.

        Note that this uses ``PdfBuilder`` and not ``self.builder_class`` due to legacy
        reasons.

        .. deprecated:: 12.0

            This method is deprecated, use :meth:`~.PdfBuilder.get_context` instead.
        """
        warnings.warn(
            "ReceiptPDFView.get_context_for_pk is deprecated; "
            "use PdfBuilder.get_context instead",
            DeprecationWarning,
            stacklevel=2,
        )
        receipt = models.Receipt.objects.get(pk=pk)
        return PdfBuilder(receipt).get_context()

    def get_context_data(self, pk: int, **kwargs) -> dict:
        context = super().get_context_data(pk=pk, **kwargs)
        context.update(self.builder.get_context())
        return context
