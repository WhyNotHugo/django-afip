from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from django_afip import models


class Command(BaseCommand):
    help = _("Loads fixtures with metadata from AFIP.")  # noqa: A003
    requires_migrations_checks = True

    def handle(self, *args, **options) -> None:
        models.load_metadata()
