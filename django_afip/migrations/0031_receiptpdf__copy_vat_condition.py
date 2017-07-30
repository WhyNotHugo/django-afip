from django.db import migrations
from django.db.models import F


def copy_vat_condition(apps, schema_editor):
    ReceiptPDF = apps.get_model('afip', 'ReceiptPDF')
    ReceiptPDF.objects.all().update(client_vat_condition=F('vat_condition'))


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0030_receiptpdf_client_vat_condition'),
    ]

    operations = [
        migrations.RunPython(copy_vat_condition),
    ]
