# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0004_auto_20150916_1934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(to='afip.PointOfSales', verbose_name='punto de ventas', related_name='receipts'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(to='afip.ReceiptType', verbose_name='tipo de comprobante', related_name='receipts'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='related_receipts',
            field=models.ManyToManyField(blank=True, to='afip.Receipt', verbose_name='comprobantes relacionados'),
        ),
        migrations.AlterUniqueTogether(
            name='pointofsales',
            unique_together=set([('number', 'owner')]),
        ),
    ]
