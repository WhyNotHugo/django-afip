import logging
from contextlib import contextmanager
from datetime import datetime

from django.contrib import admin
from django.contrib import messages
from django.db.models import F
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from django_afip import exceptions
from django_afip import models

logger = logging.getLogger(__name__)


# TODO: Add an action to populate generic types.


@contextmanager
def catch_errors(self, request):
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

    def lookups(self, request, model_admin):
        return (
            (self.VALIDATED, _("Validated")),
            (self.NOT_VALIDATED, _("Not validated")),
        )

    def queryset(self, request, queryset):
        if self.value() == self.VALIDATED:
            return queryset.filter(
                validation__result=models.ReceiptValidation.RESULT_APPROVED
            )
        if self.value() == self.NOT_VALIDATED:
            return queryset.exclude(
                validation__result=models.ReceiptValidation.RESULT_APPROVED
            )


class ReceiptTypeFilter(admin.SimpleListFilter):
    title = models.ReceiptType._meta.verbose_name
    parameter_name = "receipt_type"

    def lookups(self, request, model_admin):
        return (
            (receipt_type.code, receipt_type.description)
            for receipt_type in models.ReceiptType.objects.filter(
                receipts__isnull=False,
            ).distinct()
        )

    def queryset(self, request, queryset):
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

    __related_fields = [
        "validated",
        "cae",
    ]

    inlines = (
        VatInline,
        TaxInline,
        ReceiptEntryInline,
        ReceiptValidationInline,
    )
    ordering = ("-issued_date",)

    readonly_fields = __related_fields

    def get_queryset(self, request):
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
    def number(self, obj):
        return obj.formatted_number

    @admin.display(description=_("total amount"))
    def friendly_total_amount(self, obj):
        return "{:0.2f} ARS{}".format(
            obj.total_amount * obj.currency_quote,
            "*" if obj.currency_quote != 1 else "",
        )

    @admin.display(
        boolean=True,
        description=_("validated"),
        ordering="validation__result",
    )
    def validated(self, obj):
        return obj.validation_result == models.ReceiptValidation.RESULT_APPROVED

    @admin.display(description=_("PDF"), ordering="receiptpdf__id")
    def pdf_link(self, obj):
        if not obj.pdf_id:
            return mark_safe(
                '<a href="{}?receipt={}">{}</a>'.format(
                    reverse(self.admin_site.name + ":afip_receiptpdf_add"),
                    obj.id,
                    _("Create"),
                )
            )
        return mark_safe(
            '<a href="{}">{}</a>'.format(
                reverse(
                    self.admin_site.name + ":afip_receiptpdf_change",
                    args=(obj.pdf_id,),
                ),
                _("Edit"),
            )
        )

    @admin.display(description=_("cae"), ordering="validation__cae")
    def cae(self, obj):
        return obj.validation.cae

    @admin.display(description=_("Validate"))
    def validate(
        self,
        request: HttpRequest,
        queryset: QuerySet[models.Receipt],
    ) -> None:
        with catch_errors(self, request):
            errs = queryset.validate()  # type: ignore[attr-defined]

        if errs:
            self.message_user(
                request,
                _("Receipt validation failed: %s.") % errs,
                messages.ERROR,
            )

    actions = [validate]


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

    @admin.display(description=_("Fetch points of sales"))
    def fetch_points_of_sales(self, request, queryset):
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

    @admin.display(description=_("Generate key"))
    def generate_key(self, request, queryset):
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

    @admin.display(description=_("Generate CSR"))
    def generate_csr(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                message=_("Can only generate CSR for one taxpayer at a time."),
                level=messages.ERROR,
            )
            return

        taxpayer = queryset.first()
        if not taxpayer.key:
            taxpayer.generate_key()

        csr = taxpayer.generate_csr()
        filename = "cuit-{}-{}.csr".format(
            taxpayer.cuit,
            int(datetime.now().timestamp()),
        )

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

    def lookups(self, request, model_admin):
        return (
            (self.YES, _("Yes")),
            (self.NO, _("No")),
        )

    def queryset(self, request, queryset):
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

    def get_queryset(self, request):
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
    def taxpayer(self, obj):
        return obj.receipt.point_of_sales.owner

    @admin.display(boolean=True, description=_("Has file"), ordering="pdf_file")
    def has_file(self, obj):
        return bool(obj.pdf_file)

    @admin.display(description=_("Generate pdf"))
    def generate_pdf(self, request, queryset):
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
    def receipt_number(self, obj):
        return obj.receipt.formatted_number

    @admin.display(boolean=True, description=_("result"), ordering="result")
    def successful(self, obj):
        return obj.result == models.ReceiptValidation.RESULT_APPROVED


admin.site.register(models.ConceptType)
admin.site.register(models.DocumentType)
admin.site.register(models.VatType)
admin.site.register(models.TaxType)
admin.site.register(models.Observation)
