import datetime
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F

import django_afip.models


def backfill_processed_dates(apps, schema):
    ReceiptValidation = apps.get_model('afip', 'receiptvalidation')
    rvs = ReceiptValidation.objects.select_related('validation')

    for rv in rvs:
        ReceiptValidation.objects.filter(
            pk=rv.pk,
        ).update(
            processed_date=rv.validation.processed_date,
        )


def move_active_since(apps, schema_editor):
    TaxPayerProfile = apps.get_model('afip', 'TaxPayerProfile')
    profiles = TaxPayerProfile.objects.select_related('taxpayer')

    for profile in profiles:
        profile.taxpayer.active_since = profile.active_since
        profile.taxpayer.save()


def copy_vat_condition(apps, schema_editor):
    ReceiptPDF = apps.get_model('afip', 'ReceiptPDF')
    ReceiptPDF.objects.all().update(client_vat_condition=F('vat_condition'))


class Migration(migrations.Migration):

    replaces = [('afip', '0001_initial'), ('afip', '0002_auto_20150909_1837'), ('afip', '0003_vat_tax_digits'), ('afip', '0004_auto_20150916_1934'), ('afip', '0005_auto_20150918_0115'), ('afip', '0006_auto_20151212_1431'), ('afip', '0007_auto_20151212_1754'), ('afip', '0008_auto_20151212_1820'), ('afip', '0009_auto_20151214_1836'), ('afip', '0010_receiptpdf_pdffile_uploadto'), ('afip', '0011_receipt_entry_vat'), ('afip', '0012_taxpayer_profile_one_to_one'), ('afip', '0013_taxpayer_is_sandboxed'), ('afip', '0014_no_partially_validated_receiptvalidations'), ('afip', '0015_receiptentry__amount_to_quantity'), ('afip', '0016_auto_20170529_2012'), ('afip', '0017_receipt_issued_date'), ('afip', '0018_on_delete_fks'), ('afip', '0019_receiptvalidation__processed_date'), ('afip', '0020_backfill_receiptvalidation__processed_date'), ('afip', '0021_drop_batches'), ('afip', '0022_auto_misc_tweaks'), ('afip', '0023_taxpayer__certs_blank'), ('afip', '0024_taxpayer__certificate_expiration'), ('afip', '0025_receipt__default_currency'), ('afip', '0026_vat_conditions'), ('afip', '0027_taxpayer__active_since'), ('afip', '0028_taxpayer__copy_active_since'), ('afip', '0029_drop__taxpayerprofile__active_since'), ('afip', '0030_receiptpdf_client_vat_condition'), ('afip', '0031_receiptpdf__copy_vat_condition'), ('afip', '0032_receiptpdf__client_vat__notnull'), ('afip', '0033_receiptpdf__pdf_file__help_text'), ('afip', '0034_vat_condition_choices'), ('afip', '0035_receiptentry__vat__blankable'), ('afip', '0036_receiptpdf__client_address__blank')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_id', models.IntegerField(default=django_afip.models.AuthTicket.default_unique_id, verbose_name='id único')),
                ('generated', models.DateTimeField(default=django_afip.models.AuthTicket.default_generated, verbose_name='generado')),
                ('expires', models.DateTimeField(default=django_afip.models.AuthTicket.default_expires, verbose_name='vence')),
                ('service', models.CharField(help_text='Servicio para el cual este ticket ha sido autorizado.', max_length=6, verbose_name='servicio')),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'concept type',
                'verbose_name_plural': 'concept types',
            },
        ),
        migrations.CreateModel(
            name='CurrencyType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'currency type',
                'verbose_name_plural': 'currency types',
            },
        ),
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'document type',
                'verbose_name_plural': 'document types',
            },
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.PositiveSmallIntegerField(verbose_name='código')),
                ('message', models.CharField(max_length=255, verbose_name='mensaje')),
            ],
            options={
                'verbose_name': 'observación',
                'verbose_name_plural': 'observaciones',
            },
        ),
        migrations.CreateModel(
            name='PointOfSales',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField(verbose_name='número')),
                ('issuance_type', models.CharField(help_text='Indicates if thie POS emits using CAE and CAEA.', max_length=8, verbose_name='tipo de emisión')),
                ('blocked', models.BooleanField(verbose_name='bloqueado')),
                ('drop_date', models.DateField(blank=True, null=True, verbose_name='fecha de baja')),
            ],
            options={
                'verbose_name': 'punto de ventas',
                'verbose_name_plural': 'puntos de venta',
            },
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_number', models.BigIntegerField(help_text='El número de documento del cliente para el cual este comprobante es emitido.', verbose_name='número de documento')),
                ('receipt_number', models.PositiveIntegerField(blank=True, null=True, verbose_name='número de comprobante')),
                ('issued_date', models.DateField(help_text='Puede diverger hasta 5 días para bienes, o 10 en otros casos.', verbose_name='fecha de emisión')),
                ('total_amount', models.DecimalField(decimal_places=2, help_text='Debe ser igual al monto no gravado + monto gravado + tributos + iva.', max_digits=15, verbose_name='monto total')),
                ('net_untaxed', models.DecimalField(decimal_places=2, help_text='El total para el cual impuestos no aplican. Para comprobantes tipo C, debe ser cero.', max_digits=15, verbose_name='monto total no gravado')),
                ('net_taxed', models.DecimalField(decimal_places=2, help_text='EL total para el cual impuestos  aplican. Para comprobantes tipo C, esto es igual al subtotal.', max_digits=15, verbose_name='monto total gravado')),
                ('exempt_amount', models.DecimalField(decimal_places=2, help_text='Sólo para rubros que son exentos de impuestos. Para comprobantes tipo C, debe ser cero.', max_digits=15, verbose_name='monto exento')),
                ('service_start', models.DateField(blank=True, help_text='Fecha en la cual el servicio comenzó. No aplica a bienes.', null=True, verbose_name='fecha de comienzo de servicio')),
                ('service_end', models.DateField(blank=True, help_text='Fecha en la cual el servicio finalizó. No aplica a bienes.', null=True, verbose_name='fecha de fin de servicio')),
                ('expiration_date', models.DateField(blank=True, help_text='Fecha en la cual este comprobante expira. No aplica a bienes.', null=True, verbose_name='fecha de vencimiento del comprobante')),
                ('currency_quote', models.DecimalField(decimal_places=6, help_text='Cotizacón del día para la moneda usada en el comprobante.', max_digits=10, verbose_name='cotización de moneda')),
            ],
            options={
                'verbose_name': 'comprobante',
                'verbose_name_plural': 'comprobantes',
            },
        ),
        migrations.CreateModel(
            name='ReceiptBatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('point_of_sales', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.PointOfSales', verbose_name='punto de ventas')),
            ],
            options={
                'verbose_name': 'lote de comprobantes',
                'verbose_name_plural': 'lotes de comprobantes',
            },
        ),
        migrations.CreateModel(
            name='ReceiptType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'receipt type',
                'verbose_name_plural': 'receipt types',
            },
        ),
        migrations.CreateModel(
            name='ReceiptValidation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.CharField(choices=[('A', 'aprobado'), ('R', 'rechazado'), ('P', 'parcial')], max_length=1, verbose_name='resultado')),
                ('cae', models.CharField(max_length=14, verbose_name='cae')),
                ('cae_expiration', models.DateField(verbose_name='expiración de cae')),
                ('observations', models.ManyToManyField(related_name='valiations', to='afip.Observation', verbose_name='observaciones')),
                ('receipt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validation', to='afip.Receipt', verbose_name='comprobante')),
            ],
            options={
                'verbose_name': 'validación de comprobante',
                'verbose_name_plural': 'validaciones de comprobante',
            },
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=80, verbose_name='descripción')),
                ('base_amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto base')),
                ('aliquot', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='alicuota')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto')),
                ('receipt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taxes', to='afip.Receipt')),
            ],
            options={
                'verbose_name': 'tributo',
                'verbose_name_plural': 'tributos',
            },
        ),
        migrations.CreateModel(
            name='TaxPayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A friendly name to recognize this taxpayer.', max_length=32, verbose_name='name')),
                ('key', models.FileField(null=True, upload_to='', verbose_name='key')),
                ('certificate', models.FileField(null=True, upload_to='', verbose_name='certificate')),
                ('cuit', models.BigIntegerField(verbose_name='cuit')),
                ('is_sandboxed', models.BooleanField(default=True, help_text='Indicates if this taxpayer interacts with the sandbox servers rather than the production servers', verbose_name='is sandboxed')),
            ],
            options={
                'verbose_name': 'taxpayer',
                'verbose_name_plural': 'taxpayers',
            },
        ),
        migrations.CreateModel(
            name='TaxType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'tax type',
                'verbose_name_plural': 'tax types',
            },
        ),
        migrations.CreateModel(
            name='Validation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processed_date', models.DateTimeField(verbose_name='processed date')),
                ('result', models.CharField(choices=[('A', 'approved'), ('R', 'rejected'), ('P', 'partial')], max_length=1, verbose_name='result')),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='validation', to='afip.ReceiptBatch', verbose_name='receipt batch')),
            ],
            options={
                'verbose_name': 'validation',
                'verbose_name_plural': 'validations',
            },
        ),
        migrations.CreateModel(
            name='Vat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto base')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto')),
                ('receipt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vat', to='afip.Receipt')),
            ],
            options={
                'verbose_name': 'iva',
                'verbose_name_plural': 'iva',
            },
        ),
        migrations.CreateModel(
            name='VatType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, verbose_name='code')),
                ('description', models.CharField(max_length=250, verbose_name='description')),
                ('valid_from', models.DateField(blank=True, null=True, verbose_name='valid from')),
                ('valid_to', models.DateField(blank=True, null=True, verbose_name='valid until')),
            ],
            options={
                'verbose_name': 'vat type',
                'verbose_name_plural': 'vat types',
            },
        ),
        migrations.AddField(
            model_name='vat',
            name='vat_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.VatType', verbose_name='tipo de iva'),
        ),
        migrations.AddField(
            model_name='tax',
            name='tax_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.TaxType', verbose_name='tipo de tributo'),
        ),
        migrations.AddField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.Validation', verbose_name='validación'),
        ),
        migrations.AddField(
            model_name='receiptbatch',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.ReceiptType', verbose_name='tipo de comprobante'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='batch',
            field=models.ForeignKey(blank=True, help_text='Los comprobantes son validados en lotes, así que debe ser asignado a unou antes de que sea posible validarlo.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.ReceiptBatch', verbose_name='lote de comprobantes'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='concept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.ConceptType', verbose_name='concepto'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(help_text='Moneda en la cual el comprobante es emitido.', on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='afip.CurrencyType', verbose_name='moneda'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='document_type',
            field=models.ForeignKey(help_text='El tipo de documento del client para el cual este recibo es emitido.', on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.DocumentType', verbose_name='tipo de documento'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.PointOfSales'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.ReceiptType'),
        ),
        migrations.AddField(
            model_name='receipt',
            name='related_receipts',
            field=models.ManyToManyField(blank=True, to='afip.Receipt', verbose_name='comprobantes relacionados'),
        ),
        migrations.AddField(
            model_name='pointofsales',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.TaxPayer', verbose_name='dueño'),
        ),
        migrations.AddField(
            model_name='authticket',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_tickets', to='afip.TaxPayer', verbose_name='dueño'),
        ),
        migrations.AlterUniqueTogether(
            name='receipt',
            unique_together=set([('point_of_sales', 'receipt_type', 'receipt_number')]),
        ),
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
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='monto'),
        ),
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
        migrations.AlterField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.PointOfSales', verbose_name='punto de ventas'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.ReceiptType', verbose_name='tipo de comprobante'),
        ),
        migrations.AlterUniqueTogether(
            name='pointofsales',
            unique_together=set([('number', 'owner')]),
        ),
        migrations.CreateModel(
            name='ReceiptEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=128, verbose_name='description')),
                ('amount', models.PositiveSmallIntegerField(verbose_name='amount')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='unit price')),
            ],
            options={
                'verbose_name': 'receipt entry',
                'verbose_name_plural': 'receipt entries',
            },
        ),
        migrations.CreateModel(
            name='ReceiptPDF',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(null=True, upload_to='', verbose_name='pdf file')),
                ('issuing_name', models.TextField(verbose_name='issuing name')),
                ('issuing_address', models.TextField(verbose_name='issuing address')),
                ('issuing_email', models.TextField(null=True, verbose_name='issuing address')),
                ('vat_condition', models.CharField(max_length=48, verbose_name='vat condition')),
                ('gross_income_condition', models.CharField(max_length=48, verbose_name='gross income condition')),
                ('client_name', models.TextField(verbose_name='client name')),
                ('client_address', models.TextField(verbose_name='client address')),
                ('sales_terms', models.CharField(max_length=48, verbose_name='sales terms')),
            ],
            options={
                'verbose_name': 'receipt pdf',
                'verbose_name_plural': 'receipt pdfs',
            },
        ),
        migrations.CreateModel(
            name='TaxPayerProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issuing_name', models.CharField(max_length=128, verbose_name='issuing name')),
                ('issuing_address', models.TextField(verbose_name='issuing address')),
                ('vat_condition', models.CharField(max_length=48, verbose_name='vat condition')),
                ('gross_income_condition', models.CharField(max_length=48, verbose_name='gross income condition')),
                ('taxpayer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='afip.TaxPayer', verbose_name='taxpayer')),
                ('active_since', models.DateField(default=None, help_text='Date since which this taxpayer has been legally active.', verbose_name='active since')),
                ('issuing_email', models.CharField(blank=True, max_length=128, null=True, verbose_name='issuing email')),
                ('sales_terms', models.CharField(default=None, help_text='The terms of the sale printed onto receipts by default (eg: single payment, checking account, etc).', max_length=48, verbose_name='sales terms')),
            ],
            options={
                'verbose_name': 'taxpayer profile',
                'verbose_name_plural': 'taxpayer profiles',
            },
        ),
        migrations.AlterModelOptions(
            name='authticket',
            options={'verbose_name': 'authorization ticket', 'verbose_name_plural': 'authorization tickets'},
        ),
        migrations.AlterModelOptions(
            name='observation',
            options={'verbose_name': 'observation', 'verbose_name_plural': 'observations'},
        ),
        migrations.AlterModelOptions(
            name='pointofsales',
            options={'verbose_name': 'point of sales', 'verbose_name_plural': 'points of sales'},
        ),
        migrations.AlterModelOptions(
            name='receipt',
            options={'verbose_name': 'receipt', 'verbose_name_plural': 'receipts'},
        ),
        migrations.AlterModelOptions(
            name='receiptbatch',
            options={'verbose_name': 'receipt batch', 'verbose_name_plural': 'receipt batches'},
        ),
        migrations.AlterModelOptions(
            name='receiptvalidation',
            options={'verbose_name': 'receipt validation', 'verbose_name_plural': 'receipt validations'},
        ),
        migrations.AlterModelOptions(
            name='tax',
            options={'verbose_name': 'tax', 'verbose_name_plural': 'taxes'},
        ),
        migrations.AlterModelOptions(
            name='vat',
            options={'verbose_name': 'vat', 'verbose_name_plural': 'vat'},
        ),
        migrations.AlterField(
            model_name='authticket',
            name='expires',
            field=models.DateTimeField(default=django_afip.models.AuthTicket.default_expires, verbose_name='expires'),
        ),
        migrations.AlterField(
            model_name='authticket',
            name='generated',
            field=models.DateTimeField(default=django_afip.models.AuthTicket.default_generated, verbose_name='generated'),
        ),
        migrations.AlterField(
            model_name='authticket',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_tickets', to='afip.TaxPayer', verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='authticket',
            name='service',
            field=models.CharField(help_text='Service for which this ticket has been authorized', max_length=6, verbose_name='service'),
        ),
        migrations.AlterField(
            model_name='authticket',
            name='signature',
            field=models.TextField(verbose_name='signature'),
        ),
        migrations.AlterField(
            model_name='authticket',
            name='unique_id',
            field=models.IntegerField(default=django_afip.models.AuthTicket.default_unique_id, verbose_name='unique id'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='code',
            field=models.PositiveSmallIntegerField(verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='message',
            field=models.CharField(max_length=255, verbose_name='message'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='blocked',
            field=models.BooleanField(verbose_name='blocked'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='drop_date',
            field=models.DateField(blank=True, null=True, verbose_name='drop date'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='issuance_type',
            field=models.CharField(help_text='Indicates if thie POS emits using CAE and CAEA.', max_length=8, verbose_name='issuance type'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='number',
            field=models.PositiveSmallIntegerField(verbose_name='number'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.TaxPayer', verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='batch',
            field=models.ForeignKey(blank=True, help_text='Receipts are validated in batches, so it must be assigned one before validation is possible.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.ReceiptBatch', verbose_name='receipt batch'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='concept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.ConceptType', verbose_name='concept'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(help_text='Currency in which this receipt is issued.', on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='afip.CurrencyType', verbose_name='currency'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency_quote',
            field=models.DecimalField(decimal_places=6, help_text='Quote of the day for the currency used in the receipt', max_digits=10, verbose_name='currency quote'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='document_number',
            field=models.BigIntegerField(help_text='The document number of the customer to whom this receipt is addressed', verbose_name='document number'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='document_type',
            field=models.ForeignKey(help_text='The document type of the customer to whom this receipt is addressed', on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.DocumentType', verbose_name='document type'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='exempt_amount',
            field=models.DecimalField(decimal_places=2, help_text='Only for categories which are tax-exempt. For C-type receipts, this must be zero.', max_digits=15, verbose_name='exempt amount'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='expiration_date',
            field=models.DateField(blank=True, help_text='Date on which this receipt expires. No applicable for goods.', null=True, verbose_name='receipt expiration date'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='issued_date',
            field=models.DateField(help_text='Can diverge up to 5 days for good, or 10 days otherwise', verbose_name='issued date'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='net_taxed',
            field=models.DecimalField(decimal_places=2, help_text='The total amount to which taxes apply. For C-type receipts, this is equal to the subtotal.', max_digits=15, verbose_name='total taxable amount'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='net_untaxed',
            field=models.DecimalField(decimal_places=2, help_text='The total amount to which taxes do not apply. For C-type receipts, this must be zero.', max_digits=15, verbose_name='total untaxable amount'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.PointOfSales', verbose_name='point of sales'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_number',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='receipt number'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.ReceiptType', verbose_name='receipt type'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='related_receipts',
            field=models.ManyToManyField(blank=True, to='afip.Receipt', verbose_name='related receipts'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='service_end',
            field=models.DateField(blank=True, help_text='Date on which a service ended. No applicable for goods.', null=True, verbose_name='service end date'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='service_start',
            field=models.DateField(blank=True, help_text='Date on which a service started. No applicable for goods.', null=True, verbose_name='service start date'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, help_text='Must be equal to untaxed amount + exempt amount + taxes + vat.', max_digits=15, verbose_name='total amount'),
        ),
        migrations.AlterField(
            model_name='receiptbatch',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.PointOfSales', verbose_name='point of sales'),
        ),
        migrations.AlterField(
            model_name='receiptbatch',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.ReceiptType', verbose_name='receipt type'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='cae_expiration',
            field=models.DateField(verbose_name='cae expiration'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='observations',
            field=models.ManyToManyField(related_name='valiations', to='afip.Observation', verbose_name='observations'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='receipt',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validation', to='afip.Receipt', verbose_name='receipt'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='result',
            field=models.CharField(choices=[('A', 'approved'), ('R', 'rejected'), ('P', 'partial')], max_length=1, verbose_name='result'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.Validation', verbose_name='validation'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='aliquot',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='aliquot'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='amount'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='base_amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='base amount'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='description',
            field=models.CharField(max_length=80, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='tax_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.TaxType', verbose_name='tax type'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='amount'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='base_amount',
            field=models.DecimalField(decimal_places=2, max_digits=15, verbose_name='base amount'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='vat_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.VatType', verbose_name='vat type'),
        ),
        migrations.AddField(
            model_name='receiptpdf',
            name='receipt',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='afip.Receipt', verbose_name='receipt'),
        ),
        migrations.AddField(
            model_name='receiptentry',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entries', to='afip.Receipt', verbose_name='receipt'),
        ),
        migrations.AlterField(
            model_name='pointofsales',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_of_sales', to='afip.TaxPayer', verbose_name='owner'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='client_name',
            field=models.CharField(max_length=128, verbose_name='client name'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='issuing_email',
            field=models.CharField(max_length=128, null=True, verbose_name='issuing email'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='issuing_name',
            field=models.CharField(max_length=128, verbose_name='issuing name'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='pdf_file',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name='pdf file'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='issuing_email',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='issuing email'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='pdf_file',
            field=models.FileField(blank=True, null=True, upload_to='receipts', verbose_name='pdf file'),
        ),
        migrations.AddField(
            model_name='receiptentry',
            name='vat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipt_entries', to='afip.VatType', verbose_name='vat'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='result',
            field=models.CharField(choices=[('A', 'approved'), ('R', 'rejected')], max_length=1, verbose_name='result'),
        ),
        migrations.RenameField(
            model_name='receiptentry',
            old_name='amount',
            new_name='quantity',
        ),
        migrations.AlterField(
            model_name='receipt',
            name='issued_date',
            field=models.DateField(help_text='Can diverge up to 5 days for goods, or 10 days otherwise', verbose_name='issued date'),
        ),
        migrations.AlterField(
            model_name='receiptentry',
            name='quantity',
            field=models.PositiveSmallIntegerField(verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='sales_terms',
            field=models.CharField(help_text='Should be something like "Cash", "Payable in 30 days", etc', max_length=48, verbose_name='sales terms'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='cae',
            field=models.CharField(help_text='The CAE as returned by the AFIP', max_length=14, verbose_name='cae'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='cae_expiration',
            field=models.DateField(help_text='The CAE expiration as returned by the AFIP', verbose_name='cae expiration'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='observations',
            field=models.ManyToManyField(help_text='The observations as returned by the AFIP. These are generally present for failed validations.', related_name='validations', to='afip.Observation', verbose_name='observations'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='receipt',
            field=models.OneToOneField(help_text='The Receipt for which this validation applies', on_delete=django.db.models.deletion.CASCADE, related_name='validation', to='afip.Receipt', verbose_name='receipt'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='result',
            field=models.CharField(choices=[('A', 'approved'), ('R', 'rejected')], help_text='Indicates whether the validation was succesful or not', max_length=1, verbose_name='result'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(help_text='The validation for the batch that produced this instance.', on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='afip.Validation', verbose_name='validation'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='issued_date',
            field=models.DateField(help_text='Can diverge up to 5 days for good, or 10 days otherwise', verbose_name='issued date'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='concept',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.ConceptType', verbose_name='concept'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(help_text='Currency in which this receipt is issued.', on_delete=django.db.models.deletion.PROTECT, related_name='documents', to='afip.CurrencyType', verbose_name='currency'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='document_type',
            field=models.ForeignKey(help_text='The document type of the customer to whom this receipt is addressed', on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.DocumentType', verbose_name='document type'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.PointOfSales', verbose_name='point of sales'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.ReceiptType', verbose_name='receipt type'),
        ),
        migrations.AlterField(
            model_name='receiptbatch',
            name='point_of_sales',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='afip.PointOfSales', verbose_name='point of sales'),
        ),
        migrations.AlterField(
            model_name='receiptbatch',
            name='receipt_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='afip.ReceiptType', verbose_name='receipt type'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='receipt',
            field=models.OneToOneField(help_text='The Receipt for which this validation applies', on_delete=django.db.models.deletion.PROTECT, related_name='validation', to='afip.Receipt', verbose_name='receipt'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(help_text='The validation for the batch that produced this instance.', on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.Validation', verbose_name='validation'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='taxes', to='afip.Receipt'),
        ),
        migrations.AlterField(
            model_name='tax',
            name='tax_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='afip.TaxType', verbose_name='tax type'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='receipt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vat', to='afip.Receipt'),
        ),
        migrations.AlterField(
            model_name='vat',
            name='vat_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='afip.VatType', verbose_name='vat type'),
        ),
        migrations.AddField(
            model_name='receiptvalidation',
            name='processed_date',
            field=models.DateTimeField(null=True, verbose_name='processed date'),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(help_text='The validation for the batch that produced this instance.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='afip.Validation', verbose_name='validation'),
        ),
        migrations.RunPython(
            code=backfill_processed_dates,
        ),
        migrations.RemoveField(
            model_name='receipt',
            name='batch',
        ),
        migrations.RemoveField(
            model_name='receiptvalidation',
            name='validation',
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='processed_date',
            field=models.DateTimeField(verbose_name='processed date'),
        ),
        migrations.DeleteModel(
            name='Validation',
        ),
        migrations.DeleteModel(
            name='ReceiptBatch',
        ),
        migrations.AlterModelOptions(
            name='receipt',
            options={'ordering': ('issued_date',), 'verbose_name': 'receipt', 'verbose_name_plural': 'receipts'},
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency_quote',
            field=models.DecimalField(decimal_places=6, default=1, help_text='Quote of the day for the currency used in the receipt', max_digits=10, verbose_name='currency quote'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_number',
            field=models.PositiveIntegerField(blank=True, help_text='If left blank, the next valid number will assigned when validating the receipt.', null=True, verbose_name='receipt number'),
        ),
        migrations.AlterField(
            model_name='taxpayer',
            name='certificate',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name='certificate'),
        ),
        migrations.AlterField(
            model_name='taxpayer',
            name='key',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name='key'),
        ),
        migrations.AddField(
            model_name='taxpayer',
            name='certificate_expiration',
            field=models.DateTimeField(editable=False, help_text='Stores expiration for the current certificate. Note that this field is updated pre-save, so the value may be invalid for unsaved models.', null=True, verbose_name='certificate expiration'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(default=django_afip.models.first_currency, help_text='Currency in which this receipt is issued.', on_delete=django.db.models.deletion.PROTECT, related_name='documents', to='afip.CurrencyType', verbose_name='currency'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AlterField(
            model_name='taxpayerprofile',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AddField(
            model_name='taxpayer',
            name='active_since',
            field=models.DateField(default=datetime.datetime(1970, 1, 1, 0, 0), help_text=('Date since which this taxpayer has been legally active.',), verbose_name='active since'),
            preserve_default=False,
        ),
        migrations.RunPython(
            code=move_active_since,
        ),
        migrations.RemoveField(
            model_name='taxpayerprofile',
            name='active_since',
        ),
        migrations.AlterField(
            model_name='taxpayer',
            name='active_since',
            field=models.DateField(help_text='Date since which this taxpayer has been legally active.', verbose_name='active since'),
        ),
        migrations.AddField(
            model_name='receiptpdf',
            name='client_vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, null=True, verbose_name='client vat condition'),
        ),
        migrations.RunPython(
            code=copy_vat_condition,
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='client_vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='client vat condition'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='pdf_file',
            field=models.FileField(blank=True, help_text='The actual file which contains the PDF data.', null=True, upload_to='receipts', verbose_name='pdf file'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='client_vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Responsable No Inscripto', 'IVA Responsable No Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='client vat condition'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Responsable No Inscripto', 'IVA Responsable No Inscripto'), ('IVA Exento', 'IVA Exento'), ('No Responsable IVA', 'No Responsable IVA'), ('Responsable Monotributo', 'Responsable Monotributo')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AlterField(
            model_name='taxpayerprofile',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Responsable No Inscripto', 'IVA Responsable No Inscripto'), ('IVA Exento', 'IVA Exento'), ('No Responsable IVA', 'No Responsable IVA'), ('Responsable Monotributo', 'Responsable Monotributo')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AlterField(
            model_name='receiptentry',
            name='vat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='receipt_entries', to='afip.VatType', verbose_name='vat'),
        ),
        migrations.AlterField(
            model_name='receiptpdf',
            name='client_address',
            field=models.TextField(blank=True, verbose_name='client address'),
        ),
    ]
