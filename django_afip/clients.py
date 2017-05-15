import pytz
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport

TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])


transport = Transport(cache=SqliteCache(timeout=86400))
wsdls = {
    ('wsaa', False): 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl',
    ('wsfe', False): 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL',
    ('wsaa', True): 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl',
    ('wsfe', True): 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL',
}

cached_clients = {}


def get_client(service_name, sandbox=False):
    """
    Returns a client for a given service.

    The `sandbox` argument should only be necessary if a the client will be
    used to make a request. If it will only be used to serialize objects, it is
    irrelevant.  Avoid the overhead of determining the sandbox mode in the
    calling context if only serialization operations will take place.

    :param string service_name: The name of the web services.
    :param bool sandbox: Whether the sandbox (or production) environment should
        be used by the returned client.
    :returns: A zeep client to communicate with an AFIP webservice.
    :rtype: zeep.Client
    """
    key = (service_name.lower(), sandbox,)

    try:
        if key not in cached_clients:
            cached_clients[key] = Client(wsdls[key], transport=transport)

        return cached_clients[key]
    except KeyError:
        ValueError('Unknown service name, {}'.format(service_name))
