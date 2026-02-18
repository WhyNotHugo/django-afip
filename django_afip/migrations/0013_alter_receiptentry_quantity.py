from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0012_optionaltype_optional_alter_code_in_generics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="receiptentry",
            name="quantity",
            field=models.DecimalField(
                decimal_places=2, max_digits=15, verbose_name="quantity"
            ),
        ),
    ]
