#!/usr/bin/env python3

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import pycountry
import numpy as np
import pandas as pd

from warnings import warn
from datetime import datetime
from pprint import pprint

from easymoney.support_tools import mint
from easymoney.support_tools import min_max
from easymoney.support_tools import closest_date
from easymoney.support_tools import min_max_dates
from easymoney.support_tools import closest_value
from easymoney.support_tools import date_format_check
from easymoney.support_tools import sort_range_reverse

from easymoney.pycountry_wrap import PycountryWrap

from easymoney.options_tools import options_ranking
from easymoney.options_tools import multi_currency_dates

from easymoney.easy_pandas import items_null
from easymoney.easy_pandas import pandas_null_drop
from easymoney.easy_pandas import pandas_pretty_print

from easymoney.sources.ecb_interface import ecb_xml_exchange_data
from easymoney.sources.world_bank_interface import world_bank_pull_wrapper



class EasyPeasy(object):
    """


    :param round_to:
    :param fall_back:
    :param fuzzy_threshold:
    :param data_path:
    """

    def __init__(self, round_to=2, fall_back=True, fuzzy_threshold=False, data_path = ''):
        """
        """
        self.round_to = round_to
        self.fall_back = fall_back
        self.pycountry_wrap = PycountryWrap(fuzzy_threshold, data_path)
        self.pycountries_alpha_2 = set([c.alpha_2 for c in list(pycountry.countries)])

        # CPI Dict
        self.cpi_dict = world_bank_pull_wrapper(return_as='dict')

        # Exchange Dict
        self.exchange_dict, all_currency_codes, self.currency_date_record = ecb_xml_exchange_data(return_as='dict')

        # Column Order for options
        self.table_col_order = ['RegionFull', 'Region', 'Alpha2', 'Alpha3', 'Currencies', 'InflationDates', 'ExchangeDates']

    def _params_check(self, amount="void", pretty_print="void"):
        """

        :param amount:
        :param pretty_print:
        :return:
        """
        # Check amount is float
        if amount != "void" and not isinstance(amount, (float, int)):
            raise ValueError("amount must be numeric (intiger or float).")

        # Check pretty_print is a bool
        if pretty_print != "void" and not isinstance(pretty_print, bool):
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

    def _cpi_years(self, region, warn=True):
        """

        Get Years for which CPI information is available for a given region.

        :param region:
        :param warn:
        :return:
        """
        cpi_years_list = list()
        for year in sorted(list(self.cpi_dict.keys()), reverse=True):
            cpi = self.cpi_dict.get(year, None).get(region, None)
            if not isinstance(cpi, type(None)):
                cpi_years_list.append(year)

        if len(cpi_years_list):
            return cpi_years_list
        elif warn:
            raise KeyError("Could not obtain inflation (CPI) information for '%s' from the\n" \
                           "International Monetary Fund database currently cached." % (region))


    def _cpi_match(self, region, year):
        """

        :param region:
        :param year:
        :return:
        """
        # Init
        fall_back_year = None
        natural_region_name = None

        # replace year_b if it is 'oldest' or 'latest'
        available_years = list(map(int, self._cpi_years(region)))
        error_msg = "\nInflation (CPI) data for %s in '%s' could not be obtained from the\n" \
                    "International Monetary Fund database currently cached."
        warn_msg = error_msg + "\nFalling back to %s."

        if year == 'oldest':
            return min(available_years)
        elif year == 'latest':
            return max(available_years)
        elif int(float(year)) not in available_years:
            if self.fall_back:
                natural_region_name = self.pycountry_wrap.map_region_to_type(region, 'name')
                fall_back_year = closest_value(float(year), available_years)
                warn(warn_msg % (year, natural_region_name, str(fall_back_year)))
                return fall_back_year
            else:
                raise AttributeError(error_msg % (year, natural_region_name))
        else:
            return year


    def _cpi_region_year(self, region, year):
        """

        :param region:
        :param year:
        :return:
        """
        cpi = self.cpi_dict.get(str(int(float(year))), {}).get(self.region_map(region, 'alpha_2'), None)
        if cpi is not None:
            return float(cpi)
        else:
            raise KeyError("Could not obtain inflation information for '%s' in '%s'." % (str(region), str(year)))


    def inflation(self, region, year_a, year_b=None, return_raw_cpi_dict=False, pretty_print=False):
        """
        """
        # Check Params
        self._params_check(pretty_print=pretty_print)

        # Map Region to its alpha 2 code
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


    def _exchange_dates(self, currencies, min_max_rslt=False, date_format='%d/%m/%Y'):
        """

        Get all dates for which there is data for a given list of currencies

        :param currencies:
        :return:
        """
        dates = list()
        for c in currencies:
            if c == 'EUR':
                dates.append(sorted(list(self.exchange_dict.keys()), key=lambda x: datetime.strptime(x, date_format)))
            else:
                dates.append(self.currency_date_record.get(c.upper(), None))

        # Remove None
        dates = list(filter(None, dates))
        if not len(dates):
            return None

        if min_max_rslt:
            dates = [list(min_max_dates(d)) for d in dates if isinstance(d, (list, tuple, type(np.array)))]

        return dates[0] if len(dates) == 1 else dates


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
        error_msg = "\nCould not obtain the exchange rate for '%s' on %s from the\n" \
                    "European Central Bank database currently cached."
        warn_msg = error_msg + "\nFalling back to %s."

        # Handle Base Currency
        if currency.upper() == 'EUR':
            return 1.0

        available_data = self.currency_date_record.get(currency, None)
        if available_data == None:
            raise AttributeError("Data could not obtained for '%s' from the\n" \
                                 "European Central Bank database currently cached." % (currency))

        if date == 'oldest':
            exchange_date = min_max_dates(available_data)[0]
        elif date == 'latest':
            exchange_date = min_max_dates(available_data)[1]
        elif isinstance(date, str) and date not in available_data:
            if self.fall_back:
                exchange_date = closest_date(date, available_data)
                warn(warn_msg % (currency, date, exchange_date))
            else:
                raise AttributeError(msg % (currency, exchange_date))
        elif isinstance(date, str) and date_format_check(date, from_format="%d/%m/%Y"):
            exchange_date = date
        else:
            raise ValueError("Invalid Date Supplied. Dates must be of the form DD/MM/YYYY.")

        exchange_rate = self.exchange_dict.get(exchange_date, {}).get(currency, None)
        if not isinstance(exchange_rate, type(None)):
            return exchange_rate
        else:
            raise AttributeError(msg % (currency, exchange_date))


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
        converted_amount = (conversion_to_invert ** -1) * self._base_cur_to_lcu(to_currency_fn, date) * float(amount)

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

        exchange_year = year_extract(exchange_date)
        if not exchange_year.isdigit():
            warn("\n`exchange_date` is likely formatted improperly.")

        # Check delta between `to_year` and `exchange_date`.
        if abs(float(to_year) - float(exchange_year)) > 1:
            warn("\nThe year for which the input amount is being adjusted\n"
                 "for inflation is %s, whereas the exchange rate year is %s." % (str(to_year), str(exchange_year)))

        # Adjust input for inflation
        real_amount = self.inflation_calculator(amount, region, year_a=from_year, year_b=to_year)

        # Compute Exchange
        normalize_amount = self.currency_converter(real_amount, region, base_currency, date=exchange_date)

        # Return results (or pretty print)
        return mint(round(normalize_amount, self.round_to), self._user_currency_input(base_currency), pretty_print)

    def _options_info_error(self, rformat):
        """

        :param rformat:
        :return:
        """
        options_error_msg = "Invalid Information Request.\n" \
                            "Please supply:\n" \
                            " - 'exchange' to `info` for a %s of currencies for which exchange rates are available.\n" \
                            " - 'inflation' to `info` for a %s of countries for which inflation information is available." \
                            % (rformat, rformat)

        if rformat == 'list':
            append = "\nTo see a complete summary, please set `rformat` equal to 'table' and set `info` equal to 'all'."
        elif rformat == 'table':
            append = "\n - 'all' to `info` for a complete summary of available data."

        raise ValueError(options_error_msg + append)


    def _options_table(self, info, table_overlap_only=False, range_table_dates=True):
        """
        Note: does not currently handle currency transitions

        """
        # Use CurrencyRelationshipsDB as Base
        d = [i for i in list(self.pycountry_wrap.alpha2_currency_dict.items()) if i[0] in self.pycountries_alpha_2]
        options_df = pd.DataFrame(d).rename(columns={0 : "Alpha2", 1 : "Currencies"})

        # Add Names
        options_df['Region'] = [self.pycountry_wrap.map_region_to_type(c, 'name') for c in list(options_df['Alpha2'])]
        options_df['RegionFull'] = [self.pycountry_wrap.map_region_to_type(c, 'official_name') for c in list(options_df['Alpha2'])]

        # Add Alpha3
        options_df['Alpha3'] = [self.pycountry_wrap.map_region_to_type(c, 'alpha_3') for c in list(options_df['Alpha2'])]

        # Map available Inflation Data onto this Base
        options_df['InflationDates'] = options_df['Alpha2'].map(
              lambda x: sort_range_reverse(self._cpi_years(x, warn=False), ('reverse' if not range_table_dates else 'range')), 'ignore'
        )

        # Map available Exchange Rate Data onto this Base
        options_df['ExchangeDates'] = options_df['Currencies'].map(
            lambda x: self._exchange_dates(x, min_max_rslt=range_table_dates), na_action='ignore'
        )

        # Fill NaNs
        options_df = options_df.fillna(np.NaN)

        # Weight Rows by Completeness; Sort by Data Overlap and Alpha2 Code
        options_df['TempRanking'] = options_df.apply(lambda x: options_ranking(x['InflationDates'], x['ExchangeDates']), axis=1)
        options_df = options_df.sort_values(['TempRanking', 'Alpha2'], ascending=[False, True])

        if table_overlap_only and info == 'all':
            options_df = pandas_null_drop(options_df, subset=['InflationDates', 'ExchangeDates'])
        elif table_overlap_only and info != 'all':
            warn("`table_overlap_only` can only take effect if `info` is equal to 'all'.")

        # Subset
        col_order = self.table_col_order
        if info == 'exchange':
            col_order = [c for c in self.table_col_order if c != 'InflationDates']
        elif info == 'inflation':
            col_order = [c for c in self.table_col_order if c != 'ExchangeDates']
        elif info != 'all':
            self._options_info_error('table')

        return options_df.drop('TempRanking', axis=1)[col_order].reset_index(drop=True)


    def _options_lists(self, info):
        """

        :param info:
        :return:
        """

        if info.strip().lower() not in ['exchange', 'inflation']:
            self._options_info_error('list')

        d = self.exchange_dict if info.strip().lower() == 'exchange' else self.cpi_dict

        full = [list(v.keys()) for k, v in d.items()]
        return sorted(set([i for s in full for i in s]))


    def options(self, info='all', rformat='table', pretty_print=True, table_overlap_only=False, range_table_dates=True):
        """
        """
        pretty_df = None
        if rformat == 'list':
            request = self._options_lists(info)
            return request if not pretty_print else pprint(request, width=65, compact=True)
        elif rformat == 'table':
            request = self._options_table(info, table_overlap_only, range_table_dates)
            if pretty_print:
                pretty_df = request.drop('RegionFull', axis=1)
                pretty_df['Currencies'] = pretty_df['Currencies'].str.join("; ")
                pandas_pretty_print(pretty_df, col_align={'Region' : 'left'})
            else:
                return request
        else:
            raise ValueError("`rformat` must be one of:\n"
                             " - 'list', for a list of the requested information.\n"
                             " - 'table', for a table (dataframe) of the requested information.")





ep = EasyPeasy()

ep.options()
































