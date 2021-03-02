from django.apps import AppConfig


class AfipConfig(AppConfig):
    name = "django_afip"
    label = "afip"
    verbose_name = "AFIP"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # Register app signals:
        from django_afip import signals  # noqa: F401
