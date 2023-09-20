from __future__ import annotations

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("afip", "0006_delete_taxpayerextras"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authticket",
            name="service",
            field=models.CharField(
                help_text="Service for which this ticket has been authorized.",
                max_length=6,
                verbose_name="service",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="currency_quote",
            field=models.DecimalField(
                decimal_places=6,
                default=1,
                help_text="The currency's quote on the day this receipt was issued.",
                max_digits=10,
                verbose_name="currency quote",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="document_number",
            field=models.BigIntegerField(
                help_text="The document number of the recipient of this receipt.",
                verbose_name="document number",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="document_type",
            field=models.ForeignKey(
                help_text="The document type of the recipient of this receipt.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receipts",
                to="afip.documenttype",
                verbose_name="document type",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="exempt_amount",
            field=models.DecimalField(
                decimal_places=2,
                help_text=(
                    "Only for categories which are tax-exempt.<br>"
                    "For C-type receipts, this must be zero."
                ),
                max_digits=15,
                verbose_name="exempt amount",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="issued_date",
            field=models.DateField(
                help_text="Can diverge up to 5 days for good, or 10 days otherwise.",
                verbose_name="issued date",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="net_taxed",
            field=models.DecimalField(
                decimal_places=2,
                help_text=(
                    "The total amount to which taxes apply.<br>"
                    "For C-type receipts, this is equal to the subtotal."
                ),
                max_digits=15,
                verbose_name="total taxable amount",
            ),
        ),
        migrations.AlterField(
            model_name="receipt",
            name="net_untaxed",
            field=models.DecimalField(
                decimal_places=2,
                help_text=(
                    "The total amount to which taxes do not apply.<br>"
                    "For C-type receipts, this must be zero."
                ),
                max_digits=15,
                verbose_name="total untaxable amount",
            ),
        ),
        migrations.AlterField(
            model_name="receiptpdf",
            name="sales_terms",
            field=models.CharField(
                help_text='Should be something like "Cash", "Payable in 30 days", etc.',
                max_length=48,
                verbose_name="sales terms",
            ),
        ),
        migrations.AlterField(
            model_name="receiptvalidation",
            name="cae",
            field=models.CharField(
                help_text="The CAE as returned by the AFIP.",
                max_length=14,
                verbose_name="cae",
            ),
        ),
        migrations.AlterField(
            model_name="receiptvalidation",
            name="cae_expiration",
            field=models.DateField(
                help_text="The CAE expiration as returned by the AFIP.",
                verbose_name="cae expiration",
            ),
        ),
        migrations.AlterField(
            model_name="receiptvalidation",
            name="receipt",
            field=models.OneToOneField(
                help_text="The Receipt for which this validation applies.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="validation",
                to="afip.receipt",
                verbose_name="receipt",
            ),
        ),
        migrations.AlterField(
            model_name="receiptvalidation",
            name="result",
            field=models.CharField(
                choices=[("A", "approved"), ("R", "rejected")],
                help_text="Indicates whether the validation was succesful or not.",
                max_length=1,
                verbose_name="result",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayer",
            name="certificate_expiration",
            field=models.DateTimeField(
                editable=False,
                help_text=(
                    "Stores expiration for the current certificate.<br>"
                    "Note that this field is updated pre-save, so the value may be "
                    "invalid for unsaved models."
                ),
                null=True,
                verbose_name="certificate expiration",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayer",
            name="is_sandboxed",
            field=models.BooleanField(
                help_text=(
                    "Indicates if this taxpayer should use with the sandbox "
                    "servers rather than the production servers."
                ),
                verbose_name="is sandboxed",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayerprofile",
            name="issuing_address",
            field=models.TextField(
                help_text="The address of the issuing entity as shown on receipts.",
                verbose_name="issuing address",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayerprofile",
            name="issuing_email",
            field=models.CharField(
                blank=True,
                help_text="The email of the issuing entity as shown on receipts.",
                max_length=128,
                null=True,
                verbose_name="issuing email",
            ),
        ),
        migrations.AlterField(
            model_name="taxpayerprofile",
            name="issuing_name",
            field=models.CharField(
                help_text="The name of the issuing entity as shown on receipts.",
                max_length=128,
                verbose_name="issuing name",
            ),
        ),
    ]
