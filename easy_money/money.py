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
from statistics import mean

from easy_money.support_money import twoD_nested_dict, floater
from easy_money.ecb_interface import _ecb_exchange_data
from easy_money.world_bank_interface import WorldBankParse, world_bank_pull_wrapper


class Currency(object):
    """

    Tools to adjusting for inflation, converting to USD and normalizing (converting to USD and adjusting for inflation)
    This will take a moment to initialize.

    Functionality:
        1) Get Inflation Rate
        2) Convert Currency
        3) Exchange rate

    To do:
        1) Impliment option for linear interpolation of missing values.
    """


    def __init__(self, precision = 2):
        """

        :param precision: number of places to round to.
        """

        # Get CPI Data
        self.cpi_df = world_bank_pull_wrapper(value_true_name = "cpi", indicator = "FP.CPI.TOTL")
        # Create CPI dict
        self.cpi_dict = twoD_nested_dict(self.cpi_df, 'alpha2', 'year', 'cpi', to_float = ['cpi'], to_int = ['year'])

        # Get Exchange rate Data
        self.ex_dict = _ecb_exchange_data('dict')
        #sorted_exchange_dates = [datetime.datetime.strptime(d, "%Y-%m-%d") for d in sorted(self.ex_dict.keys())]
        self.ex_dict_keys_series = pd.Series(sorted(list(self.ex_dict.keys())))

        # Import EU join Data
        eu_join = pd.read_csv("easy_money/easy_data/JoinEuro.csv")
        eu_join_dict = dict(zip(eu_join.alpha2, eu_join.join_year))

        # Create Alpha3 --> Alpha2 Dict
        #self.alpha3_to_alpha2 = dict(zip(self.cpi_df.alpha3, self.cpi_df.alpha2))

        # Create Currency --> Alpha2 Dict
        self.currency_to_alpha2 = dict(zip(self.cpi_df.currency_code, self.cpi_df.alpha2))

        # Create Region Name --> Alpha2 Dict
        #region_to_alpha2 = dict(zip(self.cpi_df.region, self.cpi_df.alpha2))

        # Places of precision
        self.round_to = precision

    def _linear_interpolate():
        """

        In progress...

        :return:
        """
        pass

    def _eu_membership(self):
        """

        In progress...

        :return:
        """
        pass

    def iso_convert(self, iso_standard, convert_to):
        """

        In progress...

        :param iso_standard: Alpha2, Alpha2 or CurrencyCode
        :param convert_to: Alpha2, Alpha2 or CurrencyCode
        :return:
        """
        pass

    def _try_to_get_CPI(self, region, year):
        """

        :param region:
        :param year:
        :return:
        """
        try:
            cpi = floater(self.cpi_dict[region][str(year)])
        except:
            raise ValueError("Could not obtain required inflation (CPI) information for '%s' in %s." % (region, year_b))

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
        if year_a == year_b:
            return amount
        if year_a > year_b:
            raise ValueError("year_a cannot be greater than year_b")

        # Add Handling of missing years, i.e, Linear Interpolation #

        # Get the CPI information
        inflation_dict = self.inflation_rate(region, year_a, year_b, return_raw_cpi_dict = True)

        # Check all the values are floats
        if not all([floater(x, just_check = True) for x in inflation_dict.values()]):
            return np.NaN

        # Block division by zero
        if any(x == 0.0 for x in inflation_dict.values()):
            warnings.warn("Problem obtaining required inflation information.")
            return None

        # Scale w.r.t. inflation.
        adjusted_amount = inflation_dict[str(year_b)]/float(inflation_dict[str(year_a)]) * amount

        # Round and Return
        return round(adjusted_amount, self.round_to)

    def _eur_to_lcu(self, currency = 'USD', date = 'most_recent'):
        """

        :param currency:
        :param date: must be of the form: YYYY-MM-DD
        :return: exchange_rate w.r.t. the EURO (as a base currency).
        """

        # Handle things other than currency codes being passed #

        # Initialize
        date_key = None

        # Get the current date
        if date == 'most_recent':
            try:
                date_key = str(max([d.date() for d in pd.to_datetime(list(self.ex_dict.keys()))]))
            except:
                raise ValueError("Could not obtain most recent exchange information from the European Central Bank.")
        else:
            date_key = date

        return self.ex_dict[date_key][currency.upper()] * float(1)

    def currency_converter(self, amount, from_currency, to_currency, date = 'most_recent', pretty_print = False):
        """

        :param amount:
        :param from_currency:
        :param to_currency:
        :param date:
        :return:
        """

        # Add more input checking! #
        if not floater(amount, just_check = True):
            raise ValueError("Amount must be numeric (intiger or float).")

        # Initialize variables
        conversion_to_invert = None
        converted_amount = None

        # To some currency from EUR
        if from_currency == "EUR":
            converted_amount = self._eur_to_lcu(to_currency, date) * float(amount)

        # From some currency to EUR
        elif to_currency == "EUR":
            conversion_to_invert = self._eur_to_lcu(from_currency, date)

            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted to '%s'." % (to_currency))
            converted_amount = conversion_to_invert**-1 * float(amount)

        # from_currency --> EURO --> to_currency
        else:
            conversion_to_invert = self._eur_to_lcu(from_currency, date)
            if conversion_to_invert == 0.0:
                raise AttributeError("Cannot converted from '%s'." % (from_currency))

            converted_amount = conversion_to_invert**-1 * self._eur_to_lcu(to_currency, date) * float(amount)

        rounded_amount = round(converted_amount, self.round_to)

        # Return results (or print)
        return rounded_amount if not pretty_print else print(rounded_amount, to_currency)

    def _dates_in_range(self, start_date, end_date, pandas_series):
        """

        :param start_date:
        :param end_date:
        :param pandas_series:
        :return: pandas series
        """

        if datetime.datetime.strptime(self, start_date, "%Y-%m-%d") >= datetime.datetime.strptime(end_date, "%Y-%m-%d") :
            raise ValueError("Indexing Error. The start_date cannot occur before the end date.")

        return pandas_series.loc[(pd.to_datetime(pandas_series) >= start_date) & \
                                 (pd.to_datetime(pandas_series) <= end_date)]

    def _average_exchange_rate_over_range(self, from_currency, to_currency, start_date, end_date, amount = 1):
        """

        Norminal Average Exchange Rate over some daterange

        TO DO:
        Add option to adjust for inflation.

        :param amount:
        :param from_currency:
        :param to_currency:
        :param start_date: starting date; must be of the form: YYYY-MM-DD
        :param end_date:  ending date; must be of the form: YYYY-MM-DD
        :return:
        """

        date_range = self._dates_in_range(start_date, end_date, self.ex_dict_keys_series)
        return mean([self.currency_converter(amount, from_currency, to_currency, date = d) for d in date_range.tolist()])

    def normalize(self, amount, from_currency, from_year, to_year = "most_current", base_currency = "EUR", pretty_print = False):
        """

        :param amount:
        :param from_currency:
        :param from_year:
        :param to_year:
        :param base_currency:
        :return:
        """

        # Determine to CPI Data
        if to_year != "most_current":
            inflation_year_b = to_year
        elif to_year == "most_current":
            inflation_year_b = self.cpi_df[(self.cpi_df.alpha2 == self.currency_to_alpha2[from_currency]) & \
                                           (~pd.isnull(self.cpi_df.cpi))].year.max()

        # Adjust input for inflation
        from_currency_adj_inflation = self.inflation_calculator(amount, "US", from_year, inflation_year_b)

        result = self.currency_converter(from_currency_adj_inflation, from_currency, base_currency)

        if pretty_print :
            print(result, base_currency)
        else:
            return result





























































































