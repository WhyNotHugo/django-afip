"""Script used to generate AFIP metadata fixtures.

This script is used to generate the fixtures with AFIP metadata. It is only used to
BUILD django_afip, and should not be used directly by third-party apps.
"""
import django
from django.core import management


if __name__ == "__main__":
    # Set up django...
    django.setup()
    management.call_command("migrate")

    from django_afip.factories import TaxPayerFactory
    from django_afip.models import GenericAfipType

    # Initialise (uses test credentials).
    TaxPayerFactory()

    # Fetch and dump data:
    for model in GenericAfipType.SUBCLASSES:
        model.objects.populate()

        label = model._meta.label.split(".")[1].lower()

        management.call_command(
            "dumpdata",
            f"afip.{label}",
            format="yaml",
            use_natural_primary_keys=True,
            output=f"django_afip/fixtures/{label}.yaml",
        )
