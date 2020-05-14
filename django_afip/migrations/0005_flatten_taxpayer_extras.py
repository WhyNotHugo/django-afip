import django.core.files.storage
from django.db import migrations
from django.db import models


def merge_taxpayer_extras(apps, schema_editor):
    TaxPayerExtras = apps.get_model("afip", "TaxPayerExtras")

    for extras in TaxPayerExtras.objects.all():
        extras.taxpayer.logo = extras.logo
        extras.taxpayer.save()


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0004_storages_and_help_texts"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxpayer",
            name="logo",
            field=models.ImageField(
                blank=True,
                help_text="A logo to use when generating printable receipts.",
                null=True,
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to="afip/taxpayers/logos/",
                verbose_name="logo",
            ),
        ),
        migrations.RunPython(merge_taxpayer_extras),
    ]
