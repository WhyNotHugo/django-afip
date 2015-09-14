# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='cantidad'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='cantidad'),
        ),
    ]
