from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0025_receipt__default_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptpdf',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='vat condition'),
        ),
        migrations.AlterField(
            model_name='taxpayerprofile',
            name='vat_condition',
            field=models.CharField(choices=[('IVA Responsable Inscripto', 'IVA Responsable Inscripto'), ('IVA Sujeto Exento', 'IVA Sujeto Exento'), ('Consumidor Final', 'Consumidor Final'), ('Responsable Monotributo', 'Responsable Monotributo'), ('Proveedor del Exterior', 'Proveedor del Exterior'), ('Cliente del Exterior', 'Cliente del Exterior'), ('IVA Liberado - Ley Nº 19.640', 'IVA Liberado - Ley Nº 19.640'), ('IVA Responsable Inscripto - Agente de Percepción', 'IVA Responsable Inscripto - Agente de Percepción'), ('Monotributista Social', 'Monotributista Social'), ('IVA no alcanzado', 'IVA no alcanzado')], max_length=48, verbose_name='vat condition'),
        ),
    ]
