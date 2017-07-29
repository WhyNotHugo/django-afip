from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0025_receipt__default_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptpdf',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('Monotributista Social', 'Monotributista Social'), ('Consumidor Final', 'Consumidor Final'), ('IVA no alcanzado', 'IVA no alcanzado'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('Responsable Monotributo', 'Responsable Monotributo')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AlterField(
            model_name='taxpayerprofile',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('Monotributista Social', 'Monotributista Social'), ('Consumidor Final', 'Consumidor Final'), ('IVA no alcanzado', 'IVA no alcanzado'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('Responsable Monotributo', 'Responsable Monotributo')], max_length=48, verbose_name='vat condition'),
        ),
    ]
