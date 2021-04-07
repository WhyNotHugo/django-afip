from django.db.models import Sum
from django.utils.functional import LazyObject

from django_afip.clients import get_client


class _LazyFactory(LazyObject):
    """A lazy-initialised factory for WSDL objects."""

    def _setup(self):
        self._wrapped = get_client("wsfe").type_factory("ns0")


f = _LazyFactory()


def serialize_datetime(datetime):
    """
    "Another date formatting function?" you're thinking, eh? Well, this
    actually formats dates in the *exact* format the AFIP's WS expects it,
    which is almost like ISO8601.

    Note that .isoformat() works fine on production servers, but not on the
    sandbox ones.
    """
    return datetime.strftime("%Y-%m-%dT%H:%M:%S-00:00")


def serialize_date(date):
    return date.strftime("%Y%m%d")


def serialize_ticket(ticket):
    return f.FEAuthRequest(
        Token=ticket.token,
        Sign=ticket.signature,
        Cuit=ticket.owner.cuit,
    )


def serialize_multiple_receipts(receipts):
    receipts = receipts.all().order_by("receipt_number")

    first = receipts.first()
    receipts = [serialize_receipt(receipt) for receipt in receipts]

    serialised = f.FECAERequest(
        FeCabReq=f.FECAECabRequest(
            CantReg=len(receipts),
            PtoVta=first.point_of_sales.number,
            CbteTipo=first.receipt_type.code,
        ),
        FeDetReq=f.ArrayOfFECAEDetRequest(receipts),
    )

    return serialised


def serialize_receipt(receipt):
    from django_afip.models import Receipt

    subtotals = Receipt.objects.filter(pk=receipt.pk).aggregate(
        vat=Sum("vat__amount"),
        taxes=Sum("taxes__amount"),
    )

    serialized = f.FECAEDetRequest(
        Concepto=receipt.concept.code,
        DocTipo=receipt.document_type.code,
        DocNro=receipt.document_number,
        # TODO: Check that this is not None!,
        CbteDesde=receipt.receipt_number,
        CbteHasta=receipt.receipt_number,
        CbteFch=serialize_date(receipt.issued_date),
        ImpTotal=receipt.total_amount,
        ImpTotConc=receipt.net_untaxed,
        ImpNeto=receipt.net_taxed,
        ImpOpEx=receipt.exempt_amount,
        ImpIVA=subtotals["vat"] or 0,
        ImpTrib=subtotals["taxes"] or 0,
        MonId=receipt.currency.code,
        MonCotiz=receipt.currency_quote,
    )
    if int(receipt.concept.code) in (2, 3):
        serialized.FchServDesde = serialize_date(receipt.service_start)
        serialized.FchServHasta = serialize_date(receipt.service_end)
        serialized.FchVtoPago = serialize_date(receipt.expiration_date)

    if receipt.taxes.count():
        serialized.Tributos = f.ArrayOfTributo(
            [serialize_tax(tax) for tax in receipt.taxes.all()]
        )
    if receipt.vat.count():
        serialized.Iva = f.ArrayOfAlicIva(
            [serialize_vat(vat) for vat in receipt.vat.all()]
        )

    related_receipts = receipt.related_receipts.all()
    if related_receipts:
        serialized.CbtesAsoc = f.ArrayOfCbteAsoc(
            [
                f.CbteAsoc(
                    r.receipt_type.code,
                    r.point_of_sales.number,
                    r.receipt_number,
                )
                for r in related_receipts
            ]
        )

    return serialized


def serialize_tax(tax):
    return f.Tributo(
        Id=tax.tax_type.code,
        Desc=tax.description,
        BaseImp=tax.base_amount,
        Alic=tax.aliquot,
        Importe=tax.amount,
    )


def serialize_vat(vat):
    return f.AlicIva(
        Id=vat.vat_type.code,
        BaseImp=vat.base_amount,
        Importe=vat.amount,
    )
