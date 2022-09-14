from datetime import datetime
from django.utils.functional import LazyObject

from django_afip.clients import get_client
from .exceptions import CaeaCountError


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


def serialize_datetime_caea(datetime):
    """
    A similar serealizer to the above one but, use a diferent format.
    """
    return datetime.strftime("%Y%m%d%H%M%S")


def serialize_date(date):
    return date.strftime("%Y%m%d")


def serialize_ticket(ticket):
    return f.FEAuthRequest(
        Token=ticket.token,
        Sign=ticket.signature,
        Cuit=ticket.owner.cuit,
    )


def serialize_multiple_receipts_caea(receipts):

    receipts = receipts.all().order_by("receipt_number")

    first = receipts.first()
    receipts = [serialize_receipt_caea(receipt) for receipt in receipts]

    serialised = f.FECAEARequest(
        FeCabReq=f.FECAEACabRequest(
            CantReg=len(receipts),
            PtoVta=first.point_of_sales.number,
            CbteTipo=first.receipt_type.code,
        ),
        FeDetReq=f.ArrayOfFECAEADetRequest(receipts),
    )

    return serialised


def serialize_receipt_caea(receipt):
    taxes = receipt.taxes.all()
    vats = receipt.vat.all()

    serialized = f.FECAEADetRequest(
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
        ImpIVA=sum(vat.amount for vat in vats),
        ImpTrib=sum(tax.amount for tax in taxes),
        MonId=receipt.currency.code,
        MonCotiz=receipt.currency_quote,
    )
    if int(receipt.concept.code) in (2, 3):
        serialized.FchServDesde = serialize_date(receipt.service_start)
        serialized.FchServHasta = serialize_date(receipt.service_end)
        serialized.FchVtoPago = serialize_date(receipt.expiration_date)

    if taxes:
        serialized.Tributos = f.ArrayOfTributo([serialize_tax(tax) for tax in taxes])

    if vats:
        serialized.Iva = f.ArrayOfAlicIva([serialize_vat(vat) for vat in vats])

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

    serialized.CAEA = receipt.caea.caea_code
    serialized.CbteFchHsGen = serialize_datetime_caea(receipt.generated)

    return serialized


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
    taxes = receipt.taxes.all()
    vats = receipt.vat.all()

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
        ImpIVA=sum(vat.amount for vat in vats),
        ImpTrib=sum(tax.amount for tax in taxes),
        MonId=receipt.currency.code,
        MonCotiz=receipt.currency_quote,
    )
    if int(receipt.concept.code) in (2, 3):
        serialized.FchServDesde = serialize_date(receipt.service_start)
        serialized.FchServHasta = serialize_date(receipt.service_end)
        serialized.FchVtoPago = serialize_date(receipt.expiration_date)

    if taxes:
        serialized.Tributos = f.ArrayOfTributo([serialize_tax(tax) for tax in taxes])

    if vats:
        serialized.Iva = f.ArrayOfAlicIva([serialize_vat(vat) for vat in vats])

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


def serialize_receipt_data(receipt_type, receipt_number, point_of_sales):
    return f.FECompConsultaReq(
        CbteTipo=receipt_type, CbteNro=receipt_number, PtoVta=point_of_sales
    )


def serialize_caea_period(period: str = None):
    if period:
        return period
    else:
        date = datetime.now()
        return date.strftime("%Y%m")


def serialize_caea_order(order: int = None):
    if order:
        return order
    else:
        return 1
