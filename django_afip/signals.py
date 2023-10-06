from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models.signals import pre_save
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
