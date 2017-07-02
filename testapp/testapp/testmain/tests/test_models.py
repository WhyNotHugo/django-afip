from unittest.mock import call, MagicMock, patch

from django.test import TestCase

from django_afip import models
from testapp.testmain import fixtures, mocks
from testapp.testmain.tests.test_webservices import PopulatedAfipTestCase


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


class ReceiptValidateTestCase(PopulatedAfipTestCase):

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
