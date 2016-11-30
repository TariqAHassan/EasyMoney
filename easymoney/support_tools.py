# coding: utf-8

"""

    Support Tools
    ~~~~~~~~~~~~~

"""
# Imports
import re
import pandas as pd
import dateutil.parser
from datetime import datetime


# ----------------------------------------------------------------------------------------------------------
# General
# ----------------------------------------------------------------------------------------------------------


def cln(i, extent = 1):
    """

    String white space 'cleaner'.

    :param i: input str
    :type i: ``str``
    :param extent: 1 --> all white space reduced to length 1; 2 --> removal of all white space.
    :return: cleaned string
    :rtype: ``str``
    """
    if isinstance(i, str) and i != "":
        if extent == 1:
            return re.sub(r"\s\s+", " ", i)
        elif extent == 2:
            return re.sub(r"\s+", "", i)
    else:
        return i


def min_max(iterable):
    """

    Get the min and max value of an iterable of numerics.

    :param iterable: any iterable data structure of numerics
    :type iterable: ``tuple``, ``list``, ``np.array``
    :return: (min(iterable), max(iterable))
    :rtype: ``tuple``
    """
    return (min(iterable), max(iterable))


def sort_range_reverse(iterable, action='range'):
    """

    Sort, reverse, or get range of an iterable.

    :param iterable: any iterable
    :type iterable: ``iterable``
    :param action: An action to perform on the iterable.
                   Must be one of: 'sort', 'reverse' or 'range'.
                   `iterable` must only contain numerics for 'range'.
                   Defaults to 'range'.
    :param action: ``str``
    :return: i. sorted or reversed iterable; ii. the min and max of the iterable.
    :rtype: ``list``
    """
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


# ----------------------------------------------------------------------------------------------------------
# Mathematical
# ----------------------------------------------------------------------------------------------------------


def closest_value(value, list_of_values):
    """

    Get the closet value in a list of values.

    :param value: a numeric value.
    :type value: ``int``, ``float`` or ``datetime``
    :param list_of_values: an iterable.
    :type list_of_values: ``tuple``, ``list``, ``np.array``
    :return: item in `list_of_values` closet to `value`.
    :rtype: ``int``, ``float`` or ``datetime``
    """
    # Source: http://stackoverflow.com/a/12141207/4898004
    return min(list_of_values, key=lambda i: abs(i - value))


# ----------------------------------------------------------------------------------------------------------
# Dates
# ----------------------------------------------------------------------------------------------------------


def datetimer(date, from_format=None):
    """

    Converts a date string into a datetime.

    :param date: a date
    :type date: ``str``
    :param from_format: the format of `date`. If none, an attempt will be made to guess the format. Defaults to `None`.
    :type from_format: ``str`` or ``None``
    :return: a datetime object.
    :rtype: ``datetime``
    """
    formatter = datetime.strptime if from_format != None else dateutil.parser.parse
    return formatter(date, from_format)


def date_reformat(date, to_format='%d/%m/%Y', from_format=None):
    """

    Reformat a date to a given form.

    :param date: a date
    :type date: ``str``
    :param to_format: the new format of the date.
    :type to_format: ``str``
    :param from_format: the format of the string supplied.
    :type from_format: ``str``
    :return:
    """
    if not isinstance(date, str):
        return date
    return datetimer(date, from_format).strftime(to_format)


def date_sort(list_of_dates, from_format="%d/%m/%Y"):
    """

    Sort a list of datetimes.

    :param list_of_dates: iterable of date strings
    :type list_of_dates: ``iterable``
    :param from_format: the format of the strings in `list_of_dates`. Defaults to "%d/%m/%Y".
    :type from_format: ``str``
    :return: sorted date strings
    :rtype: ``list``
    """
    return sorted(list_of_dates, key=lambda x: datetime.strptime(x, from_format))


def min_max_dates(list_of_dates, from_format="%d/%m/%Y"):
    """

    Get the min and max date in a list of date strings.

    :param list_of_dates: list of date strings.
    :type list_of_dates: ``iterable``
    :param from_format: the format of the strings in `list_of_dates`. Defaults to "%d/%m/%Y".
    :type from_format: ``str``
    :return: (min(list_of_dates), max(list_of_dates))
    :rtype: tuple
    """
    pandas_datetime = pd.to_datetime(pd.Series(list_of_dates), format=from_format)
    return (pandas_datetime.min().strftime(from_format), pandas_datetime.max().strftime(from_format))


def fast_date_range(dates, from_format='%d/%m/%Y'):
    """

    Fast function to find the min and max date in an iterable of date strings.

    :param dates: iterable of strings
    :type dates: ``iterable``
    :param from_format: date format. Defaults to '%d/%m/%Y'.
    :type from_format: ``str``
    :return: [min(dates), max(dates)]
    :rtype: ``list``
    """
    return [i.strftime(from_format) for i in min_max([datetime.strptime(j, from_format) for j in dates])]


def closest_date(date, list_of_dates, from_format="%d/%m/%Y"):
    """

    Get the closet date (string) in a list of datestrings.

    :param date: a date.
    :type date: ``str``
    :param list_of_dates: an iterable of date strings.
    :type list_of_dates: ``iterable``
    :param from_format: the format of the strings in `list_of_dates`. Defaults to "%d/%m/%Y".
    :type from_format: ``str``
    :return: closest date in `list_of_dates` to `date`.
    :rtype: ``str``
    """
    list_of_datetimes = [datetimer(d, from_format) for d in list_of_dates]
    closest = closest_value(datetimer(date, from_format), list_of_datetimes)
    return closest.strftime(from_format)


def _canonical_datetime(date_format):
    """

    Converts a date format to a human-readable format.

    :param date_format: a python-recognized date format containing any of: '%d', '%m' or '%Y'.
    :type date_format: ``str``
    :return: %d --> DD;  %m --> MM;  %Y --> YYYY.
    :rtype: ``str``
    """
    for f, c in zip(['%d', '%m', '%Y'], ['DD', 'MM', 'YYYY']):
        date_format = date_format.replace(f, c)
    return date_format


def date_format_check(date, from_format="%d/%m/%Y"):
    """

    Check whether or not a date is of a given form.

    :param date_format: a date.
    :type date: ``str``
    :param from_format: a python-recognized date format.
    :type from_format: ``str``
    :return: True if `date` is of the form `from_format` else raises ValueError.
    :rtype: ``bool``
    """
    try:
        datetime.strptime(date, from_format)
        return True
    except ValueError:
        raise ValueError("Invalid date format.\n"
                         "Please supply a date of the form: %s." % (_canonical_datetime(from_format)))


def year_extract(date):
    """

    Extract year from a date.
    Assumes `date` to contain a year of the form: YYYY.

    :param date: a string containing a year
    :type date: ``str``
    :return: the first year found in string
    :rtype: ``str`` or ``None``
    """
    year = ""
    for c in str(date):
        if len(year) == 4:
            break
        if c.isdigit():
            year += c
        elif not c.isdigit() and len(year) < 4:
            year = ""
    return year if len(year) == 4 else None


# ----------------------------------------------------------------------------------------------------------
# Money Formatting
# ----------------------------------------------------------------------------------------------------------


def _money_formater(amount, precision, currency=''):
    """

    Formats money to be human-readable.

    :param amount: amount of money
    :type amount: ``float``, ``str`` or ``int``
    :param precision: number of place after the decimal to round to.
    :type amount: ``int``
    :param currency: A currency code to append to the result. Defaults to none ('').
    :type currency: ``str``
    :return: formated money
    :rtype: ``str``
    """
    return ('{:,.2f}'.format(round(float(amount), precision)) + ' ' + currency).strip()


def mint(amount, precision, currency='', pretty_print=False):
    """

    Print Money or Return it as a float.

    :param amount: amount of money
    :type amount: ``float``, ``str`` or ``int``
    :param precision: number of place after the decimal to round to.
    :param currency: A currency code to append to the result. Defaults to none ('').
    :type currency: ``str``
    :param pretty_print:
    :type pretty_print: ``bool``
    :return: money rounded to the requested precision or printed.
    :rtype: ``float`` or ``None``
    """
    if pretty_print:
        print(_money_formater(amount, precision, currency))
    else:
        return round(float(amount), precision)




