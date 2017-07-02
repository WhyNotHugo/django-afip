from django.db import migrations


def backfill_processed_dates(apps, schema):
    ReceiptValidation = apps.get_model('afip', 'receiptvalidation')
    rvs = ReceiptValidation.objects.select_related('validation')

    for rv in rvs:
        ReceiptValidation.objects.filter(
            pk=rv.pk,
        ).update(
            processed_date=rv.validation.processed_date,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0019_receiptvalidation__processed_date'),
    ]

    operations = [
        migrations.RunPython(backfill_processed_dates),
    ]
