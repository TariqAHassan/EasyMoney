#!/usr/bin/env python3

'''

    Tools for Obtaining Data from the World Bank Group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


'''

# Modules #
import os
import re
import copy
import wbdata
import numpy as np
import pandas as pd
import pkg_resources

from easymoney.support_money import pandas_str_column_to_list


DEFAULT_DATA_PATH = pkg_resources.resource_filename('sources', 'data')


class WorldBankParse(object):
    """

    | *Private Class*
    | Tools to obtain indicator data from the World Bank's API.
    | DO NOT WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param value_true_name: replacement name for the generic 'value' column, e.g., 'value' to 'cpi'.
    :type value_true_name: str
    :param indicator: a indicator used by the World Bank's API, e.g., "FP.CPI.TOTL" for CPI.
    :type indicator: str
    :param data_path: alternative path to database. Defaults to None.
    :type data_path: str
    """


    def __init__(self
                 , value_true_name
                 , indicator
                 , data_path = None):
        """

        Initialize the ``WorldBankParse()`` class.

        """
        self.indicator = indicator
        self.raw_data = wbdata.get_data(indicator)
        self.dict_keys = ['Country', 'Alpha2', 'Indicator', value_true_name, 'Year']
        self.final_col_order = ['Country', 'Alpha2', 'Alpha3', 'Currency', 'Indicator', value_true_name, 'Year']

        # Select the path to the data
        DATA_PATH = DEFAULT_DATA_PATH if data_path == None else data_path

        # Import Currency Code Database.
        self.CurrencyRelationshipsDB = pandas_str_column_to_list(pd.read_csv(DATA_PATH + "/CurrencyRelationshipsDB.csv"
                                                            , encoding = "ISO-8859-1"
                                                            , keep_default_na = False)
                                                            , columns = ['Alpha2', 'Alpha3'])

        # Import Country Codes Database.
        country_codes = pd.read_csv(DATA_PATH + "/ISOAlphaCodesDB.csv", encoding = "ISO-8859-1", keep_default_na = False)

        # Alpha2 --> Alpha 3
        self.alpha2_to_alpha3 = dict(zip(country_codes['Alpha2'].tolist(), country_codes['Alpha3'].tolist()))

        # Alpha2 --> Currency Code
        self.alpha2_to_currency_code = dict.fromkeys(set([i for sublist in self.CurrencyRelationshipsDB.Alpha2.tolist() for i in sublist]))
        for i in zip(self.CurrencyRelationshipsDB.Alpha2.tolist(), self.CurrencyRelationshipsDB.CurrencyCode.tolist()):
            for j in i[0]:
                if self.alpha2_to_currency_code[j] == None:
                    self.alpha2_to_currency_code[j] = i[1]

    def _wb_rowwise_extractor(self, wb_row):
        """

        *Private Method*
        Extracts desired (see return) row information from the raw World Bank download.

        :param wb_row: a row of the raw World Bank Data (as a dataframe).
        :type wb_row: dict
        :return: dict with keys: Country, country id, Indicator, CPI, Year
        :rtype: dict
        """
        # dict with empty keys
        extracted_data_dict = dict.fromkeys(self.dict_keys)

        # Populate extracted_data_dict
        extracted_data_dict[self.dict_keys[0]]  =  wb_row['country']['value']
        extracted_data_dict[self.dict_keys[1]]  =  wb_row['country']['id']
        extracted_data_dict[self.dict_keys[2]]  =  wb_row['indicator']['value']
        extracted_data_dict[self.dict_keys[3]]  =  wb_row['value']
        extracted_data_dict[self.dict_keys[4]]  =  wb_row['date']

        return extracted_data_dict

    def _titler(self, data_frame, to_title):
        """

        *Private Method*
        Titles entries in the column of a pandas dataframe.
        Includes some error handling.

        :param to_title: a list of columns to apply the following string operations: ``column.lower().title()``
        :type to_title: list
        :param data_frame: a dataframe with columns to be titled.
        :type data_frame: Pandas DataFrame
        :return: DataFrame with the requested indicator information.
        :rtype: Pandas DataFrame
        """
        df_cols = data_frame.columns.tolist()

        for t in to_title:
            if t not in df_cols:
                raise ValueError("%s is not a column in the data set" % (t))
            if any(x in str(data_frame[t].dtype) for x in ['float', 'int']):
                raise ValueError("Cannot Title this column; %s is a numeric." % (t))

            try:
                data_frame[t] = data_frame[t].astype(str).map(lambda x: x.lower().title())
            except:
                raise TypeError("Cannot convert the column '%s' to a str" % (t))

        return data_frame

    def _world_bank_pull(self, to_title = None):
        """

        *Private Method*
        Parse the information pulled from the world bank's API.

        :param to_title: a list of column to title. Defaults to None.
        :return: DataFrame with the requested indicator information.
        :rtype: Pandas Dataframe
        """
        if to_title != None and not isinstance(to_title, list):
            raise ValueError("title must be a list of column names (strings).")

        # Generate a list populated with dicts for each row of the raw data
        dictionaries = [self._wb_rowwise_extractor(w) for w in self.raw_data]

        # Merge by key
        merged_dict = {k: [x[k] for x in dictionaries] for k in dictionaries[0]}

        # Merge into a single data frame
        data_frame = pd.DataFrame.from_dict(merged_dict)

        # Title desired columns
        if to_title != None: data_frame = self._titler(data_frame, to_title)

        # Get Alpha3 from Alpha2
        data_frame['Alpha3'] = data_frame['Alpha2'].replace(self.alpha2_to_alpha3, inplace = False)

        # Replace failures to Match for Alpha3s with NaNs
        data_frame['Alpha3'][data_frame['Alpha2'] == data_frame['Alpha3']] = np.NaN

        # Get Currency Code from Alpha2
        data_frame['Currency'] = data_frame['Alpha2'].replace(self.alpha2_to_currency_code, inplace = False)

        # Replace failures to Match for Currency Codes with NaNs
        data_frame['Currency'][data_frame['Alpha2'] == data_frame['Currency']] = np.NaN

        # Sort by region and year
        data_frame.sort_values(['Country', 'Year'], ascending = [1, 0], inplace = True)

        # Refresh the index
        data_frame.index = range(data_frame.shape[0])

        # Reorder and Return, along with CurrencyRelationshipsDB
        return data_frame[self.final_col_order], self.CurrencyRelationshipsDB


def _world_bank_pull_wrapper(value_true_name, indicator, data_path = None, na_drop_col = None):
    """

    *Private Method*
    Wrapper for the ``WorldBankParse().world_bank_pull()`` method.
    Extracts world bank information based on a specific indicator and returns a Pandas DataFrame.

    :param value_true_name: see ``WorldBankParse()``.
    :type value_true_name: str
    :param indicator: see ``WorldBankParse()``.
    :type indicator: str
    :param data_path: see ``WorldBankParse()``.
    :type data_path: str
    :param na_drop_col: list of columns (str) to drop from the final dataframe. Defaults to None
    :type na_drop_col: list
    :return: DataFrame with the requested indicator information.
    :rtype: Pandas DateFrame
    """
    # Get the data
    data_frame, CurrencyRelationshipsDB = WorldBankParse(value_true_name, indicator, data_path)._world_bank_pull()

    # Remove Nones from the value_true_name (e.g., CPI) column
    data_frame = data_frame[data_frame[value_true_name].astype(str) != 'None']

    # Refresh the index
    data_frame.index = range(data_frame.shape[0])

    # Drop NaNs in Columns
    if na_drop_col != None:
        for col in na_drop_col:
            data_frame.drop(col, axis = 1, inplace = True)

    return data_frame, CurrencyRelationshipsDB





