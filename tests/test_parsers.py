from datetime import date
from datetime import datetime

from django_afip import parsers
from django_afip.clients import TZ_AR


def test_parse_null_datetime():
    assert parsers.parse_datetime_maybe("NULL") is None


def test_parse_none_datetime():
    assert parsers.parse_datetime_maybe(None) is None


def test_parse_datetimes():
    assert parsers.parse_datetime("20170730154330") == datetime(
        2017, 7, 30, 15, 43, 30, tzinfo=TZ_AR
    )

    assert parsers.parse_datetime_maybe("20170730154330") == datetime(
        2017, 7, 30, 15, 43, 30, tzinfo=TZ_AR
    )


def test_parse_null_date():
    assert parsers.parse_date_maybe("NULL") is None


def test_parse_none_date():
    assert parsers.parse_date_maybe(None) is None


def test_parse_dates():
    assert parsers.parse_date("20170730") == date(2017, 7, 30)
    assert parsers.parse_date_maybe("20170730") == date(2017, 7, 30)


def test_weirdly_encoded():
    # This is the encoding AFIP sometimes uses:
    string = "AÃ±adir paÃ\xads"
    assert parsers.parse_string(string) == "Añadir país"
