from __future__ import annotations

from dataclasses import dataclass

from django_afip import clients


@dataclass(frozen=True)
class ServerStatus:
    """A dataclass holding the server's reported status.

    An instance is truthy if all services are okay, or evaluates to ``False``
    if at least one isn't::

        if not server_status:
            print("At least one service is down")
        else
            print("All serivces are up")
    """

    #: Whether the application server is working.
    app: bool
    #: Whether the database server is working.
    db: bool
    #: Whether the authentication server is working.
    auth: bool

    def __bool__(self) -> bool:
        return self.app and self.db and self.auth


def get_server_status(production: bool) -> ServerStatus:
    """Return the status of AFIP's WS servers

    :param production: Whether to check the production servers. If false, the
        testing servers will be checked instead.
    """
    client = clients.get_client("wsfe", not production)
    response = client.service.FEDummy()

    return ServerStatus(
        app=response["AppServer"] == "OK",
        db=response["DbServer"] == "OK",
        auth=response["AuthServer"] == "OK",
    )
