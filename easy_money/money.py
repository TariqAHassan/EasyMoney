#!/usr/bin/env python3

'''

Money Conversions
~~~~~~~~~~~~~~~~~

Python 3.5

'''

# Modules #
import wbdata
import datetime
import warnings
import datetime
import numpy as np
import pandas as pd

from easy_money.support_money import twoD_nested_dict, floater
from easy_money.world_bank_interface import WorldBankParse

def world_bank_pull_wrapper(value_true_name, indicator):
    """

    :param value_true_name:
    :param indicator:
    :return:
    """
    data_frame = WorldBankParse(value_true_name, indicator).world_bank_pull()
    data_frame = data_frame[data_frame[value_true_name].astype(str) != 'None']
    data_frame.index = range(data_frame.shape[0])

    return data_frame

# class Currency(object):
"""

Tools to adjusting for inflation, converting to USD and normalizing (converting to USD and adjusting for inflation)
This will take a moment to initialize.


Functionality:
    1) Get Inflation Rate
    2) Convert Currency
    3) Exchange rate

To do:
    2) Impliment option for linear interpolation of missing values...but with restrictions.
    3) Fix ZW for world bank data (no longer a problem?)

"""


# Get CPI Data
cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")
# Create CPI dict
cpi_dict = twoD_nested_dict(cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

# Get Exchange rate Data
ex_dict = _ecb_exchange_data('dict')

# Import EU join Data
eu_join = pd.read_csv("easy_money/easy_data/JoinEuro.csv")
eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))

# Create Alpha3 --> Alpha2 Dict
alpha3_to_alpha2 = dict(zip(cpi_dict.alpha3, cpi_dict.alpha2))

# Create Currency --> Alpha2 Dict
currency_to_alpha2 = dict(zip(cpi_dict.currency_code, cpi_dict.alpha2))

# Create Region Name --> Alpha2 Dict
region_to_alpha2 = dict(zip(cpi_dict.region, cpi_dict.alpha2))


def _linear_interpolate():
    pass


def _try_to_get_CPI(region, year):
    """

    :param region:
    :param year:
    :return:
    """
    try:
        cpi = floater(cpi_dict[region][str(year)])
    except:
        raise ValueError("Could not obtain required inflation (CPI) information for '%s' in %s." % (region, year_b))

    return cpi

def inflation_rate(region, year_a, year_b, return_raw_cpi_dict = False):
    """

    :param region:
    :param year_a:
    :param year_b:
    :param return_dict:
    :return:
    """

    # Get the CPI for year_b and year_a
    c1 = _try_to_get_CPI(region, year_b)
    c2 = _try_to_get_CPI(region, year_a)

    if return_raw_cpi_dict:
        return dict(zip([str(year_b), str(year_a)], [c1, c2]))
    if any([np.isnan(c1), np.isnan(c2)]):
        return np.NaN
    if c2 == 0.0:
        return np.NaN

    return ((c1 - c2) / c2) * 100

def inflation_calculator(amount, region, year_a, year_b):
    """

    :param amount: a montary amount, e.g., 5
    :param region: a geographical region, e.g., US
    :param year_a: start year
    :param year_b: end year
    :return:
    """

    # Get the CPI information
    inflation_dict = inflation_rate(region, year_a, year_b, return_raw_cpi_dict = True)

    # Check all the values are floats
    if not all([floater(x, just_check = True) for x in inflation_dict.values()]):
        return np.NaN

    # Block division by zero
    if any(x == 0.0 for x in inflation_dict.values()):
        warnings.warn("Problem obtaining required inflation information.")
        return np.NaN

    # Scale w.r.t. inflation.
    adjusted_amount = inflation_dict[str(year_b)]/float(inflation_dict[str(year_a)]) * amount

    # Round and Return
    return round(adjusted_amount, 2)

def _eur_to_lcu(currency = 'USD', date = 'most_recent'):
    """

    :param currency:
    :param date: must be of the form: YYYY-MM-DD
    :return: exchange_rate w.r.t. the EURO (as a base currency).
    """

    if not floater(amount, just_check = True):
        raise ValueError("Amount not an intiger or floating point number.")

    # Handle things other than currency codes being passed #

    # Initialize
    date_key = None

    # Get the current date
    if date == 'most_recent':
        try:
            date_key = str(max([d.date() for d in pd.to_datetime(list(ex_dict.keys()))]))
        except:
            raise ValueError("Could not obtain most recent exchange information from the European Central Bank.")
    else:
        date_key = date

    return ex_dict[date_key][currency.upper()] * float(1)

def currency_converter(amount, from_currency, to_currency, date = 'most_recent', round_to = 2, pretty_print = False):
    """

    :param amount:
    :param from_currency:
    :param to_currency:
    :param date:
    :return:
    """

    # Add Input checking! #

    # Initialize variables
    conversion_to_invert = None
    converted_amount = None

    # To some currency from EUR
    if from_currency == "EUR":
        converted_amount = _eur_to_lcu(to_currency, date) * float(amount)

    # From some currency to EUR
    elif to_currency == "EUR":
        conversion_to_invert = _eur_to_lcu(from_currency, date)

        if conversion_to_invert == 0.0:
            raise AttributeError("Cannot converted to '%s'." % (to_currency))
        converted_amount = conversion_to_invert**-1 * float(amount)

    # from_currency --> EURO --> to_currency
    else:
        conversion_to_invert = _eur_to_lcu(from_currency, date)
        if conversion_to_invert == 0.0:
            raise AttributeError("Cannot converted from '%s'." % (from_currency))

        converted_amount = conversion_to_invert**-1 * _eur_to_lcu(to_currency, date) * float(amount)

    if pretty_print == False:
        return round(converted_amount, round_to)
    elif pretty_print == True:
        print(round(converted_amount, round_to), to_currency)



currency_converter(100, from_currency = 'EUR', to_currency = 'CAD', pretty_print = True)

















def normalize(base_currency = "EUR"):
    pass
    # Convert to base currency and account for inflation.












































































































