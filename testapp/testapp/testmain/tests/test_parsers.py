from datetime import date
from datetime import datetime

import pytz

from django_afip import parsers


def test_parse_null_datetime():
    assert parsers.parse_datetime("NULL") is None


def test_parse_none_datetime():
    assert parsers.parse_datetime(None) is None


def test_parse_datetimes():
    tz = pytz.timezone(pytz.country_timezones["ar"][0])

    assert parsers.parse_datetime("20170730154330") == datetime(
        2017, 7, 30, 15, 43, 30, tzinfo=tz
    )


def test_parse_null_date():
    assert parsers.parse_date("NULL") is None


def test_parse_none_date():
    assert parsers.parse_date(None) is None


def test_parse_dates():
    assert parsers.parse_date("20170730") == date(2017, 7, 30)


def test_weirdly_encoded():
    # This is the encoding AFIP sometimes uses:
    string = "AÃ±adir paÃ\xads"
    assert parsers.parse_string(string) == "Añadir país"
