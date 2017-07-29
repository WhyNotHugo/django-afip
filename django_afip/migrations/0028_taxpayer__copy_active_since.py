from django.db import migrations


def move_active_since(apps, schema_editor):
    TaxPayerProfile = apps.get_model('afip', 'TaxPayerProfile')
    profiles = TaxPayerProfile.objects.select_related('taxpayer')

    for profile in profiles:
        profile.taxpayer.active_since = profile.active_since
        profile.taxpayer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0027_taxpayer__active_since'),
    ]

    operations = [
        migrations.RunPython(move_active_since),
    ]
