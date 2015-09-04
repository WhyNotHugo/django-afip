from django.apps import apps
from django.contrib import admin, messages
from django.contrib.admin.sites import AlreadyRegistered
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.translation import ugettext as _

from . import models

# TODO: Add an action to populate generic types.


class ReceiptAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'receipt_type',
        'point_of_sales',
        'receipt_number',
        'issued_date',
        'total_amount',
        'batch_link',
        'validated',
    )
    list_filter = (
        'validation__result',
    )

    __related_fields = [
        'validated',
        'cae',
    ]

    def get_fields(self, request, obj=None):
        return super().get_fields(request, obj)

    readonly_fields = __related_fields

    def get_queryset(self, request):
        return super().get_queryset(request) \
            .select_related('validation') \
            .select_related('receipt_type')

    def validated(self, obj):
        return obj.validation.result
    validated.short_description = _('validated')
    validated.admin_order_field = 'validation__result'
    validated.boolean = True

    def cae(self, obj):
        return obj.validation.cae
    cae.short_description = _('cae')
    cae.admin_order_field = 'validation__cae'

    def create_batch(self, request, queryset):
        # TODO: use agregate
        variations = queryset \
            .order_by('receipt_type', 'point_of_sales') \
            .distinct('receipt_type', 'point_of_sales') \
            .count()

        if variations > 1:
            self.message_user(
                request,
                _(
                    'The selected receipts are not all of the same type '
                    'and from the same point of sales.'
                ),
                messages.ERROR,
            )
            return

        first = queryset.select_related('point_of_sales').first()
        batch = models.ReceiptBatch(
            receipt_type_id=first.receipt_type_id,
            point_of_sales_id=first.point_of_sales_id,
            owner_id=first.point_of_sales.owner_id,
        )
        batch.save()

        # Exclude any receipts that are already batched (either pre-selection,
        # or due to concurrency):
        queryset.filter(batch__isnull=True).update(batch=batch)
    create_batch.short_description = _('Create receipt batch')

    def batch_link(self, obj):
        if not obj.batch:
            return None
        return '<a href="{}">{}</a>'.format(
            reverse("admin:afip_receiptbatch_change", args=(obj.batch.id,)),
            obj.batch.id
        )
    batch_link.allow_tags = True
    batch_link.short_description = _('batch')

    actions = [create_batch]


class ReceiptBatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'receipts_count',
        'cae',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            Count('receipts', distinct=True)
        )

    def cae(self, obj):
        validation = obj.validation.last()
        if validation:
            return validation.cae
    cae.short_description = _('cae')
    cae.admin_order_field = 'validation__cae'

    def receipts_count(self, obj):
        return obj.receipts__count
    receipts_count.short_description = _('receipts')
    receipts_count.admin_order_field = 'receipts__count'


class AuthTicketAdmin(admin.ModelAdmin):
    list_display = (
        'unique_id',
        'owner',
        'service',
        'generated',
        'expires',
    )


admin.site.register(models.Receipt, ReceiptAdmin)
admin.site.register(models.ReceiptBatch, ReceiptBatchAdmin)
admin.site.register(models.AuthTicket, AuthTicketAdmin)

app = apps.get_app_config('afip')
for model in app.get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
