#!/usr/bin/env python3

'''

Tools for Obtaining World Bank Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

'''

# Modules #
import re
import wbdata
import numpy as np
import pandas as pd


class WorldBankParse(object):
    """

    Get indicator data from the World Bank.

    """


    def __init__(self, value_true_name, indicator):
        self.indicator = indicator
        self.raw_data = wbdata.get_data(indicator)
        self.dict_keys = ['region', 'alpha2', 'indicator', value_true_name, 'year']
        self.final_col_order = ['region', 'alpha2', 'alpha3', 'currency_code', 'indicator', value_true_name, 'year']

        # Import Currency Code Database.
        currency_df = pd.read_pickle("easy_money/easy_data/CurrencyCodes_DB.p")

        # Alpha2 --> Alpha 3
        self.alpha2_to_alpha3 = dict.fromkeys(set([i for sublist in currency_df.Alpha2.tolist() for i in sublist]))
        for i in zip(currency_df.Alpha2.tolist(), currency_df.Alpha3.tolist()):
            for j in range(len(i[0])):
                if self.alpha2_to_alpha3[i[0][j]] == None:
                    self.alpha2_to_alpha3[i[0][j]] = i[1][j]

        # Alpha2 --> Currency Code
        self.alpha2_to_currency_code = dict.fromkeys(set([i for sublist in currency_df.Alpha2.tolist() for i in sublist]))
        for i in zip(currency_df.Alpha2.tolist(), currency_df.CurrencyCode.tolist()):
            for j in i[0]:
                if self.alpha2_to_currency_code[j] == None:
                    self.alpha2_to_currency_code[j] = i[1]

    def _wb_rowwise_extractor(self, wb_row):
        """

        Extracts desired (see return) row information from the raw World Bank download.

        :param wb_row:
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

        Titles entries in the column of a pandas dataframe.
        Includes some error handling.

        :param to_title:
        :param data_frame:
        :return:
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

        :param to_title: a list of column to title.
        :return: a dataframe with
        :rtype: pandas dataframe
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







