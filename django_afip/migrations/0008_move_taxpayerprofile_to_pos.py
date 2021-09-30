from django.db import migrations
from django.db import models


def merge_taxpayer_profile(apps, schema_editor):
    TaxPayerProfile = apps.get_model("afip", "TaxPayerProfile")

    for profile in TaxPayerProfile.objects.all():  # pragma: no cover
        for pos in profile.taxpayer.points_of_sales.all():
            pos.issuing_name = profile.issuing_name
            pos.issuing_address = profile.issuing_address
            pos.issuing_email = profile.issuing_email
            pos.vat_condition = profile.vat_condition
            pos.gross_income_condition = profile.gross_income_condition
            pos.sales_terms = profile.sales_terms
            pos.save()


class Migration(migrations.Migration):

    dependencies = [
        ("afip", "0007_auto_20210409_1641"),
    ]

    operations = [
        migrations.AddField(
            model_name="pointofsales",
            name="gross_income_condition",
            field=models.CharField(
                max_length=48, null=True, verbose_name="gross income condition"
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="issuing_address",
            field=models.TextField(
                help_text="The address of the issuing entity as shown on receipts.",
                null=True,
                verbose_name="issuing address",
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="issuing_email",
            field=models.CharField(
                blank=True,
                help_text="The email of the issuing entity as shown on receipts.",
                max_length=128,
                null=True,
                verbose_name="issuing email",
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="issuing_name",
            field=models.CharField(
                help_text="The name of the issuing entity as shown on receipts.",
                max_length=128,
                null=True,
                verbose_name="issuing name",
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="sales_terms",
            field=models.CharField(
                help_text=(
                    "The terms of the sale printed onto receipts by default "
                    "(eg: single payment, checking account, etc)."
                ),
                max_length=48,
                null=True,
                verbose_name="sales terms",
            ),
        ),
        migrations.AddField(
            model_name="pointofsales",
            name="vat_condition",
            field=models.CharField(
                choices=[
                    ("IVA Responsable Inscripto", "IVA Responsable Inscripto"),
                    ("IVA Responsable No Inscripto", "IVA Responsable No Inscripto"),
                    ("IVA Exento", "IVA Exento"),
                    ("No Responsable IVA", "No Responsable IVA"),
                    ("Responsable Monotributo", "Responsable Monotributo"),
                ],
                max_length=48,
                null=True,
                verbose_name="vat condition",
            ),
        ),
        migrations.RunPython(merge_taxpayer_profile),
        migrations.DeleteModel(
            name="TaxPayerProfile",
        ),
    ]
