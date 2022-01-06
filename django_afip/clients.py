__all__ = ("get_client",)

from functools import lru_cache

from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore # noqa

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")
WSDLS = {
    ("wsaa", False): "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl",
    ("wsfe", False): "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    ("wsaa", True): "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl",
    ("wsfe", True): "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
}


@lru_cache(maxsize=32)
def get_client(service_name: str, sandbox=False) -> Client:
    """Return a client for a given AFIP web service.

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
        return Client(WSDLS[key], transport=Transport(cache=SqliteCache(timeout=86400)))
    except KeyError:
        raise ValueError(f"Unknown service name, {service_name}")
