#!/usr/bin/env python3

'''

Money Conversions
~~~~~~~~~~~~~~~~~

Python 3.5

'''

# Modules #
import os
import wbdata
import datetime
import warnings
import datetime
import numpy as np
import pandas as pd
import pkg_resources
from statistics import mean

from easy_money.support_money import twoD_nested_dict, floater, dict_key_remove, money_printer
from easy_money.ecb_interface import _ecb_exchange_data
from easy_money.world_bank_interface import WorldBankParse, world_bank_pull_wrapper


DATA_PATH = pkg_resources.resource_filename('easy_money', 'data')


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


    def __init__(self, precision = 2):
        """

        :param precision: number of places to round to
        """

        # Places of precision
        self.round_to = precision

        # Get CPI Data
        self.cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")

        # Create CPI dict
        self.cpi_dict = twoD_nested_dict(self.cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

        # Get Exchange rate Data
        self.ex_dict = _ecb_exchange_data('dict')
        #sorted_exchange_dates = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in sorted(self.ex_dict.keys())]
        self.ex_dict_keys_series = pd.Series(sorted(list(self.ex_dict.keys())))

        # Import EU join Data
        eu_join = pd.read_csv(DATA_PATH + "/JoinEuro.csv")
        self.eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))

        alpha2_alpha3_df = pd.read_csv(DATA_PATH + "/CountryAlpha2_and_3.csv")

        # Create Alpha3 --> Alpha2 Dict
        self.alpha3_to_alpha2 = dict_key_remove(dict(zip(alpha2_alpha3_df.Alpha3, alpha2_alpha3_df.Alpha2)))

        # Create Alpha2 --> Alpha3 Dict
        self.alpha2_to_alpha3 = dict([(v, k) for k, v in self.alpha3_to_alpha2.items()])

        # Create Currency --> Alpha2 Dict
        self.currency_to_alpha2 = dict_key_remove(dict(zip(self.cpi_df.currency_code, self.cpi_df.alpha2)))

        # Create Alpha2 --> Currency
        self.alpha2_to_currency = dict([(v, k) for k, v in self.currency_to_alpha2.items()])

        # Create Region Name --> Alpha2 Dict
        self.region_to_alpha2 = dict_key_remove(dict(zip(self.cpi_df.region, self.cpi_df.alpha2)))

        # Create Alpha2 --> Region Name Dict
        self.alpha2_to_region = dict([(v, k) for k, v in self.region_to_alpha2.items()])

    def _closest_date(self, list_of_dates, date):
        """

        :param list_of_dates:
        :param date:
        :return:
        """

        # Ensure dates are of type datetime
        if False in [isinstance(i, datetime.datetime) for i in list_of_dates]:
            raise ValueError("Dates must be of type: datetime.datetime")

        # Return best match
        return sorted(list_of_dates, key = lambda date_in_list: abs(date - date_in_list))[0]

    def _region_type(self, region):
        """

        :param region:
        :return:
        """

        if region in self.alpha3_to_alpha2.values():
            return region, "alpha2"
        elif region in self.alpha3_to_alpha2.keys():
            return self.alpha3_to_alpha2[region], "alpha3"
        elif region in self.currency_to_alpha2.keys():
            return self.currency_to_alpha2[region], "currency"
        elif region.lower().title() in self.region_to_alpha2.keys():
            return self.region_to_alpha2[region.lower().title()], "natural_name"
        else:
            raise ValueError("Region Error. '%s' is not recognized." % (region))

    def _iso_mapping(self, region, map_to = 'alpha2'):
        """

        :param region: a region as denoted by a 'alpha2', 'alpha3' or 'currency'
        :param map_to: 'alpha2', 'alpha3' or 'currency'
        :return:
        """

        # Determine region type
        alpha2_mapping, raw_region_type = self._region_type(region)

        # Return iso code based on map_to
        if map_to == 'alpha2':
            return alpha2_mapping
        elif map_to == 'alpha3':
            return self.alpha2_to_alpha3[alpha2_mapping]
        elif map_to == 'currency':
            return "EUR" if alpha2_mapping in self.eu_join_dict.keys() else self.alpha2_to_currency[alpha2_mapping]
        elif map_to == "natural_name":
            return "Europe" if region == "EUR" else self.alpha2_to_region[alpha2_mapping]
        else:
            raise ValueError("Invalid map_to request.")

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
            warnings.warn("Could not obtain required inflation (CPI) information for '%s' in %s."
                          " Using %s instead." % \
                         (self._iso_mapping(region, map_to = 'natural_name'), str(int(float(year))), max_cpi_year))
            cpi = floater(self.cpi_dict[cpi_region][str(int(float(max_cpi_year)))])
        else:
            cpi = floater(self.cpi_dict[cpi_region][str(int(float(year)))])

        return cpi

    def inflation_rate(self, region, year_a, year_b, return_raw_cpi_dict = False):
        """

        :param region:
        :param year_a:
        :param year_b:
        :param return_dict:
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
        inflation_dict = self.inflation_rate(  region
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
                           (self._iso_mapping(region, map_to = 'natural_name'), e))

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

        # Block self conversion
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
                                               , datetime.datetime.strptime(date, "%Y-%m-%d"))
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
        return rounded_amount if not pretty_print else print(rounded_amount, self._iso_mapping(to_currency, "currency"))

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






















































