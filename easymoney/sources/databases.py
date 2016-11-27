#!/usr/bin/env python3

"""

    Tools for Locating Required Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import pandas as pd
from collections import defaultdict
from easymoney.support_tools import cln

def currency_mapping_to_dict():
    """

    :return:
    """
    # Read in the data
    currency_mappings = pd.read_csv("easymoney/sources/data/CurrencyRelationshipsDB.csv",
                                    usecols=['Alpha3', 'CurrencyCode'])

    # Initialize a default dict
    alpha3_currency = defaultdict(list)

    # Loop though to generate a
    for all_alpha3, currency in zip(*[currency_mappings[c] for c in ['Alpha3', 'CurrencyCode']]):
        if not any(pd.isnull(i) for i in [all_alpha3, currency]):
            for alpha3 in cln(all_alpha3).split(", "):
                if currency.upper() not in alpha3_currency[alpha3.upper()]:
                    alpha3_currency[alpha3.upper()].append(currency.upper())

    return alpha3_currency
