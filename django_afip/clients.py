import pytz
from django.utils.functional import LazyObject
from zeep import Client

TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])


# XXX: Below are a set of clients for each WS. Each one is
# lazy-initialized ONCE, and only once.
#
# The code layout is somewhat ugly, so, if you have better code-pattern,
# patches are welcome.


class WsaaProductionClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
        )


class WsaaSandboxClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
        )


class WsfeProductionClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
        )


class WsfeSandboxClient(LazyObject):

    def _setup(self):
        self._wrapped = Client(
            'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
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
