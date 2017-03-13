from django.db.models import Sum

from . import clients


def _wsfe_factory():
    return clients.get_client('wsfe').type_factory('ns0')


def serialize_datetime(datetime):
    """
    "Another date formatting function?" you're thinking, eh? Well, this
    actually formats dates in the *exact* format the AFIP's WS expects it,
    which is almost like ISO8601.

    Note that .isoformat() works fine on production servers, but not on the
    sandbox ones.
    """
    return datetime.strftime('%Y-%m-%dT%H:%M:%S-00:00')


def serialize_date(date):
    return date.strftime('%Y%m%d')


def serialize_ticket(ticket):
    return _wsfe_factory().FEAuthRequest(
        Token=ticket.token,
        Sign=ticket.signature,
        Cuit=ticket.owner.cuit,
    )


def serialize_receipt_batch(batch):
    receipts = batch.receipts.all().order_by('receipt_number')
    f = _wsfe_factory()

    receipts = [serialize_receipt(receipt) for receipt in receipts]

    wso = f.FECAERequest(
        FeCabReq=f.FECAECabRequest(
            CantReg=len(receipts),
            PtoVta=batch.point_of_sales.number,
            CbteTipo=batch.receipt_type.code,
        ),
        FeDetReq=f.ArrayOfFECAEDetRequest(receipts),
    )

    # for receipt in receipts:
    #     wso.FeDetReq.FECAEDetRequest.append(receipt)

    return wso


def serialize_receipt(receipt):
    from django_afip import models
    f = _wsfe_factory()
    subtotals = models.Receipt.objects.filter(pk=receipt.pk).aggregate(
        vat=Sum('vat__amount', distinct=True),
        taxes=Sum('taxes__amount', distinct=True),
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
        ImpIVA=subtotals['vat'] or 0,
        ImpTrib=subtotals['taxes'] or 0,
        MonId=receipt.currency.code,
        MonCotiz=receipt.currency_quote,
    )
    if int(receipt.concept.code) in (2, 3,):
        serialized.FchServDesde = serialize_date(receipt.service_start)
        serialized.FchServHasta = serialize_date(receipt.service_end)
        serialized.FchVtoPago = serialize_date(receipt.expiration_date)

    if receipt.taxes.count():
        serialized.Tributos = f.ArrayOfTributo([
            serialize_tax(tax) for tax in receipt.taxes.all()
        ])
    if receipt.vat.count():
        serialized.Iva = f.ArrayOfAlicIva([
            serialize_vat(vat) for vat in receipt.vat.all()
        ])

    # XXX: This was never finished!
    # serialized.CbtesAsoc = f.ArrayOfCbteAsoc([
    #     f.CbteAsoc(
    #         receipt.receipt_type.code,
    #         receipt.point_of_sales.number,
    #         receipt.receipt_number,
    #     ) for r in receipt.related_receipts.all()
    # ])

    return serialized


def serialize_tax(tax):
    return _wsfe_factory().Tributo(
        Id=tax.tax_type.code,
        Desc=tax.description,
        BaseImp=tax.base_amount,
        Alic=tax.aliquot,
        Importe=tax.amount,
    )


def serialize_vat(vat):
    return _wsfe_factory().AlicIva(
        Id=vat.vat_type.code,
        BaseImp=vat.base_amount,
        Importe=vat.amount,
    )
