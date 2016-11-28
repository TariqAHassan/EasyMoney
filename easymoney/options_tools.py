#!/usr/bin/env python3

"""

    Tools for EasyPeasy's options() Method
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
from easymoney.easy_pandas import items_null

def options_ranking(inflation, exchange):
    """

    Ranks ``options()`` table rows by their completeness.
    Rankings:
        3: inflation and exchange information
        2: exchange information
        1: inflation information
        0: neither inflation or exchange information

    :param inflation:
    :type inflation: ``list``
    :param exchange:
    :type exchange: ``list``
    :return: completeness of row
    :rtype: ``int``
    """
    if not items_null(inflation) and not items_null(exchange):
        return 3
    elif not items_null(exchange):
        return 2
    elif not items_null(inflation):
        return 1
    else:
        return 0
















