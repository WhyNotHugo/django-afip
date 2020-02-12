from django.db import migrations, models

import django_afip.models


class Migration(migrations.Migration):

    dependencies = [
        ("afip", "0003_issuance_type_length"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receiptpdf",
            name="pdf_file",
            field=models.FileField(
                blank=True,
                help_text="The actual file which contains the PDF data.",
                null=True,
                storage=django_afip.models._get_storage_from_settings(
                    "AFIP_PDF_STORAGE"
                ),
                upload_to=django_afip.models.ReceiptPDF.upload_to,
                verbose_name="pdf file",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayer",
            name="certificate",
            field=models.FileField(
                blank=True,
                null=True,
                storage=django_afip.models._get_storage_from_settings(
                    "AFIP_CERT_STORAGE"
                ),
                upload_to="afip/taxpayers/certs/",
                verbose_name="certificate",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayer",
            name="key",
            field=models.FileField(
                blank=True,
                null=True,
                storage=django_afip.models._get_storage_from_settings(
                    "AFIP_KEY_STORAGE"
                ),
                upload_to="afip/taxpayers/keys/",
                verbose_name="key",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayerextras",
            name="logo",
            field=models.ImageField(
                blank=True,
                help_text="A logo to use when generating printable receipts.",
                null=True,
                storage=django_afip.models._get_storage_from_settings(
                    "AFIP_LOGO_STORAGE"
                ),
                upload_to="afip/taxpayers/logos/",
                verbose_name="logo",
            ),
        ),
    ]
