#!/usr/bin/env python3

"""

    General Support Tools
    ~~~~~~~~~~~~~~~~~~~~~

"""

# modules
import re
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

def min_max_dates(list_of_dates, from_format="%d/%m/%Y"):
    datetimes = [datetimer(d, from_format) for d in list_of_dates]
    return tuple([d.strftime(from_format) for d in min_max(datetimes)])


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







