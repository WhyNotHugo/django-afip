# Generated by Django 4.0.7 on 2022-09-16 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("afip", "0021_alter_receiptvalidation_cae_expiration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receiptvalidation",
            name="caea",
            field=models.BooleanField(
                default=False,
                help_text="Indicate if the validation was from a CAEA receipt, in that case the field CAE contains the CAEA number",
                verbose_name="is_caea",
            ),
        ),
    ]
