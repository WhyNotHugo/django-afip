# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0003_vat_tax_digits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(verbose_name='cantidad', max_digits=15, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='vat',
            name='amount',
            field=models.DecimalField(verbose_name='cantidad', max_digits=15, decimal_places=2),
        ),
    ]
