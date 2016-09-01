#!/usr/bin/env python3

'''

Money Conversions (offline)
~~~~~~~~~~~~~~~~~~~~~~~~~~~


'''

# Modules #
import os
import six
import pickle
import datetime
import warnings
import datetime
import numpy as np
import pandas as pd
import pkg_resources

from collections import defaultdict

from easymoney.support_money import alpha2_to_alpha2_unpack
from easymoney.support_money import date_bounds_floor
from easymoney.support_money import datetime_to_str
from easymoney.support_money import floater
from easymoney.support_money import key_value_flip
from easymoney.support_money import min_max
from easymoney.support_money import money_printer
from easymoney.support_money import pandas_print_full
from easymoney.support_money import remove_from_dict
from easymoney.support_money import strlist_to_list
from easymoney.support_money import str_to_datetime
from easymoney.support_money import twoD_nested_dict

from easymoney.ecb_interface import _ecb_exchange_data
from easymoney.ecb_interface import ecb_currency_to_alpha2_dict
from easymoney.world_bank_interface import world_bank_pull_wrapper


from easymoney.support_money import DATA_PATH



# Get CPI Data
# cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")
cpi_df = pd.read_csv("data_sources/temp/CPISAVE.csv")

# Create CPI dict
cpi_dict = twoD_nested_dict(cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

# Get Exchange rate Data
# ex_dict, currency_codes = _ecb_exchange_data('dict')

with open(r"data_sources/temp/ex_dict.pickle", "rb") as input_file:
    ex_dict = pickle.load(input_file)
ex_dict_keys_series = pd.Series(sorted(list(ex_dict.keys())))

currency_codes = list(ex_dict['2012-04-24'].keys())

# Import EU join Data
eu_join = pd.read_csv("easymoney/data/JoinEuro.csv")
eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))

alpha2_alpha3_df = pd.read_csv("easymoney/data/CountryAlpha2_and_3.csv")

# Create Alpha3 --> Alpha2 Dict
alpha3_to_alpha2 = remove_from_dict(dict(zip(alpha2_alpha3_df.Alpha3, alpha2_alpha3_df.Alpha2)))

# Create Alpha2 --> Alpha3 Dict
alpha2_to_alpha3 = dict([(v, k) for k, v in alpha3_to_alpha2.items()])

# Create Currency --> Alpha2 Dict
currency_to_alpha2 = remove_from_dict(dict(zip(cpi_df.currency_code, cpi_df.alpha2)), to_remove = [np.NaN, "EUR"])

# Create Alpha2 --> Currency
alpha2_to_currency = dict([(v, k) for k, v in currency_to_alpha2.items()])

# Create Region Name --> Alpha2 Dict
region_to_alpha2 = remove_from_dict(dict(zip(cpi_df.region, cpi_df.alpha2)))

# Create Alpha2 --> Region Name Dict
alpha2_to_region = dict([(v, k) for k, v in region_to_alpha2.items()])

round_to = 2


def _closest_date(list_of_dates, date, problem_domain=''):
    """

    *Private Method*
    Determines the closest date for which data is avaliable.

    :param list_of_dates: a list of datetimes
    :type list_of_dates: list
    :param date: a date
    :type date: datetime
    :param problem_domain: domain of the problem _closet_date() is tryping to solve. Information for error message.
    :type problem_domain: str
    :return: the closet date, as ranked by the standard python sorting algo. (sorted() method).
    :rtype: list
    """
    # Block fallback behaviour if it's not permitted
    if not fallback:
        raise AttributeError("EasyMoney could not obtain '%s' information for %s" % (problem_domain, date))

    # Ensure dates are of type datetime
    if False in [isinstance(i, datetime.datetime) for i in list_of_dates]:
        raise ValueError("Dates must be of type: datetime.datetime")

    # Return best match
    return sorted(list_of_dates, key=lambda date_in_list: abs(date - date_in_list))[0]


def _region_type(region):
    """

    *Private Method*
    Standardize Currency Code, Alpha3 and Natural Name (e.g., 'Canada') to Alpha2.

    :param region: a region (Alpha2, Alpha3, Natural Name or currency code).
    :type region: str
    :return: ISO Alpha2 code
    :rtype: str
    """
    if region in ecb_currency_to_alpha2_dict.keys():
        return ecb_currency_to_alpha2_dict[region], "currency"
    elif region in alpha3_to_alpha2.values():
        return region, "alpha2"
    elif region in alpha3_to_alpha2.keys():
        return alpha3_to_alpha2[region], "alpha3"
    elif region in currency_to_alpha2.keys():
        return currency_to_alpha2[region], "currency"
    elif region.lower().title() in region_to_alpha2.keys():
        return region_to_alpha2[region.lower().title()], "natural"
    else:
        raise ValueError("Region Error. '%s' is not recognized by EasyMoney. See options()." % (region))


def _iso_mapping(region, map_to='alpha2'):
    """

    *Private Method*
    Map a region to ISO Alpha2 and Alpha3, as well as Currency Code and Natural Name.

    :param region: a region in the format of a currency code, natural name or ISO Alpha2/3
    :type region: str
    :param map_to: 'alpha2', 'alpha3', 'currency' or 'natural'.
    :type map_to: str
    :return: the desired mapping from region to ISO Alpha2
    :rtype: str
    """
    # Define legal map_to options
    map_to_options = ['alpha2', 'alpha3', 'currency', 'natural']

    if map_to not in map_to_options:
        map_to_options = ["'" + m + "'" for m in map_to_options]
        raise ValueError(
            "map_to must be one of: %s" % (", ".join(map_to_options[:-1]) + " or " + map_to_options[-1] + "."))

    # Block EUR and Europe handling by the below _iso_mapping() code
    if region.upper() == 'EUR' or region.lower().title() == 'Europe':
        if map_to in map_to_options[:-1]:
            return 'EUR'
        else:
            return 'Europe'
    else:
        alpha2_mapping, raw_region_type = _region_type(region)

    # Return iso code (alpha2 or 3), currency code or natural name
    if map_to == 'alpha2':
        return alpha2_mapping
    elif map_to == 'alpha3':
        return alpha2_to_alpha3[alpha2_mapping]
    elif map_to == 'currency':
        return "EUR" if alpha2_mapping in eu_join_dict.keys() else alpha2_to_currency[alpha2_mapping]
    elif map_to == 'natural':
        return alpha2_to_region[alpha2_mapping]
    else:
        raise ValueError('Invalid map_to request.')


def _try_to_get_CPI(region, year):
    """

    *Private Method*
    Function to look up CPI information in the cached database information.

    :param region:
    :param year:
    :return:
    """
    # Initalize
    cpi = None
    inflation_error_message = "EasyMoney could not obtain inflation (CPI) information for '%s' in '%s'" % (
    str(region), str(year))

    # convert region to alpha2
    cpi_region = _iso_mapping(region, map_to='alpha2')

    # Get most recent CPI year avaliable
    if cpi_region not in cpi_dict.keys():
        raise LookupError("Could not find inflation information for '%s'." % (str(region)))

    max_cpi_year = str(int(max([float(i) for i in cpi_dict[cpi_region].keys()])))

    if float(year) > float(max_cpi_year):
        if fallback:
            try:
                cpi = floater(cpi_dict[cpi_region][str(int(float(max_cpi_year)))])  # add Error handling?
                warnings.warn("Could not obtain required inflation (CPI) information for '%s' in %s."
                              " Using %s instead." % \
                              (_iso_mapping(region, map_to='natural'), str(int(float(year))), max_cpi_year))
            except:
                raise LookupError(inflation_error_message)
        else:
            raise AttributeError(inflation_error_message)
    else:
        try:
            cpi = floater(cpi_dict[cpi_region][str(int(float(year)))])  # Add linear interpolation
        except:
            raise LookupError(inflation_error_message)

    return cpi


def inflation_rate(region, year_a, year_b=None, return_raw_cpi_dict=False):
    """

    Calculator to compute the inflation rate from Consumer Price Index (CPI) information.


    :param region: a region (currency codes may work, provided they are not common curriencies, e.g., Euro).
    :type region: str
    :param year_a: start year
    :type year_a: int
    :param year_b: end year. Defaults to None -- can only be left to this default if return_raw_cpi_dict is True.
    :type year_b: int
    :param return_raw_cpi_dict:
    :type return_raw_cpi_dict: bool
    :return: the rate of inflation between year_a and year_h. Defaults to False.
    :rtype: float
    """
    # Get the CPI for year_b and year_a
    c1 = _try_to_get_CPI(region, year_b) if year_b != None else None
    c2 = _try_to_get_CPI(region, year_a)

    # Dict
    if return_raw_cpi_dict:
        if year_b != None:
            return dict(zip([str(year_b), str(year_a)], [c1, c2]))
        elif year_b == None:
            return dict(zip([str(year_a), [c2]]))
    elif return_raw_cpi_dict != False and year_b == None:
        raise ValueError("year_b cannot be left to its default (None) when return_raw_cpi_dict is False.")

    # Inflation Rate Calculation
    if (any([np.isnan(c1), np.isnan(c2)])) or (c2 == 0.0):
        return np.NaN

    return ((c1 - c2) / c2) * 100


def inflation_calculator(amount, region, year_a, year_b):
    """

    Adjusts a given amount of money for inflation.

    :param amount: a montary amount, e.g., 5
    :type amount: float or int
    :param region: a geographical region, e.g., US
    :type region: str
    :param year_a: start year
    :param year_a: int
    :param year_b: end year
    :param year_b: int
    :return: amount * inflation rate.
    :rtype: float
    """
    # Input checking
    if floater(year_a) == floater(year_b):
        return amount
    if floater(year_a) > floater(year_b):
        raise ValueError("year_a cannot be greater than year_b")

    # Get the CPI information
    inflation_dict = inflation_rate(_iso_mapping(region, map_to='alpha2')
                                         , int(float(year_a))
                                         , int(float(year_b))
                                         , return_raw_cpi_dict=True)

    # Check all the values are floats
    if not all([floater(x, just_check=True) for x in inflation_dict.values()]):
        warnings.warn("Problem obtaining required inflation information.")
        return np.NaN

    # Block division by zero
    if any(x == 0.0 for x in inflation_dict.values()):
        warnings.warn("Problem obtaining required inflation information.")
        return np.NaN

    # Scale w.r.t. inflation.
    try:
        adjusted_amount = inflation_dict[str(int(float(year_b)))] / float(
            inflation_dict[str(int(float(year_a)))]) * amount
    except KeyError as e:
        raise KeyError("Could not obtain inflation information for %s in %s." % \
                       (_iso_mapping(region, map_to='natural'), e))

    # Round and Return
    return round(adjusted_amount, round_to)


def _eur_to_lcu(currency, date='most_recent'):
    """

    *Private Method*
    Convert from Euros to a local currency unit, e.g., CAD.

    :param currency: a currency code or region
    :param date: MUST be of the form: YYYY-MM-DD; defaults to 'most recent'.
    :return: exchange_rate w.r.t. the EURO (as a base currency).
    """
    # Convert currency arg. to a currency code.
    currency_to_convert = _iso_mapping(currency, 'currency')

    # Block self-conversion
    if currency_to_convert == "EUR":
        return 1.0

    # Initialize
    date_key = None

    # Get the current date
    if date == 'most_recent':
        try:
            date_key = str(max([d.date() for d in pd.to_datetime(list(ex_dict.keys()))]))
        except:
            raise ValueError("Could not obtain most recent exchange information from the European Central Bank.")
    else:
        if date in ex_dict.keys():
            date_key = date
        elif date not in ex_dict.keys():
            date_key = _closest_date([datetime.datetime.strptime(d, "%Y-%m-%d") for d in ex_dict.keys()]
                                          , datetime.datetime.strptime(date, "%Y-%m-%d"), problem_domain='currency')
            warnings.warn("Currency information could not be obtained for '%s', %s was used instead" % (date, date_key))

    return ex_dict[date_key][currency_to_convert.upper()]


def currency_converter(amount, from_currency, to_currency, date='most_recent', pretty_print=False):
    """

    Function to convert an amount of money from one currency to another.

    :param amount: an amount of money to be converted
    :type amount: float or int
    :param from_currency: the currency of the amount
    :type from_currency: str
    :param to_currency: the currency the amount is to be converted into
    :type to_currency: str
    :param date: Defaults to 'most_recent' (which will use to most recent data avaliable).
    :type date: str
    :param pretty_print: if True, prints the table otherwise returns the table as a pandas DataFrame.
    :type pretty_print: bool
    :return: converted currency
    :rtype: float
    """
    # Initialize variables
    conversion_to_invert = None
    converted_amount = None

    # Check amount is float
    if not isinstance(amount, (float, int)):
        raise ValueError("Amount must be numeric (intiger or float).")

    # Correct from_currency
    from_currency_fn = _iso_mapping(from_currency, map_to="currency")

    # Check for from_currency == to_currency
    if _iso_mapping(from_currency_fn) == _iso_mapping(to_currency):
        return round(amount, round_to) if not pretty_print else print(money_printer(amount, round_to),
                                                                           to_currency)

    # To some currency from EURO
    if from_currency_fn == "EUR":
        converted_amount = _eur_to_lcu(to_currency, date) * float(amount)

    # From some currency to EURO
    elif _eur_to_lcu(to_currency) == "EUR":
        conversion_to_invert = _eur_to_lcu(from_currency, date)

        if conversion_to_invert == 0.0:
            raise AttributeError("Cannot converted to '%s'." % (to_currency))
        converted_amount = conversion_to_invert ** -1 * float(amount)

    # from_currency --> EURO --> to_currency
    else:
        conversion_to_invert = _eur_to_lcu(from_currency_fn, date)
        if conversion_to_invert == 0.0:
            raise AttributeError("Cannot converted from '%s'." % (from_currency))

        converted_amount = conversion_to_invert ** -1 * _eur_to_lcu(to_currency, date) * float(amount)

    # Round
    rounded_amount = round(converted_amount, round_to)

    # Return results (or pretty print)
    if not pretty_print:
        return rounded_amount
    else:
        print(money_printer(rounded_amount, round_to), _iso_mapping(to_currency, "currency"))


def normalize(amount, currency, from_year, to_year="most_recent", base_currency="EUR", pretty_print=False):
    """

    Convert a Nominal Amount to a Real Amount in the same, or another, currency.

    :param amount: a numeric amount of money
    :type amount: float or int
    :param currency: a region or currency. Legal: Region Name, ISO Alpha2, Alpha3 or Currency Code (see options()).
    :type currency: str
    :param from_year: a year. For legal values see options().
    :type from_year: int
    :param to_year: a year. For legal values see options().
    :type to_year: int
    :param base_currency:  a region or currency. Legal: Region Name, ISO Alpha2, Alpha3 or Currency Code (see options()).
    :type base_currency: str
    :param pretty_print: Pretty Print the result if True; return amount if False. Defaults to False.
    :type pretty_print: bool
    :return: adjusted_amount
    :type: float
    """
    # Standardize currency input
    from_currency = _iso_mapping(currency, map_to="currency")

    if from_currency not in currency_to_alpha2.keys():
        raise ValueError(
            "'%s' cannot be mapped to a specific region, and thus inflation cannot be determined." % (currency))

    # Ensure base_currrency is a valid currency code
    to_currency = _iso_mapping(base_currency, map_to='currency')

    # Determine Alpha2 country code
    from_region = _iso_mapping(currency, map_to='alpha2')

    # Determine to CPI Data
    most_recent_cpi_record = cpi_df[(cpi_df.alpha2 == currency_to_alpha2[from_currency]) & \
                                         (~pd.isnull(cpi_df.cpi))].year.max()

    if to_year != "most_recent" and float(to_year) < float(most_recent_cpi_record):
        if floater(to_year):
            inflation_year_b = to_year
        else:
            raise ValueError("to_year invalid; '%s' is not numeric (intiger or float).")
    else:
        inflation_year_b = most_recent_cpi_record
        if float(inflation_year_b) <= (datetime.datetime.now().year - 2):
            warnings.warn("Inflation information not avaliable for '%s', using %s." % (to_year, inflation_year_b))

    # Adjust input for inflation
    currency_adj_inflation = inflation_calculator(amount, from_region, from_year, inflation_year_b)

    # Convert into the base currency
    adjusted_amount = currency_converter(currency_adj_inflation, from_currency, to_currency)

    return adjusted_amount if not pretty_print else print(money_printer(adjusted_amount, round_to), to_currency)


def _date_options(nested_date_dict, keys_as_dates=False, date_format="%Y-%m-%d"):
    """

    *Private Method*
    Function that figures out how to return dates for which data is avaliable.

    Expected structures:
        1. keys_as_dates = True:  {DATE: {KEY: VALUE}, DATE: {KEY: VALUE}...}; DATE = YYYY-MM-DD
        2. keys_as_dates = False: {KEY: {DATE: VALUE}, KEY: {DATE: VALUE}...}; DATE = YYYY

    :param nested_date_dict: nested dictionary
    :type nested_date_dict: dict
    :param keys_as_dates: whether or not the date information exists as the key or the key of the nested dict.
    :type keys_as_dates: bool
    :param date_format: a date format. Defaults to "%Y-%m-%d".
    :type date_format: str
    :return: a date options dict
    :rtype: dict
    """
    # Initalize
    date_values = None
    date_ranges_dict = dict()
    key_corrected_dict = dict()
    key_key_dict = None
    zipped_key_key = None
    flattened_key_key = None

    # Input Check
    if not isinstance(keys_as_dates, bool):
        raise ValueError('keys_as_dates must be a boolean.')

    # i.e., ex_dict
    if keys_as_dates:

        # Replace the string keys with datetimes; populate with nested keys provided they have float values
        # (i.e., data exists for that date).
        key_key_dict = {str_to_datetime([k], date_format)[0]: [k2 for k2, v2 in v.items() if floater(v2, True)] \
                        for k, v in nested_date_dict.items()}

        # Collapse to 2D list of lists by key
        zipped_key_key = [[[v_i, k] for v_i in v] for k, v in key_key_dict.items()]

        # Flatten the list for processing
        flattened_key_key = [i for s in zipped_key_key for i in s]

        # Create a new default dict
        date_ranges_dict = defaultdict(list)

        # Populate with dates; {Country : [Datetimes]}.
        for k, v in flattened_key_key:
            date_ranges_dict[k].append(v)

        # Convert Keys to Alpha2 and return
        return dict((_iso_mapping(k), v) for k, v in date_ranges_dict.items())

    # i.e., cpi_dict
    elif not keys_as_dates:
        date_ranges_dict = dict.fromkeys(nested_date_dict.keys())  # should be using _iso_mapping() here.
        # Get the date range for each key in the nested dict
        for k in date_ranges_dict:
            date_values = sorted(str_to_datetime(nested_date_dict[k].keys(), date_format=date_format))
            date_ranges_dict[k] = date_values
        return date_ranges_dict


def _currency_options(self):
    """

    *Private Method*
    Function to construct a dataframe of currencies for which EasyMoney has data on.

    :return: DataFrame with all the currencies for which EasyMoney has data.
    :rtype: Pandas DataFrame
    """
    # Make a currency code of possible currency codes
    currency_ops = pd.DataFrame(currency_codes, columns=["Currency"])

    # Make the Alpha2 Column
    currency_ops['Alpha2'] = currency_ops["Currency"].replace(
        {**currency_to_alpha2, **ecb_currency_to_alpha2_dict})

    # Make the Alpha3 and Region Columns
    currency_ops['Alpha3'] = currency_ops["Alpha2"].replace(alpha2_to_alpha3)
    currency_ops['Region'] = currency_ops["Alpha2"].replace(alpha2_to_region)

    # Reorder columns
    currency_ops = currency_ops[['Region', 'Currency', 'Alpha2', 'Alpha3']]

    # Add date information
    dates_dict = _date_options(nested_date_dict=ex_dict, keys_as_dates=True)

    ex_dict_dates = dict((k, str(datetime_to_str(min_max(v)))) for k, v in dates_dict.items())

    # Create Date Range Column
    currency_ops['Range'] = alpha2_to_alpha2_unpack(currency_ops['Alpha2'].astype(str), ex_dict_dates)
    all_date_ranges = np.array(currency_ops['Range'].tolist())

    # Create Row for Europe -- min and max are the min and max of all other conversion data,
    # because EUR is the base currency being used.
    eur_row = pd.DataFrame({'Region': 'Europe', 'Currency': 'EUR', 'Alpha2': np.nan, 'Alpha3': np.nan,
                            'Range': [[min(all_date_ranges[:, 0]), max(all_date_ranges[:, 1])]]},
                           index=[0], columns=currency_ops.columns.tolist())

    # Append the Europe Row
    currency_ops = currency_ops.append(eur_row, ignore_index=True)

    # Sort by Region
    currency_ops.sort_values(['Region'], ascending=[1], inplace=True)

    # Correct Index
    currency_ops.index = range(currency_ops.shape[0])

    return currency_ops


def _inflation_options(self):
    """

    *Private Method*
    Determines the inflation (CPI) information cached.

    :return: a dataframe with all CPI information EasyMoney has, as well as date ranges the date exists for.
    :rtype: Pandas DataFrame
    """
    cpi_ops = cpi_df[['region', 'currency_code', 'alpha2', 'alpha3']].drop_duplicates()
    cpi_ops.columns = ['Region', 'Currency', 'Alpha2', 'Alpha3']
    cpi_ops.index = range(cpi_ops.shape[0])

    dates_dict = _date_options(nested_date_dict=cpi_dict, keys_as_dates=False, date_format='%Y')

    cpi_dict_years = dict((k, str(min_max([i.year for i in v]))) for k, v in dates_dict.items())

    # Hacking the living daylights out of the pandas API
    cpi_ops['Range'] = alpha2_to_alpha2_unpack(cpi_ops['Alpha2'], cpi_dict_years)

    # Sort by Region and Return
    cpi_ops.sort_values(['Region'], ascending=[1], inplace=True)

    # Correct Index
    cpi_ops.index = range(cpi_ops.shape[0])

    return cpi_ops


def _currency_inflation_options(currency_ops_df, cpi_ops_df):
    """

    *Private Method*
    Exchange Rate and Inflation information merged together.

    :param currency_ops_df:
    :param cpi_ops_df:
    :return: a DataFrame with both Currency and Inflation information
    :rtype: Pandas DataFrame
    """
    # Use the cpi_ops_df as a base
    data_frame = cpi_ops_df

    # Make a dict of currency ranges from the currency_ops_df
    currency_range = remove_from_dict(dict(zip(currency_ops_df['Alpha2'], [str(i) for i in currency_ops_df['Range']])))

    # Create a pandas series that maps values in currency_range to the cpi Alpha2 col.
    currency_cpi_mapping = alpha2_to_alpha2_unpack(data_frame['Alpha2'], currency_range)

    data_frame.rename(columns={'Range': 'InflationRange'}, inplace=True)

    # Replace with NaNs those that could not be mapped
    data_frame['CurrencyRange'] = currency_cpi_mapping.map(lambda x: x if "," in str(x) and len(x[0]) != 2 else np.NaN)

    # Determine the Overlap in dates between CPI and Exchange
    data_frame['Overlap'] = data_frame.apply(
        lambda row: date_bounds_floor([row['InflationRange'], row['CurrencyRange']]), axis=1)

    # Sort by mapping
    data_frame['TempSort'] = data_frame.CurrencyRange.map(lambda x: 'A' if str(x) != 'nan' else 'B')

    # Apply sorting
    data_frame.sort_values(['TempSort', 'Region'], ascending=[1, 1], inplace=True)

    # Drop the Sorting Column
    data_frame.drop('TempSort', axis=1, inplace=True)

    # Refresh the index
    data_frame.index = range(data_frame.shape[0])

    return data_frame


def _list_option(info):
    """

    *Private Method*
    Generates a list of 'exchange' (Currency Codes) and 'inflation' (CPI) references EasyMoney Understands.

    :param info: 'exchange' for exchange rate; 'inflation' for inflation information; 'all' for both.
    :type info: str
    :return: a list of 'exchange' (currency codes) or 'inflation' (regions) EasyMoney recognizes.
    :rtype: list
    """
    if info == 'exchange':
        return sorted(currency_codes + ['EUR'])
    elif info == 'inflation':
        return sorted([i for i in cpi_df.alpha2.unique().tolist() if isinstance(i, str)])
    elif info == 'all':
        raise ValueError("Error in info: 'all' is only valid for when rformat is set to 'table'.")


def _table_option(info):
    """

    *Private Method*
    Wrapper for _currency_options()

    :param info: 'exchange' for exchange rate; 'inflation' for inflation information; 'all' for both.
    :type info: str
    :return: DataFrame with the requested information
    :rtype: Pandas DataFrame
    """
    if info == 'exchange':
        info_table = _currency_options()
    elif info == 'inflation':
        info_table = _inflation_options()
    elif info == 'all':
        info_table = _currency_inflation_options(_currency_options(), _inflation_options())

    # Add date when Countries Changed curriency (only to Euro for now).
    # Note: Sadly, Pandas Series of dtype 'int' cannot contain NaNs. Using a object dtype instead.
    info_table['CurrencyTransition'] = info_table['Alpha2'].replace(eu_join_dict).map(
        lambda x: int(x) if floater(x, True) and str(x) != 'nan' else '')

    return info_table


def options(info, rformat='table', pretty_table=True, pretty_print=True, overlap_only=False):
    """

    This function allows an easy inferface to explore all of the terminology EasyMoney understands
    as well the dates for which data is available.

    :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table')
    :type info: str
    :param rformat: 'table' for a table or 'list' for just the currecy codes, alone
    :type rformat: str
    :param pretty_table: prettifies the options table
    :type pretty_table: bool
    :param overlap_only: when info is set to 'all', only keep those rows for which exchange rate and inflation data
                         overlap
    :type overlap_only: bool
    :param pretty_print: if True, prints the table otherwise returns the table as a pandas DataFrame.
    :type pretty_print: bool
    :return: DataFrame of Currency Information EasyMoney Understands
    :rtype: Pandas DataFrame
    """
    # This is a jumbo function.
    # However, I've decided not to factor it any further (see all the 'option' functions above) because,
    # despite it's size, it now it represent is a single (long) thought.

    # Initalize
    list_to_return = None
    info_table = None
    date_columns_in_table = None

    # Create a lambda to convert the InflationRange lists to lists of ints (from lists of strings).
    year_to_int = lambda x: np.NaN if 'nan' in str(x) else [[floater(i, False, True) for i in x]][0]

    # Create a lambda to convert the CurrencyRange and Overlap columns to datetime
    full_date_to_datetime = lambda x: np.NaN if str(x) == 'nan' else str_to_datetime(x)

    # Check value suppled to rformat
    if rformat not in ['list', 'table']:
        raise ValueError("'%s' is an invalid setting for rformat.\nPlease use 'table' for a table (pandas dataframe)"
                         " or 'exchange' for the currency codes as a list.")

    # Check overlap_only has not been set to True inappropriately.
    if (overlap_only and info != 'all') or (overlap_only and rformat == 'list'):
        raise ValueError("overlap_only is only of utility when info = 'all' and rformat = 'table'.")

    # Generate a (sorted) list
    if rformat == 'list':
        list_to_return = _list_option(info)
        return list_to_return if not pretty_print else print(list_to_return)

    # Generate a table
    elif rformat == 'table':
        info_table = _table_option(info)
        # Limit to overlap, if requested
        if overlap_only == True:
            info_table.dropna(subset=['Overlap'], how='all', inplace=True)

        # Print the full table or return
        if pretty_print:
            # Replace number indexes with empty strings.
            if pretty_table:
                info_table.index = ['' for i in range(info_table.shape[0])]

            # Pretty print the table
            pandas_print_full(info_table)

        elif not pretty_print:
            # InflationRange --> list of ints
            if 'InflationRange' in info_table.columns:
                info_table['InflationRange'] = info_table['InflationRange'].map(year_to_int)

            # Replace the '' in the CurrencyTransition column with NaNs
            info_table['CurrencyTransition'] = \
                info_table['CurrencyTransition'].map(lambda x: np.NaN if str(x).strip() == '' else [x])

            # CurrencyRange and Overlap columns --> list of datetimes
            date_columns_in_table = [i for i in info_table.columns if i in ['CurrencyRange', 'Overlap']]
            if len(date_columns_in_table) > 0:
                for col in date_columns_in_table:
                    info_table[col] = info_table[col].map(full_date_to_datetime)

            return info_table







































