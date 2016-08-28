#!/usr/bin/env python3

'''

Money Conversions
~~~~~~~~~~~~~~~~~

Python 3.5

'''

# Modules #
import os
import six
import datetime
import warnings
import datetime
import numpy as np
import pandas as pd
import pkg_resources

from easymoney.support_money import twoD_nested_dict, floater, remove_from_dict, money_printer, key_value_flip, min_max, datetime_to_str, str_to_datetime, strlist_to_list
from easymoney.ecb_interface import _ecb_exchange_data, ecb_currency_to_alpha2_dict
from easymoney.world_bank_interface import world_bank_pull_wrapper


DATA_PATH = pkg_resources.resource_filename('easymoney', 'data')


class Currency(object):
    """

    Tools to adjusting for inflation, converting to USD and normalizing (converting to USD and adjusting for inflation)
    This will take a moment to initialize.

    Functionality:
        1) Get Inflation Rate
        2) Convert Currency
        3) Exchange rate
        4) Normalize a currency with respect to a base currecny, e.g., EUROs.

    """


    def __init__(self, precision = 2, fallback = True):
        """

        :param precision: number of places to round to
        :param fallback: fallback to closest possible date
        """

        # Places of precision
        self.round_to = precision

        # Fall back boolean
        self.fallback = fallback

        # Get CPI Data
        self.cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")

        # Create CPI dict
        self.cpi_dict = twoD_nested_dict(self.cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

        # Get Exchange Rate Data
        self.ex_dict, self.currency_codes = _ecb_exchange_data(return_as = 'dict')
        self.ex_dict_keys_series = pd.Series(sorted(list(self.ex_dict.keys())))

        # Import EU join Data
        eu_join = pd.read_csv(DATA_PATH + "/JoinEuro.csv")
        self.eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))

        alpha2_alpha3_df = pd.read_csv(DATA_PATH + "/CountryAlpha2_and_3.csv")

        # Create Alpha3 --> Alpha2 Dict
        self.alpha3_to_alpha2 = remove_from_dict(dict(zip(alpha2_alpha3_df.Alpha3, alpha2_alpha3_df.Alpha2)))

        # Create Alpha2 --> Alpha3 Dict
        self.alpha2_to_alpha3 = key_value_flip(self.alpha3_to_alpha2)

        # Create Currency --> Alpha2 Dict
        self.currency_to_alpha2 = remove_from_dict(dict(zip(self.cpi_df.currency_code.tolist(), self.cpi_df.alpha2.tolist()))
                                                   , to_remove = [np.NaN, "EUR"])

        # Create Alpha2 --> Currency
        self.alpha2_to_currency = key_value_flip(self.currency_to_alpha2)

        # Create Region Name --> Alpha2 Dict
        self.region_to_alpha2 = remove_from_dict(dict(zip(self.cpi_df.region, self.cpi_df.alpha2)))

        # Create Alpha2 --> Region Name Dict
        self.alpha2_to_region = key_value_flip(self.region_to_alpha2)

    def _closest_date(self, list_of_dates, date, problem_domain = ''):
        """

        :param list_of_dates:
        :param date:
        :return:
        """

        # Block fallback behaviour if it's not permitted
        if not self.fallback:
            raise AttributeError("EasyMoney could not obtain '%s' information for %s" % (problem_domain, date))

        # Ensure dates are of type datetime
        if False in [isinstance(i, datetime.datetime) for i in list_of_dates]:
            raise ValueError("Dates must be of type: datetime.datetime")

        # Return best match
        return sorted(list_of_dates, key = lambda date_in_list: abs(date - date_in_list))[0]

    def _region_type(self, region):
        """

        Standardize Currency, Alpha3 and Natural Name to Alpha2.

        :param region:
        :return:
        """

        if region in ecb_currency_to_alpha2_dict.keys():
            return ecb_currency_to_alpha2_dict[region], "currency"
        elif region in self.alpha3_to_alpha2.values():
            return region, "alpha2"
        elif region in self.alpha3_to_alpha2.keys():
            return self.alpha3_to_alpha2[region], "alpha3"
        elif region in self.currency_to_alpha2.keys():
            return self.currency_to_alpha2[region], "currency"
        elif region.lower().title() in self.region_to_alpha2.keys():
            return self.region_to_alpha2[region.lower().title()], "natural"
        else:
            raise ValueError("Region Error. '%s' is not recognized by EasyMoney. See options()." % (region))

    def _iso_mapping(self, region, map_to = 'alpha2'):
        """

        :param region: a region as denoted by a 'alpha2', 'alpha3' or 'currency'
        :param map_to: 'alpha2', 'alpha3', 'currency' or 'natural'.
        :return:
        """

        # Block EUR and Europe handling by the below _iso_mapping() code
        if region.upper() == 'EUR' or region.lower().title() == 'Europe':
            if map_to == 'currency':
                return 'EUR'
            elif map_to == 'natural':
                return 'Europe'
            else:
                raise ValueError("Cannot map '%s' to a specfic country." % (region))
        else:
            alpha2_mapping, raw_region_type = self._region_type(region)

        # Return iso code (alpha2 or 3), currency code or natural name
        if map_to == 'alpha2':
            return alpha2_mapping
        elif map_to == 'alpha3':
            return self.alpha2_to_alpha3[alpha2_mapping]
        elif map_to == 'currency':
            return "EUR" if alpha2_mapping in self.eu_join_dict.keys() else self.alpha2_to_currency[alpha2_mapping]
        elif map_to == 'natural':
            return self.alpha2_to_region[alpha2_mapping]
        else:
            raise ValueError('Invalid map_to request.')

    def _try_to_get_CPI(self, region, year):
        """

        :param region:
        :param year:
        :return:
        """

        # Init
        cpi = None

        # convert region to alpha2
        cpi_region = self._iso_mapping(region, map_to = 'alpha2')

        # Get most recent CPI year avaliable
        max_cpi_year = str(int(max([float(i) for i in self.cpi_dict[cpi_region].keys()])))

        if float(year) > float(max_cpi_year):
            if self.fallback:
                warnings.warn("Could not obtain required inflation (CPI) information for '%s' in %s."
                              " Using %s instead." % \
                             (self._iso_mapping(region, map_to = 'natural'), str(int(float(year))), max_cpi_year))
                cpi = floater(self.cpi_dict[cpi_region][str(int(float(max_cpi_year)))])
            else:
                raise AttributeError("EasyMoney could not obtain inflation (CPI) information for '%s' in '%s'" % (region, year))
        else:
            cpi = floater(self.cpi_dict[cpi_region][str(int(float(year)))])

        return cpi

    def inflation_rate(self, region, year_a, year_b, return_raw_cpi_dict = False):
        """

        :param region:
        :param year_a:
        :param year_b:
        :return:
        """

        # Get the CPI for year_b and year_a
        c1 = self._try_to_get_CPI(region, year_b)
        c2 = self._try_to_get_CPI(region, year_a)

        if return_raw_cpi_dict:
            return dict(zip([str(year_b), str(year_a)], [c1, c2]))
        if any([np.isnan(c1), np.isnan(c2)]):
            return np.NaN
        if c2 == 0.0:
            return np.NaN

        return ((c1 - c2) / c2) * 100

    def inflation_calculator(self, amount, region, year_a, year_b):
        """

        :param amount: a montary amount, e.g., 5
        :param region: a geographical region, e.g., US
        :param year_a: start year
        :param year_b: end year
        :return:
        """

        # Input checking
        if floater(year_a) == floater(year_b):
            return amount
        if floater(year_a) > floater(year_b):
            raise ValueError("year_a cannot be greater than year_b")

        # Get the CPI information
        inflation_dict = self.inflation_rate(  self._iso_mapping(region, map_to = 'alpha2')
                                             , int(float(year_a))
                                             , int(float(year_b))
                                             , return_raw_cpi_dict = True)

        # Check all the values are floats
        if not all([floater(x, just_check = True) for x in inflation_dict.values()]):
            warnings.warn("Problem obtaining required inflation information.")
            return np.NaN

        # Block division by zero
        if any(x == 0.0 for x in inflation_dict.values()):
            warnings.warn("Problem obtaining required inflation information.")
            return np.NaN

        # Scale w.r.t. inflation.
        try:
            adjusted_amount = inflation_dict[str(int(float(year_b)))]/float(inflation_dict[str(int(float(year_a)))]) * amount
        except KeyError as e:
            raise KeyError("Could not obtain inflation information for %s in %s." % \
                           (self._iso_mapping(region, map_to = 'natural'), e))

        # Round and Return
        return round(adjusted_amount, self.round_to)

    def _eur_to_lcu(self, currency, date = 'most_recent'):
        """

        :param currency:
        :param date: MUST be of the form: YYYY-MM-DD; defaults to 'most recent'.
        :return: exchange_rate w.r.t. the EURO (as a base currency).
        """

        # Convert currency arg. to a currency code.
        currency_to_convert = self._iso_mapping(currency, 'currency')

        # Block self-conversion
        if currency_to_convert == "EUR":
            return 1.0

        # Initialize
        date_key = None

        # Get the current date
        if date == 'most_recent':
            try:
                date_key = str(max([d.date() for d in pd.to_datetime(list(self.ex_dict.keys()))]))
            except:
                raise ValueError("Could not obtain most recent exchange information from the European Central Bank.")
        else:
            if date in self.ex_dict.keys():
                date_key = date
            elif date not in self.ex_dict.keys():
                date_key = self._closest_date([  datetime.datetime.strptime(d, "%Y-%m-%d") for d in ex_dict.keys()]
                                               , datetime.datetime.strptime(date, "%Y-%m-%d"), problem_domain = 'currency')
                warnings.warn("Currency information could not be obtained for '%s', %s was used instead" % (date, date_key))

        return self.ex_dict[date_key][currency_to_convert.upper()]

    def currency_converter(self, amount, from_currency, to_currency, date = 'most_recent', pretty_print = False):
        """

        :param amount:
        :param from_currency:
        :param to_currency:
        :param date:
        :return:
        """

        # Initialize variables
        conversion_to_invert = None
        converted_amount = None

        # Check amount is float
        if not isinstance(amount, (float, int)):
            raise ValueError("Amount must be numeric (intiger or float).")

        # Correct from_currency
        from_currency_fn = self._iso_mapping(from_currency, map_to = "currency")

        # Check for from_currency == to_currency
        if self._iso_mapping(from_currency_fn) == self._iso_mapping(to_currency):
            return round(amount, self.round_to) if not pretty_print else print(money_printer(amount, self.round_to), to_currency)

        # To some currency from EURO
        if from_currency_fn == "EUR":
            converted_amount = self._eur_to_lcu(to_currency, date) * float(amount)

        # From some currency to EURO
        elif self._eur_to_lcu(to_currency) == "EUR":
            conversion_to_invert = self._eur_to_lcu(from_currency, date)

            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted to '%s'." % (to_currency))
            converted_amount = conversion_to_invert**-1 * float(amount)

        # from_currency --> EURO --> to_currency
        else:
            conversion_to_invert = self._eur_to_lcu(from_currency_fn , date)
            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted from '%s'." % (from_currency))

            converted_amount = conversion_to_invert**-1 * self._eur_to_lcu(to_currency, date) * float(amount)

        # Round
        rounded_amount = round(converted_amount, self.round_to)

        # Return results (or pretty print)
        if not pretty_print:
            return rounded_amount
        else:
            print(money_printer(rounded_amount, self.round_to), self._iso_mapping(to_currency, "currency"))

    def normalize(self, amount, currency, from_year, to_year = "most_recent", base_currency = "EUR", pretty_print = False):
        """

        :param amount:
        :param currency:
        :param from_year:
        :param to_year:
        :param base_currency:
        :return:
        """

        # Standardize currency input
        from_currency = self._iso_mapping(currency, map_to = "currency")

        # Ensure base_currrency is a valid currency code
        to_currency = self._iso_mapping(base_currency, map_to = 'currency')

        # Determine Alpha2 country code
        from_region = self._iso_mapping(currency, map_to = 'alpha2')

        # Determine to CPI Data
        most_recent_cpi_record = self.cpi_df[(self.cpi_df.alpha2 == self.currency_to_alpha2[from_currency]) & \
                                             (~pd.isnull(self.cpi_df.cpi))].year.max()

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
        currency_adj_inflation = self.inflation_calculator(amount, from_region, from_year, inflation_year_b)

        # Convert into the base currency, e.g., EURO.
        adjusted_amount = self.currency_converter(currency_adj_inflation, from_currency, to_currency)

        return adjusted_amount if not pretty_print else print(money_printer(adjusted_amount, self.round_to), to_currency)

    def _date_options(self, nested_date_dict, min_max_only = True, keys_as_dates = False, date_format = "%Y-%m-%d"):
        """


        Jumbo function (refactor ASAP...) that figures
        out how to return dates for which data is avaliable.

        :param nested_date_dict: expected structures:
                                 1. {KEY: {DATE: VALUE}, KEY: {DATE: VALUE}...}; keys_as_dates = False; DATE = YYYY
                                 2. {DATE: {KEY: VALUE}, DATE: {KEY: VALUE}...}; keys_as_dates = True; DATE = YYYY-MM-DD
        :param min_max_only:
        :param keys_as_dates:
        :param rformat: 'str' or 'datetime'
        :return: dict
        """

        # Init
        date_values = None
        date_ranges_dict = dict()

        # Input Check
        if not isinstance(min_max_only, bool):
            raise ValueError('min_max_only must be a boolean.')
        if not isinstance(keys_as_dates, bool):
            raise ValueError('keys_as_dates must be a boolean.')

        # i.e., ex_dict
        if keys_as_dates:
            if min_max_only:
                date_values = [datetime.datetime.strptime(d, date_format) for d in nested_date_dict.keys()]
                return dict(zip(['min', 'max'], min_max(date_values)))
            elif not min_max_only:
                # Iterate though the dates (keys)
                for i in nested_date_dict:
                    # Iterate through the first nest
                    for j in nested_date_dict[i].keys():
                        # Populate the date_ranges_dict
                        alpha2_j = _iso_mapping(j)
                        date_values = str_to_datetime([i])
                        date_values = date_values if date_values != None else []
                        if alpha2_j not in date_ranges_dict.keys():
                            date_ranges_dict[alpha2_j] = date_values
                        else:
                            date_ranges_dict[alpha2_j] += date_values
                return date_ranges_dict

        # i.e., cpi_dict
        elif not keys_as_dates:
            date_ranges_dict = dict.fromkeys(nested_date_dict.keys()) # should be using _iso_mapping() here.
            if min_max_only:
                date_values = [i for s in nested_date_dict.values() for i in s]
                return dict(zip(['min', 'max'], [datetime.datetime.strptime(d, date_format) for d in min_max(date_values)]))
            elif not min_max_only:
                # Get the date range for each key in the nested dict
                for k in date_ranges_dict:
                    date_values = sorted(str_to_datetime(nested_date_dict[k].keys(), date_format = date_format))
                    date_ranges_dict[k] = date_values
                return date_ranges_dict

    def _alpha2_to_alpha2_unpack(self, pandas_series, unpack_dict):
        """

        :param pandas_series:
        :param unpack_dict:
        :return:
        """

        # Hacking the living daylights out of the pandas API
        return pandas_series.replace(unpack_dict).map(
               lambda x: np.NaN if 'nan' in str(x) else strlist_to_list(str(x)))

    def _currency_options(self):
        """

        :return:
        """

        # Make a currency code of possible currency codes
        currency_ops = pd.DataFrame(currency_codes, columns = ["CurrencyCodes"])

        # Make the Alpha2 Column
        currency_ops['Alpha2'] = currency_ops["CurrencyCodes"].replace(
            {**currency_to_alpha2, **ecb_currency_to_alpha2_dict})

        # Make the Alpha3 and Region Columns
        currency_ops['Alpha3'] = currency_ops["Alpha2"].replace(alpha2_to_alpha3)
        currency_ops['Region'] = currency_ops["Alpha2"].replace(alpha2_to_region)

        # Reorder
        currency_ops = currency_ops[['Region', 'CurrencyCodes', 'Alpha2', 'Alpha3']]

        # Add date information
        dates_dict = _date_options(1, nested_date_dict = ex_dict, min_max_only = False, keys_as_dates = True)

        ex_dict_dates = dict((k, str(datetime_to_str(min_max(v)))) for k, v in dates_dict.items())

        # Create Date Range Column
        currency_ops['Range'] = _alpha2_to_alpha2_unpack(currency_ops['Alpha2'], ex_dict_dates)
        all_date_ranges = np.array(currency_ops['Range'].tolist())

        # Create Row for Europe
        eur_row = pd.DataFrame({'Region': 'Europe', 'CurrencyCodes': 'EUR', 'Alpha2': np.nan, 'Alpha3': np.nan,
                                'Range': [[min(all_date_ranges[:,0]), max(all_date_ranges[:,1])]]},
                                 index = [0], columns = currency_ops.columns.tolist())

        # Append the Europe Row
        currency_ops = currency_ops.append(eur_row, ignore_index = True)

        # Sort by Region
        currency_ops.sort_values(['Region'], ascending = [1], inplace = True)

        # Correct Index
        currency_ops.index = range(currency_ops.shape[0])

        return currency_ops

    def _inflation_options(self):
        """

        :return:
        """
        cpi_ops = cpi_df[['region', 'currency_code', 'alpha2', 'alpha3']].drop_duplicates()
        cpi_ops.columns = ['Region', 'CurrencyCodes', 'Alpha2', 'Alpha3']
        cpi_ops.index = range(cpi_ops.shape[0])

        dates_dict = _date_options(  1, nested_date_dict = cpi_dict
                                   , min_max_only = False
                                   , keys_as_dates = False
                                   , date_format = '%Y')

        cpi_dict_years = dict((k, str(min_max([i.year for i in v]))) for k, v in dates_dict.items())

        # Hacking the living daylights out of the pandas API
        cpi_ops['Range'] = _alpha2_to_alpha2_unpack(cpi_ops['Alpha2'], cpi_dict_years)

        # Sort by Region and Return
        cpi_ops.sort_values(['Region'], ascending = [1], inplace = True)

        # Correct Index
        cpi_ops.index = range(cpi_ops.shape[0])

        return cpi_ops

    def options(self, info = 'currency', rformat = 'table', pretty_table = True, pretty_print = True):
        """

        :param information: 'currency', 'inflation', 'curr_inflat' or 'dates'.
        :param rformat: 'table' for a table or 'list' for just the currecy codes, alone
        :param pretty_table:
        :return: Currency Information EasyMoney Understands
        :rtype: DataFrame
        """

        # Add option to return only exchange infomation, CPI or both.

        list_to_return = None
        table_to_return = None

        if rformat == 'list':

            if info == 'currency':
                list_to_return =  sorted(self.currency_codes + ['EUR'])
            elif info == 'inflation':
                list_to_return =  sorted([i for i in cpi_df.alpha2.unique().tolist() if isinstance(i, str)])

            if pretty_print:
                for i in list_to_return: print(i)
            else:
                return list_to_return

        elif rformat == 'table':

            if info == 'currency':
                table_to_return = _currency_options(1)

            elif info == 'inflation':
                table_to_return = _inflation_options(1)

            # Remove indexes
            if pretty_table:
                table_to_return.index = ['' for i in range(currency_table.shape[0])]

            # Print the full table
            if pretty_print:
                pandas_print_full(table_to_return)
            else:
                return table_to_return

        else:
            raise ValueError("'%s' is an invalid setting for rformat.\n"
                             "Please use 'table' for a table (pandas dataframe) or 'codes' for the currency codes"
                             " as a list.")




















