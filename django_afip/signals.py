from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from django_afip import models

if TYPE_CHECKING:
    from django.db.models import Model


@receiver(pre_save, sender=models.TaxPayer)
def update_certificate_expiration(
    sender: type[Model],
    instance: models.TaxPayer,
    **kwargs,
) -> None:
    if instance.certificate:
        instance.certificate_expiration = instance.get_certificate_expiration()


FILE_FIELDS = ['certificate', 'logo']

# Store old files before saving.
@receiver(pre_save, sender=models.TaxPayer)
def store_old_files(
    sender: type[Model],
    instance: models.TaxPayer,
    **kwargs,
) -> None:
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            # Save the reference of the old files in the model.
            instance._old_files = {field: getattr(old_instance, field) for field in FILE_FIELDS}
        except sender.DoesNotExist:
            instance._old_files = {}

# Delete old files after saving.
@receiver(post_save, sender=models.TaxPayer)
def delete_file_taxpayer(
    sender: type[Model],
    instance: models.TaxPayer,
    **kwargs,
) -> None:
    if not instance.pk:
        return # The instance is new, there are no old files to delete.
    
    old_files = getattr(instance, '_old_files', {})

    for field_name in FILE_FIELDS:
        old_file = old_files.get(field_name)
        new_file = getattr(instance, field_name)

        if old_file and old_file != new_file:
            # Delete the old file from storage.
            old_file.delete(save=False)