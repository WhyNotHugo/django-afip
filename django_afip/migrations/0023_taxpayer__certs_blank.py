from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0022_auto_misc_tweaks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taxpayer',
            name='certificate',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='',
                verbose_name='certificate',
            ),
        ),
        migrations.AlterField(
            model_name='taxpayer',
            name='key',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='',
                verbose_name='key',
            ),
        ),
    ]
