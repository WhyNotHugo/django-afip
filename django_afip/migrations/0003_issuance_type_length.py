from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0002_taxpayerextras"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pointofsales",
            name="issuance_type",
            field=models.CharField(
                help_text="Indicates if this POS emits using CAE and CAEA.",
                max_length=24,
                verbose_name="issuance type",
            ),
        ),
    ]
