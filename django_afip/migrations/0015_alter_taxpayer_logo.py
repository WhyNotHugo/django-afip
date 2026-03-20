from __future__ import annotations

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0014_alter_pointofsales_blocked_alter_taxpayer_logo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taxpayer",
            name="logo",
            field=models.ImageField(
                blank=True,
                help_text="A logo to use when generating printable receipts.",
                null=True,
                upload_to="afip/taxpayers/logos/",
                verbose_name="logo",
            ),
        ),
    ]
