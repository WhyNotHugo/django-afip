import django.db.models.deletion
from django.db import migrations, models

import django_afip.models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0024_taxpayer__certificate_expiration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receipt',
            name='currency',
            field=models.ForeignKey(
                default=django_afip.models.first_currency,
                help_text='Currency in which this receipt is issued.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='documents',
                to='afip.CurrencyType',
                verbose_name='currency',
            ),
        ),
    ]
