# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0002_auto_20150909_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(max_digits=15, verbose_name='monto', decimal_places=2),
        ),
        migrations.AlterField(
            model_name='vat',
            name='amount',
            field=models.DecimalField(max_digits=15, verbose_name='monto', decimal_places=2),
        ),
    ]
