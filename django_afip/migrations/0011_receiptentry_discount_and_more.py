from __future__ import annotations

from decimal import Decimal

import django.core.validators
import django.db.models.expressions
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
                help_text="Total net discount applied to row's total.",
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal("0.0"))],
                verbose_name="discount",
            ),
        ),
        migrations.AddConstraint(
            model_name="receiptentry",
            constraint=models.CheckConstraint(
                condition=models.Q(("discount__gte", Decimal("0.0"))),
                name="discount_positive_value",
            ),
        ),
        migrations.AddConstraint(
            model_name="receiptentry",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "discount__lte",
                        django.db.models.expressions.CombinedExpression(
                            django.db.models.expressions.F("quantity"),
                            "*",
                            django.db.models.expressions.F("unit_price"),
                        ),
                    )
                ),
                name="discount_less_than_total",
            ),
        ),
    ]
