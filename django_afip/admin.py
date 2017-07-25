import functools
import logging
from datetime import datetime

from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from django_afip import exceptions, models


logger = logging.getLogger(__name__)


# TODO: Add an action to populate generic types.


def catch_errors(f):
    """
    Catches specific errors in admin actions and shows a friendly error.
    """

    @functools.wraps(f)
    def wrapper(self, request, *args, **kwargs):
        try:
            return f(self, request, *args, **kwargs)
        except exceptions.CertificateExpired as e:
            self.message_user(
                request,
                _('The AFIP Taxpayer certificate has expired.'),
                messages.ERROR,
            )
        except exceptions.UntrustedCertificate as e:
            self.message_user(
                request,
                _('The AFIP Taxpayer certificate is untrusted.'),
                messages.ERROR,
            )
        except exceptions.CorruptCertificate as e:
            self.message_user(
                request,
                _('The AFIP Taxpayer certificate is corrupt.'),
                messages.ERROR,
            )
        except exceptions.AuthenticationError as e:
            logger.exception('AFIP auth failed')
            self.message_user(
                request,
                _('An unknown authentication error has ocurred: %s') % e,
                messages.ERROR,
            )

    return wrapper


class VatInline(admin.TabularInline):
    model = models.Vat
    fields = (
        'vat_type',
        'base_amount',
        'amount',
    )
    extra = 1


class TaxInline(admin.TabularInline):
    model = models.Tax
    fields = (
        'tax_type',
        'description',
        'base_amount',
        'aliquot',
        'amount',
    )
    extra = 1


class ReceiptEntryInline(admin.TabularInline):
    model = models.ReceiptEntry
    fields = (
        'description',
        'quantity',
        'unit_price',
        'vat',
    )
    extra = 1


class ReceiptStatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'status'

    VALIDATED = 'validated'
    NOT_VALIDATED = 'not_validated'

    def lookups(self, request, model_admin):
        return (
            (self.VALIDATED, _('Validated')),
            (self.NOT_VALIDATED, _('Not validated')),
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


@admin.register(models.Receipt)
class ReceiptAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'receipt_type',
        'point_of_sales',
        'number',
        'issued_date',
        'friendly_total_amount',
        'validated',
    )
    list_filter = (
        ReceiptStatusFilter,
    )

    __related_fields = [
        'validated',
        'cae',
    ]

    filter_horizontal = ('related_receipts',)

    inlines = (
        VatInline,
        TaxInline,
        ReceiptEntryInline,
    )
    ordering = (
        '-issued_date',
    )

    def get_fields(self, request, obj=None):
        return super().get_fields(request, obj)

    readonly_fields = __related_fields

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .select_related(
                'validation',
                'receipt_type',
                'point_of_sales',
            )

    def number(self, obj):
        return obj.formatted_number
    number.short_description = _('receipt number')
    number.admin_order_field = 'receipt_number'

    def friendly_total_amount(self, obj):
        return '{:0.2f} ARS ({})'.format(
            obj.total_amount * obj.currency_quote,
            obj.currency,
        )
    friendly_total_amount.short_description = _('total amount')

    def validated(self, obj):
        try:
            return (
                obj.validation.result ==
                models.ReceiptValidation.RESULT_APPROVED
            )
        except models.ReceiptValidation.DoesNotExist:
            return False
    validated.short_description = _('validated')
    validated.admin_order_field = 'validation__result'
    validated.boolean = True

    def cae(self, obj):
        return obj.validation.cae
    cae.short_description = _('cae')
    cae.admin_order_field = 'validation__cae'

    @catch_errors
    def validate(self, request, queryset):
        errs = queryset.validate()
        if errs:
            self.message_user(
                request,
                _('Receipt validation failed: %s') % errs,
                messages.ERROR,
            )
    validate.short_description = _('Validate')

    actions = [validate]


@admin.register(models.AuthTicket)
class AuthTicketAdmin(admin.ModelAdmin):
    list_display = (
        'unique_id',
        'owner',
        'service',
        'generated',
        'expires',
    )


@admin.register(models.TaxPayer)
class TaxPayerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cuit',
        'certificate_expiration',
    )

    @catch_errors
    def fetch_points_of_sales(self, request, queryset):
        poses = [
            pos
            for taxpayer in queryset.all()
            for pos in taxpayer.fetch_points_of_sales()
        ]

        created = len([pos for pos in poses if pos[1]])
        total = len(poses)

        self.message_user(
            request,
            message=(
                _(
                    '%(total)d points of sales fetched. %(created)d created.'
                ) % {
                    'total': total,
                    'created': created,
                }
            ),
            level=messages.SUCCESS,
        )

    fetch_points_of_sales.short_description = _('Fetch points of sales')

    def generate_key(self, request, queryset):
        key_count = sum(t.generate_key() for t in queryset.all())

        if key_count is 1:
            message = _('Key generated successfully.')
            level = messages.SUCCESS
        elif key_count is 1:
            message = _('%d keys generated successfully.') % key_count
            level = messages.SUCCESS
        else:
            message = _('No keys generated; Taxpayers already had keys.')
            level = messages.ERROR

        self.message_user(
            request,
            message=message,
            level=level,
        )
    generate_key.short_description = _('Generate key')

    def generate_csr(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                message=_('Can only generate CSR for one taxpayer at a time'),
                level=messages.ERROR,
            )
            return

        taxpayer = queryset.first()
        if not taxpayer.key:
            taxpayer.generate_key()

        csr = taxpayer.generate_csr()
        filename = 'cuit-{}-{}.csr'.format(
            taxpayer.cuit,
            int(datetime.now().timestamp()),
        )

        response = HttpResponse(content_type='application/pkcs10')
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            filename
        )

        response.write(csr.read())
        return response
    generate_csr.short_description = _('Generate CSR')

    actions = (
        fetch_points_of_sales,
        generate_key,
        generate_csr,
    )


@admin.register(models.PointOfSales)
class PointOfSalesAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'number',
        'issuance_type',
        'blocked',
        'drop_date',
    )


@admin.register(models.CurrencyType)
class CurrencyTypeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'description',
        'valid_from',
        'valid_to',
    )


@admin.register(models.ReceiptPDF)
class ReceiptPDFAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_id',
        'client_name',
        'has_file',
    )

    def has_file(self, obj):
        return bool(obj.pdf_file)
    has_file.admin_order_field = 'pdf_file'
    has_file.boolean = True
    has_file.short_description = _('Has file')

    def generate_pdf(self, request, queryset):
        for pdf in queryset:
            pdf.save_pdf()
    generate_pdf.short_description = _('Generate pdf')

    actions = (
        generate_pdf,
    )


@admin.register(models.ReceiptValidation)
class ReceiptValidationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'receipt_number',
        'successful',
        'cae',
        'processed_date',
    )

    raw_id_fields = (
        'receipt',
    )

    def receipt_number(self, obj):
        return obj.receipt.formatted_number
    receipt_number.short_description = _('receipt number')
    receipt_number.admin_order_field = 'receipt_id'

    def successful(self, obj):
        return obj.result == models.ReceiptValidation.RESULT_APPROVED
    successful.short_description = _('result')
    successful.admin_order_field = 'result'
    successful.boolean = True


app = apps.get_app_config('afip')
for model in app.get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
