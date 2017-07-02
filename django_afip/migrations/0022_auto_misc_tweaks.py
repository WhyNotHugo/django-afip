from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0021_drop_batches'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='receipt',
            options={
                'ordering': ('issued_date',),
                'verbose_name': 'receipt',
                'verbose_name_plural': 'receipts',
            },
        ),
        migrations.AlterField(
            model_name='receipt',
            name='currency_quote',
            field=models.DecimalField(
                decimal_places=6,
                default=1,
                help_text=(
                    'Quote of the day for the currency used in the receipt'
                ),
                max_digits=10,
                verbose_name='currency quote',
            ),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='receipt_number',
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    'If left blank, the next valid number will assigned when '
                    'validating the receipt.'
                ),
                null=True,
                verbose_name='receipt number',
            ),
        ),
    ]
