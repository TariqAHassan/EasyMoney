#!/usr/bin/env python3

"""

    Tools for Obtaining Data from the World Bank Group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import re
import wbdata
import numpy as np
import pandas as pd

from easymoney.easy_pandas import twoD_nested_dict


def _wb_rowwise_extractor(wb_row, dict_keys):
    """

    Extracts desired (see return) row information from the raw World Bank download.

    :param wb_row: a row of the raw World Bank Data (as a dataframe).
    :type wb_row: dict
    :return: dict with keys: Country, country id, Indicator, CPI, Year
    :rtype: dict
    """
    # dict with empty keys
    extracted_data_dict = dict.fromkeys(dict_keys)

    # Populate extracted_data_dict
    extracted_data_dict[dict_keys[0]]  =  wb_row['country']['value']
    extracted_data_dict[dict_keys[1]]  =  wb_row['country']['id']
    extracted_data_dict[dict_keys[2]]  =  wb_row['indicator']['value']
    extracted_data_dict[dict_keys[3]]  =  wb_row['value']
    extracted_data_dict[dict_keys[4]]  =  wb_row['date']

    return extracted_data_dict


def _world_bank_pull(dict_keys, raw_data):
    """

    Parse the information pulled from the world bank's API.

    :param dict_keys:
    :return: DataFrame with the requested indicator information.
    :rtype: Pandas Dataframe
    """
    # Generate a list populated with dicts for each row of the raw data
    dictionaries = [_wb_rowwise_extractor(w, dict_keys) for w in raw_data]

    # Merge by key
    merged_dict = {k: [x[k] for x in dictionaries] for k in dictionaries[0]}

    # Merge into a single data frame
    data_frame = pd.DataFrame.from_dict(merged_dict)

    # Sort by region and year
    return data_frame.sort_values(['Alpha2', 'Year'], ascending = [1, 0]).reset_index(drop=True)


def world_bank_pull_wrapper(value_true_name="CPI", indicator="FP.CPI.TOTL", return_as='data_frame'):
    """

    Wrapper for the ``WorldBankParse().world_bank_pull()`` method.
    Extracts world bank information based on a specific indicator and returns a Pandas DataFrame.

    :param value_true_name:
    :type value_true_name: str
    :param indicator:
    :type indicator: str
    :param return_as: 'data_frame' or 'dict'
    :type return_as: str
    :return: DataFrame with the requested indicator information or a dictionary
    :rtype: Pandas DateFrame or dict
    """
    raw_data = wbdata.get_data(indicator)
    dict_keys = ['Country', 'Alpha2', 'Indicator', value_true_name, 'Year']

    # Convert to DataFrame
    df = _world_bank_pull(dict_keys, raw_data)

    # Fill Empty Values with NaNs
    df = df.fillna(value=np.NaN).dropna(subset=['Year', 'Alpha2', 'CPI']).reset_index(drop=True)

    if return_as == 'data_frame':
        return df
    elif return_as == 'dict':
        return twoD_nested_dict(df, 'Year', 'Alpha2', 'CPI')
    elif return_as == 'both':
        return df, twoD_nested_dict(df, 'Year', 'Alpha2', 'CPI')
    else:
        raise ValueError("Invalid option passed to `return_as`.")

































