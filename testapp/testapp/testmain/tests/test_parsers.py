from datetime import date, datetime

import pytz
from django.test import TestCase

from django_afip import parsers


class ParseDatetimeTestCase(TestCase):
    def test_parse_null(self):
        self.assertEqual(parsers.parse_datetime('NULL'), None)

    def test_parse_none(self):
        self.assertEqual(parsers.parse_datetime(None), None)

    def test_parse_datetimes(self):
        tz = pytz.timezone(pytz.country_timezones['ar'][0])
        self.assertEqual(
            parsers.parse_datetime('20170730154330'),
            datetime(2017, 7, 30, 15, 43, 30, tzinfo=tz),
        )


class ParseDateTestCase(TestCase):
    def test_parse_null(self):
        self.assertEqual(parsers.parse_date('NULL'), None)

    def test_parse_none(self):
        self.assertEqual(parsers.parse_date(None), None)

    def test_parse_dates(self):
        self.assertEqual(
            parsers.parse_date('20170730'),
            date(2017, 7, 30),
        )


class ParseString(TestCase):
    def test_weirdly_encoded(self):
        # This is the encoding AFIP sometimes uses:
        string = 'AÃ±adir paÃ\xads'
        self.assertEqual(parsers.parse_string(string), 'Añadir país')
