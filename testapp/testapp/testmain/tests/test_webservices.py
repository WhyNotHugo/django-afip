"""Tests for AFIP-WS related classes."""
import os
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core import management
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils.timezone import now

from django_afip import exceptions, models
from testapp.testmain import mocks


class AfipTestCase(TestCase):
    """
    Base class for AFIP-WS related tests.

    Since AFIP rate-limits how often authentication tokens can be fetched, we
    need to keep one between tests.
    This class is a simple hack to keep that ticket in-memory and saves it into
    the DB every time a new class is ``setUp``.
    """

    taxpayer = None
    ticket = None

    def setUp(self):
        """Save a TaxPayer and Ticket into the database."""
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
    """Test AuthTicket methods."""

    def test_bad_cuit(self):
        """Test using the wrong cuit for a key pair."""

        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            # This is the wrong CUIT for our keypair:
            cuit=20329642339,
            is_sandboxed=True,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        taxpayer.create_ticket('wsfe')

        with self.assertRaisesRegex(
            exceptions.AfipException,
            # Note: AFIP apparently edited this message and added a typo:
            'ValidacionDeToken: No apareci[oó] CUIT en lista de relaciones:',
        ):
            models.populate_all()

    def test_bogus_certificate_exception(self):
        """Test that using a junk ceritificates raises as expected."""
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            is_sandboxed=True,
        )
        # Note that we swap key and crt so that it's bogus input:
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.crt')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.key')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.CorruptCertificate) as e:
            taxpayer.create_ticket('wsfe')

        self.assertNotIsInstance(e, exceptions.AfipException)

    def test_no_active_taxpayer(self):
        """Test that no TaxPayers raises an understandable error."""
        with self.assertRaisesMessage(
            exceptions.AuthenticationError,
            'There are no taxpayers to generate a ticket.',
        ):
            models.AuthTicket.objects.get_any_active('wsfe')

    def test_expired_certificate_exception(self):
        """Test that using an expired ceritificate raises as expected."""
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            is_sandboxed=True,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test_expired.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test_expired.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.CertificateExpired):
            taxpayer.create_ticket('wsfe')

    def test_untrusted_certificate_exception(self):
        """
        Test that using an untrusted ceritificate raises as expected.
        """
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            # Note that we hit production with a sandbox cert here:
            is_sandboxed=False,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.UntrustedCertificate):
            taxpayer.create_ticket('wsfe')


class PopulationTest(AfipTestCase):
    """
    Tests models population view.

    As a side effect, also test valid ticket generation.
    """

    def test_population_command(self):
        """Test the afipmetadata command."""
        management.call_command('afipmetadata')

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
    """Test TaxPayer methods."""

    def test_fetch_points_of_sale(self):
        """Test the ``fetch_points_of_sales`` method."""
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        points_of_sales = models.PointOfSales.objects.count()
        self.assertGreater(points_of_sales, 0)


class ReceiptBatchTest(AfipTestCase):
    """Test ReceiptBatch methods."""

    def setUp(self):
        """Populate AFIP metadata and create a TaxPayer and PointOfSales."""
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

    def _good_receipt(self):
        return mocks.receipt()

    def _bad_receipt(self):
        return mocks.receipt(80)

    def test_creation_empty(self):
        """
        Test creation of an empty batch.

        An empty batch has no sense, and None should be returned.
        """
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.none(),
        )
        self.assertIsNone(batch)

    def test_creation_exclusion(self):
        """Test that batch creation excludes already batched receipts."""
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
        """Test that validating an empty batch does not crash."""
        # Hack to easily create an empty batch:
        self._good_receipt()
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.all(),
        )
        models.Receipt.objects.all().delete()

        errs = batch.validate()
        self.assertEqual(errs, [])

    def test_validation_good(self):
        """Test validating valid receipts."""
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
        """Test validating invalid receipts."""
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
        """
        Test validating a mixture of valid and invalid receipts.

        Receipts are validated by AFIP in-order, so all receipts previous to
        the bad one are validated, and nothing else is even parsed after the
        invalid one.
        """
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

    def test_validation_validated(self):
        """Test validating invalid receipts."""
        receipt = self._good_receipt()
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.all()
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
            receipt=receipt,
        )

        receipt.batch = None
        receipt.save()

        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.all()
        )
        self.assertIsNotNone(batch)
        errs = batch.validate()

        self.assertEqual(errs, [])

    def test_validation_good_service(self):
        """Test validating a receipt for a service (rather than product)."""
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

    def test_validation_good_without_tax(self):
        """Test validating valid receipts."""
        mocks.receipt(with_tax=False)

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            batch.validation.last().result,
            models.Validation.RESULT_APPROVED,
        )
        self.assertEqual(batch.validation.count(), 1)
        self.assertEqual(batch.receipts.count(), 1)

    def test_validation_good_without_vat(self):
        """Test validating valid receipts."""
        mocks.receipt(with_vat=False, receipt_type=11)

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            batch.validation.last().result,
            models.Validation.RESULT_APPROVED,
        )
        self.assertEqual(batch.validation.count(), 1)
        self.assertEqual(batch.receipts.count(), 1)


class ReceiptPDFTest(AfipTestCase):
    """Test ReceiptPDF methods."""

    # TODO: Test generation via ReceiptHTMLView

    def setUp(self):
        """Generate a valid receipt for later PDF generation."""
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
            document_number='203012345',
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

    def _create_valid_receipt(self):
        receipt = models.Receipt.objects.first()
        pdf = models.ReceiptPDF.objects.create_for_receipt(
            receipt=receipt,
            client_name='John Doe',
            client_address='12 Green Road\nGreenville\nUK',
        )
        pdf.save_pdf()

        return pdf

    def test_pdf_generation(self):
        """
        Test PDF file generation.

        For the moment, this test case mostly verifies that pdf generation
        *works*, but does not actually validate the pdf file itself.

        Running this locally *will* yield the file itself, which is useful for
        manual inspection.
        """
        pdf = self._create_valid_receipt()
        self.assertTrue(pdf.pdf_file.name.startswith('receipts/'))
        self.assertTrue(pdf.pdf_file.name.endswith('.pdf'))

    def test_html_view(self):
        """
        Test the PDF generation view.
        """
        pdf = self._create_valid_receipt()

        client = Client()
        response = client.get(
            reverse('receipt_html_view', args=(pdf.receipt.pk,))
        )
        self.assertContains(
            response,
            '<div class="client">\n<strong>Facturado a:</strong><br>\n John '
            'Doe,\nDNI\n203012345\n<!-- linkbreaks adds a br here -->\n<p>12 '
            'Green Road<br />Greenville<br />UK</p>\n Exempt<br>\nCredit '
            'Card\n</div>',
            html=True,
        )

    def test_pdf_view(self):
        """
        Test the PDF generation view.
        """
        pdf = self._create_valid_receipt()

        client = Client()
        response = client.get(
            reverse('receipt_pdf_view', args=(pdf.receipt.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:10], b'%PDF-1.5\n%')

        headers = sorted(response.serialize_headers().decode().splitlines())
        expected_headers = sorted([
            'Content-Type: application/pdf',
            'X-Frame-Options: SAMEORIGIN',
            'Content-Disposition: attachment; filename=receipt {}.pdf'.format(
                pdf.receipt.pk
            ),
        ])
        self.assertEqual(headers, expected_headers)

    def test_unauthorized_receipt_generation(self):
        """
        Test PDF file generation for unauthorized receipts.

        Confirm that attempting to generate a PDF for an unauthorized receipt
        raises.
        """
        receipt = models.Receipt.objects.first()
        receipt.receipt_number = None
        receipt.save()
        pdf = models.ReceiptPDF.objects.create_for_receipt(
            receipt=receipt,
            client_name='John Doe',
            client_address='12 Green Road\nGreenville\nUK',
        )
        with self.assertRaisesMessage(
            Exception,
            'Cannot generate pdf for non-authorized receipt'
        ):
            pdf.save_pdf()


class ReceiptAdminTest(AfipTestCase):
    """Test ReceiptAdmin methods."""

    def setUp(self):
        """Initialized AFIP metadata and a single django superuser."""
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
        """
        Test the admin validation filters.

        This filters receipts by the validation status.
        """
        validated_receipt = mocks.receipt()
        not_validated_receipt = mocks.receipt()
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
