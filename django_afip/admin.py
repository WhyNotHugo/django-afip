from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING
from typing import TypedDict

from django.contrib import admin
from django.contrib import messages
from django.db.models import F
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_afip import exceptions
from django_afip import models
from django_afip.models import ReceiptQuerySet

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable
    from collections.abc import Sequence

    from django_stubs_ext import WithAnnotations

logger = logging.getLogger(__name__)


# TODO: Add an action to populate generic types.


@contextmanager
def catch_errors(
    self: admin.ModelAdmin,
    request: HttpRequest,
) -> Generator[None, None, None]:
    """Catches specific errors in admin actions and shows a friendly error."""
    try:
        yield
    except exceptions.CertificateExpired as e:
        logger.exception(e)
        self.message_user(
            request,
            _("The AFIP Taxpayer certificate has expired."),
            messages.ERROR,
        )
    except exceptions.UntrustedCertificate as e:
        logger.exception(e)
        self.message_user(
            request,
            _("The AFIP Taxpayer certificate is untrusted."),
            messages.ERROR,
        )
    except exceptions.CorruptCertificate as e:
        logger.exception(e)
        self.message_user(
            request,
            _("The AFIP Taxpayer certificate is corrupt."),
            messages.ERROR,
        )
    except exceptions.AuthenticationError as e:
        logger.exception(e)
        self.message_user(
            request,
            _("An unknown authentication error has ocurred: %s") % e,
            messages.ERROR,
        )


class VatInline(admin.TabularInline):
    model = models.Vat
    fields = (
        "vat_type",
        "base_amount",
        "amount",
    )
    extra = 1


class TaxInline(admin.TabularInline):
    model = models.Tax
    fields = (
        "tax_type",
        "description",
        "base_amount",
        "aliquot",
        "amount",
    )
    extra = 1


class ReceiptEntryInline(admin.TabularInline):
    model = models.ReceiptEntry
    fields = (
        "description",
        "quantity",
        "unit_price",
        "vat",
    )
    extra = 1


class ReceiptValidationInline(admin.StackedInline):
    model = models.ReceiptValidation
    readonly_fields = (
        "result",
        "processed_date",
        "cae",
        "cae_expiration",
        "observations",
    )
    extra = 0


class ReceiptStatusFilter(admin.SimpleListFilter):
    title = _("status")
    parameter_name = "status"

    VALIDATED = "validated"
    NOT_VALIDATED = "not_validated"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> Iterable[tuple[str, str]]:
        return (
            (self.VALIDATED, _("Validated")),
            (self.NOT_VALIDATED, _("Not validated")),
        )

    # TODO: generics
    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == self.VALIDATED:
            return queryset.filter(
                validation__result=models.ReceiptValidation.RESULT_APPROVED
            )
        if self.value() == self.NOT_VALIDATED:
            return queryset.exclude(
                validation__result=models.ReceiptValidation.RESULT_APPROVED
            )
        return queryset


class ReceiptTypeFilter(admin.SimpleListFilter):
    title = models.ReceiptType._meta.verbose_name
    parameter_name = "receipt_type"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> Iterable[tuple[str, str]]:
        return (
            (receipt_type.code, receipt_type.description)
            for receipt_type in models.ReceiptType.objects.filter(
                receipts__isnull=False,
            ).distinct()
        )

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value:
            queryset = queryset.filter(receipt_type__code=value)
        return queryset


@admin.register(models.Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    search_fields = ("receipt_number",)
    list_display = (
        "id",
        "receipt_type",
        "point_of_sales",
        "number",
        "issued_date",
        "friendly_total_amount",
        "validated",
        "pdf_link",
    )
    list_filter = (
        ReceiptStatusFilter,
        ReceiptTypeFilter,
    )
    autocomplete_fields = (
        "currency",
        "receipt_type",
        "related_receipts",
    )
    date_hierarchy = "issued_date"

    __related_fields = (
        "validated",
        "cae",
    )

    inlines = (
        VatInline,
        TaxInline,
        ReceiptEntryInline,
        ReceiptValidationInline,
    )
    ordering = ("-issued_date",)

    readonly_fields = __related_fields

    class Annotations(TypedDict):
        pdf_id: int
        validation_result: str

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "receipt_type",
                "point_of_sales",
            )
            .annotate(
                pdf_id=F("receiptpdf__id"),
                validation_result=F("validation__result"),
            )
        )

    @admin.display(description=_("receipt number"), ordering="receipt_number")
    def number(self, obj: models.Receipt) -> str | None:
        return obj.formatted_number

    @admin.display(description=_("total amount"))
    def friendly_total_amount(self, obj: models.Receipt) -> str:
        return "{:0.2f} ARS{}".format(
            obj.total_amount * obj.currency_quote,
            "*" if obj.currency_quote != 1 else "",
        )

    @admin.display(
        boolean=True,
        description=_("validated"),
        ordering="validation__result",
    )
    def validated(self, obj: WithAnnotations[models.Receipt, Annotations]) -> bool:
        validation_result = obj.validation_result
        return validation_result == models.ReceiptValidation.RESULT_APPROVED

    @admin.display(description=_("PDF"), ordering="receiptpdf__id")
    def pdf_link(self, obj: WithAnnotations[models.Receipt, Annotations]) -> str:
        if not obj.pdf_id:
            return format_html(
                '<a href="{}?receipt={}">{}</a>',
                reverse(self.admin_site.name + ":afip_receiptpdf_add"),
                obj.id,
                _("Create"),
            )
        return format_html(
            '<a href="{}">{}</a>',
            reverse(
                self.admin_site.name + ":afip_receiptpdf_change",
                args=(obj.pdf_id,),
            ),
            _("Edit"),
        )

    @admin.display(description=_("cae"), ordering="validation__cae")
    def cae(self, obj: models.Receipt) -> str:
        return obj.validation.cae

    @admin.action(description=_("Validate"))
    def validate(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.Receipt],
    ) -> None:
        assert isinstance(queryset, ReceiptQuerySet)  # required for mypy
        with catch_errors(self, request):
            errs = queryset.validate()

        if errs:
            self.message_user(
                request,
                _("Receipt validation failed: %s.") % errs,
                messages.ERROR,
            )

    actions = (validate,)


@admin.register(models.AuthTicket)
class AuthTicketAdmin(admin.ModelAdmin):
    list_display = (
        "unique_id",
        "owner",
        "service",
        "generated",
        "expires",
    )


@admin.register(models.TaxPayer)
class TaxPayerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cuit",
        "certificate_expiration",
    )

    @admin.action(description=_("Fetch points of sales"))
    def fetch_points_of_sales(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.TaxPayer],
    ) -> None:
        with catch_errors(self, request):
            poses = [
                pos
                for taxpayer in queryset.all()
                for pos in taxpayer.fetch_points_of_sales()
            ]

            created = len([pos for pos in poses if pos[1]])
            skipped = len(poses) - created

            self.message_user(
                request,
                message=(_("%d points of sales created.") % created),
                level=messages.SUCCESS,
            )
            self.message_user(
                request,
                message=(_("%d points of sales already existed.") % skipped),
                level=messages.WARNING,
            )

    @admin.action(description=_("Generate key"))
    def generate_key(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.TaxPayer],
    ) -> None:
        key_count = sum(t.generate_key() for t in queryset.all())

        if key_count == 1:
            message = _("Key generated successfully.")
            level = messages.SUCCESS
        elif key_count:
            message = _("%d keys generated successfully.") % key_count
            level = messages.SUCCESS
        else:
            message = _("No keys generated; Taxpayers already had keys.")
            level = messages.ERROR

        self.message_user(
            request,
            message=message,
            level=level,
        )

    @admin.action(description=_("Generate CSR"))
    def generate_csr(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.TaxPayer],
    ) -> HttpResponse | None:
        if queryset.count() > 1:
            self.message_user(
                request,
                message=_("Can only generate CSR for one taxpayer at a time."),
                level=messages.ERROR,
            )
            return None

        taxpayer = queryset.first()
        assert taxpayer is not None, "At least one taxpayer must be selected"
        if not taxpayer.key:
            taxpayer.generate_key()

        csr = taxpayer.generate_csr()
        filename = f"cuit-{taxpayer.cuit}-{int(datetime.now().timestamp())}.csr"

        response = HttpResponse(content_type="application/pkcs10")
        response["Content-Disposition"] = f"attachment; filename={filename}"

        response.write(csr.read())
        return response

    actions = (
        fetch_points_of_sales,
        generate_key,
        generate_csr,
    )


@admin.register(models.PointOfSales)
class PointOfSalesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "number",
        "issuance_type",
        "blocked",
        "drop_date",
    )


@admin.register(models.CurrencyType)
class CurrencyTypeAdmin(admin.ModelAdmin):
    search_fields = (
        "code",
        "description",
    )
    list_display = (
        "code",
        "description",
        "valid_from",
        "valid_to",
    )


@admin.register(models.ReceiptType)
class ReceiptTypeAdmin(admin.ModelAdmin):
    search_fields = (
        "code",
        "description",
    )
    list_display = (
        "code",
        "description",
        "valid_from",
        "valid_to",
    )


class ReceiptHasFileFilter(admin.SimpleListFilter):
    title = _("has file")
    parameter_name = "has_file"

    YES = "yes"
    NO = "no"

    def lookups(
        self,
        request: HttpRequest,
        model_admin: admin.ModelAdmin,
    ) -> Sequence[tuple[str, str]]:
        return (
            (self.YES, _("Yes")),
            (self.NO, _("No")),
        )

    def queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.ReceiptPDF],
    ) -> QuerySet[models.ReceiptPDF]:
        if self.value() == self.YES:
            return queryset.exclude(pdf_file="")
        if self.value() == self.NO:
            return queryset.filter(pdf_file="")
        return queryset


@admin.register(models.ReceiptPDF)
class ReceiptPDFAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_id",
        "taxpayer",
        "receipt",
        "client_name",
        "has_file",
    )
    list_filter = (
        ReceiptHasFileFilter,
        "receipt__point_of_sales__owner",
        "receipt__receipt_type",
    )
    raw_id_fields = ("receipt",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[models.ReceiptPDF]:
        return (
            super()
            .get_queryset(request)
            .select_related(
                "receipt",
                "receipt__point_of_sales__owner",
                "receipt__receipt_type",
            )
        )

    @admin.display(description=_("taxpayer"))
    def taxpayer(self, obj: models.ReceiptPDF) -> str:
        return str(obj.receipt.point_of_sales.owner)

    @admin.display(boolean=True, description=_("Has file"), ordering="pdf_file")
    def has_file(self, obj: models.ReceiptPDF) -> bool:
        return bool(obj.pdf_file)

    @admin.action(description=_("Generate pdf"))
    def generate_pdf(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.ReceiptPDF],
    ) -> None:
        for pdf in queryset:
            pdf.save_pdf()

    actions = (generate_pdf,)


@admin.register(models.ReceiptValidation)
class ReceiptValidationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "receipt_number",
        "successful",
        "cae",
        "processed_date",
    )

    raw_id_fields = ("receipt",)

    @admin.display(description=_("receipt number"), ordering="receipt_id")
    def receipt_number(self, obj: models.ReceiptValidation) -> str | None:
        return obj.receipt.formatted_number

    @admin.display(boolean=True, description=_("result"), ordering="result")
    def successful(self, obj: models.ReceiptValidation) -> bool:
        return obj.result == models.ReceiptValidation.RESULT_APPROVED


admin.site.register(models.ConceptType)
admin.site.register(models.DocumentType)
admin.site.register(models.VatType)
admin.site.register(models.TaxType)
admin.site.register(models.Observation)
