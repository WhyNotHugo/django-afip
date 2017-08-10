from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0035_receiptentry__vat__blankable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptpdf',
            name='client_address',
            field=models.TextField(blank=True, verbose_name='client address'),
        ),
    ]
