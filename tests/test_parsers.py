from __future__ import annotations

from datetime import date
from datetime import datetime

from django_afip import parsers
from django_afip.clients import TZ_AR


def test_parse_null_datetime() -> None:
    assert parsers.parse_datetime_maybe("NULL") is None


def test_parse_none_datetime() -> None:
    assert parsers.parse_datetime_maybe(None) is None


def test_parse_datetimes() -> None:
    assert parsers.parse_datetime("20170730154330") == datetime(
        2017, 7, 30, 15, 43, 30, tzinfo=TZ_AR
    )

    assert parsers.parse_datetime_maybe("20170730154330") == datetime(
        2017, 7, 30, 15, 43, 30, tzinfo=TZ_AR
    )


def test_parse_null_date() -> None:
    assert parsers.parse_date_maybe("NULL") is None


def test_parse_none_date() -> None:
    assert parsers.parse_date_maybe(None) is None


def test_parse_dates() -> None:
    assert parsers.parse_date("20170730") == date(2017, 7, 30)
    assert parsers.parse_date_maybe("20170730") == date(2017, 7, 30)


def test_weirdly_encoded() -> None:
    # This is the encoding AFIP sometimes uses:
    string = "AÃ±adir paÃ\xads"
    assert parsers.parse_string(string) == "Añadir país"
