from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0009_alter_pointofsales_issuance_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authticket",
            name="service",
            field=models.CharField(
                help_text="Service for which this ticket has been authorized.",
                max_length=34,
                verbose_name="service",
            ),
        ),
    ]
