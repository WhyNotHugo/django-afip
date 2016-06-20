from django.db.models import Sum

from . import clients


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
    wso = clients.get_client('wsfe').factory.create('FEAuthRequest')
    wso.Token = ticket.token
    wso.Sign = ticket.signature
    wso.Cuit = ticket.owner.cuit
    return wso


def serialize_receipt_batch(batch):
    receipts = batch.receipts.all().order_by('receipt_number')

    client = clients.get_client('wsfe')
    wso = client.factory.create('FECAERequest')
    wso.FeCabReq.CantReg = len(receipts)
    wso.FeCabReq.PtoVta = batch.point_of_sales.number
    wso.FeCabReq.CbteTipo = batch.receipt_type.code

    for receipt in receipts:
        wso.FeDetReq.FECAEDetRequest.append(serialize_receipt(receipt))

    return wso


def serialize_receipt(receipt):
    subtotals = receipt._meta.model.objects.filter(pk=receipt.pk).aggregate(
        vat=Sum('vat__amount', distinct=True),
        taxes=Sum('taxes__amount', distinct=True),
    )

    client = clients.get_client('wsfe')
    wso = client.factory.create('FECAEDetRequest')
    wso.Concepto = receipt.concept.code
    wso.DocTipo = receipt.document_type.code
    wso.DocNro = receipt.document_number
    # TODO: Check that this is not None!
    wso.CbteDesde = receipt.receipt_number
    wso.CbteHasta = receipt.receipt_number
    wso.CbteFch = serialize_date(receipt.issued_date)
    wso.ImpTotal = receipt.total_amount
    wso.ImpTotConc = receipt.net_untaxed
    wso.ImpNeto = receipt.net_taxed
    wso.ImpOpEx = receipt.exempt_amount
    wso.ImpIVA = subtotals['vat'] or 0
    wso.ImpTrib = subtotals['taxes'] or 0
    if int(receipt.concept.code) in (2, 3,):
        wso.FchServDesde = serialize_date(receipt.service_start)
        wso.FchServHasta = serialize_date(receipt.service_end)
        wso.FchVtoPago = serialize_date(receipt.expiration_date)
    wso.MonId = receipt.currency.code
    wso.MonCotiz = receipt.currency_quote

    for tax in receipt.taxes.all():
        wso.Tributos.Tributo.append(serialize_tax(tax))

    for vat in receipt.vat.all():
        wso.Iva.AlicIva.append(serialize_vat(vat))

    # XXX: Need to create a CbteAsoc object:
    for receipt in receipt.related_receipts.all():
        receipt_wso = client.factory.create('CbteAsoc')
        receipt_wso.receipt.receipt_type.code
        receipt_wso.receipt.point_of_sales.number
        receipt_wso.receipt.receipt_number
        wso.CbtesAsoc.append(receipt_wso)

    return wso


def serialize_tax(tax):
    wso = clients.get_client('wsfe').factory.create('Tributo')
    wso.Id = tax.tax_type.code
    wso.Desc = tax.description
    wso.BaseImp = tax.base_amount
    wso.Alic = tax.aliquot
    wso.Importe = tax.amount

    return wso


def serialize_vat(vat):
    wso = clients.get_client('wsfe').factory.create('AlicIva')
    wso.Id = vat.vat_type.code
    wso.BaseImp = vat.base_amount
    wso.Importe = vat.amount

    return wso
