from django.apps import AppConfig

from . import monkeys


class AfipConfig(AppConfig):
    name = 'django_afip'
    label = 'afip'
    verbose_name = 'AFIP'

    def ready(self):
        monkeys.patch_https_for_afip()
