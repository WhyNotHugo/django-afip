from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0013_alter_receiptentry_quantity"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pointofsales",
            name="blocked",
            field=models.BooleanField(default=False, verbose_name="blocked"),
        ),
    ]
