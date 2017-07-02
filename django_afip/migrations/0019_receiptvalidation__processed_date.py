import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0018_on_delete_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptvalidation',
            name='processed_date',
            field=models.DateTimeField(
                verbose_name='processed date',
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='receiptvalidation',
            name='validation',
            field=models.ForeignKey(
                help_text=(
                    'The validation for the batch that produced this '
                    'instance.'
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='receipts',
                to='afip.Validation',
                verbose_name='validation',
            ),
        ),
    ]
