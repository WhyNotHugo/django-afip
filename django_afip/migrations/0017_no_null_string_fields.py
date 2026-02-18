from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0016_clientvatcondition_receipt_client_vat_condition"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pointofsales",
            name="gross_income_condition",
            field=models.CharField(
                blank=True,
                default="",
                max_length=48,
                verbose_name="gross income condition",
            ),
        ),
        migrations.AlterField(
            model_name="pointofsales",
            name="issuing_address",
            field=models.TextField(
                blank=True,
                default="",
                help_text="The address of the issuing entity as shown on receipts.",
                verbose_name="issuing address",
            ),
        ),
        migrations.AlterField(
            model_name="pointofsales",
            name="issuing_email",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The email of the issuing entity as shown on receipts.",
                max_length=128,
                verbose_name="issuing email",
            ),
        ),
        migrations.AlterField(
            model_name="pointofsales",
            name="issuing_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The name of the issuing entity as shown on receipts.",
                max_length=128,
                verbose_name="issuing name",
            ),
        ),
        migrations.AlterField(
            model_name="pointofsales",
            name="sales_terms",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The terms of the sale printed onto receipts by default "
                "(eg: single payment, checking account, etc).",
                max_length=48,
                verbose_name="sales terms",
            ),
        ),
        migrations.AlterField(
            model_name="pointofsales",
            name="vat_condition",
            field=models.CharField(
                blank=True,
                choices=[
                    ("IVA Responsable Inscripto", "IVA Responsable Inscripto"),
                    ("IVA Responsable No Inscripto", "IVA Responsable No Inscripto"),
                    ("IVA Exento", "IVA Exento"),
                    ("No Responsable IVA", "No Responsable IVA"),
                    ("Responsable Monotributo", "Responsable Monotributo"),
                ],
                default="",
                max_length=48,
                verbose_name="vat condition",
            ),
        ),
        migrations.AlterField(
            model_name="receiptpdf",
            name="issuing_email",
            field=models.CharField(
                blank=True, default="", max_length=128, verbose_name="issuing email"
            ),
        ),
    ]
