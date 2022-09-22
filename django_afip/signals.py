from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver

from django_afip import models, exceptions


@receiver(pre_save, sender=models.TaxPayer)
def update_certificate_expiration(sender, instance: models.TaxPayer, **kwargs):
    if instance.certificate:
        instance.certificate_expiration = instance.get_certificate_expiration()


@receiver(post_save, sender=models.ReceiptPDF)
def generate_receipt_pdf(sender, instance: models.ReceiptPDF, **kwargs):
    if not instance.pdf_file:
        if "CAEA" in instance.receipt.point_of_sales.issuance_type:
            instance.save_pdf(save_model=True)
        if (
            "CAE" in instance.receipt.point_of_sales.issuance_type
            and instance.receipt.is_validated
        ):
            instance.save_pdf(save_model=True)


@receiver(pre_save, sender=models.Receipt)
def save_caea_data(sender, instance: models.TaxPayer, **kwargs):
    if "CAEA" in instance.point_of_sales.issuance_type:
        if instance.caea == "" or instance.caea == None:
            caea = models.Caea.objects.all().filter(active=True)
            if caea.count() != 1:
                raise exceptions.CaeaCountError
            else:
                if instance.caea == None or instance.caea == "":
                    instance.caea = caea[0]

            if instance.receipt_number == None or instance.receipt_number == "":
                counter = models.CaeaCounter.objects.get_or_create(
                    pos=instance.point_of_sales, receipt_type=instance.receipt_type
                )[0]
                instance.receipt_number = counter.next_value
                counter.next_value += 1
                counter.save()
