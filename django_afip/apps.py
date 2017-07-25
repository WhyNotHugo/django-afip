from django.apps import AppConfig

from . import monkeys


class AfipConfig(AppConfig):
    name = 'django_afip'
    label = 'afip'
    verbose_name = 'AFIP'

    def ready(self):
        # Register app signals:
        from django_afip import signals  # noqa: F401
        monkeys.patch_https_for_afip()
