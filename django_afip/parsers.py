from datetime import datetime

import pytz

TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])


def parse_datetime(datestring):
    if datestring == 'NULL' or datestring is None:
        return None
    return datetime.strptime(datestring, '%Y%m%d%H%M%S') \
        .replace(tzinfo=TZ_AR)


def parse_date(datestring):
    if datestring == 'NULL' or datestring is None:
        return None
    return datetime.strptime(datestring, '%Y%m%d').date()


def parse_string(string):
    """
    Re-encodes strings from AFIP's weird encoding to UTF-8.
    """
    return string.encode('latin-1').decode()
