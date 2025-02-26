from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from django_afip import clients, models, serializers


class Command(BaseCommand):
    help = _(
        "Retrieves all the ClientVatConditions from the AFIP server and updates it in the DB."
    )
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            "cuit",
            type=int,
            help=_("CUIT of the tax payer to be used to authenticate."),
        )

    def handle(self, *args, **options) -> None:
        from django_afip.models import TaxPayer

        tax_payer = TaxPayer.objects.get(cuit=options["cuit"])
        ticket = tax_payer.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", sandbox=tax_payer.is_sandboxed)
        response = client.service.FEParamGetCondicionIvaReceptor(
            serializers.serialize_ticket(ticket),
        )

        for condition in response.ResultGet.CondicionIvaReceptor:
            models.ClientVatCondition.objects.get_or_create(
                code=condition.Id,
                defaults={
                    "description": condition.Desc,
                    "cmp_clase": condition.Cmp_Clase,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Loaded {condition.Desc}"))
        self.stdout.write(self.style.SUCCESS("All done!"))
