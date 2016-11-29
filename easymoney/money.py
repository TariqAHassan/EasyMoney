# coding: utf-8

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import pycountry
import numpy as np
import pandas as pd

from pprint import pprint
from warnings import warn
from datetime import datetime

# Support Tools
from easymoney.support_tools import mint
from easymoney.support_tools import min_max
from easymoney.support_tools import closest_date
from easymoney.support_tools import year_extract
from easymoney.support_tools import min_max_dates
from easymoney.support_tools import closest_value
from easymoney.support_tools import date_format_check
from easymoney.support_tools import sort_range_reverse

# Pycountry Wrap
from easymoney.pycountry_wrap import PycountryWrap

# options_tools
from easymoney.options_tools import options_ranking
from easymoney.options_tools import year_date_overlap

# Easy Pandas
from easymoney.easy_pandas import pandas_null_drop
from easymoney.easy_pandas import pandas_pretty_print

# Online Data Sources
from easymoney.sources.ecb_interface import ecb_xml_exchange_data
from easymoney.sources.world_bank_interface import world_bank_pull



class EasyPeasy(object):
    """

    Tools for Monetary Information and Conversions.

    :param precision: number of places to round to when returning results. Defaults to 2.
    :type precision: ``int``
    :param fall_back: if True, fall back to closest possible date for which data is available. Defaults to True.
    :type fall_back: ``bool``
    :param fuzzy_match_threshold: a threshold for fuzzy matching confidence (requires the ``fuzzywuzzy`` package).
                                  The value must be an number between 0 and 100. The *suggested* minimum values is 85.
                                  This will only impact attempts to match on natural names, e.g., attempting to match
                                  'Canada' by passing 'Canadian'. Defaults to False.

                                  .. warning::

                                        Fuzzy matching may yield inaccurate results.

                                        Whenever possible, use terminology *exactly* as it appears in ``options()``.

    :type fuzzy_threshold: ``int`` or ``float``
    :param data_path: alternative path to the database file(s). Defaults to None.
    :type data_path: ``str``
    """
    # Fix: `EasyPeasy()` does not handle currencies like 'EEK' properly.
    #       They may not been appearing in options() correctly.
    #       See: _user_currency_input() below.

    def __init__(self, precision=2, fall_back=True, fuzzy_threshold=False, data_path=None):
        """

        Initialize the ``EasyPeasy()`` class.

        """
        self._precision = precision
        self._fall_back = fall_back

        min_suggested_fuzzy_threshold = 85
        # Check fuzzy_threshold
        if fuzzy_threshold != False and not isinstance(fuzzy_threshold, (float, int)):
            raise ValueError("`fuzzy_threshold` must be either `False`, a `float` or an `int`.")
        elif isinstance(fuzzy_threshold, (float, int)) and not isinstance(fuzzy_threshold, bool) and fuzzy_threshold <= 0:
            raise ValueError("`fuzzy_threshold` must be greater than 0.")
        elif isinstance(fuzzy_threshold, (float, int)) and not isinstance(fuzzy_threshold, bool) and fuzzy_threshold > 100:
            raise ValueError("`fuzzy_threshold` must be less than 100.")
        elif isinstance(fuzzy_threshold, (float, int)) and not isinstance(fuzzy_threshold, bool) \
                and fuzzy_threshold < min_suggested_fuzzy_threshold:
            warn("Low `fuzzy_threshold` values, such as %s, may yield innaccurate results." % (str(fuzzy_threshold)))

        path_to_data = data_path if isinstance(data_path, str) else None
        self._pycountry_wrap = PycountryWrap(path_to_data, fuzzy_threshold)
        self._pycountries_alpha_2 = set([c.alpha_2 for c in list(pycountry.countries)])

        # CPI Dict
        self._cpi_dict = world_bank_pull(return_as='dict')

        # Exchange Dict
        self._exchange_dict, self.ecb_currency_codes, self._currency_date_record = ecb_xml_exchange_data(return_as='dict')

        # Column Order for options
        self._table_col_order = ['RegionFull', 'Region', 'Alpha2', 'Alpha3', 'Currencies',
                                 'InflationDates', 'ExchangeDates', 'Overlap']


    def _params_check(self, amount="void", pretty_print="void"):
        """

        Check `amount` and `pretty_print` have been passed valid values.

        :param amount: numeric amount
        :type amount: ``float`` or ``int``
        :param pretty_print: must be a boolean
        :type pretty_print: ``bool``
        """
        # Check amount is float
        if amount != "void" and not isinstance(amount, (float, int)):
            raise ValueError("amount must be numeric (intiger or float).")

        # Check pretty_print is a bool
        if pretty_print != "void" and not isinstance(pretty_print, bool):
            raise ValueError("pretty_print must be either True or False.")


    def region_map(self, region, map_to='alpha_2'):
        """

        Map a 'region' to any one of: ISO Alpha 2, ISO Alpha 3, it's Name or Offical Name.

            Examples::
                - ``EasyPeasy().region_map(region='CA', map_to='alpha_2')``       :math:`=` 'CA'
                - ``EasyPeasy().region_map(region='Canada', map_to='alpha_3')``   :math:`=` 'CAN'

        :param region: a 'region' in the format of a ISO Alpha2, ISO Alpha3 or currency code, as well as natural name.
        :type region: ``str``
        :param map_to: 'alpha_2', 'alpha_3' 'name' or 'offical_name'. Defaults to 'alpha_2'.
        :type map_to: ``str``
        :return: the desired mapping from region to ISO Alpha2.
        :rtype: ``str`` or ``tuple``
        """
        return self._pycountry_wrap.map_region_to_type(region=region, extract_type=map_to)


    def _cpi_years(self, region, warn=True):
        """

        Get Years for which CPI information is available for a given region.

        :param region: region of the form allowed by `EasyPeasy().region_map()`
        :type region: ``str``
        :param warn: warn if data could not be obtained
        :type warn: ``bool``
        :return: list of years for which CPI information is available.
        :rtype: ``list``
        """
        cpi_years_list = list()
        for year in sorted(list(self._cpi_dict.keys()), reverse=True):
            cpi = self._cpi_dict.get(year, None).get(region, None)
            if not isinstance(cpi, type(None)):
                cpi_years_list.append(year)

        if len(cpi_years_list):
            return cpi_years_list
        elif warn:
            raise KeyError("Could not obtain inflation (CPI) information for '%s' from the\n" \
                           "International Monetary Fund database currently cached." % (region))


    def _cpi_match(self, region, year):
        """

        Match region to the best possible year.

        :param region: region of the form allowed by `EasyPeasy().region_map()`
        :type region: ``str``
        :param year: a year for which CPI information is desired.
                     Can also be one of: 'oldest' or 'latest'.
        :type year: ``int`` or ``str``
        :return: best matching of CPI information for the given region w.r.t. the year supplied.
        :rtype: ``float``, ``int`` or ``str``
        """
        # Initialize
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
            if self._fall_back:
                natural_region_name = self._pycountry_wrap.map_region_to_type(region, 'name')
                fall_back_year = closest_value(float(year), available_years)
                warn(warn_msg % (year, natural_region_name, str(fall_back_year)))
                return fall_back_year
            else:
                raise AttributeError(error_msg % (year, natural_region_name))
        else:
            return year


    def _cpi_region_year(self, region, year):
        """

        Get the Consumer Price Index (CPI) in a given region for a given year.

        :param region: region of the form allowed by `EasyPeasy().region_map()`
        :type region: ``str``
        :param year: a year for which CPI information is desired.
                     Can also be one of: 'oldest' or 'latest'.
        :type year: ``int`` or ``str``
        :return: CPI for a given year.
        :rtype: ``float``
        """
        cpi = self._cpi_dict.get(str(int(float(year))), {}).get(self.region_map(region, 'alpha_2'), None)
        if cpi is not None:
            return float(cpi)
        else:
            raise KeyError("Could not obtain inflation information for '%s' in '%s'." % (str(region), str(year)))


    def inflation(self, region, year_a, year_b=None, return_raw_cpi_dict=False, pretty_print=False):
        """

        Calculator to compute the inflation rate from Consumer Price Index (CPI) information.

        Inflation Formula:

        .. math:: Inflation_{region} = \dfrac{c_{1} - c_{2}}{c_{2}} \cdot 100

        | :math:`where`:
        |   :math:`c_{1}` = CPI of the region in *year_b*.
        |   :math:`c_{2}` = CPI of the region in *year_a*.

        :param region: a region.
        :type region: ``str``
        :param year_a: start year.
        :type year_a: ``int``
        :param year_b: end year. Defaults to None -- can only be left to this default if *return_raw_cpi_dict* is True.
        :type year_b: ``int``
        :param return_raw_cpi_dict: If True, returns the CPI information in a dict. Defaults to False.
        :type return_raw_cpi_dict: ``bool``
        :param pretty_print: if True, pretty prints the result otherwise returns the result as a float. Defaults to False.
        :type pretty_print: ``bool``
        :return: (a) the rate of inflation between year_a and year_h.

                 (b) a dictionary of CPI information with the years as keys, CPI as values.
        :rtype: ``float``, ``dict`` or ``NaN``
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
            rate = round(((c1 - c2) / float(c2)) * 100, self._precision)

        # Return or Pretty Print.
        if not pretty_print:
            return rate
        else:
            print(rate, "%")


    def inflation_calculator(self, amount, region, year_a, year_b, pretty_print=False):
        """

        Adjusts a given amount of money for inflation.

        :param amount: a monetary amount.
        :type amount: ``float`` or ``int``
        :param region: a geographical region.
        :type region: ``str``
        :param year_a: start year.
        :type year_a: ``int``
        :param year_b: end year.
        :type year_b: ``int``
        :param pretty_print: if True, pretty prints the result otherwise returns the result as a float.
                             Defaults to False.
        :type pretty_print: ``bool``
        :return: :math:`amount \cdot inflation \space rate`.
        :rtype: ``float`` or ``NaN``
        """
        # Check Params
        self._params_check(amount, pretty_print)

        # Input checking
        if year_a == year_b:
            return mint(amount, self._precision, self.region_map(region, map_to='currency_alpha_3'), pretty_print)

        # Get the CPI information
        inflation_dict, years = self.inflation(region, year_a, year_b, return_raw_cpi_dict='complete')

        # Block division by zero
        if inflation_dict[years['year_a']] == 0:
            warn("Problem obtaining required inflation information.")
            return np.NaN

        # Scale w.r.t. inflation.
        adjusted_amount = inflation_dict[years['year_b']] / float(inflation_dict[years['year_a']]) * amount

        # Print or Return
        return mint(adjusted_amount, self._precision, self.region_map(region, map_to='currency_alpha_3'), pretty_print)


    def _exchange_dates(self, currencies, min_max_rslt=False, date_format='%d/%m/%Y'):
        """

        Get all dates for which there is data for a given list of currencies

        :param currencies: a list of currencies
        :type currencies: ``list``
        :param min_max_rslt: compute the earliest and latest date for which exchange rate information is available.
                             Defaults to False.
        :type min_max_rslt: ``bool``
        :param date_format: a data format. Defaults to '%d/%m/%Y'.
        :type date_format: ``str``
        :return:
        :rtype: 1D ``list`` or 2D ``list``
        """
        dates = list()
        for c in currencies:
            if c == 'EUR':
                dates.append(sorted(list(self._exchange_dict.keys()), key=lambda x: datetime.strptime(x, date_format)))
            else:
                dates.append(self._currency_date_record.get(c.upper(), None))

        # Remove None
        dates = list(filter(None, dates))
        if not len(dates):
            return None

        if min_max_rslt:
            dates = [list(min_max_dates(d)) for d in dates if isinstance(d, (list, tuple, type(np.array)))]

        return dates[0] if len(dates) == 1 else dates


    def _user_currency_input(self, currency_or_region):
        """

        Converts User supplied reference to a currency into an actual ISO Alpha 3 Currency Code.

        :param currency_or_region: reference to a currency
        :type currency_or_region: ``str``
        :return: ISO Alpha 3 Currency Code
        :rtype: ``pycountry object``
        """
        # Note: 'temp. fix' has been added to handle currencies like 'EEK'.
        #        This capability should be integrated into region_map() in the future.
        try:
            return pycountry.currencies.lookup(currency_or_region).alpha_3
        except:
            if currency_or_region in self.ecb_currency_codes: # temp fix
                return currency_or_region
            else:
                return self.region_map(currency_or_region, "currency_alpha_3")


    def _base_cur_to_lcu(self, currency, date):
        """

        Convert from a base currency (Euros) to a local currency unit, e.g., CAD.

        :param currency: a currency code or region
        :type currency: ``str``
        :param date: date of allowed form (currently limited to DD/MM/YYYY).
        :type date: ``str``
        :return: exchange_rate w.r.t. the Euro as a base currency.
        """
        error_msg = "\nCould not obtain the exchange rate for '%s' on %s from the\n" \
                    "European Central Bank database currently cached."
        warn_msg = error_msg + "\nFalling back to %s."

        # Handle Base Currency
        if currency.upper() == 'EUR':
            return 1.0

        available_data = self._currency_date_record.get(currency, None)
        if available_data == None:
            raise AttributeError("Data could not obtained for '%s' from the\n" \
                                 "European Central Bank database currently cached." % (currency))

        if date == 'oldest':
            exchange_date = min_max_dates(available_data)[0]
        elif date == 'latest':
            exchange_date = min_max_dates(available_data)[1]
        elif isinstance(date, str) and date not in available_data:
            if self._fall_back:
                exchange_date = closest_date(date, available_data)
                warn(warn_msg % (currency, date, exchange_date))
            else:
                raise AttributeError(msg % (currency, exchange_date))
        elif isinstance(date, str) and date_format_check(date, from_format="%d/%m/%Y"):
            exchange_date = date
        else:
            raise ValueError("Invalid Date Supplied. Dates must be of the form DD/MM/YYYY.")

        exchange_rate = self._exchange_dict.get(exchange_date, {}).get(currency, None)
        if not isinstance(exchange_rate, type(None)):
            return exchange_rate
        else:
            raise AttributeError(msg % (currency, exchange_date))


    def currency_converter(self, amount, from_currency, to_currency, date="latest", pretty_print=False):
        """

        Function to perform currency conversion based on, **not** directly reported from, data obtained
        from the European Central Bank (ECB).
        Base Currency: EUR.

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

            From :math:`CUR_{1}` to :math:`CUR_{2}`:

                .. math:: amount_{CUR_{2}} = \dfrac{1}{LCU(\phi_{EUR}, CUR_{1})} \cdot LCU(\phi_{EUR}, CUR_{2}) \cdot amount_{CUR_{1}}

        :param amount: an amount of money to be converted.
        :type amount: ``float`` or ``int``
        :param from_currency: the currency of the amount.
        :type from_currency: ``str``
        :param to_currency: the currency the amount is to be converted into.
        :type to_currency: ``str``
        :param date: date of data to perform the conversion with. Dates must be of the form: ``DD/MM/YYYY``.
        :type date: ``str``
        :param pretty_print: if True, pretty prints the table otherwise returns the table as a pandas DataFrame. Defaults to False.
        :type pretty_print: ``bool``
        :return: converted currency.
        :rtype: ``float``
        """
        # Check Params
        self._params_check(amount, pretty_print)

        # to/from_currency --> Alpha 3 Currency Code
        to_currency_fn, from_currency_fn = (self._user_currency_input(arg) for arg in (to_currency, from_currency))

        # Return amount unaltered if self-conversion was requested.
        if from_currency_fn == to_currency_fn:
            return mint(amount, self._precision, to_currency_fn, pretty_print)

        if any(x == None or x is None for x in [to_currency_fn, from_currency_fn]):
            raise ValueError("Could not convert '%s' to '%s'." % (from_currency, to_currency))

        # from_currency --> Base Currency --> to_currency
        conversion_to_invert = self._base_cur_to_lcu(from_currency_fn, date)
        if conversion_to_invert == 0.0:
            raise ZeroDivisionError("Cannot converted from '%s' on %s." % (from_currency, date))
        converted_amount = (conversion_to_invert ** -1) * self._base_cur_to_lcu(to_currency_fn, date) * float(amount)

        # Return results (or pretty print)
        return mint(converted_amount, self._precision, to_currency_fn, pretty_print)


    def normalize(self
                  , amount
                  , region
                  , from_year
                  , to_year="latest"
                  , base_currency="EUR"
                  , exchange_date="latest"
                  , pretty_print=False):
        """

        | Convert a Nominal Amount of money to a Real Amount in the same, or another, currency.
        |
        | This requires both inflation (for *currency*) and exchange rate information (*currency* to *base_currency*).
          See ``options(info = 'all', overlap_only = True)`` for an exhaustive listing of valid values to pass to this method.
        |
        | Currency Normalization occurs in two steps:
        |       1. Adjust the currency for inflation, e.g., 100 (2010 :math:`CUR_{1}`) → x (2015 :math:`CUR_{1}`).
        |       2. Convert the adjusted amount into the *base_currency*.

        :param amount: a numeric amount of money.
        :type amount: ``float`` or ``int``
        :param currency: a region or currency.
                         Legal options: Region Name, ISO Alpha2, Alpha3 or Currency Code (see ``options()``).
        :type currency: ``str``
        :param from_year: a year. For valid values see ``options()``.
        :type from_year: ``int``
        :param to_year: a year. For valid values see ``options()``.
                        Defaults to 'latest' (which will use the most recent data available).
        :type to_year: ``str`` or ``int``
        :param base_currency:  a region or currency. Legal: Region Name, ISO Alpha2, Alpha3 or Currency Code
                               (see ``options()``). Defaults to 'EUR'.
        :type base_currency: ``str``
        :param pretty_print: Pretty print the result if True; return amount if False. Defaults to False.
        :type pretty_print: ``bool``
        :return: amount adjusted for inflation and converted into the base currency.
        :rtype: ``float``
        """
        # Check Params
        self._params_check(amount, pretty_print)

        exchange_year = year_extract(exchange_date)
        if exchange_date not in ['oldest', 'latest'] and not str(exchange_year).isdigit():
            warn("\n`exchange_date` is likely formatted improperly.")

            # Check delta between `to_year` and `exchange_date`.
            if abs(float(to_year) - float(exchange_year)) > 1: # note, this doesn't currently handle oldest v. latest.
                warn("\nThe year for which the input amount is being adjusted\n"
                     "for inflation is %s, whereas the exchange rate year is %s." % (str(to_year), str(exchange_year)))

        # Adjust input for inflation
        real_amount = self.inflation_calculator(amount, region, year_a=from_year, year_b=to_year)

        # Compute Exchange
        normalize_amount = self.currency_converter(real_amount, region, base_currency, date=exchange_date)

        # Return results (or pretty print)
        return mint(normalize_amount, self._precision, self._user_currency_input(base_currency), pretty_print)


    def _options_info_error(self, rformat):
        """

        Error Messages for invalid information requests.

        :param rformat: one of: 'list' or 'table'.
        :type rformat: ``str``
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

        Tool to Generate Information for ``options()`` in table form.

        :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table').
        :type info: ``str``
        :param table_overlap_only:
        :param table_overlap_only: when info is set to 'all', keep only those rows for which exchange rate and inflation data overlap.
        :type table_overlap_only: ``bool``
        :param range_table_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which data is available will be reported. Defaults to True.
        :type range_table_dates: ``bool``
        :return: dataframe summarizing databases currently cached by ``EasyPeasy()``.
        :rtype: ``Pandas DataFrame``
        """
        # Note: does not currently handle currency transitions

        # Use CurrencyRelationshipsDB as Base
        d = [i for i in list(self._pycountry_wrap.alpha2_currency_dict.items()) if i[0] in self._pycountries_alpha_2]
        options_df = pd.DataFrame(d).rename(columns={0 : "Alpha2", 1 : "Currencies"})

        # Add Names
        options_df['Region'] = [self._pycountry_wrap.map_region_to_type(c, 'name') for c in list(options_df['Alpha2'])]
        options_df['RegionFull'] = [self._pycountry_wrap.map_region_to_type(c, 'official_name') for c in list(options_df['Alpha2'])]

        # Add Alpha3
        options_df['Alpha3'] = [self._pycountry_wrap.map_region_to_type(c, 'alpha_3') for c in list(options_df['Alpha2'])]

        # Map available Inflation Data onto this Base
        options_df['InflationDates'] = options_df['Alpha2'].map(
              lambda x: sort_range_reverse(self._cpi_years(x, warn=False), ('reverse' if not range_table_dates else 'range')), 'ignore'
        )

        # Map available Exchange Rate Data onto this Base
        options_df['ExchangeDates'] = options_df['Currencies'].map(
            lambda x: self._exchange_dates(x, min_max_rslt=range_table_dates), na_action='ignore'
        )

        # Add Overlap
        options_df['Overlap'] = options_df.apply(
            lambda x: year_date_overlap(x['InflationDates'], x['ExchangeDates'], date_format="%d/%m/%Y"), axis=1
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
        col_order = self._table_col_order
        if info == 'exchange':
            col_order = [c for c in self._table_col_order if c != 'InflationDates']
        elif info == 'inflation':
            col_order = [c for c in self._table_col_order if c != 'ExchangeDates']
        elif info != 'all':
            self._options_info_error('table')

        return options_df.drop('TempRanking', axis=1)[col_order].reset_index(drop=True)


    def _options_lists(self, info):
        """

        Tool to Generate Information for ``options()`` in list form.

        :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table').
        :type info: ``str``
        :return: list of requested information.
        :rtype: ``list``
        """
        if info.strip().lower() not in ['exchange', 'inflation']:
            self._options_info_error('list')

        d = self._exchange_dict if info.strip().lower() == 'exchange' else self._cpi_dict

        full = [list(v.keys()) for k, v in d.items()]
        return sorted(set([i for s in full for i in s]))


    def options(self, info='all', rformat='table', pretty_print=True, table_overlap_only=False, range_table_dates=True):
        """

        An easy interface to explore all of the terminology EasyPeasy understands
        as well the dates for which data is available.

        :param info: 'exchange', 'inflation' or 'all' ('all' requires rformat is set to 'table').
        :type info: ``str``
        :param rformat: 'table' for a table or 'list' for just the currency codes, alone. Defaults to 'table'.
        :type rformat: ``str``
        :param pretty_print: if True, prints the list or table. If False, returns the list or table (as a Pandas DataFrame).
                             Defaults to True.
        :type pretty_print: ``bool``
        :param table_overlap_only: when info is set to 'all', keep only those rows for which exchange rate and inflation data overlap.
        :type table_overlap_only: ``bool``
        :param range_table_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which data is available will be reported. Defaults to True.
        :type range_table_dates: ``bool``
        :return: information table or list
        :rtype: ``Pandas DataFrame`` or ``list``
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
















