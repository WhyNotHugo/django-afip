from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0005_flatten_taxpayer_extras"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TaxPayerExtras",
        ),
    ]
