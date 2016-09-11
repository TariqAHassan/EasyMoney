#!/usr/bin/env python3

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""

# Modules #
import sys
import copy
import datetime
import numpy as np
import pandas as pd

try:
    from fuzzywuzzy import process
except:
    pass

from warnings import warn
from collections import defaultdict

from easymoney.support_money import date_bounds_floor
from easymoney.support_money import datetime_to_str
from easymoney.support_money import dict_list_unpack
from easymoney.support_money import dict_merge
from easymoney.support_money import floater
from easymoney.support_money import key_value_flip
from easymoney.support_money import list_flatten
from easymoney.support_money import min_max
from easymoney.support_money import money_printer
from easymoney.support_money import prettify_list_of_strings
from easymoney.support_money import remove_from_dict
from easymoney.support_money import str_to_datetime

from easymoney.easy_pandas import pandas_dictkey_to_key_unpack
from easymoney.easy_pandas import pandas_print_full
from easymoney.easy_pandas import pandas_list_column_to_str
from easymoney.easy_pandas import prettify_all_pandas_list_cols
from easymoney.easy_pandas import twoD_nested_dict

from sources.databases import DatabaseManagment
from sources.databases import _exchange_rates_from_datafile
from sources.ecb_interface import ecb_currency_to_alpha2_dict


class EasyPeasy(object):
    """

    Tools for Monetary Information and Conversions.

    :param database_path: an alternative path to the database files.
                          Databases therein will supplant those used automatically by EasyMoney.
                          If this directory does not contain all of the required databases, those that are missing will
                          be generated. Defaults to None.
    :type database_path: str
    :param precision: number of places to round to when returning results. Defaults to 2.
    :type precision: int
    :param fall_back: if True, fall back to closest possible date for which data is available. Defaults to True.
    :type fall_back: bool
    :param fuzzy_match_threshold: a threshold for fuzzy matching confidence (requires the ``fuzzywuzzy`` package).
                                  The value must be an integer between 0 and 100. The *suggested* minimum values is 85.
                                  This will only impact attempts to match on natural names, e.g., attempting to match
                                  'Canada' by passing 'Canadian'. Defaults to None.

                                  .. warning::

                                        Fuzzy matching may yield inaccurate results.

                                        Whenever possible, use terminology *exactly* as it appears in ``options()``.

    :type fuzzy_match_threshold: int
    """


    def __init__(self, database_path = None, precision = 2, fall_back = True, fuzzy_match_threshold = None):
        """

        Initialize the ``EasyPeasy()`` class.

        """
        # Places of precision
        self.round_to = precision

        # Fall back boolean
        self.fall_back = fall_back

        # Try to import fuzzywuzzy, if requested.
        if isinstance(fuzzy_match_threshold, int):
            if 'fuzzywuzzy' not in sys.modules:
                raise ImportError("to use 'fuzzy_match_threshold' please install 'fuzzywuzzy'.\n"
                                  "For optimal performance, please also consider installing 'python-Levenshtein'.")
        elif fuzzy_match_threshold != None and not isinstance(fuzzy_match_threshold, int):
            raise ValueError("fuzzy_match_threshold must be an intiger.")

        # Issue warning if the threshold is below 85
        # (arbitrary, but this appears to mark begining of notable decrements in accuracy).
        if fuzzy_match_threshold != None and fuzzy_match_threshold < 85:
            warn('\nLow fuzzy_match_threshold. Please Consider Increasing this Value.')

        # Set fuzzy_match_threshold
        self.fuzzy_match_threshold = fuzzy_match_threshold

        # Obtain required databases
        required_databases = DatabaseManagment(database_path)._database_wizard()

        # Define Databases
        self.ISOAlphaCodesDB         = required_databases[0]
        self.CurrencyTransitionDB    = required_databases[1]
        self.ExchangeRatesDB         = required_databases[2]
        self.currency_codes          = required_databases[3]
        self.ConsumerPriceIndexDB    = required_databases[4]
        self.CurrencyRelationshipsDB = required_databases[5]

        # Transition Tuples
        t_tuples_lambda = lambda x: (x['OldCurrency'], x['NewCurrency'], x['Date'])
        self.CurrencyTransitionDB['transition_tuples'] = self.CurrencyTransitionDB.apply(t_tuples_lambda, axis = 1)

        # Exchange Rates Dates as strings.
        self.ExchangeRatesDB['Date'] = self.ExchangeRatesDB['Date'].astype(str)

        # Group Dates by Currency
        currency_ex_dates = self.ExchangeRatesDB.groupby('Currency')['Date'].apply(
            lambda x: sorted(x.tolist())).reset_index()

        # Convert currency_ex_dates to Dict
        self.currency_ex_dict = dict(zip(currency_ex_dates['Currency'].tolist(), currency_ex_dates['Date'].tolist()))

        # Convert the ExchangeRatesDB to a dict for faster look up speed.
        self.exchange_dict = _exchange_rates_from_datafile(self.ExchangeRatesDB)[0]

        # Find the min and max exchange date in the dictionary
        min_exchange_date = pd.to_datetime(self.ExchangeRatesDB['Date'].min()).year
        max_exchange_date = pd.to_datetime(self.ExchangeRatesDB['Date'].max()).year

        # Create currency transitions dictionary
        # with only those transitions ocurring between min and max.
        self.transition_dict = self.CurrencyTransitionDB[
            self.CurrencyTransitionDB['Date'].between(min_exchange_date, max_exchange_date)].groupby(
            'Alpha2').apply(lambda x: x['transition_tuples'].tolist()).to_dict()

        # Create CPI dict
        self.cpi_dict = twoD_nested_dict(self.ConsumerPriceIndexDB, 'Alpha2', 'Year', 'CPI', to_float = ['CPI'], to_int = ['Year'])

        # Create Alpha3 --> Alpha2 Dict
        self.alpha3_to_alpha2 = remove_from_dict(dict(zip(self.ISOAlphaCodesDB.Alpha3, self.ISOAlphaCodesDB.Alpha2)))

        # Create Alpha2 --> Alpha3 Dict
        self.alpha2_to_alpha3 = key_value_flip(self.alpha3_to_alpha2)

        # Create the dict and populate using uniques in the ConsumerPriceIndexDB.
        currency_to_alpha2 = dict()
        for k in self.ConsumerPriceIndexDB['Currency'].unique().tolist():
            currency_to_alpha2[k] = self.ConsumerPriceIndexDB['Alpha2'][self.ConsumerPriceIndexDB['Currency'].astype(str) == k].unique().tolist()

        # Drop NaNs
        self.currency_to_alpha2 = remove_from_dict(currency_to_alpha2)

        # Create a flipped dict from currency_to_alpha2.
        self.alpha2_to_currency = dict_list_unpack(currency_to_alpha2)

        # Create Region Name --> Alpha2 Dict
        self.region_to_alpha2 = remove_from_dict(dict(zip(self.ConsumerPriceIndexDB['Country'], self.ConsumerPriceIndexDB['Alpha2'])))

        # Create Alpha2 --> Region Name Dict
        self.alpha2_to_region = key_value_flip(self.region_to_alpha2)

    def _closest_date(self, list_of_dates, date, problem_domain = '', date_format = None):
        """

        *Private Method*
        Determines the closest date for which data is available.

        :param list_of_dates: a list of datetimes.
        :type list_of_dates: list
        :param date: a date of the form YYYY-MM-DD.
        :type date: datetime
        :param problem_domain: domain of the problem _closet_date() is tryping to solve. Information for error message.
                               Defaults to empty string.
        :type problem_domain: str
        :param date_format: a date format. Defaults to None (which results in a datetime.datetime object being returned),
                           instead of a string.
        :type date_format: str
        :return: the closet date, as ranked by the standard python sorting algo. (sorted() method).
        :rtype: ``list``
        :raises AttributeError: if fall_back is set to False.
        :raises ValueError: if an element in list_of_dates is not of class datetime.datetime.
        """
        # Block fall_back behaviour if it's not permitted.
        if not self.fall_back:
            raise AttributeError("EasyMoney could not obtain '%s' information for %s" % (problem_domain, date))

        # Ensure dates are of type datetime.
        if False in [isinstance(i, datetime.datetime) for i in list_of_dates]:
            raise ValueError("Dates must be of type: datetime.datetime")

        # Return best match
        best_match = sorted(list_of_dates, key = lambda date_in_list: abs(date - date_in_list))[0]

        if date_format == None:
            return best_match
        else:
            return datetime_to_str([best_match], date_format = date_format)[0]

    def _fuzzy_search(self, region):
        """

        *Private Method*
        Use the fuzzywuzzy package to map the region to an ISO Alpha2 Code

        :param region:
        :type region: str
        :return:
        :rtype: ``str``
        """
        # Precaution to block usage of fuzzywuzzy if it is not enabled.
        if self.fuzzy_match_threshold == None:
            return None

        # Try to get the best match for the region
        best_match = process.extractOne(region, self.region_to_alpha2.keys())

        # Return the best match if the confidence
        # is greater than, or equal to, fuzzy_match_threshold.
        if best_match[1] >= self.fuzzy_match_threshold:
            return self.region_to_alpha2[best_match[0]]
        else:
            return None

    def _region_type(self, region):
        """

        *Private Method*
        Standardize Currency Code, Alpha3 and Natural Name (e.g., 'Canada') to Alpha2.

        :param region: a region (Alpha2, Alpha3, Natural Name or currency code).
        :type region: str
        :return: ISO Alpha2 code.
        :rtype: ``str``
        :raises ValueError: if ``region`` is not recognized by EasyMoney (see ``options()``).
        """
        if not isinstance(region, str):
            raise TypeError("'%s' is not a string." % (str(region)))

        # Initialize
        currency_region = None
        fuzzy_match = None

        if region.upper() in ecb_currency_to_alpha2_dict.keys():
            return ecb_currency_to_alpha2_dict[region.upper()], "currency"

        elif region.upper() in self.alpha3_to_alpha2.values():
            return region.upper(), "alpha2"

        elif region.upper() in self.alpha3_to_alpha2.keys():
            return self.alpha3_to_alpha2[region.upper()], "alpha3"

        elif region.upper() in self.currency_to_alpha2.keys():
            currency_region = self.currency_to_alpha2[region.upper()]
            if len(currency_region) == 1:
                return currency_region[0], "currency"
            else:
                raise ValueError("'%s' is used in several countries thus cannot be mapped to a single nation." % (region))

        elif region.lower().title() in self.region_to_alpha2.keys():
            return self.region_to_alpha2[region.lower().title()], "natural"

        elif self.fuzzy_match_threshold != None:
            fuzzy_match = self._fuzzy_search(region)
            if fuzzy_match != None:
                return fuzzy_match, "natural"
            else:
                raise ValueError("Region Error. '%s' could not be matched to a known country. See options()." % (region))

        else:
            raise ValueError("Region Error. '%s' is not recognized by EasyMoney. See options()." % (region))

    def region_map(self, region, map_to = 'alpha2', return_region_type = False):
        """

        Map a 'region' to any one of: ISO Alpha2, ISO Alpha3 or Currency Code as well as its Natural Name.

            Examples Converting From Currency:
                - ``EasyPeasy().region_map(region = 'CAD', map_to = 'alpha2')``   :math:`=` 'CA'
                - ``EasyPeasy().region_map(region = 'CAD', map_to = 'alpha3')``   :math:`=` 'CAN'

            Examples Converting From Alpha2:
                - ``EasyPeasy().region_map(region = 'FR', map_to = 'currency')`` :math:`=` 'EUR'
                - ``EasyPeasy().region_map(region = 'FR', map_to = 'natural')``  :math:`=` 'France'

        :param region: a 'region' in the format of a ISO Alpha2, ISO Alpha3 or currency code, as well as natural name.
        :type region: str
        :param map_to: 'alpha2', 'alpha3' 'currency' or 'natural' for ISO Alpha2, ISO Alpha2, Currency Code and
                        Natural Names, respectively. Defaults to 'alpha2'.
        :type map_to: str
        :param return_region_type: if True return the type of input supplied (one of:'alpha2', 'alpha3' 'currency' or 'natural')
                                   Defaults to False.
        :type return_region_type: bool
        :return: the desired mapping from region to ISO Alpha2.
        :rtype: ``str`` or ``tuple``
        :raises ValueError: if *map_to* is not one of 'alpha2', 'alpha3', 'currency' or 'natural'.

        .. warning::
            Attempts to map common currencies to a single nation will fail.


            For instance: ``EasyPeasy().region_map(region = 'EUR', map_to = 'alpha2')`` will fail because the Euro (EUR)
            is used in several nations and thus a request to map it to a single ISO Alpha2 country code creates insurmountable
            ambiguity.
        """
        # Initialize
        error_list = None
        map_to_options = ['alpha2', 'alpha3', 'currency', 'natural']
        mapping = None

        # Check that map_to is valid.
        if map_to not in map_to_options:
            raise ValueError("map_to must be one of: %s." % (prettify_list_of_strings(map_to_options, 'or')))

        # Seperately handle requests for map_to == 'currency' when region is a currency used by several nations.
        if region.upper() in self.currency_to_alpha2.keys() and len(self.currency_to_alpha2[region.upper()]) > 1:
            if map_to == 'currency':
                return region.upper()
            else:
                raise ValueError("The '%s' currency is used in multiple nations and thus cannot be mapped to a single one." \
                 % (region))

        # Get the Alpha2 Mapping
        alpha2_mapping, raw_region_type = self._region_type(region)

        # Return iso code (alpha2 or 3), currency code or natural name
        if map_to == 'alpha2':
            mapping = alpha2_mapping
        elif map_to == 'alpha3':
            mapping = self.alpha2_to_alpha3[alpha2_mapping]
        elif map_to == 'currency':
            mapping = self.alpha2_to_currency[alpha2_mapping]
        elif map_to == 'natural':
            mapping = self.alpha2_to_region[alpha2_mapping]

        return (mapping, raw_region_type) if return_region_type else mapping

    def _try_to_get_CPI(self, region, year):
        """

        *Private Method*
        Function to look up CPI information in the cached database information.

        :param region: a region (currency codes may work, provided they are not common currencies, e.g., Euro).
        :type region: str
        :param year: year for which CPI information is desired.
        :type year: int
        :return: CPI information in the requested region for the requested year.
        :rtype: ``float``
        :raises LookupError: if cannot obtain CPI information from the database.
        :raises AttributeError: if not fall_back
        """
        # Initialize
        cpi = None
        inflation_error_message = "EasyMoney could not obtain inflation (CPI) information for '%s' in '%s'." % (str(region), str(year))

        # convert region to alpha2
        cpi_region = self.region_map(region, map_to = 'alpha2')

        # Get most recent CPI year available
        if cpi_region not in self.cpi_dict.keys():
            raise LookupError("Could not find inflation information for '%s'." % (str(region)))

        max_cpi_year = str(int(max([float(i) for i in self.cpi_dict[cpi_region].keys()])))

        if float(year) > float(max_cpi_year):
            if self.fall_back:
                try:
                    cpi = floater(self.cpi_dict[cpi_region][str(int(float(max_cpi_year)))]) # add Error handling?
                    warn("Could not obtain required inflation (CPI) information for '%s' in %s."
                                  " Using %s instead." % \
                                  (self.region_map(region, map_to = 'natural'), str(int(float(year))), max_cpi_year))
                except:
                    raise LookupError(inflation_error_message)
            else:
                raise AttributeError(inflation_error_message)
        else:
            try:
                cpi = floater(self.cpi_dict[cpi_region][str(int(float(year)))])
            except:
                raise LookupError(inflation_error_message)

        return cpi

    def inflation_rate(self, region, year_a, year_b = None, return_raw_cpi_dict = False, pretty_print = False):
        """

        Calculator to compute the inflation rate from Consumer Price Index (CPI) information.

        Inflation Formula:

        .. math:: Inflation_{region} = \dfrac{c_{1} - c_{2}}{c_{2}} \cdot 100

        | :math:`where`:
        |   :math:`c_{1}` = CPI of the region in *year_b*.
        |   :math:`c_{2}` = CPI of the region in *year_a*.

        :param region: a region (currency codes may work, provided they are not common currencies, e.g., Euro).
        :type region: str
        :param year_a: start year.
        :type year_a: int
        :param year_b: end year. Defaults to None -- can only be left to this default if return_raw_cpi_dict is True.
        :type year_b: int
        :param return_raw_cpi_dict: If True, returns the CPI information in a dict. Defaults to False.
        :type return_raw_cpi_dict: bool
        :param pretty_print: if True, pretty prints the result otherwise returns the result as a float. Defaults to False.
        :type pretty_print: bool
        :return: (a) the rate of inflation between year_a and year_h.

                        Note: returns *nan* if :math:`c_{1}` or :math:`c_{2}` are *nan* OR :math:`c_{2}` is zero.

                 (b) a dictionary of CPI information with years as keys, CPI as values.
        :rtype: ``float``, ``dict`` or ``nan``
        :raises ValueError: if year_b is None and return_raw_cpi_dict is False.
        """
        # Get the CPI for year_b and year_a
        c1 = self._try_to_get_CPI(region, year_b) if year_b != None else None
        c2 = self._try_to_get_CPI(region, year_a)

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

        # Compute the rate of Inflation
        rate = ((c1 - c2) / c2) * 100

        # Return or Pretty Print.
        if not pretty_print:
            return round(rate, self.round_to)
        else:
            print(money_printer(rate, self.region_map(region, 'currency'), round_to = self.round_to))

    def inflation_calculator(self, amount, region, year_a, year_b, pretty_print = False):
        """

        Adjusts a given amount of money for inflation.

        :param amount: a monetary amount, e.g., 5.23.
        :type amount: float or int
        :param region: a geographical region, e.g., 'US'.
        :type region: str
        :param year_a: start year.
        :type year_a: int
        :param year_b: end year.
        :type year_b: int
        :param pretty_print: if True, pretty prints the result otherwise returns the result as a float. Defaults to False.
        :type pretty_print: bool
        :return: :math:`amount \cdot inflation \space rate`.
        :rtype: ``float``
        :raises ValueError: if  year_a occurs after year_b.
        :raises KeyError: if inflation (CPI) information cannot be found in the inflation database.
        """
        # Input checking
        if floater(year_a) == floater(year_b):
            return amount
        if floater(year_a) > floater(year_b):
            raise ValueError("year_a cannot be greater than year_b")

        # Get the CPI information
        inflation_dict = self.inflation_rate(  self.region_map(region, map_to = 'alpha2')
                                             , int(float(year_a))
                                             , int(float(year_b))
                                             , return_raw_cpi_dict = True)

        # Check all the values are floats
        if not all([floater(x, just_check = True) for x in inflation_dict.values()]):
            warn("Problem obtaining required inflation information.")
            return np.NaN

        # Block division by zero
        if any(x == 0.0 for x in inflation_dict.values()):
            warn("Problem obtaining required inflation information.")
            return np.NaN

        # Scale w.r.t. inflation.
        try:
            adjusted_amount = inflation_dict[str(int(float(year_b)))]/float(inflation_dict[str(int(float(year_a)))]) * amount
        except KeyError as e:
            raise KeyError("Could not obtain inflation information for %s in %s." % \
                           (self.region_map(region, map_to = 'natural'), e))

        # Return or Pretty Print.
        if not pretty_print:
            return round(adjusted_amount, self.round_to)
        else:
            print(money_printer(adjusted_amount, self.region_map(region, 'currency'), round_to = self.round_to))

    def _base_cur_to_lcu(self, currency, date = "latest", return_max_date = False, date_format = "%Y-%m-%d"):
        """

        *Private Method*
        Convert from a base currency (Euros if usin ECB data) to a local currency unit, e.g., CAD.

        :param currency: a currency code or region
        :type currency: str
        :param date: MUST be of the form: ``YYYY-MM-DD`` OR ``YYYY``*; defaults to "latest".

                     .. warning::
                        If a date of the form YYYY is passed, the average exchange rate will be returned for that year.

        :type date: str
        :param return_max_date: if True, returns the max date for EUR to LCU.
        :type return_max_date: bool
        :param date_format: a date format. Defaults to "%Y-%m-%d".
        :type date_format: str
        :return: exchange_rate w.r.t. the EURO (as a base currency).
        :raises ValueError: if date is not 'latest' and return_max_date is True.
        :raises AttributeError: if exchange rate information cannot be found in the exchange rate database.
        """
        # Initialize
        date_key = None
        date_key_list = None
        str_time = datetime.datetime.strptime
        error_msg = "Could not obtain most recent exchange information from the European Central Bank."

        # Check for invalid request
        if date != 'latest' and return_max_date == True:
            raise ValueError("date must be equal to 'latest' if return_max_date is True.")

        # Convert currency arg. to a currency code.
        currency_to_convert = self.region_map(currency, 'currency')

        # Block self-conversion
        if currency_to_convert == "EUR" and return_max_date == False:
            return 1.0
        elif currency_to_convert == "EUR" and date == 'latest' and return_max_date == True:
            return str(max(self.exchange_dict.keys()))

        # Get the current date
        if date == "latest":
            try:
                date_key_list = [k for k, v in self.exchange_dict.items() if currency_to_convert in v.keys()]
            except:
                raise AttributeError(error_msg)
            if len(date_key_list) > 0:
                date_key = str(max(date_key_list))
            else:
                raise ValueError(error_msg)
            if return_max_date:
                return date_key
        else:
            if floater(date, just_check = True) and len(str(date).strip()) == 4:
                # Compute the average conversion rate over the whole year
                return np.mean([v[currency_to_convert] for k, v in self.exchange_dict.items()
                                if currency_to_convert in v and str(str_to_datetime(k).year) == str(date)])
            elif date in self.exchange_dict.keys():
                date_key = date
            elif date not in self.exchange_dict.keys():
                date_key = self._closest_date(  list_of_dates = [str_time(d, date_format) for d in self.exchange_dict.keys()]
                                              , date = str_time(date, date_format)
                                              , problem_domain = 'currency'
                                              , date_format = date_format)
                warn("\nCurrency information could not be obtained for '%s', %s was used instead." % (date, date_key))

        # Return the exchange rate on a given date
        return self.exchange_dict[date_key][currency_to_convert.upper()]

    def currency_converter(self, amount, from_currency, to_currency, date = "latest", pretty_print = False):
        """

        Function to perform currency conversion based on, **not** directly reported from, data obtained
        from the European Central Bank (ECB). This data contains the exchange rate from Euros (EUR) to
        many local currency units (LCUs).

        **Formulae Used**

        Let :math:`LCU` be defined as:

            .. math:: LCU(\phi_{EUR}, CUR) = ExchangeRate_{\phi_{EUR} → CUR}

        | :math:`where`:
        |   :math:`CUR` is some local currency unit.
        |   :math:`\phi = 1`, as in the ECB data.
        |
        That is, less formally:

            .. math:: LCU(1 \space EUR, CUR) = \dfrac{x \space \space CUR}{1 \space EUR}

        :math:`Thus`:

            From :math:`EUR` to :math:`CUR`:

                .. math:: amount_{CUR} = LCU(\phi_{EUR}, CUR) \cdot amount_{EUR}

            From :math:`CUR` to :math:`EUR`:

                .. math:: amount_{EUR} = \dfrac{1}{LCU(\phi_{EUR}, CUR)} \cdot amount_{CUR}

            From :math:`CUR_{1}` to :math:`CUR_{2}`:

                .. math:: amount_{CUR_{2}} = \dfrac{1}{LCU(\phi_{EUR}, CUR_{1})} \cdot LCU(\phi_{EUR}, CUR_{2}) \cdot amount_{CUR_{1}}

        :param amount: an amount of money to be converted.
        :type amount: float or int
        :param from_currency: the currency of the amount.
        :type from_currency: str
        :param to_currency: the currency the amount is to be converted into.
        :type to_currency: str
        :param date: date of data to perform the conversion with. Dates must be of the form: ``YYYY-MM-DD`` or ``YYYY``.
                     Defaults to "latest" (which will use the most recent data available).

                     .. warning::
                         If a date of the form *YYYY*  is passed, the average exchange rate will be returned for that entire year.

                         For this reason, using a value other than a date of the form *YYYY-MM-DD*
                         or the default is not recommended.

        :type date: str
        :param pretty_print: if True, pretty prints the table otherwise returns the table as a pandas DataFrame. Defaults to False.
        :type pretty_print: bool
        :return: converted currency.
        :rtype: ``float``
        :raises ValueError: if

                            (a) pretty_print is not a boolean

                            (b) amount is not numeric (``float`` or ``int``).

        :raises AttributeError: conversion would result in division by zero (rare).
        """
        # Initialize
        conversion_to_invert = None
        converted_amount = None

        # Check amount is float
        if not isinstance(amount, (float, int)):
            raise ValueError("amount must be numeric (intiger or float).")

        # Check pretty_print is a bool
        if not isinstance(pretty_print, bool): raise ValueError("pretty_print must be either True or False.")

        # Correct from_currency
        from_currency_fn = self.region_map(from_currency, map_to = "currency")

        # Correct to_currency
        to_currency_fn = self.region_map(to_currency, map_to = "currency")

        # Return amount unaltered if self-conversion was requested.
        if not pretty_print and from_currency_fn == to_currency_fn:
            return amount

        # From Euro to some currency
        if from_currency_fn == "EUR":
            converted_amount = self._base_cur_to_lcu(to_currency_fn, date) * float(amount)

        # From some currency to Euro
        elif self._base_cur_to_lcu(to_currency_fn) == "EUR":
            conversion_to_invert = self._base_cur_to_lcu(from_currency, date)

            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted to '%s'." % (to_currency_fn))
            converted_amount = conversion_to_invert**-1 * float(amount)

        # from_currency --> Euro --> to_currency
        else:
            conversion_to_invert = self._base_cur_to_lcu(from_currency_fn, date)
            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted from '%s'." % (from_currency))
            converted_amount = conversion_to_invert**-1 * self._base_cur_to_lcu(to_currency_fn, date) * float(amount)

        # Round
        rounded_amount = round(converted_amount, self.round_to)

        # Return results (or pretty print)
        if not pretty_print:
            return rounded_amount
        else:
            print(money_printer(rounded_amount, self.region_map(to_currency, 'currency'), round_to = self.round_to))

    def normalize(self, amount, currency, from_year, to_year = "latest", base_currency = "EUR", exchange_date = None, pretty_print = False):
        """

        | Convert a Nominal Amount to a Real Amount in the same, or another, currency.
        |
        | This requires both inflation (for *currency*) and exchange rate information (*currency* to *base_currency*).
          See ``options(info = 'all', overlap_only = True)`` for an exhaustive listing of valid values to pass to this method.
        |
        | Currency Normalization occurs in two steps:
        |       1. Adjust the currency for inflation, e.g., 100 (2010 :math:`CUR_{1}`) → x (2015 :math:`CUR_{1}`).
        |       2. Convert the adjusted amount into the *base_currency*.

        :param amount: a numeric amount of money.
        :type amount: float or int
        :param currency: a region or currency. Legal: Region Name, ISO Alpha2, Alpha3 or Currency Code (see ``options()``).
        :type currency: str
        :param from_year: a year. For legal values see ``options()``.
        :type from_year: int
        :param to_year: a year. For legal values see ``options()``. Defaults to 'latest' (which will use the most recent data available).

                        .. warning::
                            If *to_year* is set to a specific year rather than to its default ('latest') and
                            *exchange_date* is left to its default (*None*), the *average* exchange rate for *to_year*
                            will be used :sup:`1`.

                            For this reason, it is suggested that if you wish to pass a specific year via *to_year*,
                            you also supply a specific date to *exchange_date* for this method to perform the currency
                            conversion. Recall that the exchange rate is only computed after *amount* has been
                            converted into real local currency units (LCUs; e.g., Real US Dollars or Real Euros.).

                            :sup:`1` The only exception to this generalization is if *currency* and *base_currency*
                            are the same (as currency conversion is not needed in such an instance).

        :type to_year: str or int
        :param base_currency:  a region or currency. Legal: Region Name, ISO Alpha2, Alpha3 or Currency Code
                               (see ``options()``). Defaults to 'EUR'.
        :type base_currency: str
        :param pretty_print: Pretty print the result if True; return amount if False. Defaults to False.
        :type pretty_print: bool
        :param exchange_date: date to perform the currency conversion on. Dates must be of the form: ``YYYY-MM-DD``.
                              Defaults to None.
        :type exchange_date: str
        :return: amount adjusted for inflation and converted into the base currency.
        :rtype: ``float``
        :raises ValueError: if:

                               (a) *from_currency* does not map onto a specific region,

                               (b) *to_year* is not numeric (``float`` or ``int``) OR

                               (c) *to_year* is greater than the year for which most recent inflation information is available.
        """
        # Initialize
        most_recent_cpi_record = None
        inflation_year_b = None

        # Standardize currency input
        from_currency = self.region_map(currency, map_to = 'currency')

        # Determine Alpha2 country code
        from_region = self.region_map(currency, map_to = 'alpha2')

        # Ensure base_currrency is a valid currency code
        to_currency = self.region_map(base_currency, map_to = 'currency')

        # Determine to CPI Data
        cpi_record = self.ConsumerPriceIndexDB[(self.ConsumerPriceIndexDB['Alpha2'] == from_region) & (~pd.isnull(self.ConsumerPriceIndexDB['CPI']))]
        if cpi_record.shape[0] != 0:
            most_recent_cpi_record = cpi_record['Year'].max()
        else:
            raise ValueError("'%s' cannot be mapped to a specific region, and thus inflation cannot be determined." % (currency))

        if to_year != "latest" and float(to_year) < float(most_recent_cpi_record):
            if floater(to_year, just_check = True):
                inflation_year_b = int(float(to_year))
            else:
                raise ValueError("to_year invalid; '%s' is not numeric (intiger or float).")
        elif to_year != "latest" and float(to_year) > float(most_recent_cpi_record):
            raise ValueError("No data available for '%s' in %s. Try %s or earlier." % (currency, str(to_year), str(most_recent_cpi_record)))
        else:
            inflation_year_b = most_recent_cpi_record
            if float(inflation_year_b) <= (datetime.datetime.now().year - 2):
                warn("Inflation information not available for '%s', using %s." % (to_year, inflation_year_b))

        # Adjust input for inflation
        currency_adj_inflation = self.inflation_calculator(amount, from_region, from_year, inflation_year_b)

        # Convert into the base currency
        adjusted_amount = self.currency_converter(  amount = currency_adj_inflation
                                                  , from_currency = from_currency
                                                  , to_currency = to_currency
                                                  , date = (to_year if exchange_date == None else exchange_date))

        # Return or Pretty Print
        if not pretty_print:
            return adjusted_amount
        else:
            print(money_printer(adjusted_amount, self.region_map(to_currency, 'currency'), round_to = self.round_to))

    def _currency_duplicate_remover(self, currency_ops):

        df = copy.deepcopy(currency_ops)

        # Generate the list of all overlapping currencies
        new_currency_col = df.groupby('Alpha2').apply(lambda x: x['Currency'].tolist()).reset_index()

        # Count the number of Each instance of the Alpha2 Column
        alpha2_counts = df['Alpha2'].value_counts().reset_index()

        # Return those Alpha2 Codes that exist more than twice
        multi_alpha2 = alpha2_counts[alpha2_counts['Alpha2'] >= 2]['index'].tolist()

        # Function to check if a row should be removed
        def _keep(currency, alpha2):
            if currency in self.CurrencyTransitionDB['OldCurrency'].tolist() and alpha2 in multi_alpha2:
                return False
            else:
                return True

        # Drop Duplicates
        df = df[df.apply(lambda row: _keep(row['Currency'], row['Alpha2']), axis=1)]

        # Refresh the index and return
        return df.reset_index(drop=True), multi_alpha2

    def _currency_transition_integrator(self, currency_ops, currency_ops_no_dups, multi_alpha2, min_max_dates):
        """

        *Private Method*
        Solutions to some *VERY* tricky problems.

        :param currency_ops:
        :param currency_ops_no_dups:
        :param multi_alpha2:
        :param min_max_dates:
        :return:
        """

        df = copy.deepcopy(currency_ops_no_dups)

        # Create a dict of multi_alpha2's with the full range of exchange information available
        # (regarless of currency used).
        merged_multi_dates = {k: sorted(list_flatten(currency_ops[currency_ops['Alpha2'] == k]['CurrencyRange']))
                              for k in multi_alpha2}

        # min_max dates, if requested
        multi_dates = {k: min_max(v) for k, v in merged_multi_dates.items()} if min_max_dates else merged_multi_dates

        # Replace CurrencyRange of multi_alpha2's with the full range of date information for that Alpha2
        df['CurrencyRange'] = df.apply(
            lambda x: x['CurrencyRange'] if x['Alpha2'] not in multi_dates.keys() else multi_dates[x['Alpha2']]
            , axis=1)

        # Add Transitions
        df['Transitions'] = df['Alpha2'].map(
            lambda x: self.transition_dict[x] if x in self.transition_dict.keys() else np.NaN)

        # For countries with noted transitions, update their Currency to the most recent used.
        def most_recent_transition(transitions):
            return list(filter(lambda x: str(x[2]) == max(np.array(transitions)[:, 2]), transitions))[0]

        # Create a temp. column of currencies to update
        df['CurrenciesToUpdate'] = df['Transitions'].map(
            lambda x: x if str(x) == 'nan' else most_recent_transition(x))

        # Define function to get CurrencyRange following merge
        def date_range_update(current_range, new_currency, min_max_dates):
            new_range = df['CurrencyRange'][df['Currency'] == new_currency].tolist()[0]
            merged_dates = sorted(list_flatten([current_range, new_range]))
            return min_max(merged_dates) if min_max_dates else merged_dates

        # Update Date CurrencyRange
        df['CurrencyRange'] = df.apply(
            lambda x: x['CurrencyRange'] if str(x['CurrenciesToUpdate']) == 'nan' \
                else date_range_update(x['CurrencyRange'], x['CurrenciesToUpdate'][1], min_max_dates)
            , axis=1)

        # Update Currency
        df['Currency'] = df.apply(
            lambda x: x['Currency'] if str(x['CurrenciesToUpdate']) == 'nan' else x['CurrenciesToUpdate'][1],
            axis=1)

        # Drop 'CurrenciesToUpdate'.
        df.drop('CurrenciesToUpdate', 1, inplace=True)

        # Sort Transitions
        df['Transitions'] = df['Transitions'].map(lambda x: sorted(x, key=lambda y: y[2]) if str(x) != 'nan' else x)

        return df

    def _currency_options(self, min_max_dates):
        """

        *Private Method*
        Function to construct a dataframe of currencies for which EasyMoney has data on.

        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which which data is available will be reported.
        :type min_max_dates: bool
        :return: DataFrame with all the currencies for which EasyMoney has data.
        :rtype: ``Pandas DataFrame``
        """
        # Initialize
        all_date_ranges = None
        eur_row_dates = None

        # Make a currency code of possible currency codes
        currency_ops = pd.DataFrame(self.currency_codes, columns=["Currency"])

        # Make the Alpha2 Column
        currency_ops['Alpha2'] = currency_ops["Currency"].replace(
            dict_merge(self.currency_to_alpha2, ecb_currency_to_alpha2_dict))

        # Make the Alpha3 and Region Columns
        currency_ops['Alpha3'] = currency_ops["Alpha2"].replace(self.alpha2_to_alpha3)
        currency_ops['Region'] = currency_ops["Alpha2"].replace(self.alpha2_to_region)

        # Reorder columns
        currency_ops = currency_ops[['Region', 'Currency', 'Alpha2', 'Alpha3']]

        # Add date information
        def currency_ex_dict_lookup(x, min_max_dates):
            try:
                return min_max(self.currency_ex_dict[x]) if min_max_dates else sorted(self.currency_ex_dict[x])
            except:
                return np.NaN

        # Create Date Range Column
        currency_ops['CurrencyRange'] = currency_ops['Currency'].map(
            lambda x: currency_ex_dict_lookup(x, min_max_dates))

        if min_max_dates:
            all_date_ranges = np.array(currency_ops['CurrencyRange'].tolist())
            eur_row_dates = [min(all_date_ranges[:, 0]), max(all_date_ranges[:, 1])]
        else:
            eur_row_dates = sorted(set([i for s in currency_ops['CurrencyRange'].tolist() for i in s]))

        eur_row = pd.DataFrame({'Region': 'Euro', 'Currency': 'EUR', 'Alpha2': np.nan, 'Alpha3': np.nan,
                                'CurrencyRange': [eur_row_dates]}, index=[0], columns=currency_ops.columns.tolist())

        # Append the Europe Row
        currency_ops = currency_ops.append(eur_row, ignore_index=True)

        # Sort by Region
        currency_ops.sort_values(['Region'], ascending=[1], inplace=True)

        # Correct Index
        currency_ops.reset_index(drop=True, inplace=True)

        # Remove Duplicates
        currency_ops_no_dups = self._currency_duplicate_remover(currency_ops)

        return self._currency_transition_integrator(  currency_ops
                                                    , currency_ops_no_dups[0]
                                                    , currency_ops_no_dups[1]
                                                    , min_max_dates)

    def _inflation_options(self, min_max_dates):
        """

        *Private Method*
        Determines the inflation (CPI) information cached.
        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which which data is available will be reported.
        :type min_max_dates: bool
        :return: a dataframe with all CPI information EasyMoney has, as well as date ranges the date exists for.
        :rtype: ``Pandas DataFrame``
        """
        # Initialize
        cpi_dict_years = None

        cpi_ops = self.ConsumerPriceIndexDB[['Country', 'Currency', 'Alpha2', 'Alpha3']].drop_duplicates()
        cpi_ops.columns = ['Region', 'Currency', 'Alpha2', 'Alpha3']
        cpi_ops.index = range(cpi_ops.shape[0])

        dates_dict = {k: sorted(str_to_datetime(v.keys(), "%Y")) for k, v in self.cpi_dict.items()}

        if min_max_dates:
            cpi_dict_years = dict((k, str(min_max([i.year for i in v]))) for k, v in dates_dict.items())
        else:
            cpi_dict_years = dict((k, str([i.year for i in v])) for k, v in dates_dict.items())

        # Hacking the living daylights out of the pandas API
        cpi_ops['InflationRange'] = pandas_dictkey_to_key_unpack(cpi_ops['Alpha2'], cpi_dict_years)

        # Sort by Region and Return
        cpi_ops.sort_values(['InflationRange'], ascending = [1], inplace = True)

        # Correct Index
        cpi_ops.index = range(cpi_ops.shape[0])

        return cpi_ops

    def _date_overlap_calc(self, list_a, list_b):
        """

        *Private Method*
        Tool to work out the the min and max date shared between two lists. Min date will be 'floored' and max date
        will be 'ceilinged'. See ``date_bounds_floor()``.

        :param list_a: of list of numerics
        :type list_a: list
        :param list_b: of list of numerics
        :type list_b: list
        :return: in pseudocode: [floor_date(min), ceiling_date(max)]
        :rtype: ``list``
        """
        return date_bounds_floor([min_max(list_a, True), min_max(list_b, True)])

    def _currency_inflation_options(self, min_max_dates):
        """

        *Private Method*
        Exchange Rate and Inflation information merged together.

        :param min_max_dates:
        :type min_max_dates: bool
        :return: a DataFrame with both Currency and Inflation information
        :rtype: ``Pandas DataFrame``
        """
        # Column Order
        col_order = ['Region', 'Currency', 'Alpha2', 'Alpha3', 'InflationRange', 'CurrencyRange', 'Overlap', 'Transitions']

        # Generate the Currency Options
        currency_ops_df = self._currency_options(min_max_dates)

        # Generate the Inflation Options
        cpi_ops_df = self._inflation_options(min_max_dates)

        # Define only Columns to include in currency_ops_df when merging
        currency_cols = (currency_ops_df.columns.difference(cpi_ops_df.columns)).tolist() + ['Alpha2']

        # Merge on Inflation options
        df = pd.merge(cpi_ops_df, currency_ops_df[currency_cols], on='Alpha2', how='left')

        # Determine the Overlap in dates between CPI and Exchange
        df['Overlap'] = df.apply(lambda row: self._date_overlap_calc(row['InflationRange'], row['CurrencyRange']), axis=1)

        # Sort by mapping
        df['TempSort'] = df['CurrencyRange'].map(lambda x: 'A' if str(x) != 'nan' else 'B')

        # Apply sorting
        df.sort_values(['TempSort', 'Region'], ascending=[1, 1], inplace=True)

        # Drop the Sorting Column
        df.drop('TempSort', axis=1, inplace=True)

        # Refresh the index
        df.reset_index(drop=True, inplace=True)

        # Overlap, Add Base Currency and Non Overlap
        overlap_subset = df[df['Overlap'].astype(str) != 'nan']
        base_cur_row = currency_ops_df[currency_ops_df['Region'] == 'Euro']
        non_overlap_subset = df[df['Overlap'].astype(str) == 'nan']

        # Concat
        df = pd.concat([overlap_subset, base_cur_row, non_overlap_subset], ignore_index=True, axis=0)

        # Reorder Columns
        return df[col_order]

    def _list_option(self, info):
        """

        *Private Method*
        Generates a list of 'exchange' (Currency Codes) and 'inflation' (CPI) references EasyMoney Understands.

        :param info: 'exchange' for exchange rate; 'inflation' for inflation information; 'all' for both.
        :type info: str
        :return: a list of 'exchange' (currency codes) or 'inflation' (regions) EasyMoney recognizes.
        :rtype: ``list``
        :raises ValueError: if info is not either 'exchange' or 'inflation'.
        """
        if info == 'exchange':
            return sorted(self.currency_codes + ['EUR'])
        elif info == 'inflation':
            return sorted([i for i in self.ConsumerPriceIndexDB['Alpha2'].unique().tolist() if isinstance(i, str)])
        elif info == 'all':
            raise ValueError("Error in info: 'all' is only valid for when rformat is set to 'table'.")

    def _table_option(self, info, min_max_dates):
        """

        *Private Method*
        Wrapper for ``_currency_options()``

        :param info: 'exchange' for exchange rate; 'inflation' for inflation information; 'all' for both.
        :type info: str
        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which which data is available will be reported.
        :type min_max_dates: bool
        :return: DataFrame with the requested information
        :rtype: ``Pandas DataFrame``
        """
        # Initialize
        info_table = None

        if info == 'exchange':
            info_table = self._currency_options(min_max_dates)
        elif info == 'inflation':
            info_table = self._inflation_options(min_max_dates)
        elif info == 'all':
            info_table = self._currency_inflation_options(min_max_dates)

        return info_table

    def _table_pretty_print(self, info_table, min_max_dates):
        """

        *Private Method*
        Manipulations to pretty print the input DataFrame

        :param info_table:
        :type info_table: Pandas DataFrame
        :return:
        :rtype:
        """
        # Convert all lists into strings seperated by " : " if min_max else ", " (exclude Transitions column).
        info_table = prettify_all_pandas_list_cols(data_frame=info_table
                                                   , join_on=(" : " if min_max_dates else ", ")
                                                   , exclude=['Transitions']
                                                   , bracket_wrap=True)

        # Join Transitions on commas, regardless of min_max_dates.
        def transition_pretty_print_formater(t):
            return str(t[2]) + " (" + t[0] + " to " + t[1] + ")"

        if 'Transitions' in info_table.columns.tolist():
            info_table['Transitions'] = info_table['Transitions'].map(
                lambda x: ", ".join([transition_pretty_print_formater(t) for t in x]) if str(x) != 'nan' else x)

        # Replace nans with whitespace
        for col in info_table.columns:
            info_table[col] = info_table[col].map(
                lambda x: x if x != 'NAN' and str(x).lower().strip() != 'nan' else '')

        # Replace number indexes with empty strings.
        info_table.index = ['' for i in range(info_table.shape[0])]

        # Pretty print the table
        pandas_print_full(info_table)

    def _options_as_raw_dataframe(self, info_table):
        """

        *Private Method*
        Manipulations to return the dataframe for general use.

        :param info_table:
        :type info_table:
        :return:
        :rtype:
        """
        # Create a lambda to convert the InflationRange lists to lists of ints (from lists of strings).
        year_to_int = lambda x: np.NaN if 'nan' in str(x) else [[floater(i, False, True) for i in x]][0]

        # InflationRange --> list of ints
        if 'InflationRange' in info_table.columns:
            info_table['InflationRange'] = info_table['InflationRange'].map(year_to_int)

        # CurrencyRange and Overlap columns --> list of datetimes
        date_columns_in_table = [i for i in info_table.columns if i in ['CurrencyRange', 'Overlap']]

        # Convert to date_columns to datetimes
        if len(date_columns_in_table) > 0:
            for col in date_columns_in_table:
                info_table[col] = info_table[col].map(lambda x: np.NaN if str(x) == 'nan' else str_to_datetime(x))

        return info_table

    def options(self
                , info
                , rformat = 'table'
                , pretty_table = True
                , pretty_print = True
                , overlap_only = False
                , min_max_dates = True):
        """

        An easy interface to explore all of the terminology EasyMoney understands
        as well the dates for which data is available.

        :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table').
        :type info: str
        :param rformat: 'table' for a table or 'list' for just the currency codes, alone. Defaults to 'table'.
        :type rformat: str
        :param pretty_table: prettifies the options table. Defaults to True.
        :type pretty_table: bool
        :param pretty_print: if True, prints the list or table. If False, returns the list or table (as a Pandas DataFrame).
                             Defaults to True.
        :type pretty_print: bool
        :param overlap_only: when info is set to 'all', keep only those rows for which exchange rate and inflation data
                             overlap.
        :type overlap_only: bool
        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which data is available will be reported. Defaults to True.
        :type min_max_dates: bool
        :return: DataFrame of Currency Information EasyMoney Understands.
        :rtype: ``Pandas DataFrame``
        :raises ValueError: if

                            (a) rformat is not either 'list' or 'table' OR

                            (b) *overlap_only* is True while info is not 'all' and rformat is not 'table'.

        """
        # Initialize
        info_table = None
        list_options = None
        date_columns_in_table = None

        # Check options request
        if info not in ['exchange', 'inflation', 'all']:
            raise ValueError("'%' not recognized. Info must be one of 'exchange', 'inflation' or 'all'." % (info))

        # Check value suppled to rformat
        if rformat not in ['list', 'table']:
            raise ValueError("'%s' is an invalid setting for rformat.\nPlease use 'table' for a table (pandas dataframe)"
                             " or 'exchange' for the currency codes as a list.")

        # Check overlap_only has not been set to True inappropriately.
        if (overlap_only and info != 'all') or (overlap_only and rformat == 'list'):
            raise ValueError("overlap_only is only of utility when info = 'all' and rformat = 'table'.")

        # Generate a (sorted) list
        if rformat == 'list':
            list_options = self._list_option(info)
            return list_options if not pretty_print else print(list_options)

        # Generate a table
        elif rformat == 'table':

            # Generate Requested Table
            info_table = self._table_option(info, min_max_dates)

            # Limit to overlap, if requested
            if overlap_only == True: info_table.dropna(subset = ['Overlap'], how = 'all', inplace = True)

            # Print the full table or return
            if pretty_print:
                self._table_pretty_print(info_table, min_max_dates)
            elif not pretty_print:
                return self._options_as_raw_dataframe(info_table)






































