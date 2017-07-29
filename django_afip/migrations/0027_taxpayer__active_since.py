from datetime import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0026_vat_conditions'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxpayer',
            name='active_since',
            field=models.DateField(
                default=datetime.fromtimestamp(0),
                help_text=(
                    'Date since which this taxpayer has been legally active.',
                ),
                verbose_name='active since',
            ),
            preserve_default=False,
        ),
    ]
