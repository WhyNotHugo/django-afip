from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from django_afip import models


class Command(BaseCommand):
    help = _('Fetches required AFIP metadata and stores it locally')
    requires_migrations_checks = True

    def handle(self, *args, **options):
        models.populate_all()
