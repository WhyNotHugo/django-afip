from unittest.mock import call, MagicMock, patch

from django.test import TestCase

from django_afip import exceptions, models
from testapp.testmain import fixtures, mocks
from testapp.testmain.tests.testcases import PopulatedLiveAfipTestCase


class ReceiptQuerySetTestCase(TestCase):

    def test_default_manager(self):
        self.assertIsInstance(
            models.Receipt.objects.all(),
            models.ReceiptQuerySet,
        )

    def test_validate(self):
        receipt = fixtures.ReceiptFactory()
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
        receipt = fixtures.ReceiptFactory()
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


class ReceiptValidateTestCase(PopulatedLiveAfipTestCase):

    def test_validation(self):
        """Test validating valid receipts."""
        receipt = mocks.receipt()

        errs = receipt.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)

    def test_failed_validation(self):
        """Test validating valid receipts."""
        receipt = mocks.receipt(80)

        errs = receipt.validate()

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
        receipt = mocks.receipt(80)

        with self.assertRaisesRegex(
            exceptions.ValidationError,
            # Note: AFIP apparently edited this message and added a typo:
            'DocNro 203012345 no se encuentra registrado en los padrones',
        ):
            receipt.validate(raise_=True)

        # FIXME: We're not creating rejection entries
        # self.assertEqual(
        #     receipt.validation.result,
        #     models.ReceiptValidation.RESULT_REJECTED,
        # )
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)


class ReceiptIsValidatedTestCase(TestCase):
    def test_not_validated(self):
        receipt = fixtures.ReceiptFactory()
        self.assertEqual(receipt.is_validated, False)

    def test_validated(self):
        receipt = fixtures.ReceiptFactory(receipt_number=1)
        fixtures.ReceiptValidationFactory(receipt=receipt)
        self.assertEqual(receipt.is_validated, True)

    def test_failed_validation(self):
        # These should never really exist,but oh well:
        receipt = fixtures.ReceiptFactory()
        fixtures.ReceiptValidationFactory(
            receipt=receipt,
            result=models.ReceiptValidation.RESULT_REJECTED,
        )
        self.assertEqual(receipt.is_validated, False)

        receipt = fixtures.ReceiptFactory(receipt_number=1)
        fixtures.ReceiptValidationFactory(
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
        c1 = fixtures.CurrencyTypeFactory(pk=2)
        c2 = fixtures.CurrencyTypeFactory(pk=1)
        c3 = fixtures.CurrencyTypeFactory(pk=3)

        receipt = models.Receipt()
        self.assertNotEqual(receipt.currency, c1)
        self.assertEqual(receipt.currency, c2)
        self.assertNotEqual(receipt.currency, c3)
