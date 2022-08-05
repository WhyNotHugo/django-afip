# Generated by Django 4.0.7 on 2022-08-04 22:21

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("afip", "0010_alter_authticket_service"),
    ]

    operations = [
        migrations.AddField(
            model_name="receiptentry",
            name="discount",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Total net discount applied to tax base.",
                max_digits=15,
                verbose_name="discount",
            ),
        ),
    ]
