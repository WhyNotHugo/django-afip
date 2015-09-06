# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_afip.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthTicket',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('unique_id', models.IntegerField(verbose_name='id único', default=django_afip.models.AuthTicket.default_unique_id)),
                ('generated', models.DateTimeField(verbose_name='generado', default=django_afip.models.AuthTicket.default_generated)),
                ('expires', models.DateTimeField(verbose_name='vence', default=django_afip.models.AuthTicket.default_expires)),
                ('service', models.CharField(verbose_name='servicio', help_text='Servicio para el cual este ticket ha sido autorizado.', max_length=6)),
                ('token', models.TextField(verbose_name='token')),
                ('signature', models.TextField(verbose_name='firma')),
            ],
            options={
                'verbose_name': 'ticket de autorización',
                'verbose_name_plural': 'tickets de autorización',
            },
        ),
        migrations.CreateModel(
            name='ConceptType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de concepto',
                'verbose_name_plural': 'tipos de concepto',
            },
        ),
        migrations.CreateModel(
            name='CurrencyType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de moneda',
                'verbose_name_plural': 'tipos de moneda',
            },
        ),
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de documento',
                'verbose_name_plural': 'tipos de documento',
            },
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.PositiveSmallIntegerField(verbose_name='código')),
                ('message', models.CharField(verbose_name='mensaje', max_length=255)),
            ],
            options={
                'verbose_name': 'observación',
                'verbose_name_plural': 'observaciones',
            },
        ),
        migrations.CreateModel(
            name='PointOfSales',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(verbose_name='número')),
                ('issuance_type', models.CharField(verbose_name='tipo de emisión', help_text='Indicates if thie POS emits using CAE and CAEA.', max_length=8)),
                ('blocked', models.BooleanField(verbose_name='bloqueado')),
                ('drop_date', models.DateField(null=True, blank=True, verbose_name='fecha de baja')),
            ],
            options={
                'verbose_name': 'punto de ventas',
                'verbose_name_plural': 'puntos de venta',
            },
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('document_number', models.BigIntegerField(verbose_name='número de documento', help_text='El número de documento del cliente para el cual este comprobante es emitido.')),
                ('receipt_number', models.PositiveIntegerField(null=True, blank=True, verbose_name='número de comprobante')),
                ('issued_date', models.DateField(verbose_name='fecha de emisión', help_text='Puede diverger hasta 5 días para bienes, o 10 en otros casos.')),
                ('total_amount', models.DecimalField(verbose_name='monto total', max_digits=15, help_text='Debe ser igual al monto no gravado + monto gravado + tributos + iva.', decimal_places=2)),
                ('net_untaxed', models.DecimalField(verbose_name='monto total no gravado', max_digits=15, help_text='El total para el cual impuestos no aplican. Para comprobantes tipo C, debe ser cero.', decimal_places=2)),
                ('net_taxed', models.DecimalField(verbose_name='monto total gravado', max_digits=15, help_text='EL total para el cual impuestos  aplican. Para comprobantes tipo C, esto es igual al subtotal.', decimal_places=2)),
                ('exempt_amount', models.DecimalField(verbose_name='monto exento', max_digits=15, help_text='Sólo para rubros que son exentos de impuestos. Para comprobantes tipo C, debe ser cero.', decimal_places=2)),
                ('service_start', models.DateField(null=True, blank=True, help_text='Fecha en la cual el servicio comenzó. No aplica a bienes.', verbose_name='fecha de comienzo de servicio')),
                ('service_end', models.DateField(null=True, blank=True, help_text='Fecha en la cual el servicio finalizó. No aplica a bienes.', verbose_name='fecha de fin de servicio')),
                ('expiration_date', models.DateField(null=True, blank=True, help_text='Fecha en la cual este comprobante expira. No aplica a bienes.', verbose_name='fecha de vencimiento del comprobante')),
                ('currency_quote', models.DecimalField(verbose_name='cotización de moneda', max_digits=10, help_text='Cotizacón del día para la moneda usada en el comprobante.', decimal_places=6)),
            ],
            options={
                'verbose_name': 'comprobante',
                'verbose_name_plural': 'comprobantes',
            },
        ),
        migrations.CreateModel(
            name='ReceiptBatch',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('point_of_sales', models.ForeignKey(verbose_name='punto de ventas', to='afip.PointOfSales')),
            ],
            options={
                'verbose_name': 'lote de comprobantes',
                'verbose_name_plural': 'lotes de comprobantes',
            },
        ),
        migrations.CreateModel(
            name='ReceiptType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de comprobante',
                'verbose_name_plural': 'tipos de comprobante',
            },
        ),
        migrations.CreateModel(
            name='ReceiptValidation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('result', models.CharField(verbose_name='resultado', max_length=1, choices=[('A', 'aprobado'), ('R', 'rechazado'), ('P', 'parcial')])),
                ('cae', models.CharField(verbose_name='cae', max_length=14)),
                ('cae_expiration', models.DateField(verbose_name='expiración de cae')),
                ('observations', models.ManyToManyField(verbose_name='observaciones', to='afip.Observation', related_name='valiations')),
                ('receipt', models.OneToOneField(verbose_name='comprobante', to='afip.Receipt', related_name='validation')),
            ],
            options={
                'verbose_name': 'validación de comprobante',
                'verbose_name_plural': 'validaciones de comprobante',
            },
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('description', models.CharField(verbose_name='descripción', max_length=80)),
                ('base_amount', models.DecimalField(verbose_name='monto base', max_digits=15, decimal_places=2)),
                ('aliquot', models.DecimalField(verbose_name='alicuota', max_digits=5, decimal_places=2)),
                ('amount', models.DecimalField(verbose_name='monto', max_digits=15, decimal_places=2)),
                ('receipt', models.ForeignKey(related_name='taxes', to='afip.Receipt')),
            ],
            options={
                'verbose_name': 'tributo',
                'verbose_name_plural': 'tributos',
            },
        ),
        migrations.CreateModel(
            name='TaxPayer',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(verbose_name='nombre', help_text='Un nombre amigable para reconocer a este contribuyente.', max_length=32)),
                ('key', models.FileField(null=True, verbose_name='clave', upload_to='')),
                ('certificate', models.FileField(null=True, verbose_name='certificado', upload_to='')),
                ('cuit', models.BigIntegerField(verbose_name='cuit')),
            ],
            options={
                'verbose_name': 'contribuyente',
                'verbose_name_plural': 'contribuyentes',
            },
        ),
        migrations.CreateModel(
            name='TaxType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de tributo',
                'verbose_name_plural': 'tipos de tributo',
            },
        ),
        migrations.CreateModel(
            name='Validation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('processed_date', models.DateTimeField(verbose_name='fecha procesado')),
                ('result', models.CharField(verbose_name='resultado', max_length=1, choices=[('A', 'aprobado'), ('R', 'rechazado'), ('P', 'parcial')])),
                ('batch', models.ForeignKey(verbose_name='lote de comprobantes', to='afip.ReceiptBatch', related_name='validation')),
            ],
            options={
                'verbose_name': 'validación',
                'verbose_name_plural': 'validaciones',
            },
        ),
        migrations.CreateModel(
            name='Vat',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('base_amount', models.DecimalField(verbose_name='monto base', max_digits=15, decimal_places=2)),
                ('amount', models.DecimalField(verbose_name='monto', max_digits=15, decimal_places=2)),
                ('receipt', models.ForeignKey(related_name='vat', to='afip.Receipt')),
            ],
            options={
                'verbose_name': 'iva',
                'verbose_name_plural': 'iva',
            },
        ),
        migrations.CreateModel(
            name='VatType',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('code', models.CharField(verbose_name='código', max_length=3)),
                ('description', models.CharField(verbose_name='descripción', max_length=250)),
                ('valid_from', models.DateField(null=True, blank=True, verbose_name='válido desde')),
                ('valid_to', models.DateField(null=True, blank=True, verbose_name='válido hasta')),
            ],
            options={
                'verbose_name': 'tipo de iva',
                'verbose_name_plural': 'tipos de iva',
            },
        ),
        migrations.AddField(
            model_name='vat',
            name='vat_type',
            field=models.ForeignKey(verbose_name='tipo de iva', to='afip.VatType'),
        ),
        migrations.AddField(
            model_name='tax',
            name='tax_type',
            field=models.ForeignKey(verbose_name='tipo de tributo', to='afip.TaxType'),
        ),
        migrations.AddField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(verbose_name='validación', to='afip.Validation', related_name='receipts'),
        ),
        migrations.AddField(
            model_name='receiptbatch',
            name='receipt_type',
            field=models.ForeignKey(verbose_name='tipo de comprobante', to='afip.ReceiptType'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='batch',
            field=models.ForeignKey(null=True, blank=True, help_text='Los comprobantes son validados en lotes, así que debe ser asignado a unou antes de que sea posible validarlo.', verbose_name='lote de comprobantes', to='afip.ReceiptBatch', related_name='receipts'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='concept',
            field=models.ForeignKey(verbose_name='concepto', to='afip.ConceptType', related_name='receipts'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(verbose_name='moneda', to='afip.CurrencyType', related_name='documents', help_text='Moneda en la cual el comprobante es emitido.'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='document_type',
            field=models.ForeignKey(verbose_name='tipo de documento', to='afip.DocumentType', related_name='receipts', help_text='El tipo de documento del client para el cual este recibo es emitido.'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(to='afip.PointOfSales'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(to='afip.ReceiptType'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='related_receipts',
            field=models.ManyToManyField(to='afip.Receipt', blank=True, db_constraint='comprobantes relacionados'),
        ),
        migrations.AddField(
            model_name='pointofsales',
            name='owner',
            field=models.ForeignKey(verbose_name='dueño', to='afip.TaxPayer'),
        ),
        migrations.AddField(
            model_name='authticket',
            name='owner',
            field=models.ForeignKey(verbose_name='dueño', to='afip.TaxPayer', related_name='auth_tickets'),
        ),
        migrations.AlterUniqueTogether(
            name='receipt',
            unique_together=set([('point_of_sales', 'receipt_type', 'receipt_number')]),
        ),
    ]
