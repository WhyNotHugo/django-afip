from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0011_receiptentry_discount_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OptionalType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=4, verbose_name="code")),
                (
                    "description",
                    models.CharField(max_length=250, verbose_name="description"),
                ),
                (
                    "valid_from",
                    models.DateField(blank=True, null=True, verbose_name="valid from"),
                ),
                (
                    "valid_to",
                    models.DateField(blank=True, null=True, verbose_name="valid until"),
                ),
            ],
            options={
                "verbose_name": "optional type",
                "verbose_name_plural": "optional types",
            },
        ),
        migrations.CreateModel(
            name="Optional",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "value",
                    models.CharField(max_length=250, verbose_name="optional value"),
                ),
                (
                    "optional_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="afip.optionaltype",
                        verbose_name="optional type",
                    ),
                ),
                (
                    "receipt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="optionals",
                        to="afip.receipt",
                    ),
                ),
            ],
            options={
                "verbose_name": "optional",
                "verbose_name_plural": "optionals",
            },
        ),
    ]
