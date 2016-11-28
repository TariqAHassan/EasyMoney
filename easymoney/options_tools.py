#!/usr/bin/env python3

"""

    Tools for EasyPeasy's options() Method
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from easymoney.easy_pandas import items_null
from easymoney.support_tools import min_max_dates

def multi_currency_dates(list_of_currencies, _exchange_dates, get_range=False):
    """

    :param list_of_currencies:
    :param _exchange_dates: method
    :param get_range:
    :return:
    """
    currency_dates = list(filter(None, map(_exchange_dates, list_of_currencies)))

    # Return if all sublists are null
    if not len(currency_dates):
        return None

    if get_range:
        currency_dates = [list(min_max_dates(l)) for l in currency_dates]

    return currency_dates[0] if len(currency_dates) == 1 else currency_dates


def options_ranking(inflation, exchange):
    """

    :param inflation:
    :param exchange:
    :return:
    """
    if not items_null(inflation) and not items_null(exchange):
        return 3
    elif not items_null(exchange):
        return 2
    elif not items_null(inflation):
        return 1
    else:
        return 0
















