#!/usr/bin/env python3

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""

# Functionality to add:
#   - options

# Imports
import pycountry
import numpy as np
import pandas as pd

from warnings import warn
from datetime import datetime

from easymoney.support_tools import mint
from easymoney.support_tools import min_max_dates
from easymoney.pycountry_wrap import PycountryWrap
from easymoney.sources.world_bank_interface import world_bank_pull_wrapper
from easymoney.sources.ecb_interface import ecb_xml_exchange_data


class EasyPeasy(object):
    """

    """

    def __init__(self, round_to=2, fall_back=True, curr_path=''):
        self.round_to = round_to
        # self.fall_back = fall_back
        self.pycountry_wrap = PycountryWrap(curr_path)
        self.cpi_dict = world_bank_pull_wrapper(return_type='dict')
        self.exchange_dict = ecb_xml_exchange_data('dict')[0]
        self.exchange_date_range = min_max_dates(list_of_dates=list(self.exchange_dict.keys()))

    def _params_check(self, amount, pretty_print):
        """

        :param amount:
        :param pretty_print:
        :return:
        """
        # Check amount is float
        if not isinstance(amount, (float, int)):
            raise ValueError("amount must be numeric (intiger or float).")

        # Check pretty_print is a bool
        if not isinstance(pretty_print, bool):
            raise ValueError("pretty_print must be either True or False.")

    def region_map(self, region, map_to='alpha_2'):
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
        :param map_to: 'alpha_2', 'alpha_3' 'name' or 'offical_name'. Defaults to 'alpha_2'.
        :type map_to: str
        :return: the desired mapping from region to ISO Alpha2.
        :rtype: ``str`` or ``tuple``

        .. warning::
            Attempts to map common currencies to a single nation will fail.


            For instance, ``EasyPeasy().region_map(region = 'EUR', map_to = 'alpha2')`` will fail because the Euro (EUR)
            is used in several nations and thus a request to map it to a single ISO Alpha2 country code creates
            insurmountable ambiguity.
        """
        return self.pycountry_wrap.map_region_to_type(region=region, extract_type=map_to)

    def _cpi_years(self, region):
        """

        Get Years for which CPI information is available for a given region.

        :param region:
        :return:
        """
        cpi_years_list = list()
        for year in sorted(list(self.cpi_dict.keys()), reverse=True):
            cpi = self.cpi_dict.get(year, None).get(region, None)
            if not isinstance(cpi, type(None)):
                cpi_years_list.append(year)

        if len(cpi_years_list):
            return cpi_years_list
        else:
            raise KeyError("Could not obtain inflation (CPI) information for '%s." % (region))

    def _cpi_match(self, region, year):
        """

        :param region:
        :param year:
        :return:
        """
        # replace year_b if it is 'oldest' or 'latest'
        year_bounds = [int(float(func(self._cpi_years(region)))) for func in (min, max)]

        if year == 'oldest':
            return year_bounds[0]
        elif year == 'latest':
            return year_bounds[1]
        elif float(year) < year_bounds[0]:
            warn("Inflation (CPI) data for %s in '%s' could not be obtained. Falling back to %s." % (year, region, int(year_bounds[0])))
            return year_bounds[0]
        elif float(year) > year_bounds[1]:
            warn("Inflation (CPI) data for %s in '%s' could not be obtained. Falling back to %s." % (year, region, int(year_bounds[1])))
            return year_bounds[1]
        else:
            return year

    def _cpi_region_year(self, region, year):
        cpi = self.cpi_dict.get(str(int(float(year))), {}).get(self.region_map(region, 'alpha_2'), None)
        if cpi is not None:
            return float(cpi)
        else:
            raise KeyError("Could not obtain inflation information for '%s' in '%s'." % (str(region), str(year)))

    def inflation(self, region, year_a, year_b=None, return_raw_cpi_dict=False, pretty_print=False):
        """
        """
        # Check Params
        # self._params_check(amount, pretty_print)

        # Map Region
        mapped_region = self.region_map(region, 'alpha_2')

        # Set to_year
        to_year = self._cpi_match(mapped_region, year_b) if year_b is not None else None

        # Set from_year
        if year_a is not None:
            from_year = self._cpi_match(mapped_region, year_a)
        else:
            raise ValueError("year_a cannot be NoneType.")

        # Get the CPI for to_year and year_a
        c1 = self._cpi_region_year(mapped_region, to_year) if to_year is not None else None
        c2 = self._cpi_region_year(mapped_region, from_year)

        # Return dict, if requested
        if return_raw_cpi_dict != False:
            d = dict(zip(filter(None, [to_year, from_year]), filter(None, [c1, c2])))
            if return_raw_cpi_dict == 'complete':
                return d, {"year_a": from_year, "year_b": to_year}
            elif return_raw_cpi_dict == True:
                return d

        # Compute the rate of Inflation (and round).
        if (any([pd.isnull(c1), pd.isnull(c2)])) or (c2 == 0.0):
            return np.NaN
        else:
            rate = round(((c1 - c2) / float(c2)) * 100, self.round_to)

        # Return or Pretty Print.
        return rate if not pretty_print else print(rate, "%")

    def inflation_calculator(self, amount, region, year_a, year_b, pretty_print=False):
        """

        Adjusts a given amount of money for inflation.
        """
        # Check Params
        self._params_check(amount, pretty_print)

        # Input checking
        if year_a == year_b:
            return round(amount, self.round_to)

        # Get the CPI information
        inflation_dict, years = self.inflation(region, year_a, year_b, return_raw_cpi_dict='complete')

        # Block division by zero
        if inflation_dict[years['year_a']] == 0:
            warn("Problem obtaining required inflation information.")
            return np.NaN

        # Scale w.r.t. inflation.
        adjusted_amount = inflation_dict[years['year_b']] / float(inflation_dict[years['year_a']]) * amount

        # Print or Return
        return mint(adjusted_amount, currency=self.region_map(region, map_to='currency_alpha_3'), pretty_print=pretty_print)

    def _user_currency_input(self, currency_or_region):
        """

        :param currency_or_region:
        :return:
        """
        try:
            return pycountry.currencies.lookup(currency_or_region).alpha_3
        except:
            return self.region_map(currency_or_region, "currency_alpha_3")

    def _base_cur_to_lcu(self, currency, date):
        """

        :param currency:
        :param date:
        :return:
        """
        # Handle Base Currency
        if currency.upper() == 'EUR':
            return 1.0

        # Set Date for the Exchange -- Improve (this assumes uniformity in dates and currencies).
        if date == 'oldest':
            exchange_date = self.exchange_date_range[0]
        elif date == 'latest':
            exchange_date = self.exchange_date_range[1]
        elif isinstance(date, str) and date.count("/") == 2: # improve
            exchange_date = date
        else:
            raise ValueError("Invalid Date Passed. Dates must be of the form DD/MM/YYYY.")

        exchange_rate = exchange_dict.get(exchange_date, None).get(currency, None)
        if not isinstance(exchange_rate, type(None)):
            return exchange_rate
        else:
            msg = "Could not obtain the exchange rate for %s on %s from the European Central Bank." % (currency, exchange_date)
            raise AttributeError(msg)

    def currency_converter(self, amount, from_currency, to_currency, date="latest", pretty_print=False):
        """
        """
        # Check Params
        self._params_check(amount, pretty_print)

        # to/from_currency --> Alpha 3 Currency Code
        to_currency_fn, from_currency_fn = (self._user_currency_input(arg) for arg in (to_currency, from_currency))

        # Return amount unaltered if self-conversion was requested.
        if from_currency_fn == to_currency_fn:
            return mint(amount, currency=to_currency_fn, pretty_print=pretty_print)

        # from_currency --> Base Currency --> to_currency
        conversion_to_invert = self._base_cur_to_lcu(from_currency_fn, date)
        if conversion_to_invert == 0.0:
            raise ZeroDivisionError("Cannot converted from '%s' on %s." % (from_currency, date))
        converted_amount = conversion_to_invert ** -1 * self._base_cur_to_lcu(to_currency_fn, date) * float(amount)

        # Return results (or pretty print)
        return mint(round(converted_amount, self.round_to), currency=to_currency_fn, pretty_print=pretty_print)

    def normalize(self
                  , amount
                  , region
                  , from_year
                  , to_year="latest"
                  , base_currency="EUR"
                  , exchange_date="latest"
                  , pretty_print=False):
        """

        """
        # Check Params
        self._params_check(amount, pretty_print)

        # Adjust input for inflation
        real_amount = self.inflation_calculator(amount, region, year_a=from_year, year_b=to_year)

        # Compute Exchange
        normalize_amount = self.currency_converter(real_amount, region, base_currency, date=exchange_date)

        # Return results (or pretty print)
        return mint(round(normalize_amount, self.round_to), self._user_currency_input(base_currency), pretty_print)






















