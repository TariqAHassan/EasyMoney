#!/usr/bin/env python3

'''

    Tools for Obtaining Data from the World Bank Group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


'''

# Modules #
import os
import re
import wbdata
import numpy as np
import pandas as pd
import pkg_resources


from easymoney.support_money import DATA_PATH


class WorldBankParse(object):
    """

    | Tools to obtain indicator data from the World Bank's API.
    | DO NOT WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param value_true_name: replacement name for the generic 'value' column, e.g., 'value' to 'cpi'.
    :type value_true_name: str
    :param indicator: a indicator used by the World Bank's API, e.g., "FP.CPI.TOTL" for CPI.
    :type indicator: str
    """


    def __init__(self, value_true_name, indicator):
        """

        *Private Method*
        Int the WorldBankParse() class.

        """
        self.indicator = indicator
        self.raw_data = wbdata.get_data(indicator)
        self.dict_keys = ['region', 'alpha2', 'indicator', value_true_name, 'year']
        self.final_col_order = ['region', 'alpha2', 'alpha3', 'currency_code', 'indicator', value_true_name, 'year']

        # Import Currency Code Database.
        currency_df = pd.read_pickle(DATA_PATH + "/CurrencyCodes_DB.p")

        # Import Country Codes Database
        country_codes = pd.read_csv(DATA_PATH + "/CountryAlpha2_and_3.csv"
                                    , encoding = "ISO-8859-1"
                                    , keep_default_na = False)

        # Alpha2 --> Alpha 3
        self.alpha2_to_alpha3 = dict(zip(country_codes.Alpha2.tolist(), country_codes.Alpha3.tolist()))

        # Alpha2 --> Currency Code
        self.alpha2_to_currency_code = dict.fromkeys(set([i for sublist in currency_df.Alpha2.tolist() for i in sublist]))
        for i in zip(currency_df.Alpha2.tolist(), currency_df.CurrencyCode.tolist()):
            for j in i[0]:
                if self.alpha2_to_currency_code[j] == None:
                    self.alpha2_to_currency_code[j] = i[1]

    def _wb_rowwise_extractor(self, wb_row):
        """

        *Private Method*
        Extracts desired (see return) row information from the raw World Bank download.

        :param wb_row: a row of the raw World Bank Data (as a dataframe).
        :type wb_row: dict
        :return: dict with keys: region, region_id, indicator, cpi, year
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

        :param to_title: a list of columns to apply the following string operations: column.lower().title()
        :type to_title: list
        :param data_frame: a dataframe with columns to be titled.
        :type data_frame: Pandas DataFrame
        :return: DataFrame with the requested indicator information.
        :rtype: Pandas DataFrame
        """
        df_cols = data_frame.columns.tolist()

        for t in to_title:
            if t not in df_cols:
                raise ValueError("%s is not a column in the %s indicator data set.\n"
                                 "Perhaps you meant one of these: %s." % (t, indicator, ", ".join(df_cols)))
            if any(x in str(data_frame[t].dtype) for x in ['float', 'int']):
                raise ValueError("Cannot Title this column; %s is a numeric." % (t))

            try:
                data_frame[t] = data_frame[t].astype(str).map(lambda x: x.lower().title())
            except:
                raise TypeError("Cannot convert the column '%s' to a str" % (t))

        return data_frame

    def world_bank_pull(self, to_title = None):
        """

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
        data_frame['alpha3'] = data_frame['alpha2'].replace(self.alpha2_to_alpha3, inplace = False)

        # Replace failures to Match for Alpha3s with NaNs
        data_frame['alpha3'][data_frame['alpha2'] == data_frame['alpha3']] = np.NaN

        # Get Currency Code from Alpha2
        data_frame['currency_code'] = data_frame['alpha2'].replace(self.alpha2_to_currency_code, inplace = False)

        # Replace failures to Match for Currency Codes with NaNs
        data_frame['currency_code'][data_frame['alpha2'] == data_frame['currency_code']] = np.NaN

        # Reorder and Return
        return data_frame[self.final_col_order]


def world_bank_pull_wrapper(value_true_name, indicator, na_drop_col = None):
    """

    Wrapper for the WorldBankParse().world_bank_pull() method.
    Extracts world bank information based on a specific indicator and returns a Pandas DataFrame.

    :param value_true_name: replacement name for the generic 'value' column, e.g., 'value' to 'cpi'.
    :type value_true_name: str
    :param indicator: a indicator used by the World Bank's API, e.g., "FP.CPI.TOTL" for CPI.
    :type indicator: str
    :param na_drop_col: list of columns (str) to drop from the final dataframe.
    :type na_drop_col: list
    :return: DataFrame with the requested indicator information.
    :rtype: Pandas DateFrame
    """
    data_frame = WorldBankParse(value_true_name, indicator).world_bank_pull()
    data_frame = data_frame[data_frame[value_true_name].astype(str) != 'None']
    data_frame.index = range(data_frame.shape[0])

    # Drop NaNs in Columns
    if na_drop_col != None:
        for col in na_drop_col:
            data_frame.drop(col, axis = 1, inplace = True)

    return data_frame

