from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0017_no_null_string_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="receiptvalidation",
            name="result",
        ),
    ]
