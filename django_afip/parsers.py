from __future__ import annotations

from datetime import date
from datetime import datetime

from django_afip.clients import TZ_AR


def parse_datetime(datestring: str) -> datetime:
    return datetime.strptime(datestring, "%Y%m%d%H%M%S").replace(tzinfo=TZ_AR)


def parse_datetime_maybe(datestring: str | None) -> datetime | None:
    if datestring == "NULL" or datestring is None:
        return None
    return parse_datetime(datestring)


def parse_date(datestring: str) -> date:
    return datetime.strptime(datestring, "%Y%m%d").date()


def parse_date_maybe(datestring: str | None) -> date | None:
    if datestring == "NULL" or datestring is None:
        return None
    return parse_date(datestring)


def parse_string(string: str) -> str:
    """Re-encodes strings from AFIP's weird encoding to UTF-8."""
    try:
        return string.encode("latin-1").decode()
    except UnicodeDecodeError:
        # It looks like SOME errors are plain UTF-8 text.
        return string
