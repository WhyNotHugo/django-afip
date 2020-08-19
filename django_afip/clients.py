__all__ = (
    'get_client',
)

from urllib.parse import urlparse

import pytz
from django.utils.functional import LazyObject
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context, DEFAULT_CIPHERS
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport

TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])
CIPHERS = DEFAULT_CIPHERS + 'HIGH:!DH:!aNULL'
WSDLS = {
    ('wsaa', False): 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl',
    ('wsfe', False): 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL',
    ('wsaa', True): 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',
    ('wsfe', True): 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL',
}


class AFIPAdapter(HTTPAdapter):
    """An adapter with reduced security so it'll work with AFIP."""

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs['ssl_context'] = context
        return super().proxy_manager_for(*args, **kwargs)


class LazyTransport(LazyObject):
    """A lazy-initialized Zeep transport.

    This transport does two non-default things:
    - Reduces TLS security. Sadly, AFIP only has insecure endpoints, so we're
      forced to reduce security to talk to them.
    - Cache the WSDL file for a whole day.
    """

    def _setup(self):
        """Initialise this lazy object with a celery app instance."""
        session = Session()

        # For each WSDL, extract the domain, and add it as an exception:
        for url in WSDLS.values():
            parsed = urlparse(url)
            base_url = f'{parsed.scheme}://{parsed.netloc}'
            session.mount(base_url, AFIPAdapter())

        self._wrapped = Transport(
            cache=SqliteCache(timeout=86400),
            session=session,
        )


transport = LazyTransport()
cached_clients = {}


def get_client(service_name, sandbox=False):
    """
    Return a client for a given service.

    The `sandbox` argument should only be necessary if a the client will be
    used to make a request. If it will only be used to serialize objects, it is
    irrelevant. A caller can avoid the overhead of determining the sandbox
    mode in the calling context if only serialization operations will take
    place.

    :param string service_name: The name of the web services.
    :param bool sandbox: Whether the sandbox (or production) environment should
        be used by the returned client.
    :returns: A zeep client to communicate with an AFIP web service.
    :rtype: zeep.Client
    """
    key = (service_name.lower(), sandbox,)

    try:
        if key not in cached_clients:
            cached_clients[key] = Client(WSDLS[key], transport=transport)

        return cached_clients[key]
    except KeyError:
        raise ValueError('Unknown service name, {}'.format(service_name))
