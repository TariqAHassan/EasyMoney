# coding: utf-8

"""

    Tools for Processing Included Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import pandas as pd
from collections import defaultdict
from easymoney.support_tools import cln


def currency_mapping_to_dict(path_to_data):
    """

    Constructs a mapping between country ISO Alpha 2 codes and currency ISO Alpha 3 codes.

    :param path_to_data: path to the 'CurrencyRelationshipsDB.csv' database.
    :type path_to_data: ``str``
    :return: a dictionary mapping alpha2 codes to currency codes
    :rtype: ``dict``
    """
    # Read in the data
    data_path = (path_to_data if not path_to_data.endswith("/") else path_to_data[:-1])
    currency_mappings = pd.read_csv(data_path + "/CurrencyRelationshipsDB.csv", usecols=['Alpha2', 'CurrencyCode'])

    # Initialize a default dict
    alpha2_currency = defaultdict(list)

    # Loop though to generate a
    for all_alpha2, currency in zip(*[currency_mappings[c] for c in ['Alpha2', 'CurrencyCode']]):
        if not any(pd.isnull(i) for i in [all_alpha2, currency]):
            for alpha2 in cln(all_alpha2).split(", "):
                if currency.upper() not in alpha2_currency[alpha2.upper()]:
                    alpha2_currency[alpha2.upper()].append(currency.upper())

    return alpha2_currency









