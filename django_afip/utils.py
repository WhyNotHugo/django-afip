from datetime import datetime

from django.conf import settings
from django.utils.functional import LazyObject
from suds import Client


def format_datetime(datetime):
    """
    "Another date formatting function?" you're thinking, eh? Well, this
    actually formats dates in the *exact* format the AFIP's WS expects it,
    which is almost like ISO8601.

    Note that .isoformat() works fine on PROD, but not on TESTING.
    """
    return datetime.strftime("%Y-%m-%dT%H:%M:%S-00:00")


def format_date(date):
    return date.strftime("%Y%m%d")


def parse_date(datestring):
    if datestring == 'NULL':
        return None
    datetime.strptime(datestring, '%Y%m%d').date()

endpoints = {}
if settings.AFIP_DEBUG:
    endpoints['wsaa'] = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # NOQA
    endpoints['wsfe'] = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
else:
    endpoints['wsaa'] = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"
    endpoints['wsfe'] = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"  # NOQA


class WsaaClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(endpoints['wsaa'])


class WsfeClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(endpoints['wsfe'])

wsaa_client = WsaaClient()
wsfe_client = WsfeClient()
