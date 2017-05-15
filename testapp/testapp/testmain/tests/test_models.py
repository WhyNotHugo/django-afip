from unittest.mock import call, MagicMock, patch

from django.test import TestCase

from django_afip import models
from testapp.testmain import fixtures


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
            'django_afip.models.ReceiptBatch.validate', spec=True,
        ) as mocked_validate:
            queryset.validate(ticket)

        self.assertEqual(mocked_validate.call_count, 1)
        self.assertEqual(mocked_validate.call_args, call(ticket))


class ReceiptManagerTestCase(TestCase):

    def test_default_manager(self):
        self.assertIsInstance(models.Receipt.objects, models.ReceiptManager)


class ReceiptTestCase(TestCase):

    def test_validate(self):
        receipt = fixtures.ReceiptFactory()
        ticket = MagicMock()

        with patch(
            'django_afip.models.ReceiptBatchManager.create', spec=True,
        ) as mocked_validate:
            receipt.validate(ticket)

        self.assertEqual(mocked_validate.call_count, 1)
        self.assertQuerysetEqual(
            mocked_validate.call_args[0][0],
            (receipt.pk,),
            lambda x: (x.pk),
        )
        self.assertEqual(mocked_validate.call_args[0][0].count(), 1)

        mocked_batch = mocked_validate()
        self.assertEqual(mocked_batch.validate.call_count, 1)
        self.assertEqual(mocked_batch.validate.call_args, call(ticket))
