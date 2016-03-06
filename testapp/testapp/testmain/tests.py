import os
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management
from django.core.files import File
from django.test import TestCase, Client
from django.utils.timezone import now
from django_afip import models


# We keep the taxpayer and it's ticket in-memory, since the webservice does not
# allow too frequent requests, and each unit test needs a ticket to work.

def mock_receipt(document_type=96):
    receipt = models.Receipt.objects.create(
        concept=models.ConceptType.objects.get(code=1),
        document_type=models.DocumentType.objects.get(
            code=document_type,
        ),
        document_number="203012345",
        issued_date=date.today(),
        total_amount=130,
        net_untaxed=0,
        net_taxed=100,
        exempt_amount=0,
        currency=models.CurrencyType.objects.get(code='PES'),
        currency_quote=1,

        receipt_type=models.ReceiptType.objects.get(code=6),
        point_of_sales=models.PointOfSales.objects.first(),
    )
    models.Vat.objects.create(
        vat_type=models.VatType.objects.get(code=5),
        base_amount=100,
        amount=21,
        receipt=receipt,
    )
    models.Tax.objects.create(
        tax_type=models.TaxType.objects.get(code=3),
        base_amount=100,
        aliquot=9,
        amount=9,
        receipt=receipt,
    )
    return receipt


class AfipTestCase(TestCase):

    taxpayer = None
    ticket = None

    def setUp(self):
        if not AfipTestCase.taxpayer:
            taxpayer = models.TaxPayer(
                pk=1,
                name='test taxpayer',
                cuit=20329642330,
                is_sandboxed=True,
            )

            basepath = settings.BASE_DIR
            with open(os.path.join(basepath, 'test.key')) as key:
                taxpayer.key.save('test.key', File(key))
            with open(os.path.join(basepath, 'test.crt')) as crt:
                taxpayer.certificate.save('test.crt', File(crt))

            AfipTestCase.taxpayer = taxpayer

        if not AfipTestCase.ticket:
            ticket = models.AuthTicket.objects.get_any_active('wsfe')
            AfipTestCase.ticket = ticket

        AfipTestCase.taxpayer.save()
        AfipTestCase.ticket.save()


class AuthTicketTest(TestCase):

    def test_no_active_taxpayer(self):
        with self.assertRaisesMessage(
            Exception,
            'There are no taxpayers to generate a ticket.',
        ):
            models.AuthTicket.objects.get_any_active('wsfe')


class PopulationTest(AfipTestCase):
    """
    Tests models population view.

    As a side effect, also test valid ticket generation.
    """

    def setUp(self):
        super().setUp()

    def test_population_command(self):
        management.call_command("afipmetadata")

        receipts = models.ReceiptType.objects.count()
        concepts = models.ConceptType.objects.count()
        documents = models.DocumentType.objects.count()
        vat = models.VatType.objects.count()
        tax = models.TaxType.objects.count()
        currencies = models.CurrencyType.objects.count()

        self.assertGreater(receipts, 0)
        self.assertGreater(concepts, 0)
        self.assertGreater(documents, 0)
        self.assertGreater(vat, 0)
        self.assertGreater(tax, 0)
        self.assertGreater(currencies, 0)


class TaxPayerTest(AfipTestCase):

    def test_fetch_points_of_sale(self):
        """
        Test the ``fetch_points_of_sales`` method.
        """
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        points_of_sales = models.PointOfSales.objects.count()
        self.assertGreater(points_of_sales, 0)


class ReceiptBatchTest(AfipTestCase):

    def setUp(self):
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

    def _good_receipt(self):
        return mock_receipt()

    def _bad_receipt(self):
        return mock_receipt(80)

    def test_creation_empty(self):
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.none(),
        )
        self.assertIsNone(batch)

    def test_creation_exclusion(self):
        """
        Test that batch creation excludes already batched receipts.
        """
        self._good_receipt()
        self._good_receipt()
        self._good_receipt()

        models.ReceiptBatch.objects.create(
            models.Receipt.objects.filter(pk=1),
        )
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.filter(batch_id__isnull=True),
        )

        self.assertEquals(batch.receipts.count(), 2)

    def test_validate_empty(self):
        # Hack to easily create an empty batch:
        self._good_receipt()
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.all(),
        )
        models.Receipt.objects.all().delete()

        errs = batch.validate()
        self.assertIsNone(errs)

    def test_validation_good(self):
        self._good_receipt()
        self._good_receipt()
        self._good_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            batch.validation.last().result,
            models.Validation.RESULT_APPROVED,
        )
        self.assertEqual(batch.validation.count(), 1)
        self.assertEqual(batch.receipts.count(), 3)

    def test_validation_bad(self):
        self._bad_receipt()
        self._bad_receipt()
        self._bad_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertEqual(batch.receipts.count(), 0)

    def test_validation_mixed(self):
        self._good_receipt()
        self._bad_receipt()
        self._good_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertEqual(batch.receipts.count(), 1)

    def test_validation_good_service(self):
        receipt = self._good_receipt()
        receipt.concept_id = 2
        receipt.service_start = datetime.now() - timedelta(days=10)
        receipt.service_end = datetime.now()
        receipt.expiration_date = datetime.now() + timedelta(days=10)
        receipt.save()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            batch.validation.last().result,
            models.Validation.RESULT_APPROVED,
        )
        self.assertEqual(batch.receipts.count(), 1)


class ReceiptPDFTest(AfipTestCase):
    """
    For the moment, this test case mostly verifies that pdf generation *works*,
    but does not actually validate the pdf file itself.

    Running this locally *will* yield the file itself, which is useful for
    manual inspection.
    """
    # TODO: Test generation via ReceiptHTMLView

    def setUp(self):
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()
        models.TaxPayerProfile.objects.create(
            taxpayer=taxpayer,
            issuing_name='Red Company Inc.',
            issuing_address='100 Red Av\nRedsville\nUK',
            issuing_email='billing@example.com',
            vat_condition='Exempt',
            gross_income_condition='Exempt',
            sales_terms='Credit Card',
            active_since=datetime(2011, 10, 3),
        )

        models.Receipt.objects.create(
            concept=models.ConceptType.objects.get(code=1),
            document_type=models.DocumentType.objects.get(code=96),
            document_number="203012345",
            issued_date=date.today(),
            total_amount=100,
            net_untaxed=0,
            net_taxed=100,
            exempt_amount=0,
            currency=models.CurrencyType.objects.get(code='PES'),
            currency_quote=1,

            receipt_number=4236,
            receipt_type=models.ReceiptType.objects.get(code=11),
            point_of_sales=models.PointOfSales.objects.first(),
        )

        # TODO: Add a ReceiptEntry

    def test_pdf_generation(self):
        receipt = models.Receipt.objects.first()
        pdf = models.ReceiptPDF.objects.create_for_receipt(
            receipt=receipt,
            client_name="John Doe",
            client_address="12 Green Road\nGreenville\nUK",
        )
        pdf.save_pdf()


class ReceiptAdminTest(AfipTestCase):

    def setUp(self):
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        User.objects._create_user(
           username='superuser',
           email='superuser@email.com',
           password='123',
           is_staff=True,
           is_superuser=True,
        )

    def test_validation_filters(self):
        validated_receipt = mock_receipt()
        not_validated_receipt = mock_receipt()
        # XXX: Receipt with failed validation?

        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.filter(pk=validated_receipt.pk)
        )
        validation = models.Validation.objects.create(
            processed_date=now(),
            result=models.Validation.RESULT_APPROVED,
            batch=batch,
        )
        models.ReceiptValidation.objects.create(
            validation=validation,
            result=models.Validation.RESULT_APPROVED,
            cae='123',
            cae_expiration=now(),
            receipt=validated_receipt,
        )

        client = Client()
        client.force_login(User.objects.first())

        response = client.get('/admin/afip/receipt/?status=validated')
        self.assertContains(
            response,
            '<input class="action-select" name="_selected_action" value="{}" '
            'type="checkbox">'.format(validated_receipt.pk),
            html=True,
        )
        self.assertNotContains(
            response,
            '<input class="action-select" name="_selected_action" value="{}" '
            'type="checkbox">'.format(not_validated_receipt.pk),
            html=True,
        )

        response = client.get('/admin/afip/receipt/?status=not_validated')
        self.assertNotContains(
            response,
            '<input class="action-select" name="_selected_action" value="{}" '
            'type="checkbox">'.format(validated_receipt.pk),
            html=True,
        )
        self.assertContains(
            response,
            '<input class="action-select" name="_selected_action" value="{}" '
            'type="checkbox">'.format(not_validated_receipt.pk),
            html=True,
        )


# TODO: Test receipts with related_receipts
