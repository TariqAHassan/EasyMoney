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
import numpy as np
import pandas as pd

from easy_money.support_money import twoD_nested_dict
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
    1) Figure out a solution to handle 2016/Current year currency.
    2) Impliment option for linear interpolation of missing values...but with restrictions.
    3) Fix ZW

"""


# Get CPI Data
cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")
# Create CPI dict
cpi_dict = twoD_nested_dict(cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

# Get Exchange rate Data
ex_df = world_bank_pull_wrapper(value_true_name = "exchange_rate", indicator = "PA.NUS.FCRF")
# Create Exchange Rate dict
ex_dict = twoD_nested_dict(ex_df, 'alpha2', 'year', 'exchange_rate', to_float = ['exchange_rate'], to_int = ['year'])

# Import EU join Data
eu_join = pd.read_csv("easy_money/easy_data/JoinEuro.csv")
eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))


# Create Alpha3 --> Alpha2 Dict
alpha3_to_alpha2 = dict(zip(ex_df.alpha3, ex_df.alpha2))

# Create Currency --> Alpha2 Dict
currency_to_alpha2 = dict(zip(ex_df.currency_code, ex_df.alpha2))

# Create Region Name --> Alpha2 Dict
region_to_alpha2 = dict(zip(ex_df.region, ex_df.alpha2))


def _linear_interpolate():
    pass





def _floater(input_to_check, just_check=False):
    """

    :param input_to_check:
    :param just_check: return boolean if string can be converted to a float.
    :return:
    """

    try:
        float(input_to_check)
        return float(input_to_check) if not just_check else True
    except:
        return np.NaN if not just_check else False

def inflation_rate(region, year_a, year_b, return_raw_cpi = False):
    """

    :param region:
    :param year_a:
    :param year_b:
    :param return_dict:
    :return:
    """

    c1 = _floater(cpi_dict[region][str(year_b)])
    c2 = _floater(cpi_dict[region][str(year_a)])

    if return_raw_cpi:
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
    inflation_dict = inflation_rate(region, year_a, year_b, return_raw_cpi = True)

    # Check all the values are floats
    if not all([_floater(x, just_check = True) for x in inflation_dict.values()]):
        return np.NaN

    if any(x == 0.0 for x in inflation_dict.values()):
        warnings.warn("Problem obtaining required inflation information.")
        return np.NaN

    # Scale w.r.t. inflation.
    adjusted_amount = inflation_dict[str(year_b)]/float(inflation_dict[str(year_a)]) * amount

    # Round and Return
    return round(adjusted_amount, 2)











































