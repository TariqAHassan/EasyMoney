#!/usr/bin/env python3

"""

    Tools for Navigating the Data Cached by EasyMoney
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

# Modules #
import copy
import numpy as np
import pandas as pd

try:
    from fuzzywuzzy import process
except:
    pass

from warnings import warn
from collections import defaultdict

from easymoney.support_money import date_bounds_floor
from easymoney.support_money import dict_list_unpack
from easymoney.support_money import dict_merge
from easymoney.support_money import floater
from easymoney.support_money import key_value_flip
from easymoney.support_money import list_flatten
from easymoney.support_money import min_max
from easymoney.support_money import remove_from_dict
from easymoney.support_money import str_to_datetime

from easymoney.easy_pandas import pandas_dictkey_to_key_unpack
from easymoney.easy_pandas import pandas_print_full
from easymoney.easy_pandas import prettify_all_pandas_list_cols
from easymoney.easy_pandas import twoD_nested_dict

from sources.databases import DatabaseManagment
from sources.ecb_interface import ecb_currency_to_alpha2_dict



class DataNavigator(object):
    """

    This class houses database data that has been coerced into dictionaries.
    These have far better time complexity (big O) than a Pandas DataFrame.

    Additionaly, this class contains an array of tools for exploring the data in the databases.

    :param database_path: see ``EasyPeasy()``
    :type database_path: str
    """


    def __init__(self, database_path):
        """

        Initialize the ``DataNavigator()`` class.

        """
        # Obtain required databases
        required_databases = DatabaseManagment(database_path)._database_wizard()

        # Define Databases
        self.ISOAlphaCodesDB = required_databases[0]
        self.CurrencyTransitionDB = required_databases[1]
        self.ExchangeRatesDB = required_databases[2]
        self.currency_codes = required_databases[3]
        self.ConsumerPriceIndexDB = required_databases[4]
        self.CurrencyRelationshipsDB = required_databases[5]

        # Transition Tuples
        t_tuples_lambda = lambda x: (x['OldCurrency'], x['NewCurrency'], x['Date'])
        self.CurrencyTransitionDB['TransitionTuples'] = self.CurrencyTransitionDB.apply(t_tuples_lambda, axis=1)

        # Exchange Rates Dates as strings.
        self.ExchangeRatesDB['Date'] = self.ExchangeRatesDB['Date'].astype(str)

        # Group Dates by Currency
        currency_ex_dates = self.ExchangeRatesDB.groupby('Currency')['Date'].apply(
            lambda x: sorted(x.tolist())).reset_index()

        # Convert currency_ex_dates to Dict
        self.currency_ex_dict = dict(zip(currency_ex_dates['Currency'].tolist(), currency_ex_dates['Date'].tolist()))

        # Find the min and max exchange date in the dictionary
        min_exchange_date = pd.to_datetime(self.ExchangeRatesDB['Date'].min()).year
        max_exchange_date = pd.to_datetime(self.ExchangeRatesDB['Date'].max()).year

        # Currency transitions dictionary (only those transitions between min and max year).
        self.transition_dict = self.CurrencyTransitionDB[
            self.CurrencyTransitionDB['Date'].between(min_exchange_date, max_exchange_date)].groupby(
            'Alpha2').apply(lambda x: x['TransitionTuples'].tolist()).to_dict()

        # Create CPI dict
        self.cpi_dict = twoD_nested_dict(self.ConsumerPriceIndexDB, 'Alpha2', 'Year', 'CPI', to_float=['CPI']
                                        , to_int=['Year'])

        # Create Alpha3 --> Alpha2 Dict
        self.alpha3_to_alpha2 = remove_from_dict(dict(zip(self.ISOAlphaCodesDB.Alpha3, self.ISOAlphaCodesDB.Alpha2)))

        # Create Alpha2 --> Alpha3 Dict
        self.alpha2_to_alpha3 = key_value_flip(self.alpha3_to_alpha2)

        # Create the dict and populate using uniques in the ConsumerPriceIndexDB.
        currency_to_alpha2 = dict()
        for k in self.ConsumerPriceIndexDB['Currency'].unique().tolist():
            currency_to_alpha2[k] = self.ConsumerPriceIndexDB['Alpha2'][
                self.ConsumerPriceIndexDB['Currency'].astype(str) == k].unique().tolist()

        # Drop NaNs
        self.currency_to_alpha2 = remove_from_dict(currency_to_alpha2)

        # Create a flipped dict from currency_to_alpha2.
        self.alpha2_to_currency = dict_list_unpack(currency_to_alpha2)

        # Create Region Name --> Alpha2 Dict
        self.region_to_alpha2 = remove_from_dict(dict(zip(self.ConsumerPriceIndexDB['Country'], self.ConsumerPriceIndexDB['Alpha2'])))

        # Create Alpha2 --> Region Name Dict
        self.alpha2_to_region = key_value_flip(self.region_to_alpha2)

    def _currency_duplicate_remover(self, currency_ops):
        """

        *Private Method*
        This algo. removes duplicate rows w.r.t. Alpha2 code.
        It conserves the most recent currency code for each Alpha2 code and
        ablates all other entries.

        :param currency_ops: _currency_options() -> *_currency_duplicate_remover()* ->_currency_transition_integrator()
        :type currency_ops: Pandas DataFrame
        :return: currency_ops with duplicates removed
        :rtype: Pandas DataFrame
        """
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
        Namely, using CurrencyTransitionDB information to:
            (1) Define the range of dates for which exchange rate information is avaliable
                accross currency transitions.
            (2) Update the currency column to the most currency *currently* used in a given country
                (again, according to the CurrencyTransitionDB).
            (3) Generate column in the dataframe, each row of which which contains
                a list of tuples containing information about known currency transitions (where applicable).
                These rows are of the form [(OLD, NEW, YEAR1), (OLD, NEW, YEAR2)...],
                where OLD is the currency and NEW is the new currency. The year in the tuple denotes the year
                in which the transition occured.

        :param currency_ops: _currency_options() -> _currency_duplicate_remover() -> *_currency_transition_integrator()*
        :type currency_ops: Pandas DataFrame
        :param currency_ops_no_dups: yeild from _currency_duplicate_remover
        :type currency_ops_no_dups: Pandas DataFrame
        :param multi_alpha2: those Alpha2 codes that exist more than twice in the original dataframe.
        :type multi_alpha2: list
        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which data is available will be reported. Defaults to True.
        :type min_max_dates: bool
        :return: dataframe with information
        :rtype: ``Pandas DataFrame``
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
            lambda x: x['CurrencyRange'] if x['Alpha2'] not in multi_dates.keys() else multi_dates[x['Alpha2']], axis=1)

        # Add Transitions
        df['Transitions'] = df['Alpha2'].map(
            lambda x: self.transition_dict[x] if x in self.transition_dict.keys() else np.NaN)

        # For countries with noted transitions, update their Currency to the most recent used.
        def most_recent_transition(transitions):
            return list(filter(lambda x: str(x[2]) == max(np.array(transitions)[:,2]), transitions))[0]

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
            lambda x: x['Currency'] if str(x['CurrenciesToUpdate']) == 'nan' else x['CurrenciesToUpdate'][1], axis=1)

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
            eur_row_dates = sorted(set(list_flatten(currency_ops['CurrencyRange'].tolist())))

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

        return self._currency_transition_integrator(currency_ops
                                                    , currency_ops_no_dups[0]
                                                    , currency_ops_no_dups[1]
                                                    , min_max_dates)

    def _inflation_options(self, min_max_dates):
        """

        *Private Method*
        Determines the inflation (CPI) information cached by EasyMoney.

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
        cpi_ops.sort_values(['InflationRange'], ascending=[1], inplace=True)

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

        :param min_max_dates: if True, only report the minimum and maximum date for which data is available;
                              if False, all dates for which which data is available will be reported.
        :type min_max_dates: bool
        :return: a DataFrame with both Currency and Inflation information
        :rtype: ``Pandas DataFrame``
        """
        # Column Order
        col_order = ['Region', 'Currency', 'Alpha2', 'Alpha3', 'InflationRange', 'CurrencyRange', 'Overlap',
                     'Transitions']

        # Generate the Currency Options
        currency_ops_df = self._currency_options(min_max_dates)

        # Generate the Inflation Options
        cpi_ops_df = self._inflation_options(min_max_dates)

        # Define only Columns to include in currency_ops_df when merging
        currency_cols = (currency_ops_df.columns.difference(cpi_ops_df.columns)).tolist() + ['Alpha2']

        # Merge on Inflation options
        df = pd.merge(cpi_ops_df, currency_ops_df[currency_cols], on='Alpha2', how='left')

        # Determine the Overlap in dates between CPI and Exchange
        df['Overlap'] = df.apply(lambda row: self._date_overlap_calc(row['InflationRange'], row['CurrencyRange'])
                                 , axis=1)

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
            return self._currency_options(min_max_dates)
        elif info == 'inflation':
            return self._inflation_options(min_max_dates)
        elif info == 'all':
            return self._currency_inflation_options(min_max_dates)

    def _table_pretty_print(self, info_table, min_max_dates):
        """

        *Private Method*
        Manipulations to pretty print the info_table DataFrame.

        :param info_table: yeild from ``_table_option()``.
        :type info_table: Pandas DataFrame
        :param min_max_dates: see ``_table_option()``.
        :type min_max_dates: bool
        """
        # Convert all lists into strings seperated by " : " if min_max else ", " (exclude Transitions column).
        info_table = prettify_all_pandas_list_cols(data_frame=info_table
                                                   , join_on=(" : " if min_max_dates else ", ")
                                                   , exclude=['Transitions']
                                                   , bracket_wrap=True)

        # Join Transitions on commas, regardless of min_max_dates.
        def _transition_pretty_print_formater(t):
            return str(t[2]) + " (" + t[0] + " to " + t[1] + ")"

        if 'Transitions' in info_table.columns.tolist():
            info_table['Transitions'] = info_table['Transitions'].map(
                lambda x: ", ".join([_transition_pretty_print_formater(t) for t in x]) if str(x) != 'nan' else x)

        # Replace nans with whitespace
        for col in info_table.columns:
            info_table[col] = info_table[col].map(
                lambda x: x if x != 'NAN' and str(x).lower().strip() != 'nan' else '')

        # Replace number indexes with empty strings.
        info_table.index = ['' for i in range(info_table.shape[0])]

        # Pretty print the table
        pandas_print_full(info_table)

    def _options_as_raw_dataframe(self, info_table, convert_to_datetimes):
        """

        *Private Method*
        Manipulations to return the info table dataframe for general use.

        :param info_table: yeild from ``_table_option()``.
        :type info_table: Pandas DataFrame
        :param convert_to_datetimes: if True, convert the 'CurrencyRange' and 'Overlap' columns to datetimes.
        :type convert_to_datetimes: bool
        :return: info_table dataframe with the 'InflationRange' column as a list of ints and dates as datetimes
                (if convert_to_datetimes is True).
        :rtype: ``Pandas DataFrame``
        """
        date_columns_in_table = None

        # Create a lambda to convert the InflationRange lists to lists of ints (from lists of strings).
        year_to_int = lambda x: np.NaN if 'nan' in str(x) else [[floater(i, False, override_to_int = True) for i in x]][0]

        # InflationRange --> list of ints
        if 'InflationRange' in info_table.columns:
            info_table['InflationRange'] = info_table['InflationRange'].map(year_to_int)

        if convert_to_datetimes:
            # CurrencyRange and Overlap columns --> list of datetimes
            date_columns_in_table = [i for i in info_table.columns if i in ['CurrencyRange', 'Overlap']]

            # Convert to date_columns to datetimes
            if len(date_columns_in_table) > 0:
                for col in date_columns_in_table:
                    info_table[col] = info_table[col].map(lambda x: np.NaN if str(x) == 'nan' else str_to_datetime(x))

        return info_table










































































