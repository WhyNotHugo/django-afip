from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from django_afip import models


@receiver(pre_save, sender=models.TaxPayer)
def update_certificate_expiration(sender, instance, **kwargs):
    if instance.certificate:
        instance.certificate_expiration = instance.get_certificate_expiration()


@receiver(post_save, sender=models.ReceiptPDF)
def generate_receipt_pdf(sender, instance, **kwargs):
    if not instance.pdf_file and instance.receipt.is_validated:
        instance.save_pdf(save_model=True)
