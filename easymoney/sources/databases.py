#!/usr/bin/env python3

"""

    Tools for Locating Required Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import pandas as pd
from collections import defaultdict
from easymoney.support_tools import cln
from easymoney.easy_pandas import twoD_nested_dict
from easymoney.sources.world_bank_interface import world_bank_pull_wrapper

def currency_mapping_to_dict(data_path=''):
    """

    :return:
    """
    # Read in the data
    currency_mappings = pd.read_csv(data_path + "easymoney/sources/data/CurrencyRelationshipsDB.csv",
                                    usecols=['Alpha2', 'CurrencyCode'])

    # Initialize a default dict
    alpha2_currency = defaultdict(list)

    # Loop though to generate a
    for all_alpha2, currency in zip(*[currency_mappings[c] for c in ['Alpha2', 'CurrencyCode']]):
        if not any(pd.isnull(i) for i in [all_alpha2, currency]):
            for alpha2 in cln(all_alpha2).split(", "):
                if currency.upper() not in alpha2_currency[alpha2.upper()]:
                    alpha2_currency[alpha2.upper()].append(currency.upper())

    return alpha2_currency













