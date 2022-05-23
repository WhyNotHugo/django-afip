__all__ = ("get_client",)

from functools import lru_cache
from urllib.parse import urlparse

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import DEFAULT_CIPHERS  # type:ignore
from urllib3.util.ssl_ import create_urllib3_context
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore # noqa

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")
CIPHERS = DEFAULT_CIPHERS + "HIGH:!DH:!aNULL"
WSDLS = {
    ("wsaa", False): "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl",
    ("wsfe", False): "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    ("wsaa", True): "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl",
    ("wsfe", True): "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
}


class AFIPAdapter(HTTPAdapter):
    """An adapter with reduced security so it'll work with AFIP."""

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=CIPHERS)
        kwargs["ssl_context"] = context
        return super().proxy_manager_for(*args, **kwargs)


@lru_cache(maxsize=1)
def get_or_create_transport() -> Transport:
    """Create a specially-configured Zeep transport.

    This transport does two non-default things:
    - Reduces TLS security. Sadly, AFIP only has insecure endpoints, so we're
      forced to reduce security to talk to them.
    - Cache the WSDL file for a whole day.

    This function will only create a transport once, and return the same
    transport in subsequent calls.
    """

    session = Session()

    # For each WSDL, extract the domain, and add it as an exception:
    for url in WSDLS.values():
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        session.mount(base_url, AFIPAdapter())

    return Transport(cache=SqliteCache(timeout=86400), session=session)


@lru_cache(maxsize=32)
def get_client(service_name: str, sandbox=False) -> Client:
    """
    Return a client for a given service.

    The `sandbox` argument should only be necessary if the client will be
    used to make a request. If it will only be used to serialize objects, it is
    irrelevant. A caller can avoid the overhead of determining the sandbox mode in the
    calling context if only serialization operations will take place.

    This function is cached with `lru_cache`, and will re-use existing clients
    if possible.

    :param service_name: The name of the web services.
    :param sandbox: Whether the sandbox (or production) environment should
        be used by the returned client.
    :returns: A zeep client to communicate with an AFIP web service.
    """
    key = (service_name.lower(), sandbox)

    try:
        return Client(WSDLS[key], transport=get_or_create_transport())
    except KeyError:
        raise ValueError(f"Unknown service name, {service_name}")
