import http.client
import logging
import socket
import ssl
from http.client import HTTPS_PORT, HTTPConnection
from ssl import (_RESTRICTED_SERVER_CIPHERS, CERT_NONE, CERT_REQUIRED,
                 OP_NO_SSLv2, OP_NO_SSLv3, PROTOCOL_TLSv1, Purpose, SSLContext,
                 _ASN1Object, _ssl)

logger = logging.getLogger(__name__)


def create_afip_compatible_context(purpose=Purpose.SERVER_AUTH, *, cafile=None,
                                   capath=None, cadata=None):
    """Create a SSLContext object with default settings.

    NOTE: The protocol and settings may change anytime without prior
          deprecation. The values represent a fair balance between maximum
          compatibility and security.
    """
    if not isinstance(purpose, _ASN1Object):
        raise TypeError(purpose)

    context = SSLContext(PROTOCOL_TLSv1)

    # SSLv2 considered harmful.
    context.options |= OP_NO_SSLv2

    # SSLv3 has problematic security and is only required for really old
    # clients such as IE6 on Windows XP
    context.options |= OP_NO_SSLv3

    # disable compression to prevent CRIME attacks (OpenSSL 1.0+)
    context.options |= getattr(_ssl, "OP_NO_COMPRESSION", 0)

    if purpose == Purpose.SERVER_AUTH:
        # verify certs and host name in client mode
        context.verify_mode = CERT_REQUIRED
        context.check_hostname = True
    elif purpose == Purpose.CLIENT_AUTH:
        # Prefer the server's ciphers by default so that we get stronger
        # encryption
        context.options |= getattr(_ssl, "OP_CIPHER_SERVER_PREFERENCE", 0)

        # Use single use keys in order to improve forward secrecy
        context.options |= getattr(_ssl, "OP_SINGLE_DH_USE", 0)
        context.options |= getattr(_ssl, "OP_SINGLE_ECDH_USE", 0)

        # disallow ciphers with known vulnerabilities
        context.set_ciphers(_RESTRICTED_SERVER_CIPHERS)

    if cafile or capath or cadata:
        context.load_verify_locations(cafile, capath, cadata)
    elif context.verify_mode != CERT_NONE:
        # no explicit cafile, capath or cadata but the verify mode is
        # CERT_OPTIONAL or CERT_REQUIRED. Let's try to load default system
        # root CA certificates for the given purpose. This may fail silently.
        context.load_default_certs(purpose)
    return context


class MonkeyPatchedHTTPSConnection(HTTPConnection):

    default_port = HTTPS_PORT

    # XXX Should key_file and cert_file be deprecated in favour of context?

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None, *, context=None,
                 check_hostname=None):
        super().__init__(host, port, timeout, source_address)
        self.key_file = key_file
        self.cert_file = cert_file
        if context is None:
            if host == "wswhomo.afip.gov.ar":
                context = create_afip_compatible_context()
            elif hasattr(ssl, '_create_default_https_context'):  # py 3.4.3
                context = ssl._create_default_https_context()
            else:  # py 3.4.2
                context = ssl._create_stdlib_context()
        will_verify = context.verify_mode != ssl.CERT_NONE
        if check_hostname is None:
            check_hostname = context.check_hostname
        if check_hostname and not will_verify:
            raise ValueError("check_hostname needs a SSL context with "
                             "either CERT_OPTIONAL or CERT_REQUIRED")
        if key_file or cert_file:
            context.load_cert_chain(cert_file, key_file)
        self._context = context
        self._check_hostname = check_hostname

    def connect(self):
        "Connect to a host on a given (SSL) port."

        super().connect()

        if self._tunnel_host:
            server_hostname = self._tunnel_host
        else:
            server_hostname = self.host

        self.sock = self._context.wrap_socket(self.sock,
                                              server_hostname=server_hostname)
        if not self._context.check_hostname and self._check_hostname:
            try:
                ssl.match_hostname(self.sock.getpeercert(), server_hostname)
            except Exception:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                raise


def patch_https_for_afip():
    logger.info(
        "Monkey patching HTTPSConnection to work with AFIP's servers"
    )
    http.client.HTTPSConnection = MonkeyPatchedHTTPSConnection
