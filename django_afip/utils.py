from datetime import datetime

import pytz
from django.utils.functional import LazyObject
from suds import Client

TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])


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


def parse_datetime(datestring):
    if datestring == 'NULL' or datestring is None:
        return None
    return datetime.strptime(datestring, '%Y%m%d%H%M%S') \
        .replace(tzinfo=TZ_AR)


def parse_date(datestring):
    if datestring == 'NULL' or datestring is None:
        return None
    return datetime.strptime(datestring, '%Y%m%d').date()


def encode_str(string):
    """
    Re-encodes strings from AFIP's weird encoding to unicode.
    """
    return string.encode('latin-1').decode()


class AfipException(Exception):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, err):
        Exception.__init__(self, "Error {}: {}".format(
            err.Code,
            encode_str(err.Msg),
        ))

# XXX: Below are a set of clients for each WS. Each one is
# lazy-initialized ONCE, and only once.
#
# The code layout is somewhat ugly, so, if you have better code-pattern,
# patches are welcome.


class WsaaProductionClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"
        )


class WsaaSandboxClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
        )


class WsfeProductionClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"
        )


class WsfeSandboxClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
        )

production_clients = dict(
    wsaa=WsaaProductionClient(),
    wsfe=WsfeProductionClient(),
)

sandbox_clients = dict(
    wsaa=WsaaSandboxClient(),
    wsfe=WsfeSandboxClient(),
)


def get_client(service_name, sandbox=False):
    """
    Returns a client for a given service.

    The `sandbox` argument should only be necessary if a the client will be
    used to make a request. If it will only be used to serialize objects, it is
    irrelevant.  Avoid the overhead of determining the sandbox mode in the
    calling context if only serialization operations will take place.
    """
    if sandbox:
        return sandbox_clients[service_name]
    else:
        return production_clients[service_name]
