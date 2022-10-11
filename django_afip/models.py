from __future__ import annotations

import base64
import logging
import os
import random
import re
import warnings
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from decimal import Decimal
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import BinaryIO
from uuid import uuid4

from django.conf import settings
from django.core import management
from django.core.files import File
from django.core.files.storage import Storage
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import RegexValidator
from django.db import connection
from django.db import models
from django.db.models import CheckConstraint
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.utils.dateparse import parse_date
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_renderpdf.helpers import render_pdf
from lxml import etree
from lxml.builder import E
from OpenSSL.crypto import FILETYPE_PEM
from OpenSSL.crypto import X509
from OpenSSL.crypto import load_certificate
from zeep.exceptions import Fault

from django_afip.clients import TZ_AR

from . import clients
from . import crypto
from . import exceptions
from . import parsers
from . import serializers

logger = logging.getLogger(__name__)

# http://www.afip.gov.ar/afip/resol1415_anexo2.html
VAT_CONDITIONS = (
    "IVA Responsable Inscripto",
    "IVA Responsable No Inscripto",
    "IVA Exento",
    "No Responsable IVA",
    "Responsable Monotributo",
)
# NOTE: If you find a VAT condition not listed here, please open an issue, and
# a reference to where it's defined.
CLIENT_VAT_CONDITIONS = (
    "IVA Responsable Inscripto",
    "IVA Responsable No Inscripto",
    "IVA Sujeto Exento",
    "Consumidor Final",
    "Responsable Monotributo",
    "Proveedor del Exterior",
    "Cliente del Exterior",
    "IVA Liberado - Ley Nº 19.640",
    "IVA Responsable Inscripto - Agente de Percepción",
    "Monotributista Social",
    "IVA no alcanzado",
)


def load_metadata() -> None:
    """Loads metadata from fixtures into the database."""

    for model in GenericAfipType.SUBCLASSES:
        label = model._meta.label.split(".")[1].lower()
        management.call_command("loaddata", label, app="afip")


def check_response(response) -> None:
    """Check that a response is not an error.

    AFIP allows us to create valid tickets with invalid key/CUIT pairs, so we
    can end up with tickets that fail on any service.

    Due to how zeep works, we can't quite catch these sort of errors on some
    middleware level (well, honestly, we need to do a large refactor).

    This method checks if responses have an error, and raise a readable
    message.
    """
    if "Errors" in response:
        if response.Errors:
            raise exceptions.AfipException(response)
    elif "errorConstancia" in response:
        if response.errorConstancia:
            raise exceptions.AfipException(response)


def first_currency() -> int | None:
    """Returns the id for the first currency

    The `default` parameter of a foreign key *MUST* be a primary key (and not
    an instance), else migrations break. This helper method exists solely for
    that purpose.
    """
    ct = CurrencyType.objects.filter(code="PES").first()
    if ct:
        return ct.pk


def _get_storage_from_settings(setting_name: str) -> Storage:
    path = getattr(settings, setting_name, None)
    if not path:
        return import_string(settings.DEFAULT_FILE_STORAGE)()
    return import_string(path)


def caea_is_active(valid_since, valid_to) -> bool:
    valid_since = parsers.parse_date(valid_since)
    valid_to = parsers.parse_date(valid_to)
    today = datetime.now().date()

    if valid_since <= today <= valid_to:
        return True
    else:
        return False


class GenericAfipTypeManager(models.Manager):
    """Default Manager for GenericAfipType."""

    def __init__(self, service_name: str, type_name: str):
        """Create a new Manager instance for a GenericAfipType.

        This should generally only be required to manually populate a single
        type with upstream data.
        """
        super().__init__()
        self.__service_name = service_name
        self.__type_name = type_name

    def populate(self, ticket: AuthTicket = None) -> None:
        """Fetch and save data for this model from AFIP's WS.

        Direct usage of this method is discouraged, use
        :func:`~.models.load_metadata` instead.
        """
        ticket = ticket or AuthTicket.objects.get_any_active("wsfe")
        client = clients.get_client("wsfe", ticket.owner.is_sandboxed)
        service = getattr(client.service, self.__service_name)
        response_xml = service(serializers.serialize_ticket(ticket))

        check_response(response_xml)

        for result in getattr(response_xml.ResultGet, self.__type_name):
            self.get_or_create(
                code=result.Id,
                description=result.Desc,
                valid_from=parsers.parse_date(result.FchDesde),
                valid_to=parsers.parse_date(result.FchHasta),
            )

    def get_by_natural_key(self, code: str) -> GenericAfipType:
        return self.get(code=code)

    def exists_by_natural_key(self, code: str) -> bool:
        return self.filter(code=code).exists()


class GenericAfipType(models.Model):
    """An abstract class for several of AFIP's metadata types.

    You should not use this class directly, only subclasses of it. You should
    not create subclasses of this model unless you really know what you're doing.
    """

    SUBCLASSES: list[type[models.Model]] = []

    def __init_subclass__(cls, **kwargs):
        """Keeps a registry of known subclasses."""
        super().__init_subclass__(**kwargs)
        GenericAfipType.SUBCLASSES.append(cls)

    code = models.CharField(
        _("code"),
        max_length=3,
    )
    description = models.CharField(
        _("description"),
        max_length=250,
    )
    valid_from = models.DateField(
        _("valid from"),
        null=True,
        blank=True,
    )
    valid_to = models.DateField(
        _("valid until"),
        null=True,
        blank=True,
    )

    def natural_key(self) -> tuple[str]:
        return (self.code,)

    def __str__(self) -> str:
        return self.description

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):
    """An AFIP receipt type.

    See the AFIP's documentation for details on each receipt type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposCbte", "CbteTipo")

    class Meta:
        verbose_name = _("receipt type")
        verbose_name_plural = _("receipt types")


class ConceptType(GenericAfipType):
    """An AFIP concept type.

    See the AFIP's documentation for details on each concept type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposConcepto", "ConceptoTipo")

    class Meta:
        verbose_name = _("concept type")
        verbose_name_plural = _("concept types")


class DocumentType(GenericAfipType):
    """An AFIP document type.

    See the AFIP's documentation for details on each document type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposDoc", "DocTipo")

    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class VatType(GenericAfipType):
    """An AFIP VAT type.

    See the AFIP's documentation for details on each VAT type.
    """

    @property
    def as_decimal(self) -> Decimal:
        """Return this VatType as a Decimal.

        Parses the percent amount from the ``description`` field. This number is usable
        when calculating the Vat for entries which have this type. If Vat is 21%, then
        the returned value is ``Decimal("0.21")``.

        Assuming that an item pays 21% vat, when using a net price for the calculation,
        the following are all correct::

            total_price = net_price * Decimal(1.21)
            vat = net_price * Decimal(0.21)
            vat = total_price - net_price

        If using the total price, this approach should be used (this can be derived from
        the above)::

            net_price = total_price / Decimal(1.21)
            vat = total_price - net_price

        Keep in mind that AFIP requires the usage of "round half even", which is what
        Python's ``Decimal`` class uses by default (See ``decimal.ROUND_HALF_EVEN``).
        """
        match = re.match(r"^([0-9]{1,2}\.?[0-9]{0,2})%$", self.description)
        if not match:
            raise ValueError("The description for this VatType is not a percentage.")
        return Decimal(match.groups()[0]) / 100

    objects = GenericAfipTypeManager("FEParamGetTiposIva", "IvaTipo")

    class Meta:
        verbose_name = _("vat type")
        verbose_name_plural = _("vat types")


class TaxType(GenericAfipType):
    """An AFIP tax type.

    See the AFIP's documentation for details on each tax type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposTributos", "TributoTipo")

    class Meta:
        verbose_name = _("tax type")
        verbose_name_plural = _("tax types")


class CurrencyType(GenericAfipType):
    """An AFIP curreny type.

    See the AFIP's documentation for details on each currency type.
    """

    objects = GenericAfipTypeManager("FEParamGetTiposMonedas", "Moneda")

    def __str__(self) -> str:
        return f"{self.description} ({self.code})"

    class Meta:
        verbose_name = _("currency type")
        verbose_name_plural = _("currency types")


class TaxPayer(models.Model):
    """Represents an AFIP TaxPayer.

    Note that multiple instances of this object can actually represent the same
    taxpayer, each using a different key.

    The following fields are only used for generating printables, and are never
    sent to AFIP, hence, are entirely optional:

    - logo
    """

    # XXX: Split this into TaxPayer and Credentials
    # The former has a unique CUIT, which will be its natural key.
    # The latter has the key and cert and alike.
    #
    # For the migration path:
    # - Make sure that if there's 1:1 TaxPayer:Credentials,
    #   everything continues to work as it does now.
    # - Provide data migrations

    name = models.CharField(
        _("name"),
        max_length=32,
        help_text=_("A friendly name to recognize this taxpayer."),
    )
    key = models.FileField(
        verbose_name=_("key"),
        upload_to="afip/taxpayers/keys/",
        storage=_get_storage_from_settings("AFIP_KEY_STORAGE"),
        blank=True,
        null=True,
    )
    certificate = models.FileField(
        verbose_name=_("certificate"),
        upload_to="afip/taxpayers/certs/",
        storage=_get_storage_from_settings("AFIP_CERT_STORAGE"),
        blank=True,
        null=True,
    )
    cuit = models.BigIntegerField(
        _("cuit"),
    )
    is_sandboxed = models.BooleanField(
        _("is sandboxed"),
        help_text=_(
            "Indicates if this taxpayer should use with the sandbox servers "
            "rather than the production servers."
        ),
    )
    certificate_expiration = models.DateTimeField(
        _("certificate expiration"),
        editable=False,
        null=True,  # Either no cert, or an old TaxPayer.
        help_text=_(
            "Stores expiration for the current certificate.<br>Note that this "
            "field is updated pre-save, so the value may be invalid for unsaved models."
        ),
    )
    active_since = models.DateField(
        _("active since"),
        help_text=_("Date since which this taxpayer has been legally active."),
    )
    logo = models.ImageField(
        verbose_name=_("logo"),
        upload_to="afip/taxpayers/logos/",
        storage=_get_storage_from_settings("AFIP_LOGO_STORAGE"),
        blank=True,
        null=True,
        help_text=_("A logo to use when generating printable receipts."),
    )

    @property
    def logo_as_data_uri(self) -> str:
        """This TaxPayer's logo as a data uri.

        This can be used to embed the image into an HTML or PDF file.
        """
        _, ext = os.path.splitext(self.logo.file.name)
        with self.logo.open() as f:
            data = base64.b64encode(f.read())

        return "data:image/{};base64,{}".format(
            ext[1:], data.decode()  # Remove the leading dot.
        )

    @property
    def certificate_object(self) -> X509 | None:
        """Returns the certificate as an OpenSSL object

        Returns the certificate as an OpenSSL object (rather than as a file
        object).
        """

        if not self.certificate:
            return None
        self.certificate.seek(0)
        return load_certificate(FILETYPE_PEM, self.certificate.read())

    def get_certificate_expiration(self) -> datetime | None:
        """Return the certificate expiration from the current certificate

        Gets the certificate expiration from the certificate file. Note that
        this value is stored into ``certificate_expiration`` when an instance
        is saved, so you should generally prefer that method (since this one
        requires reading and parsing the entire certificate).
        """
        cert = self.certificate_object
        if not cert:
            return None
        not_after = cert.get_notAfter()
        if not not_after:
            return None
        datestring = not_after.decode()
        dt = datetime.strptime(datestring, "%Y%m%d%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc)

    def generate_key(self, force=False) -> bool:
        """Creates a key file for this TaxPayer

        Creates a key file for this TaxPayer if it does not have one, and
        immediately saves it.

        A new key will not be generated if one is already set, unless the ``force``
        parameter is true. This is to prevent overwriting a potentially in-use key.

        Returns True if and only if a key was created.
        """
        if self.key and not force:
            logger.warning("Tried to generate key for a taxpayer that already had one")
            return False

        with NamedTemporaryFile(suffix=".key") as file_:
            crypto.create_key(file_)
            self.key = File(file_, name=f"{uuid4().hex}.key")
            self.save()

        return True

    def generate_csr(self, basename="djangoafip") -> BinaryIO:
        """Creates a CSR with this TaxPayer's key

        The CSR (certificate signing request) can be used to request a new certificate
        via AFIP's website. After generating a new CSR, it should be manually uploaded
        to AFIP's website, and a new certificate will be returned. That certificate
        should be uploaded to the ``certificate`` field.

        It is safe to use with when renovating expired certificates on production
        systems.
        """
        csr = BytesIO()
        crypto.create_csr(
            self.key.file,
            self.name,
            f"{basename}{int(datetime.now().timestamp())}",
            f"CUIT {self.cuit}",
            csr,
        )
        csr.seek(0)
        return csr

    def create_ticket(self, service: str) -> AuthTicket:
        """Create an AuthTicket for a given service.

        Tickets are saved to the database. It is recommended to use the
        :meth:`~.TaxPayer.get_or_create_ticket` method instead.
        """
        ticket = AuthTicket(owner=self, service=service)
        ticket.authorize()
        return ticket

    def get_ticket(self, service: str) -> AuthTicket | None:
        """Return an existing AuthTicket for a given service, if any.

        It is recommended to use the :meth:`~.TaxPayer.get_or_create_ticket` method
        instead.
        """
        return self.auth_tickets.filter(
            expires__gt=datetime.now(timezone.utc),
            service=service,
        ).last()

    def get_or_create_ticket(self, service: str) -> AuthTicket:
        """
        Return or create a new AuthTicket for a given serivce.

        Return an existing ticket for a service if one is available, otherwise,
        create a new one and return that.

        This is generally the preferred method of obtaining tickets for any
        service.
        """
        return self.get_ticket(service) or self.create_ticket(service)

    def fetch_points_of_sales(
        self,
        ticket: AuthTicket = None,
    ) -> list[tuple[PointOfSales, bool]]:
        """
        Fetch all point of sales objects.

        Fetch all point of sales from the WS and store (or update) them
        locally.

        Returns a list of tuples with the format ``(pos, created,)``.
        """
        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)
        response = client.service.FEParamGetPtosVenta(
            serializers.serialize_ticket(ticket),
        )
        check_response(response)

        results = []
        for pos_data in response.ResultGet.PtoVenta:
            results.append(
                PointOfSales.objects.update_or_create(
                    number=pos_data.Nro,
                    owner=self,
                    defaults={
                        "issuance_type": pos_data.EmisionTipo,
                        "blocked": pos_data.Bloqueado == "S",
                        "drop_date": parsers.parse_date(pos_data.FchBaja),
                    },
                )
            )

        return results

    def get_caea(
        self,
        period: int = None,
        order: int = None,
        ticket: AuthTicket = None,
    ) -> Caea:
        """
        Get a CAEA code for the TaxPayer, if a CAEA alredy exists the check_response will raise and exception

        Returns a caea object.
        """
        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)

        response = client.service.FECAEASolicitar(
            serializers.serialize_ticket(ticket),
            Periodo=serializers.serialize_caea_period(period),
            Orden=serializers.serialize_caea_order(order),
        )
        check_response(
            response
        )  # be aware that this func raise an error if it's present

        caea = Caea.objects.create(
            caea_code=int(response.ResultGet.CAEA),
            period=int(response.ResultGet.Periodo),
            order=int(response.ResultGet.Orden),
            valid_since=parsers.parse_date(response.ResultGet.FchVigDesde),
            expires=parsers.parse_date(response.ResultGet.FchVigHasta),
            generated=parsers.parse_datetime(response.ResultGet.FchProceso),
            final_date_inform=parsers.parse_date(response.ResultGet.FchTopeInf),
            taxpayer=self,
            active=caea_is_active(
                valid_since=response.ResultGet.FchVigDesde,
                valid_to=response.ResultGet.FchVigHasta,
            ),
        )
        return caea

    def consult_caea(
        self,
        period: str = None,
        order: int = None,
        ticket: AuthTicket = None,
    ) -> Caea:
        """
        Consult the CAEA code  given by AFIP, if for some reason the code it's not saved in the db it will be created

        Returns a CAEA model.
        """
        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)
        response = client.service.FECAEAConsultar(
            serializers.serialize_ticket(ticket),
            Periodo=serializers.serialize_caea_period(period),
            Orden=serializers.serialize_caea_order(order),
        )

        check_response(
            response
        )  # be aware that this func raise an error if it's present
        update = {
            "caea_code": int(response.ResultGet.CAEA),
            "period": int(response.ResultGet.Periodo),
            "order": int(response.ResultGet.Orden),
            "valid_since": parsers.parse_date(response.ResultGet.FchVigDesde),
            "expires": parsers.parse_date(response.ResultGet.FchVigHasta),
            "generated": parsers.parse_datetime(response.ResultGet.FchProceso),
            "final_date_inform": parsers.parse_date(response.ResultGet.FchTopeInf),
            "taxpayer": self,
            "active": caea_is_active(
                valid_since=response.ResultGet.FchVigDesde,
                valid_to=response.ResultGet.FchVigHasta,
            ),
        }

        caea = Caea.objects.update_or_create(
            caea_code=int(response.ResultGet.CAEA), defaults=update
        )

        return caea

    def _inform_caea_without_operations(
        self,
        pos: PointOfSales,
        caea: Caea,
        ticket: AuthTicket = None,
    ) -> InformedCaeas:
        """
        Inform to AFIP that the PointOfSales and CAEA passed have not any movement between the duration of the CAEA
        """
        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)
        response = client.service.FECAEASinMovimientoInformar(
            serializers.serialize_ticket(ticket),
            PtoVta=pos.number,
            CAEA=caea.caea_code,
        )

        check_response(
            response
        )  # be aware that this func raise an error if it's present
        registry = InformedCaeas.objects.create(
            pos=pos,
            caea=caea,
            processed_date=datetime.strptime(response.FchProceso, "%Y%m%d").date(),
        )
        return registry

    def consult_caea_without_operations(
        self,
        pos: PointOfSales,
        caea: Caea,
        ticket: AuthTicket = None,
    ) -> InformedCaeas or None:
        """
        Consult the state of the CAEA with AFIP, if the consult raise an error (probably CAEA without movement was never informed)
        the method handle this an inform to AFIP the CAEA and POS
        """

        try:
            registry = InformedCaeas.objects.get(pos=pos, caea=caea)
            return registry
        except InformedCaeas.DoesNotExist:
            registry = None

        ticket = ticket or self.get_or_create_ticket("wsfe")

        client = clients.get_client("wsfe", self.is_sandboxed)
        response = client.service.FECAEASinMovimientoConsultar(
            serializers.serialize_ticket(ticket),
            PtoVta=pos.number,
            CAEA=caea.caea_code,
        )
        try:
            check_response(
                response
            )  # be aware that this func raise an error if it's present

            # if for some reason a CAEA code was informed into AFIP DB but we have not a InformedCAEA this solve that
            registry = InformedCaeas.objects.create(
                pos=pos,
                caea=caea,
                processed_date=datetime.strptime(response.FchProceso, "%Y%m%d").date(),
            )
            return registry
        except exceptions.AfipException:
            registry = self._inform_caea_without_operations(
                pos=pos, caea=caea, ticket=ticket
            )
            return registry

    def __repr__(self) -> str:
        return "<TaxPayer {}: {}, CUIT {}>".format(
            self.pk,
            self.name,
            self.cuit,
        )

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        verbose_name = _("taxpayer")
        verbose_name_plural = _("taxpayers")


class Caea(models.Model):
    """Represents a CAEA code to continue operating when AFIP is offline.

    The methods provideed by AFIP like: consulting CAEA or informing a Receipt will be attached the TaxPayer model.

    """

    caea_code = models.PositiveBigIntegerField(
        validators=[
            RegexValidator(regex="[0-9]{14}"),
            MaxValueValidator(99999999999999),
        ],
        help_text=_("CAEA code to operate offline AFIP"),
        unique=True,
        null=False,
        blank=False,
    )

    period = models.IntegerField(
        help_text=_("Period to send in the CAEA request (yyyymm)")
    )

    order = models.IntegerField(
        choices=[(1, "1"), (2, "2")],
        help_text=_("Month is divided in 1st quarter or 2nd quarter"),
    )

    valid_since = models.DateField(
        _("valid_to"),
    )
    expires = models.DateField(
        _("expires"),
    )

    generated = models.DateTimeField(
        _("generated"),
    )
    final_date_inform = models.DateField(
        _("final_date_inform"),
    )

    taxpayer = models.ForeignKey(
        TaxPayer,
        verbose_name=_("taxpayer"),
        related_name="caea_tickets",
        on_delete=models.CASCADE,
    )

    active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.caea_code)


class PointOfSales(models.Model):
    """
    Represents an existing AFIP point of sale.

    Points of sales need to be created via AFIP's web interface and it is
    recommended that you use :meth:`~.TaxPayer.fetch_points_of_sales` to fetch
    these programatically.

    Note that deleting or altering these models will not affect upstream point
    of sales.

    This model also contains a few fields that are not required or sent to the
    AFIP when validating receipt. They are used *only* for PDF generation.
    Those fields are:

    - issuing_name
    - issuing_address
    - issuing_email
    - vat_condition
    - gross_income_condition
    - sales_terms

    These fields may be ignored when using an external mechanism to generate
    PDF or printable receipts.
    """

    number = models.PositiveSmallIntegerField(
        _("number"),
    )
    # AFIP has replied that this field may be up to 200bytes,
    # so 200 characters should always be more than enough.
    issuance_type = models.CharField(
        _("issuance type"),
        max_length=200,
        help_text="Indicates if this POS emits using CAE and CAEA.",
    )
    blocked = models.BooleanField(
        _("blocked"),
    )
    drop_date = models.DateField(
        _("drop date"),
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        TaxPayer,
        related_name="points_of_sales",
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
    )

    # The following fields are only used for PDF generation.
    issuing_name = models.CharField(
        max_length=128,
        null=True,
        verbose_name=_("issuing name"),
        help_text=_("The name of the issuing entity as shown on receipts."),
    )
    issuing_address = models.TextField(
        _("issuing address"),
        null=True,
        help_text=_("The address of the issuing entity as shown on receipts."),
    )
    issuing_email = models.CharField(
        max_length=128,
        verbose_name=_("issuing email"),
        blank=True,
        null=True,
        help_text=_("The email of the issuing entity as shown on receipts."),
    )
    vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                condition,
                condition,
            )
            for condition in VAT_CONDITIONS
        ),
        null=True,
        verbose_name=_("vat condition"),
    )
    gross_income_condition = models.CharField(
        max_length=48,
        null=True,
        verbose_name=_("gross income condition"),
    )
    sales_terms = models.CharField(
        max_length=48,
        null=True,
        verbose_name=_("sales terms"),
        help_text=_(
            "The terms of the sale printed onto receipts by default "
            "(eg: single payment, checking account, etc)."
        ),
    )

    def __str__(self) -> str:
        return str(self.number)

    class Meta:
        unique_together = (("number", "owner"),)
        verbose_name = _("point of sales")
        verbose_name_plural = _("points of sales")


class AuthTicketManager(models.Manager):
    def get_any_active(self, service: str) -> AuthTicket:
        """Return a valid, active ticket for a given service."""
        ticket = AuthTicket.objects.filter(
            token__isnull=False,
            expires__gt=datetime.now(timezone.utc),
            service=service,
        ).first()
        if ticket:
            return ticket

        taxpayer = TaxPayer.objects.order_by("?").first()

        if not taxpayer:
            raise exceptions.AuthenticationError(
                _("There are no taxpayers to generate a ticket."),
            )

        return taxpayer.create_ticket(service)


def default_generated() -> datetime:
    """The default generated date for new tickets."""
    return datetime.now(TZ_AR)


def default_expires() -> datetime:
    """The default expiration date for new tickets."""
    tomorrow = datetime.now(TZ_AR) + timedelta(hours=12)
    return tomorrow


def default_unique_id() -> int:
    """A random unique id for new tickets."""
    return random.randint(0, 2147483647)


class AuthTicket(models.Model):
    """An AFIP Authorization ticket.

    This is a signed ticket used to communicate with AFIP's webservices.

    Applications should not generally have to deal with these tickets
    themselves; most services will find or create one as necessary.
    """

    owner = models.ForeignKey(
        TaxPayer,
        verbose_name=_("owner"),
        related_name="auth_tickets",
        on_delete=models.CASCADE,
    )
    unique_id = models.IntegerField(
        _("unique id"),
        default=default_unique_id,
    )
    generated = models.DateTimeField(
        _("generated"),
        default=default_generated,
    )
    expires = models.DateTimeField(
        _("expires"),
        default=default_expires,
    )
    service = models.CharField(
        _("service"),
        max_length=34,
        help_text=_("Service for which this ticket has been authorized."),
    )

    token = models.TextField(
        _("token"),
    )
    signature = models.TextField(
        _("signature"),
    )

    objects = AuthTicketManager()

    TOKEN_XPATH = "/loginTicketResponse/credentials/token"
    SIGN_XPATH = "/loginTicketResponse/credentials/sign"

    def __create_request_xml(self) -> bytes:
        """Create a new ticket request XML

        This is the payload we sent to AFIP to request a new ticket."""
        request_xml = E.loginTicketRequest(
            {"version": "1.0"},
            E.header(
                E.uniqueId(str(self.unique_id)),
                E.generationTime(serializers.serialize_datetime(self.generated)),
                E.expirationTime(serializers.serialize_datetime(self.expires)),
            ),
            E.service(self.service),
        )
        # Hint: tostring returns bytes.
        return etree.tostring(request_xml, pretty_print=True)

    def __sign_request(self, request: bytes) -> bytes:
        with self.owner.certificate.file.open("rb") as f:
            cert = f.read()

        with self.owner.key.file.open("rb") as f:
            key = f.read()

        return crypto.create_embeded_pkcs7_signature(request, cert, key)

    def authorize(self) -> None:
        """Send this ticket to AFIP for authorization."""
        request_xml = self.__create_request_xml()
        signed_request = self.__sign_request(request_xml)
        request = base64.b64encode(signed_request).decode()

        client = clients.get_client("wsaa", self.owner.is_sandboxed)
        try:
            raw_response = client.service.loginCms(request)
        except Fault as e:
            if str(e) == "Certificado expirado":
                raise exceptions.CertificateExpired(str(e)) from e
            if str(e) == "Certificado no emitido por AC de confianza":
                raise exceptions.UntrustedCertificate(str(e)) from e
            raise exceptions.AuthenticationError(str(e)) from e
        response = etree.fromstring(raw_response.encode("utf-8"))

        self.token = response.xpath(self.TOKEN_XPATH)[0].text
        self.signature = response.xpath(self.SIGN_XPATH)[0].text

        self.save()

    def __str__(self) -> str:
        return str(self.unique_id)

    class Meta:
        verbose_name = _("authorization ticket")
        verbose_name_plural = _("authorization tickets")


class ReceiptQuerySet(models.QuerySet):
    """The default queryset obtains when querying via :class:`~.ReceiptManager`."""

    # This private flag is provided only to disable the durability checks in tests.
    # Inspired by Django's flag of the same name for `Atomic`.
    _ensure_durability = True

    def _assign_numbers(self) -> None:
        """Assign numbers in preparation for validating these receipts.

        WARNING: Don't call the method manually unless you know what you're
        doing!
        """
        first = self.select_related("point_of_sales", "receipt_type").first()
        assert first is not None  # should never happen; mostly a hint for mypy

        next_num = (
            Receipt.objects.fetch_last_receipt_number(
                first.point_of_sales,
                first.receipt_type,
            )
            + 1
        )

        for receipt in self.filter(receipt_number__isnull=True):
            # Atomically update receipt number
            Receipt.objects.filter(pk=receipt.id, receipt_number__isnull=True,).update(
                receipt_number=next_num,
            )
            next_num += 1

    def check_groupable(self) -> ReceiptQuerySet:
        """Check that all receipts returned by this queryset are groupable.

        "Groupable" means that they can be validated together: they have the
        same POS and receipt type.

        Returns the same queryset is all receipts are groupable, otherwise,
        raises :class:`~.CannotValidateTogether`.
        """
        types = self.aggregate(
            poses=Count(
                "point_of_sales_id",
            ),
            types=Count("receipt_type"),
        )

        if set(types.values()) > {1}:
            raise exceptions.CannotValidateTogether()

        return self

    def validate(self, ticket: AuthTicket = None) -> list[str]:
        """Validate all receipts matching this queryset.

        Note that, due to how AFIP implements its numbering, this method is not
        thread-safe, or even multiprocess-safe. You MAY however, call this method
        concurrently for receipts from different :class:`~.PointOfSales`.

        It is possible that not all instances matching this queryset are validated
        properly. This method is written in a way that the database will always remain
        in a consistent state.

        Only successfully validated receipts will marked as such. This method takes care
        of saving all changes to database.

        Returns a list of errors as returned from AFIP's webservices. When AFIP returns
        a failure response, an exception is not raised because partial failures are
        possible. Network issues (e.g.: DNS failure) _will_ raise an exception.

        Receipts that successfully validate will have a :class:`~.ReceiptValidation`
        object attached to them with a validation date and CAE information.

        Already-validated receipts are ignored.

        Attempting to validate an empty queryset will simply return an empty
        list.

        This method takes the following steps:

            - Assigns numbers to all receipts.
            - Saves the assigned numbers to the database.
            - Sends the receipts to AFIP.
            - Saves the results into the local DB.

        Should execution be interrupted (e.g.: a power failure), receipts will have been
        saved with their number. In this case, the ``revalidate`` method should be used,
        to determine if they have been registered by AFIP, or if the interruption
        happened before sending them.

        Calling this method inside a transaction will raise ``RuntimeError``, since
        doing so risks leaving the database in an inconsistent state should there be any
        fatal interruptions. In particular, the receipt numbers will not have been
        saved, so it would be impossible to recover from the incomplete operation.
        """
        if self._ensure_durability and connection.in_atomic_block:
            raise RuntimeError("This function cannot be called within a transaction")
        # Skip any already-validated ones:
        qs = self.filter(validation__isnull=True).check_groupable()
        if qs.count() == 0:
            return []

        pos = qs[0].point_of_sales.issuance_type == "CAEA"

        if pos:
            qs.order_by("issued_date", "id")
        else:
            qs.order_by("issued_date", "id")._assign_numbers()

        return qs._validate(ticket)

    def _validate(self, ticket=None) -> list[str]:
        first = self.first()
        assert first is not None  # should never happen; mostly a hint for mypy
        ticket = ticket or first.point_of_sales.owner.get_or_create_ticket("wsfe")
        client = clients.get_client("wsfe", first.point_of_sales.owner.is_sandboxed)

        if not "CAEA" in first.point_of_sales.issuance_type:
            response = client.service.FECAESolicitar(
                serializers.serialize_ticket(ticket),
                serializers.serialize_multiple_receipts(self),
            )
            check_response(response)
            errs = []
            for cae_data in response.FeDetResp.FECAEDetResponse:
                if cae_data.Resultado == ReceiptValidation.RESULT_APPROVED:
                    validation = ReceiptValidation.objects.create(
                        result=cae_data.Resultado,
                        cae=cae_data.CAE,
                        cae_expiration=parsers.parse_date(cae_data.CAEFchVto),
                        receipt=self.get(
                            receipt_number=cae_data.CbteDesde,
                        ),
                        processed_date=parsers.parse_datetime(
                            response.FeCabResp.FchProceso,
                        ),
                    )
                    if cae_data.Observaciones:
                        for obs in cae_data.Observaciones.Obs:
                            observation = Observation.objects.create(
                                code=obs.Code,
                                message=obs.Msg,
                            )
                        validation.observations.add(observation)
                elif cae_data.Observaciones:
                    for obs in cae_data.Observaciones.Obs:
                        errs.append(
                            "Error {}: {}".format(
                                obs.Code,
                                parsers.parse_string(obs.Msg),
                            )
                        )

            # Remove the number from ones that failed to validate:
            self.filter(validation__isnull=True).update(receipt_number=None)
            return errs

        else:
            response = client.service.FECAEARegInformativo(
                serializers.serialize_ticket(ticket),
                serializers.serialize_multiple_receipts_caea(self),
            )
            check_response(response)
            errs = []
            for cae_data in response.FeDetResp.FECAEADetResponse:
                if cae_data.Resultado == ReceiptValidation.RESULT_APPROVED:
                    validation = ReceiptValidation.objects.create(
                        result=cae_data.Resultado,
                        cae=cae_data.CAEA,
                        # cae_expiration=parsers.parse_date(self.caea.expires),
                        receipt=self.get(
                            receipt_number=cae_data.CbteDesde,
                        ),
                        processed_date=parsers.parse_datetime(
                            response.FeCabResp.FchProceso,
                        ),
                        caea=True,
                    )
                    if cae_data.Observaciones:
                        for obs in cae_data.Observaciones.Obs:
                            observation = Observation.objects.create(
                                code=obs.Code,
                                message=obs.Msg,
                            )
                        validation.observations.add(observation)
                elif cae_data.Observaciones:
                    for obs in cae_data.Observaciones.Obs:
                        errs.append(
                            "Error {}: {}".format(
                                obs.Code,
                                parsers.parse_string(obs.Msg),
                            )
                        )
            return errs


class ReceiptManager(models.Manager):
    """Default manager for the :class:`~.Receipt` class.

    This should be accessed using ``Receipt.objects``.
    """

    def fetch_last_receipt_number(
        self,
        point_of_sales: PointOfSales,
        receipt_type: ReceiptType,
    ) -> int:
        """Returns the number for the last validated receipt."""
        client = clients.get_client("wsfe", point_of_sales.owner.is_sandboxed)
        response_xml = client.service.FECompUltimoAutorizado(
            serializers.serialize_ticket(
                point_of_sales.owner.get_or_create_ticket("wsfe")
            ),
            point_of_sales.number,
            receipt_type.code,
        )
        check_response(response_xml)

        # TODO XXX: Error handling
        # (FERecuperaLastCbteResponse){
        #    PtoVta = 0
        #    CbteTipo = 0
        #    CbteNro = 0
        #    Errors =
        #       (ArrayOfErr){
        #          Err[] =
        #             (Err){
        #                Code = 601
        #                Msg = "CUIT representada no incluida en Token"
        #             },
        #       }
        #  }

        return response_xml.CbteNro

    def fetch_receipt_data(
        self,
        receipt_type: ReceiptType,
        receipt_number: int,
        point_of_sales: PointOfSales,
    ):  # TODO: Wrap this in a dataclass
        """Returns receipt related data"""

        if not receipt_number:
            return None

        client = clients.get_client("wsfe", point_of_sales.owner.is_sandboxed)
        response_xml = client.service.FECompConsultar(
            serializers.serialize_ticket(
                point_of_sales.owner.get_or_create_ticket("wsfe")
            ),
            serializers.serialize_receipt_data(
                receipt_type, receipt_number, point_of_sales.number
            ),
        )
        try:
            check_response(response_xml)
            return response_xml.ResultGet
        except exceptions.AfipException:
            return None

    def get_queryset(self) -> ReceiptQuerySet:
        """Return a new QuerySet object.

        This always joins with :class:`~.ReceiptType`."""
        return ReceiptQuerySet(self.model, using=self._db).select_related(
            "receipt_type",
        )


class Receipt(models.Model):
    """A receipt, as sent to AFIP.

    Note that AFIP allows sending ranges of receipts, but this isn't generally
    what you want, so we model invoices individually.

    You'll probably want to relate some `Sale` or `Order` object from your
    model with each Receipt.

    All ``document_`` fields contain the recipient's data.

    If the taxpayer has taxes or pays VAT, you need to attach :class:`~.Tax`
    and/or :class:`~.Vat` instances to the Receipt.

    Application code SHOULD NOT set the `receipt_number` code. It will be set by
    :meth:`~.Receipt.validate()` internally. When writing code outside `django-afip`,
    this should be considered read-only. The sole exception is importing
    previously-validated receipts from another database.
    `
    """

    point_of_sales = models.ForeignKey(
        PointOfSales,
        related_name="receipts",
        verbose_name=_("point of sales"),
        on_delete=models.PROTECT,
    )
    receipt_type = models.ForeignKey(
        ReceiptType,
        related_name="receipts",
        verbose_name=_("receipt type"),
        on_delete=models.PROTECT,
    )
    concept = models.ForeignKey(
        ConceptType,
        verbose_name=_("concept"),
        related_name="receipts",
        on_delete=models.PROTECT,
    )
    document_type = models.ForeignKey(
        DocumentType,
        verbose_name=_("document type"),
        related_name="receipts",
        help_text=_("The document type of the recipient of this receipt."),
        on_delete=models.PROTECT,
    )
    document_number = models.BigIntegerField(
        _("document number"),
        help_text=_("The document number of the recipient of this receipt."),
    )
    # NOTE: WS will expect receipt_from and receipt_to.
    receipt_number = models.PositiveIntegerField(
        _("receipt number"),
        null=True,
        blank=True,
        help_text=_(
            "If left blank, the next valid number will assigned when "
            "validating the receipt."
        ),
    )
    issued_date = models.DateField(
        verbose_name=_("issued date"),
        help_text=_("Can diverge up to 5 days for good, or 10 days otherwise."),
    )
    total_amount = models.DecimalField(
        # ImpTotal
        _("total amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "Must be equal to the sum of net_taxed, exempt_amount, net_taxes, "
            "and all taxes and vats."
        ),
    )
    net_untaxed = models.DecimalField(
        # ImpTotConc
        _("total untaxable amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "The total amount to which taxes do not apply.<br>"
            "For C-type receipts, this must be zero."
        ),
    )
    net_taxed = models.DecimalField(
        # ImpNeto
        _("total taxable amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "The total amount to which taxes apply.<br>"
            "For C-type receipts, this is equal to the subtotal."
        ),
    )
    exempt_amount = models.DecimalField(
        # ImpOpEx
        # Sólo para emisores que son IVA exento
        _("exempt amount"),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            "Only for categories which are tax-exempt.<br>"
            "For C-type receipts, this must be zero."
        ),
    )
    service_start = models.DateField(
        _("service start date"),
        help_text=_("Date on which a service started. No applicable for goods."),
        null=True,
        blank=True,
    )
    service_end = models.DateField(
        _("service end date"),
        help_text=_("Date on which a service ended. No applicable for goods."),
        null=True,
        blank=True,
    )
    expiration_date = models.DateField(
        _("receipt expiration date"),
        help_text=_("Date on which this receipt expires. No applicable for goods."),
        null=True,
        blank=True,
    )
    currency = models.ForeignKey(
        CurrencyType,
        verbose_name=_("currency"),
        related_name="documents",
        help_text=_("Currency in which this receipt is issued."),
        on_delete=models.PROTECT,
        default=first_currency,
    )
    currency_quote = models.DecimalField(
        _("currency quote"),
        max_digits=10,
        decimal_places=6,
        default=1,
        help_text=_("The currency's quote on the day this receipt was issued."),
    )
    related_receipts = models.ManyToManyField(
        "Receipt",
        verbose_name=_("related receipts"),
        blank=True,
    )

    generated = models.DateTimeField(
        _("Time when the receipt was created"),
        auto_now_add=True,
    )

    caea = models.ForeignKey(
        Caea,
        related_name="receipts",
        on_delete=models.PROTECT,
        help_text=_("CAEA in case that the receipt must contain it"),
        blank=True,
        null=True,
    )

    objects = ReceiptManager()

    # TODO: Not implemented: optionals
    # TODO: methods to validate totals

    @property
    def total_vat(self) -> int:
        """Returns the sum of all Vat objects."""
        q = Vat.objects.filter(receipt=self).aggregate(total=Sum("amount"))
        return q["total"] or 0

    @property
    def total_tax(self) -> int:
        """Returns the sum of all Tax objects."""
        q = Tax.objects.filter(receipt=self).aggregate(total=Sum("amount"))
        return q["total"] or 0

    @property
    def formatted_number(self) -> str | None:
        """This receipt's number in the usual format: ``0001-00003087``."""
        if self.receipt_number:
            return "{:04d}-{:08d}".format(
                self.point_of_sales.number,
                self.receipt_number,
            )
        return None

    @property
    def is_validated(self) -> bool:
        """True if this instance is validated.

        Note that resolving this property requires a DB query, so if you've a
        very large amount of receipts you should prefetch (see django's
        ``select_related``) the ``validation`` field. Even so, a DB query *may*
        be triggered.

        If you need a large list of validated receipts, you should actually
        filter them via a QuerySet::

            Receipt.objects.filter(validation__result==RESULT_APPROVED)
        """
        # Avoid the DB lookup if possible:
        if not self.receipt_number:
            return False

        try:
            return self.validation.result == ReceiptValidation.RESULT_APPROVED
        except ReceiptValidation.DoesNotExist:
            return False

    def validate(self, ticket: AuthTicket = None, raise_=False) -> list[str]:
        """Validates this receipt.

        This is a shortcut to :meth:`~.ReceiptQuerySet.validate`. See the documentation
        for that method for details. Calling this validates only this instance.


        .. versionchanged:: 11

            The ``raise_`` flag has been deprecated.

        :param ticket: Use this ticket. If None, one will be loaded or created
            automatically.
        :param raise_: If True, an exception will be raised when validation fails.
        """
        if raise_:
            warnings.warn(
                "The raise_ flag is deprecated and will be removed in django_afip 12.",
                DeprecationWarning,
                stacklevel=2,
            )

        # XXX: Maybe actually have this sortcut raise an exception?
        rv = Receipt.objects.filter(pk=self.pk).validate(ticket)
        # Since we're operating via a queryset, this instance isn't properly
        # updated:
        self.refresh_from_db()
        if raise_ and rv:
            raise exceptions.ValidationError(rv[0])
        return rv

    def revalidate(self) -> ReceiptValidation | None:
        """Revalidate this receipt.

        Fetches data of a validated receipt from AFIP's servers.
        If the receipt exists a ``ReceiptValidation`` instance is
        created and returned, otherwise, returns ``None``.
        If there is already a ``ReceiptValidation`` for this instance,
        returns ``self.validation``.
        This should be used for verification purpose, here's a list of
        some use cases:
         - Incomplete validation process
         - Fetch CAE data from AFIP's servers
        """
        # This may avoid unnecessary revalidation
        if self.is_validated:
            return self.validation
        if not self.receipt_number:
            return None

        receipt_data = Receipt.objects.fetch_receipt_data(
            self.receipt_type.code, self.receipt_number, self.point_of_sales
        )

        if not receipt_data:
            return None

        if receipt_data.Resultado == ReceiptValidation.RESULT_APPROVED:
            if receipt_data.EmisionTipo == "CAEA":
                cae_expiration = None
            else:
                cae_expiration = receipt_data.FchVto

            validation = ReceiptValidation.objects.create(
                result=receipt_data.Resultado,
                cae=receipt_data.CodAutorizacion,
                cae_expiration=parsers.parse_date(cae_expiration),
                receipt=self,
                processed_date=parsers.parse_datetime(
                    receipt_data.FchProceso,
                ),
            )
            if receipt_data.Observaciones:
                for obs in receipt_data.Observaciones.Obs:
                    observation, _ = Observation.objects.get_or_create(
                        code=obs.Code,
                        message=obs.Msg,
                    )
                validation.observations.add(observation)
            return validation
        return None

    def __repr__(self) -> str:
        return "<Receipt {}: {} {} for {}>".format(
            self.pk,
            self.receipt_type,
            self.receipt_number,
            self.point_of_sales.owner,
        )

    def __str__(self) -> str:
        if self.receipt_number:
            return f"{self.receipt_type} {self.formatted_number}"
        else:
            return _("Unnumbered %s") % self.receipt_type

    class Meta:
        ordering = (
            "issued_date",
        )  # this ordering return the same values for first(),last() when filter on 1 day
        verbose_name = _("receipt")
        verbose_name_plural = _("receipts")
        unique_together = [["point_of_sales", "receipt_type", "receipt_number"]]
        # TODO: index_together...


class ReceiptPDFManager(models.Manager):
    def create_for_receipt(self, receipt: Receipt, **kwargs) -> ReceiptPDF:
        """Creates a ReceiptPDF object for a given receipt.

        Does not actually generate the related PDF file.

        All attributes will be completed with the information for the relevant
        :class:`~.PointOfSales` instance.

        :param receipt: The receipt for the PDF which will be generated.
        :param **kwargs: Passed directly to the :class:`~.ReceiptPDF` constructor.
        """
        pdf = ReceiptPDF.objects.create(
            receipt=receipt,
            issuing_name=receipt.point_of_sales.issuing_name,
            issuing_address=receipt.point_of_sales.issuing_address,
            issuing_email=receipt.point_of_sales.issuing_email,
            vat_condition=receipt.point_of_sales.vat_condition,
            gross_income_condition=receipt.point_of_sales.gross_income_condition,
            sales_terms=receipt.point_of_sales.sales_terms,
            **kwargs,
        )
        return pdf


class ReceiptPDF(models.Model):
    """Printable version of a receipt.

    Contains all print-related data of a receipt.

    All ``issuing_*`` fields contain data for the entity issuing the Receipt
    (these may change from one receipt to the next if, for example, the entity
    moved).

    The PDF file itself is saved into the ``pdf_file`` attribute, and is
    generated when saving the model for the first time. If any attributes are
    changed, you should manually call :meth:`~.ReceiptPDF.save_pdf` to
    regenerate the PDF file.

    PDF generation is skipped if the receipt has not been validated.
    """

    def upload_to(self, filename="untitled", instance: ReceiptPDF = None) -> str:
        """
        Returns the full path for generated receipts.

        These are bucketed inside nested directories, to avoid hundreds of
        thousands of children in single directories (which can make reading
        them excessively slow).
        """
        _, extension = os.path.splitext(os.path.basename(filename))
        uuid = uuid4().hex
        buckets = uuid[0:2], uuid[2:4]
        filename = "".join([uuid, extension])

        return os.path.join("afip/receipts", buckets[0], buckets[1], filename)

    receipt = models.OneToOneField(
        Receipt,
        verbose_name=_("receipt"),
        on_delete=models.PROTECT,
    )
    pdf_file = models.FileField(
        verbose_name=_("pdf file"),
        upload_to=upload_to,
        storage=_get_storage_from_settings("AFIP_PDF_STORAGE"),
        blank=True,
        null=True,
        help_text=_("The actual file which contains the PDF data."),
    )
    issuing_name = models.CharField(
        max_length=128,
        verbose_name=_("issuing name"),
    )
    issuing_address = models.TextField(
        _("issuing address"),
    )
    issuing_email = models.CharField(
        max_length=128,
        verbose_name=_("issuing email"),
        blank=True,
        null=True,
    )
    vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                condition,
                condition,
            )
            for condition in VAT_CONDITIONS
        ),
        verbose_name=_("vat condition"),
    )
    gross_income_condition = models.CharField(
        max_length=48,
        verbose_name=_("gross income condition"),
    )
    client_name = models.CharField(
        max_length=128,
        verbose_name=_("client name"),
    )
    client_address = models.TextField(
        _("client address"),
        blank=True,
    )
    client_vat_condition = models.CharField(
        max_length=48,
        choices=(
            (
                cond,
                cond,
            )
            for cond in CLIENT_VAT_CONDITIONS
        ),
        verbose_name=_("client vat condition"),
    )
    sales_terms = models.CharField(
        max_length=48,
        verbose_name=_("sales terms"),
        help_text=_('Should be something like "Cash", "Payable in 30 days", etc.'),
    )

    objects = ReceiptPDFManager()

    def save_pdf(self, save_model: bool = True) -> None:
        """
        Save the receipt as a PDF related to this model.

        The related :class:`~.Receipt` should be validated first, of course.
        This model instance must have been saved prior to calling this method.

        :param save_model: If True, immediately save this model instance.
        """
        from django_afip.views import ReceiptPDFView

        if not self.receipt.is_validated:
            if not "CAEA" in self.receipt.point_of_sales.issuance_type:
                raise exceptions.DjangoAfipException(
                    _("Cannot generate pdf for non-authorized receipt")
                )

        self.pdf_file = File(BytesIO(), name=f"{uuid4().hex}.pdf")
        render_pdf(
            template=ReceiptPDFView().get_template_names(self.receipt),
            file_=self.pdf_file,
            context=ReceiptPDFView.get_context_for_pk(self.receipt_id),
        )

        if save_model:
            self.save()

    def __str__(self) -> str:
        return _("Receipt PDF for %s") % self.receipt_id

    class Meta:
        verbose_name = _("receipt pdf")
        verbose_name_plural = _("receipt pdfs")


class ReceiptEntry(models.Model):
    """An entry in a receipt.

    Each ReceiptEntry represents a line in printable version of a Receipt. You
    should generally have one instance per product or service.

    Note that each entry has a :class:`~.Vat` because a single Receipt can have
    multiple products with different :class:`~.VatType`.
    """

    receipt = models.ForeignKey(
        Receipt,
        related_name="entries",
        verbose_name=_("receipt"),
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        max_length=128,
        verbose_name=_("description"),
    )
    quantity = models.PositiveSmallIntegerField(
        _("quantity"),
    )
    unit_price = models.DecimalField(
        _("unit price"),
        max_digits=15,
        decimal_places=2,
        help_text=_("Price per unit before vat or taxes."),
    )
    discount = models.DecimalField(
        _("discount"),
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text=_("Total net discount applied to row's total."),
        validators=[MinValueValidator(Decimal("0.0"))],
    )
    vat = models.ForeignKey(
        VatType,
        related_name="receipt_entries",
        verbose_name=_("vat"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    @property
    def total_price(self) -> Decimal:
        """The total price for this entry is: ``quantity * price - discount``."""
        return self.quantity * self.unit_price - self.discount

    class Meta:
        verbose_name = _("receipt entry")
        verbose_name_plural = _("receipt entries")
        constraints = [
            CheckConstraint(
                check=Q(discount__gte=Decimal("0.0")), name="discount_positive_value"
            ),
            CheckConstraint(
                check=Q(discount__lte=F("quantity") * F("unit_price")),
                name="discount_less_than_total",
            ),
        ]


class Tax(models.Model):
    """A tax (type+amount) for a specific Receipt."""

    tax_type = models.ForeignKey(
        TaxType,
        verbose_name=_("tax type"),
        on_delete=models.PROTECT,
    )
    description = models.CharField(
        _("description"),
        max_length=80,
    )
    base_amount = models.DecimalField(
        _("base amount"),
        max_digits=15,
        decimal_places=2,
    )
    aliquot = models.DecimalField(
        _("aliquot"),
        max_digits=5,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _("amount"),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name="taxes",
        on_delete=models.PROTECT,
    )

    def compute_amount(self) -> Decimal:
        """Auto-assign and return the total amount for this tax."""
        self.amount = self.base_amount * self.aliquot / 100
        return self.amount

    class Meta:
        verbose_name = _("tax")
        verbose_name_plural = _("taxes")


class Vat(models.Model):
    """A VAT (type+amount) for a specific Receipt."""

    vat_type = models.ForeignKey(
        VatType,
        verbose_name=_("vat type"),
        on_delete=models.PROTECT,
    )
    base_amount = models.DecimalField(
        _("base amount"),
        max_digits=15,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _("amount"),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name="vat",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("vat")
        verbose_name_plural = _("vat")


class Observation(models.Model):
    """An observation returned by AFIP.

    AFIP seems to assign re-used codes to Observation, so we actually store
    them as separate objects, and link to them from failed validations.
    """

    code = models.PositiveSmallIntegerField(
        _("code"),
    )
    message = models.CharField(
        _("message"),
        max_length=255,
    )

    class Meta:
        verbose_name = _("observation")
        verbose_name_plural = _("observations")


class ReceiptValidation(models.Model):
    """The validation for a single :class:`~.Receipt`.

    This contains all validation-related data for a receipt, including its CAE
    and the CAE expiration, unless validation has failed.

    The ``observation`` field may contain any data returned by AFIP regarding
    validation failure.
    """

    RESULT_APPROVED = "A"
    RESULT_REJECTED = "R"

    # TODO: replace this with a `successful` boolean field.
    result = models.CharField(
        _("result"),
        max_length=1,
        choices=(
            (RESULT_APPROVED, _("approved")),
            (RESULT_REJECTED, _("rejected")),
        ),
        help_text=_("Indicates whether the validation was succesful or not."),
    )
    processed_date = models.DateTimeField(
        _("processed date"),
    )
    cae = models.CharField(
        _("cae"),
        max_length=14,
        help_text=_("The CAE as returned by the AFIP."),
    )
    cae_expiration = models.DateField(
        _("cae expiration"),
        help_text=_("The CAE expiration as returned by the AFIP."),
        blank=True,  # Must be blank or null when was approved from CAEA operations
        null=True,
    )
    observations = models.ManyToManyField(
        Observation,
        verbose_name=_("observations"),
        related_name="validations",
        help_text=_(
            "The observations as returned by the AFIP. These are generally "
            "present for failed validations."
        ),
    )

    receipt = models.OneToOneField(
        Receipt,
        related_name="validation",
        verbose_name=_("receipt"),
        help_text=_("The Receipt for which this validation applies."),
        on_delete=models.PROTECT,
    )

    caea = models.BooleanField(
        default=False,
        help_text=_(
            "Indicate if the validation was from a CAEA receipt, in that case the field CAE contains the CAEA number"
        ),
        verbose_name=_("is_caea"),
    )

    def __str__(self) -> str:
        return _("Validation for %s. Result: %s") % (
            self.receipt,
            self.get_result_display(),
        )

    def __repr__(self) -> str:
        return "<{} {}: {} for Receipt {}>".format(
            self.__class__.__name__,
            self.pk,
            self.result,
            self.receipt_id,
        )

    class Meta:
        verbose_name = _("receipt validation")
        verbose_name_plural = _("receipt validations")


class CaeaCounter(models.Model):

    pos = models.ForeignKey(
        PointOfSales, related_name="counter", on_delete=models.PROTECT
    )

    receipt_type = models.ForeignKey(
        ReceiptType, related_name="counter", on_delete=models.PROTECT
    )

    next_value = models.BigIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pos", "receipt_type"],
                name="unique_migration_pos_receipt_combination",
            )
        ]

    def __str__(self):
        return "Counter for POS:{}, receipt_type:{}. Next_value is {}".format(
            self.pos, self.receipt_type, self.next_value
        )


class InformedCaeas(models.Model):

    pos = models.ForeignKey(
        PointOfSales, related_name="informed", on_delete=models.PROTECT
    )

    caea = models.ForeignKey(Caea, related_name="informed", on_delete=models.PROTECT)

    processed_date = models.DateField(
        _("processed date"),
    )

    def __str__(self):
        return "POS:{}, with CAEA:{}, informed as without movement in {}".format(
            self.pos, self.caea, self.processed_date
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pos", "caea"],
                name="unique_migration_pos_caea_combination",
            )
        ]
