#!/usr/bin/env python3

"""

    Support Tools
    ~~~~~~~~~~~~~

"""
# Imports
import re
import pandas as pd
import dateutil.parser
from datetime import datetime


# ---------------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------------

def cln(i, extent = 1):
    """
    String white space 'cleaner'.
    :param i:
    :param extent: 1 --> all white space reduced to length 1; 2 --> removal of all white space.
    :return:
    """
    if isinstance(i, str) and i != "":
        if extent == 1:
            return re.sub(r"\s\s+", " ", i)
        elif extent == 2:
            return re.sub(r"\s+", "", i)
    else:
        return i

def min_max(iterable):
    return (min(iterable), max(iterable))

def sort_range_reverse(iterable, action='range'):
    if not isinstance(iterable, list):
        return iterable
    elif action == 'sort':
        return sorted(iterable)
    elif action == 'reverse':
        return list(reversed(iterable))
    elif action == 'range':
        return list(min_max(iterable))
    else:
        return iterable

# ---------------------------------------------------------------------------------
# Mathematical
# ---------------------------------------------------------------------------------

def closest_value(value, list_of_values):
    # Source: http://stackoverflow.com/a/12141207/4898004
    return min(list_of_values, key=lambda i: abs(i - value))

# ---------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------

def datetimer(date, from_format=None):
    formatter = datetime.strptime if from_format != None else dateutil.parser.parse
    return formatter(date, from_format)

def date_reformat(date, to_format='%d/%m/%Y', from_format=None):
    if not isinstance(date, str):
        return date
    return datetimer(date, from_format).strftime(to_format)

def date_sort(list_of_dates, from_format="%d/%m/%Y"):
    return sorted(list_of_dates, key=lambda x: datetime.strptime(x, from_format))

def min_max_dates(list_of_dates, from_format="%d/%m/%Y"):
    pandas_datetime = pd.to_datetime(pd.Series(list_of_dates), format=from_format)
    return (pandas_datetime.min().strftime(from_format), pandas_datetime.max().strftime(from_format))

def closest_date(date, list_of_dates, from_format="%d/%m/%Y"):
    list_of_datetimes = [datetimer(d, from_format) for d in list_of_dates]
    closest = closest_value(datetimer(date, from_format), list_of_datetimes)
    return closest.strftime(from_format)

def _canonical_datetime(date_format):
    for f, c in zip(['%d', '%m', '%Y'], ['DD', 'MM', 'YYYY']):
        date_format = date_format.replace(f, c)
    return date_format

def date_format_check(date, from_format="%d/%m/%Y"):
    try:
        datetime.strptime(date, from_format)
        return True
    except ValueError:
        raise ValueError("Invalid date format.\n"
                         "Please supply a date of the form: %s." % (_canonical_datetime(from_format)))

def year_extract(date):
    year = ""
    for c in str(date):
        if len(year) == 4:
            break
        if c.isdigit():
            year += c
        elif not c.isdigit() and len(year) < 4:
            year = ""
    return year if len(year) == 4 else None

# ---------------------------------------------------------------------------------
# Money Formatting
# ---------------------------------------------------------------------------------

def money_formater(amount, currency=''):
    return ('{:,.2f}'.format(round(float(amount), 2)) + ' ' + currency).strip()

def mint(amount, currency='', pretty_print=False):
    if pretty_print:
        print(money_formater(amount, currency=currency))
    else:
        return float(amount)














