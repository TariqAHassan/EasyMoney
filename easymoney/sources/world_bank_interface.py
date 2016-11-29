#!/usr/bin/env python3

"""

    World Bank Group Data
    ~~~~~~~~~~~~~~~~~~~~~

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


def _wb_pull(dict_keys, raw_data):
    """

    Parse the information pulled from the World Bank's API.

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


def world_bank_pull(value_true_name=None, indicator="FP.CPI.TOTL", return_as='data_frame'):
    """

    | Tool to harvest data for specific indicator from the World Bank Group via their generously provided API.
    | Extracts world bank information based on a specific indicator and returns a Pandas DataFrame.
    | Currently, this tools expects the following in the XML data:
                country, ISO alpha 2 code, an indicator, value name (to be replaced by value_true_name) and year.
    | Please do not write procedures that slam their servers.
    |
    | Acknowledgement: this tools is made possible by the `wbdata` package.¹
    |
    | ¹Sherouse, Oliver (2014). Wbdata. Arlington, VA.
    |

    :param value_true_name: reable name for the indicator. If None, this information will be extract from ``indicator``.
                            Defaults to None.
    :type value_true_name: ``str``
    :param indicator: World Bank Indicator. Defaults to "FP.CPI.TOTL".
    :type indicator: ``str``
    :param return_as: 'data_frame' or 'dict'
    :type return_as: ``str``
    :return: DataFrame with the requested indicator information or a dictionary
    :rtype: ``dict`` or ``Pandas DateFrame``
    """
    raw_data = wbdata.get_data(indicator)
    readable_name = value_true_name.split(".")[1] if value_true_name != None else value_true_name
    dict_keys = ['Country', 'Alpha2', 'Indicator', readable_name, 'Year']

    # Convert to DataFrame
    df = _wb_pull(dict_keys, raw_data)

    # Fill Empty Values with NaNs
    df = df.fillna(value=np.NaN).dropna(subset=['Year', 'Alpha2', readable_name]).reset_index(drop=True)

    if return_as == 'data_frame':
        return df
    elif return_as == 'dict':
        return twoD_nested_dict(df, 'Year', 'Alpha2', readable_name)
    elif return_as == 'both':
        return df, twoD_nested_dict(df, 'Year', 'Alpha2', readable_name)
    else:
        raise ValueError("Invalid option passed to `return_as`.")

































