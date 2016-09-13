#!/usr/bin/env python3

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# Modules #
import sys
import datetime
import numpy as np
import pandas as pd

try:
    from fuzzywuzzy import process
except:
    pass

import warnings
from warnings import warn

from easymoney.support_money import datetime_to_str
from easymoney.support_money import floater
from easymoney.support_money import money_printer
from easymoney.support_money import str_to_datetime
from easymoney.support_money import year_from_string
from easymoney.data_navigation_tools import DataNavigator

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
    :param base_currency: a currency to use as the base currency. Defaults to 'EUR'.
    :type base_currency: str
    """


    def __init__(self
                 , database_path = None
                 , precision = 2
                 , fall_back = True
                 , fuzzy_match_threshold = None
                 , base_currency = 'EUR'):
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

        # Instantiate the class housing all required data and tools for exploring it.
        self.nav_data = DataNavigator(database_path=database_path, base_currency=base_currency)

        # Define Databases
        self.ISOAlphaCodesDB = self.nav_data.ISOAlphaCodesDB
        self.CurrencyTransitionDB = self.nav_data.CurrencyTransitionDB
        self.ExchangeRatesDB = self.nav_data.ExchangeRatesDB
        self.currency_codes = self.nav_data.currency_codes
        self.ConsumerPriceIndexDB = self.nav_data.ConsumerPriceIndexDB
        self.CurrencyRelationshipsDB = self.nav_data.CurrencyRelationshipsDB

        # Convert the ExchangeRatesDB to a dict for faster look up speed.
        self.exchange_dict = _exchange_rates_from_datafile(self.nav_data.ExchangeRatesDB)[0]

        # Natural name --> CurrencyTransitionDB Alpha2.
        self.transition_nat_alpha2 = dict(zip(self.CurrencyTransitionDB['CountryName'], self.CurrencyTransitionDB['Alpha2']))

        # OldCurrency --> CurrencyTransitionDB Alpha2.
        self.transition_old_cur_alpha2 = dict(zip(self.CurrencyTransitionDB['OldCurrency'], self.CurrencyTransitionDB['Alpha2']))

        # Alpha3 --> CurrencyTransitionDB Alpha2.
        self.transition_alpha3_alpha2 = dict(zip(self.CurrencyTransitionDB['Alpha3'], self.CurrencyTransitionDB['Alpha2']))

        # OldCurrency --> New Currency
        self.transition_old_new = dict(zip(self.CurrencyTransitionDB['OldCurrency'], self.CurrencyTransitionDB['NewCurrency']))

        # All Alpha2 codes in CurrencyTransitionDB.
        self.transition_alpha2 = self.CurrencyTransitionDB['Alpha2'].tolist()

        # Group TransitionTuples by their Alpha2 Code.
        ct_alpha2_group = self.CurrencyTransitionDB.groupby('Alpha2').apply(
            lambda x: x['TransitionTuples'].tolist()).reset_index()

        # All tuples of currency transitions, based on Alpha2 code.
        self.alpha2_transition_dict = dict(zip(ct_alpha2_group['Alpha2'], ct_alpha2_group[0]))

        # Generate a DataFrame of the year a currency was introduced.
        new_curs = self.CurrencyTransitionDB.groupby('NewCurrency').apply(lambda x: min(x['Date'].tolist())).reset_index()

        # Create a dict of the years currencies were introduced.
        self.currency_introduction_dict = dict(zip(new_curs['NewCurrency'], new_curs[0]))

        # Generate a DataFrame of the years old currencies were retired.
        old_curs = self.CurrencyTransitionDB.groupby('OldCurrency').apply(lambda x: min(x['Date'].tolist())).reset_index()

        # Create a dict of the years currencies were retired.
        self.currency_depreciated_dict = dict(zip(old_curs['OldCurrency'], old_curs[0]))

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
        best_match = sorted(list_of_dates, key=lambda date_in_list: abs(date - date_in_list))[0]

        if date_format == None:
            return best_match
        else:
            return datetime_to_str([best_match], date_format=date_format)[0]

    def _fuzzy_search(self, region, dictionary):
        """

        *Private Method*
        Use the fuzzywuzzy package to search for the keys' of a dictionary for the closest match to *region*
        and return the corresponding value.

        :param region: a string likely to be in the keys of the dictionary.
        :type region: str
        :param dictionary: the dictionary for to search they keys of.
        :type dictionary: dict
        :return: the value corresponding to they key that best matched *region*.
        :rtype: ``str``
        """
        # Precaution to block usage of fuzzywuzzy if it is not enabled.
        if self.fuzzy_match_threshold == None:
            return None

        # Try to get the best match for the region
        best_match = process.extractOne(region, dictionary.keys())

        # Return the best match if the confidence
        # is greater than, or equal to, fuzzy_match_threshold.
        if best_match[1] >= self.fuzzy_match_threshold:
            return dictionary[best_match[0]]
        else:
            return None

    def _currency_transition_handler(self, region, year, map_to):
        """

        *Private Method*
        Procedure:
        Check if the region is in the transition database.
            - if it is, work out its alpha2 code
                - Get the date in the transition dict which is closest
                    - if the date is < transition year, return t[0] else return t[1] of the TransitionTuple.
            - else:
                 return None

        Note: assumes a maximum of one transition per year.

        :param region: a 'region' in the format of a ISO Alpha2, ISO Alpha3 or currency code, as well as natural name.
        :type region: str
        :param year: any year
        :type year: int
        :return: currency, the type of input (i.e., whether an Alpha2/3 code, currency code or natural name).
        :rtype: str
        """
        # Initialize
        transitions= None
        transition_dates = None
        nearest_transition_year = None
        closest_match = None
        alpha2_mapping = None
        raw_region_type = None
        fuzzy_match = None

        # Extract year
        year = year_from_string(year)

        # Note: while ``_region_type()`` should be able to work out the Alpha2 code 99% of the time, to surmount
        # possible discrepancies between CurrencyTransitionDB and other DBs, its own account of the codes is used here.
        if region.upper() in self.transition_alpha2:
            alpha2_mapping, raw_region_type = region.upper(), 'alpha2'
        elif region.upper() in self.transition_alpha3_alpha2:
            alpha2_mapping, raw_region_type = self.transition_alpha3_alpha2[region.upper()], 'alpha3'
        elif region.upper() in self.transition_old_cur_alpha2:
            alpha2_mapping, raw_region_type = self.transition_old_cur_alpha2[region.upper()], 'currency'
        elif region in self.transition_nat_alpha2:
            alpha2_mapping, raw_region_type = self.transition_nat_alpha2[region], 'natural'
        else:
            return None, None

        # Return Alpha2 on request
        if map_to == 'alpha2':
            return alpha2_mapping, raw_region_type

        elif map_to == 'currency':

            # Obtain transition information
            transitions = self.alpha2_transition_dict[alpha2_mapping]

            # Get a numpy array of all transition dates
            transition_dates = np.array(sorted([t[2] for t in transitions]))

            # Work out the date of the nearest transition w.r.t. `year`.
            # Source: http://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
            nearest_transition_year = int(float(transition_dates.flat[np.abs(transition_dates - int(float(year))).argmin()]))

            # Closest Match
            closest_match = [m for m in transitions if m[2] == nearest_transition_year][0]

            if int(float(year)) < nearest_transition_year:
                return closest_match[0], raw_region_type
            else:
                return closest_match[1], raw_region_type

    def _fuzzy_region_type_matcher(self, region, year):
        """

        *Private Method*
        Uses ``_fuzzy_search()`` to try and match *region* to the keys in the
        transition_nat_alpha2 and nav_data.region_to_alpha2 dictionaries.

        :param region: a region (Alpha2, Alpha3, Natural Name or currency code).
        :type region: str
        :param year: any year.
        :type year: int
        :return: an alpha2 code
        :rtype: ``tuple``
        """
        # Initialize
        transition_db_attempt = None, None

        # Attempt to match with transition_nat_alpha2 data
        fuzzy_match = self._fuzzy_search(region, dictionary=self.transition_nat_alpha2)

        # If that works, try to return the alpha2 code
        if fuzzy_match != None:
            transition_db_attempt = self._currency_transition_handler(fuzzy_match, year, map_to='alpha2')
            if transition_db_attempt[0] != None:
                return transition_db_attempt[0], transition_db_attempt[1]  # more explict.

        # If First attempt failed to return, try to match on the more general data
        fuzzy_match = self._fuzzy_search(region, dictionary=self.nav_data.region_to_alpha2)

        # If a match was obtained with the more general data
        if fuzzy_match != None:
            return fuzzy_match, "natural"
        else:
            raise ValueError("Region Error. '%s' could not be matched to a known country. See options()." % (region))

    def _region_type(self, region, year):
        """

        *Private Method*
        Standardize Currency Code, Alpha3 and Natural Name (e.g., 'Canada') to Alpha2.

        :param region: a region (Alpha2, Alpha3, Natural Name or currency code).
        :type region: str
        :param year: any year
        :type year: int
        :return: ISO Alpha2 code.
        :rtype: ``str``
        :raises ValueError: if ``region`` is not recognized by EasyMoney (see ``options()``).
        """
        # Initialize
        currency_region = None
        fuzzy_match = None
        transition_db_attempt = None, None

        if not isinstance(region, str):
            raise TypeError("'%s' is not a string." % (str(region)))

        if region.upper() in ecb_currency_to_alpha2_dict.keys():
            return ecb_currency_to_alpha2_dict[region.upper()], "currency"

        elif region.upper() in self.nav_data.alpha3_to_alpha2.values():
            return region.upper(), "alpha2"

        elif region.upper() in self.nav_data.alpha3_to_alpha2.keys():
            return self.nav_data.alpha3_to_alpha2[region.upper()], "alpha3"

        elif region.upper() in self.nav_data.currency_to_alpha2.keys():
            currency_region = self.nav_data.currency_to_alpha2[region.upper()]
            if len(currency_region) == 1: return currency_region[0], "currency"
            else:
                raise ValueError("'%s' is used in several countries thus cannot be mapped to a single nation." % (region))

        elif region.lower().title() in self.nav_data.region_to_alpha2.keys():
            return self.nav_data.region_to_alpha2[region.lower().title()], "natural"

        elif self.fuzzy_match_threshold != None:
            return self._fuzzy_region_type_matcher(region, year)

        else:
            raise ValueError("Region Error. '%s' is not recognized by EasyMoney. See options()." % (region))

    def _currency_existence_checker(self, currency, year, return_bool = False):
        """

        *Private Method*
        Tool to check if a currency existed in a given year.
        If currency is not in ``CurrencyTransitionDB``, this is *assumed* to be true.

        :param currency: any currency
        :type currency: str
        :param year: a year to check if the currency existed
        :type year: int
        :param return_bool: if True, return if the currency Existed (True) or if it did not (False). Defaults to False.
        :type return_bool: bool
        :raises ValueError: if

                                (a) the currency was retired prior to *year*.

                                (b) the currency was not yet introduced in *year*.
        """
        # Extract year
        year = year_from_string(year)

        if currency.upper() in self.currency_depreciated_dict:
            if year >= self.currency_depreciated_dict[currency.upper()]:
                if return_bool:
                    return False
                warn("'%s' is not valid in %s as it was replaced by '%s' in %s.\nPlease see options()." % \
                    (currency, str(year), self.transition_old_new[currency.upper()]
                     , self.currency_depreciated_dict[currency.upper()]))

        if currency.upper() in self.currency_introduction_dict:
            if year < self.currency_introduction_dict[currency.upper()]:
                if return_bool:
                    return False
                warn("'%s' is not valid in %s as it was introduced in %s.\nPlease see options()." % \
                     (currency, str(year), self.currency_introduction_dict[currency.upper()]))

        # Assume True
        if return_bool:
            return True

    def region_map(self, region, map_to = 'alpha2', return_region_type = False, year = 'latest'):
        """

        Map a 'region' to any one of: ISO Alpha2, ISO Alpha3 or Currency Code as well as its Natural Name.

            Examples Converting From Currency:
                - ``EasyPeasy().region_map(region='CAD', map_to='alpha2')``   :math:`=` 'CA'
                - ``EasyPeasy().region_map(region='CAD', map_to='alpha3')``   :math:`=` 'CAN'

            Examples Converting From Alpha2:
                - ``EasyPeasy().region_map(region='FR', map_to='currency')`` :math:`=` 'EUR'
                - ``EasyPeasy().region_map(region='FR', map_to='natural')``  :math:`=` 'France'

        :param region: a 'region' in the format of a ISO Alpha2, ISO Alpha3 or currency code, as well as natural name.
        :type region: str
        :param map_to: 'alpha2', 'alpha3' 'currency' or 'natural' for ISO Alpha2, ISO Alpha2, Currency Code and
                        Natural Names, respectively. Defaults to 'alpha2'.
        :type map_to: str
        :param return_region_type: if True return the type of input supplied (one of:'alpha2', 'alpha3' 'currency' or
                                   'natural'). Defaults to False.
        :type return_region_type: bool
        :param year: Defaults to 'latest' (which will use the current year).
        :type year: int
        :return: the desired mapping from region to ISO Alpha2.
        :rtype: ``str`` or ``tuple``
        :raises ValueError: if *map_to* is not one of 'alpha2', 'alpha3', 'currency' or 'natural'.

        .. warning::
            Attempts to map common currencies to a single nation will fail.


            For instance, ``EasyPeasy().region_map(region = 'EUR', map_to = 'alpha2')`` will fail because the Euro (EUR)
            is used in several nations and thus a request to map it to a single ISO Alpha2 country code creates
            insurmountable ambiguity.
        """
        # Initialize
        mapping = None
        alpha2_mapping = None
        raw_region_type = None
        transition_mapping = None

        # If region is a currency, check if it existed in *year*.
        self._currency_existence_checker(currency=region, year=year)

        # Check that map_to is valid.
        if map_to not in ['alpha2', 'alpha3', 'currency', 'natural']:
            raise ValueError("map_to must be one of: 'alpha2', 'alpha3', 'currency' or 'natural'.")

        # Seperately handle requests for map_to == 'currency' when 'region' is a currency used by several nations.
        # This code break with some currency transitions, e.g., country leaving a common currency.
        if region.upper() in self.nav_data.currency_to_alpha2.keys() and len(self.nav_data.currency_to_alpha2[region.upper()]) > 1:
            if map_to == 'currency':
                return region.upper()
            else:
                raise ValueError("The '%s' currency is used in multiple nations and thus cannot be mapped to a single one." \
                 % (region))

        # Seperately handle currency transitions.
        if map_to == 'currency':
            transition_mapping = self._currency_transition_handler(region, year, 'currency')
            if transition_mapping[0] != None:
                return transition_mapping if return_region_type else transition_mapping[0]
        else:
            transition_mapping = self._currency_transition_handler(region, year, 'alpha2')
            if transition_mapping[0] != None:
                alpha2_mapping, raw_region_type = transition_mapping

        # Use _region_type() if _currency_transition_handler only returned None.
        if transition_mapping[0] == None:
            alpha2_mapping, raw_region_type = self._region_type(region, year)

        # Return iso code (alpha2 or 3), currency code or natural name
        if map_to == 'alpha2':
            mapping = alpha2_mapping
        elif map_to == 'alpha3':
            mapping = self.nav_data.alpha2_to_alpha3[alpha2_mapping]
        elif map_to == 'currency':
            mapping = self.nav_data.alpha2_to_currency[alpha2_mapping]
        elif map_to == 'natural':
            mapping = self.nav_data.alpha2_to_region[alpha2_mapping]

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
        inflation_error_message = "EasyMoney could not obtain inflation (CPI) information for '%s' in '%s'." % \
                                  (str(region), str(year))

        # convert region to alpha2
        cpi_region = self.region_map(region, 'alpha2', year=year)

        # Get most recent CPI year available
        if cpi_region not in self.nav_data.cpi_dict.keys():
            raise LookupError("Could not find inflation information for '%s'." % (str(region)))

        # Get the max year for which CPI information is available
        max_cpi_year = str(int(max([float(i) for i in self.nav_data.cpi_dict[cpi_region].keys()])))

        if float(year) > float(max_cpi_year):
            if self.fall_back:
                try:
                    cpi = floater(self.nav_data.cpi_dict[cpi_region][str(int(float(max_cpi_year)))]) # add Error handling?
                    warn("Could not obtain required inflation (CPI) information for '%s' in %s."
                                  " Using %s instead." % \
                                  (self.region_map(region, 'natural', year=year), str(int(float(year))), max_cpi_year))
                except:
                    raise LookupError(inflation_error_message)
            else:
                raise AttributeError(inflation_error_message)
        else:
            try:
                cpi = floater(self.nav_data.cpi_dict[cpi_region][str(int(float(year)))])
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
        :param year_b: end year. Defaults to None -- can only be left to this default if *return_raw_cpi_dict* is True.
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
        c1 = self._try_to_get_CPI(self.region_map(region, 'alpha2', year=year_b), year_b) if year_b != None else None
        c2 = self._try_to_get_CPI(self.region_map(region, 'alpha2', year=year_a), year_a)

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

        # Compute the rate of Inflation (and round).
        rate = round(((c1 - c2) / float(c2)) * 100, self.round_to)

        # Return or Pretty Print.
        if not pretty_print:
            return rate
        else:
            print(rate, "%")

    def inflation_calculator(self, amount, region, year_a, year_b, pretty_print = False):
        """

        Adjusts a given amount of money for inflation.

        :param amount: a monetary amount.
        :type amount: float or int
        :param region: a geographical region.
        :type region: str
        :param year_a: start year.
        :type year_a: int
        :param year_b: end year.
        :type year_b: int
        :param pretty_print: if True, pretty prints the result otherwise returns the result as a float.
                             Defaults to False.
        :type pretty_print: bool
        :return: :math:`amount \cdot inflation \space rate`.
        :rtype: ``float``
        :raises ValueError: if  year_a occurs after year_b.
        :raises KeyError: if inflation (CPI) information cannot be found in the inflation database.
        """
        # Input checking
        if floater(year_a) == floater(year_b):
            return round(amount, self.round_to)

        # Get the CPI information
        inflation_dict = self.inflation_rate(region
                                             , int(float(year_a))
                                             , int(float(year_b))
                                             , return_raw_cpi_dict=True)

        # Check all the values are floats
        if not all([floater(x, just_check=True) for x in inflation_dict.values()]):
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
                           (self.region_map(region, map_to='natural'), e))

        # Return or Pretty Print.
        if not pretty_print:
            return round(adjusted_amount, self.round_to)
        else:
            money_printer(adjusted_amount, self.region_map(region, 'currency', year=year_b), round_to=self.round_to)

    def _base_cur_to_lcu(self, currency, date = "latest", return_max_date = False, date_format = "%Y-%m-%d"):
        """

        *Private Method*
        Convert from a base currency (Euros if using ECB data) to a local currency unit, e.g., CAD.

        :param currency: a currency code or region
        :type currency: str
        :param date: MUST be of the form: ``YYYY-MM-DD`` OR ``YYYY``; defaults to "latest".

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

        # Block self-conversion
        if currency == "EUR" and return_max_date == False:
            return 1.0
        elif currency == "EUR" and date == 'latest' and return_max_date == True:
            return str(max(self.exchange_dict.keys()))

        # Get the current date
        if date == "latest":
            try:
                date_key_list = [k for k, v in self.exchange_dict.items() if currency in v.keys()]
            except:
                raise AttributeError(error_msg)
            if len(date_key_list) > 0:
                date_key = str(max(date_key_list))
            else:
                raise ValueError(error_msg)
            if return_max_date:
                return date_key
        else:
            if floater(date, just_check=True) and len(str(date).strip()) == 4:
                # Compute the average conversion rate over the whole year
                return np.mean([v[currency] for k, v in self.exchange_dict.items()
                                if currency in v and str(str_to_datetime(k).year) == str(date)])
            elif date in self.exchange_dict.keys():
                date_key = date
            elif date not in self.exchange_dict.keys():
                date_key = self._closest_date(list_of_dates=[str_time(d, date_format) for d in self.exchange_dict.keys()]
                                              , date=str_time(date, date_format)
                                              , problem_domain='exchange rate'
                                              , date_format=date_format)
                warn("\nExchange rate information for '%s' could not be obtained on '%s'; %s was used instead." % \
                     (currency, date, date_key))

        # Return the exchange rate on a given date
        return self.exchange_dict[date_key][currency.upper()]

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

            .. math:: LCU(\phi_{EUR}, CUR) = \dfrac{x \space \space CUR}{1 \space EUR}

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
        from_currency_fn = self.region_map(from_currency, "currency", year=date)

        # Correct to_currency
        to_currency_fn = self.region_map(to_currency, "currency", year=date)

        # Return amount unaltered if self-conversion was requested.
        if not pretty_print and from_currency_fn == to_currency_fn:
            return round(amount, self.round_to)

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
        rounded_amount = round(float(converted_amount), self.round_to)

        # Return results (or pretty print)
        if not pretty_print:
            return rounded_amount
        else:
            money_printer(rounded_amount, self.region_map(to_currency, 'currency', year=date), round_to=self.round_to)

    def normalize(self
                  , amount
                  , currency
                  , from_year
                  , to_year = "latest"
                  , base_currency = "EUR"
                  , exchange_date = None
                  , pretty_print = False):
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
                            *exchange_date* is left to its default (None), the *average* exchange rate for *to_year*
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
        old_data_warning = 2 # i.e., if the data >= 2 years old, issue a warning.

        # Standardize currency input
        from_currency = self.region_map(currency, 'currency', year=from_year)

        # Determine Alpha2 country code
        from_region = self.region_map(currency, 'alpha2', year=from_year)

        # Ensure base_currrency is a valid currency code
        to_currency = self.region_map(base_currency, 'currency', year=to_year)

        # Determine to CPI Data
        cpi_record = self.ConsumerPriceIndexDB[(self.ConsumerPriceIndexDB['Alpha2'] == from_region) & (~pd.isnull(self.ConsumerPriceIndexDB['CPI']))]
        if cpi_record.shape[0] != 0:
            most_recent_cpi_record = cpi_record['Year'].max()
        else:
            raise ValueError("'%s' cannot be mapped to a specific region, and thus inflation cannot be determined." % \
                             (currency))

        if to_year != "latest" and float(to_year) < float(most_recent_cpi_record):
            if floater(to_year, just_check=True):
                inflation_year_b = int(float(to_year))
            else:
                raise ValueError("to_year invalid; '%s' is not numeric (intiger or float).")
        elif to_year != "latest" and float(to_year) > float(most_recent_cpi_record):
            raise ValueError("No data available for '%s' in %s. Try %s or earlier." % \
                             (currency, str(to_year), str(most_recent_cpi_record)))
        else:
            inflation_year_b = most_recent_cpi_record
            if float(inflation_year_b) <= (datetime.datetime.now().year - old_data_warning):
                warn("Inflation information not available for '%s', using %s." % (to_year, inflation_year_b))

        # Adjust input for inflation
        currency_adj_inflation = self.inflation_calculator(amount, from_region, from_year, inflation_year_b)

        # Convert into the base currency
        adjusted_amount = self.currency_converter(amount=currency_adj_inflation
                                                  , from_currency=currency
                                                  , to_currency=base_currency
                                                  , date=(to_year if exchange_date == None else exchange_date))

        # Return or Pretty Print
        if not pretty_print:
            return round(float(adjusted_amount), self.round_to)
        else:
            money_printer(adjusted_amount
                          , self.region_map(to_currency
                                            , 'currency'
                                            , year=(to_year if exchange_date == None else exchange_date))
                          , round_to=self.round_to)

    def options(self
                , info
                , rformat = 'table'
                , pretty_print = True
                , overlap_only = False
                , min_max_dates = True
                , convert_to_datetimes = False):
        """

        An easy interface to explore all of the terminology EasyMoney understands
        as well the dates for which data is available.

        :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table').
        :type info: str
        :param rformat: 'table' for a table or 'list' for just the currency codes, alone. Defaults to 'table'.
        :type rformat: str
        :param pretty_print: if True, prints the list or table. If False, returns the list or table (as a Pandas DataFrame).
                             Defaults to True.
        :type pretty_print: bool
        :param overlap_only: when info is set to 'all', keep only those rows for which exchange rate and inflation data
                             overlap.
        :type overlap_only: bool
        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which data is available will be reported. Defaults to True.
        :type min_max_dates: bool
        :param convert_to_datetimes: If True, converts all date information to datetimes.
                                     Note: Years, with no day or month information, will remain as ints.
                                     Defaults to False.
        :type convert_to_datetimes: bool
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
            raise ValueError("'%s' is an invalid setting for rformat.\nPlease use 'table' for a table (Pandas DataFrame)"
                             " or 'list' for the currency codes as a list.")

        # Check overlap_only is applicable.
        if (overlap_only and info != 'all') or (overlap_only and rformat == 'list'):
            raise ValueError("overlap_only is only of utility when info is 'all' and rformat is 'table'.")

        # Check convert_to_datetimes is applicable.
        if convert_to_datetimes and rformat != 'table' and pretty_print != False:
            raise ValueError("convert_to_datetimes is only of utility when rformat is 'all' and pretty_print is False.")

        # Generate a (sorted) list
        if rformat == 'list':
            list_options = self.nav_data._list_option(info)
            return list_options if not pretty_print else print(list_options)

        # Generate a table
        elif rformat == 'table':

            # Generate Requested Table
            info_table = self.nav_data._table_option(info, min_max_dates)

            # Limit to overlap, if requested
            if overlap_only == True: info_table.dropna(subset=['Overlap'], how='all', inplace=True)

            # Print the full table or return
            if pretty_print:
                self.nav_data._table_pretty_print(info_table, min_max_dates)
            elif not pretty_print:
                return self.nav_data._options_as_raw_dataframe(info_table, convert_to_datetimes)




































