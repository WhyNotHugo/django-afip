from unittest.mock import call, MagicMock, patch

from django.test import TestCase

from django_afip import exceptions, factories, models
from testapp.testmain.tests.testcases import PopulatedLiveAfipTestCase


class ReceiptQuerySetTestCase(TestCase):

    def test_default_manager(self):
        self.assertIsInstance(
            models.Receipt.objects.all(),
            models.ReceiptQuerySet,
        )

    def test_validate(self):
        receipt = factories.ReceiptFactory()
        queryset = models.Receipt.objects.filter(pk=receipt.pk)
        ticket = MagicMock()

        with patch(
            'django_afip.models.ReceiptQuerySet._assign_numbers', spec=True,
        ) as mocked_assign_numbers, patch(
            'django_afip.models.ReceiptQuerySet._validate', spec=True,
        ) as mocked__validate:
            queryset.validate(ticket)

        self.assertEqual(mocked_assign_numbers.call_count, 1)

        self.assertEqual(mocked__validate.call_count, 1)
        self.assertEqual(mocked__validate.call_args, call(ticket))

        # TODO: Also another tests that checks that we only pass filtered-out
        # receipts


class ReceiptManagerTestCase(TestCase):

    def test_default_manager(self):
        self.assertIsInstance(models.Receipt.objects, models.ReceiptManager)


class ReceiptTestCase(TestCase):

    def test_validate(self):
        receipt = factories.ReceiptFactory()
        ticket = MagicMock()
        self.called = False

        def fake_validate(qs, ticket=None):
            self.assertQuerysetEqual(qs, [receipt.pk], lambda r: r.pk)
            self.called = True

        with patch(
            'django_afip.models.ReceiptQuerySet.validate',
            fake_validate,
        ):
            receipt.validate(ticket)

        self.assertTrue(self.called)


class ReceiptSuccessfulValidateTestCase(PopulatedLiveAfipTestCase):

    def setUp(self):
        super().setUp()
        self.receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
        )
        factories.VatFactory(vat_type__code=5, receipt=self.receipt)
        factories.TaxFactory(tax_type__code=3, receipt=self.receipt)

    def test_validation(self):
        """Test validating valid receipts."""
        errs = self.receipt.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            self.receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)


class ReceiptFailedValidateTestCase(PopulatedLiveAfipTestCase):

    def setUp(self):
        super().setUp()
        self.receipt = factories.ReceiptFactory(
            document_type__code=80,
            point_of_sales=models.PointOfSales.objects.first(),
        )
        factories.VatFactory(vat_type__code=5, receipt=self.receipt)
        factories.TaxFactory(tax_type__code=3, receipt=self.receipt)

    def test_failed_validation(self):
        """Test validating valid receipts."""
        errs = self.receipt.validate()

        self.assertEqual(len(errs), 1)
        # FIXME: We're not creating rejection entries
        # self.assertEqual(len(errs), 1)
        # self.assertEqual(
        #     receipt.validation.result,
        #     models.ReceiptValidation.RESULT_REJECTED,
        # )
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)

    def test_raise_validation(self):
        """Test validating valid receipts."""

        with self.assertRaisesRegex(
            exceptions.ValidationError,
            # Note: AFIP apparently edited this message and added a typo:
            'DocNro 203012345 no se encuentra registrado en los padrones',
        ):
            self.receipt.validate(raise_=True)

        # FIXME: We're not creating rejection entries
        # self.assertEqual(
        #     receipt.validation.result,
        #     models.ReceiptValidation.RESULT_REJECTED,
        # )
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)


class ReceiptIsValidatedTestCase(TestCase):
    def test_not_validated(self):
        receipt = factories.ReceiptFactory()
        self.assertEqual(receipt.is_validated, False)

    def test_validated(self):
        receipt = factories.ReceiptFactory(receipt_number=1)
        factories.ReceiptValidationFactory(receipt=receipt)
        self.assertEqual(receipt.is_validated, True)

    def test_failed_validation(self):
        # These should never really exist,but oh well:
        receipt = factories.ReceiptFactory()
        factories.ReceiptValidationFactory(
            receipt=receipt,
            result=models.ReceiptValidation.RESULT_REJECTED,
        )
        self.assertEqual(receipt.is_validated, False)

        receipt = factories.ReceiptFactory(receipt_number=1)
        factories.ReceiptValidationFactory(
            receipt=receipt,
            result=models.ReceiptValidation.RESULT_REJECTED,
        )
        self.assertEqual(receipt.is_validated, False)


class ReceiptDefaultCurrencyTestCase(TestCase):
    def test_no_currencies(self):
        receipt = models.Receipt()
        with self.assertRaises(models.CurrencyType.DoesNotExist):
            receipt.currency

    def test_multieple_currencies(self):
        c1 = factories.CurrencyTypeFactory(pk=2)
        c2 = factories.CurrencyTypeFactory(pk=1)
        c3 = factories.CurrencyTypeFactory(pk=3)

        receipt = models.Receipt()
        self.assertNotEqual(receipt.currency, c1)
        self.assertEqual(receipt.currency, c2)
        self.assertNotEqual(receipt.currency, c3)


class ReceiptTotalVatTestCase(TestCase):
    def test_no_vat(self):
        receipt = factories.ReceiptFactory()

        self.assertEqual(receipt.total_vat, 0)

    def test_multiple_vats(self):
        receipt = factories.ReceiptFactory()
        factories.VatFactory(receipt=receipt)
        factories.VatFactory(receipt=receipt)

        self.assertEqual(receipt.total_vat, 42)

    def test_proper_filtering(self):
        receipt = factories.ReceiptFactory()
        factories.VatFactory(receipt=receipt)
        factories.VatFactory()

        self.assertEqual(receipt.total_vat, 21)


class ReceiptTotalTaxTestCase(TestCase):
    def test_no_tax(self):
        receipt = factories.ReceiptFactory()

        self.assertEqual(receipt.total_tax, 0)

    def test_multiple_taxes(self):
        receipt = factories.ReceiptFactory()
        factories.TaxFactory(receipt=receipt)
        factories.TaxFactory(receipt=receipt)

        self.assertEqual(receipt.total_tax, 18)

    def test_proper_filtering(self):
        receipt = factories.ReceiptFactory()
        factories.TaxFactory(receipt=receipt)
        factories.TaxFactory()

        self.assertEqual(receipt.total_tax, 9)


class CurrencyTypeStrTestCase(TestCase):
    def test_success(self):
        currency_type = models.CurrencyType(
            code='011',
            description='Pesos Uruguayos',
        )
        self.assertEqual(str(currency_type), 'Pesos Uruguayos (011)')
