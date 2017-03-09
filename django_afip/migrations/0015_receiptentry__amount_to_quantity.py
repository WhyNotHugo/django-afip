from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0014_no_partially_validated_receiptvalidations'),
    ]

    operations = [
        migrations.RenameField(
            model_name='receiptentry',
            old_name='amount',
            new_name='quantity',
        ),
    ]
