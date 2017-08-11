import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0001_squashed_0036_receiptpdf__client_address__blank'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxPayerExtras',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    )
                ),
                (
                    'logo',
                    models.ImageField(
                        blank=True,
                        help_text=('A logo to use when generating printable '
                                   'receipts.'),
                        null=True,
                        upload_to='afip/taxpayers/logos/',
                        verbose_name='pdf file',
                    )
                ),
                (
                    'taxpayer',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='extras',
                        to='afip.TaxPayer',
                        verbose_name='taxpayer',
                    )
                ),
            ],
            options={
                'verbose_name': 'taxpayer extras',
                'verbose_name_plural': 'taxpayers extras',
            },
        ),
    ]
