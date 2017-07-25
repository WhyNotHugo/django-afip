from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0023_taxpayer__certs_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxpayer',
            name='certificate_expiration',
            field=models.DateTimeField(
                editable=False,
                help_text='Stores expiration for the current certificate. '
                'Note that this field is updated pre-save, so the value may '
                'be invalid for unsaved models.',
                null=True,
                verbose_name='certificate expiration',
            ),
        ),
    ]
