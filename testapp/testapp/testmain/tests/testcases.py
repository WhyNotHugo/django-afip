from django.test import tag, TestCase

from django_afip import factories, models


@tag('live')
class LiveAfipTestCase(TestCase):
    """
    Base class for AFIP-WS related tests.

    Since AFIP rate-limits how often authentication tokens can be fetched, we
    need to keep one between tests.
    This class is a simple hack to keep that ticket in-memory and saves it into
    the DB every time a new class is ``setUp``.
    """

    ticket = None

    def setUp(self):
        """Save a TaxPayer and Ticket into the database."""
        LiveAfipTestCase.taxpayer = factories.TaxPayerFactory(pk=1)

        if not LiveAfipTestCase.ticket:
            ticket = models.AuthTicket.objects.get_any_active('wsfe')
            LiveAfipTestCase.ticket = ticket

        LiveAfipTestCase.ticket.save()


class PopulatedLiveAfipTestCase(LiveAfipTestCase):
    def setUp(self):
        """Populate AFIP metadata and create a TaxPayer and PointOfSales."""
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()
