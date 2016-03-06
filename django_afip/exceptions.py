from . import parsers


class AfipException(Exception):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, err):
        Exception.__init__(self, "Error {}: {}".format(
            err.Code,
            parsers.parse_string(err.Msg),
        ))
