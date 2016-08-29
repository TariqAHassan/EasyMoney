#!/usr/bin/env python3

"""

Support Tools
~~~~~~~~~~~~~

Python 3.5

"""

# Imports
import numpy as np
import pandas as pd
import datetime


def floater(input_to_process, just_check = False, override_to_int = False):
    """

    :param input_to_process:
    :param just_check: return boolean if string can be converted to a float.
    :return:
    """

    try:
        float(input_to_process)

        return (int(float(input_to_process)) if override_to_int else float(input_to_process)) if not just_check else True
    except:
        return np.NaN if not just_check else False

def twoD_nested_dict(data_frame, nest_col_a, nest_col_b, nest_col_c, to_float = None, to_int = None):
    """

    Generate a nested dictionary from the columns of a pandas dataframe

    :param data_frame: a pandas dataframe
    :param nest_col_a: string reference to column in the dataframe; to become the master key in dict
    :param nest_col_b: string reference to column in the dataframe; to become the sub-key
    :param nest_col_c: string reference to column in the dataframe; to become the value to corresponding to the sub-key
    :param c_col_to_float: a list of the lists to float
    :return: nested dict
    :rtype: dict
    """

    # Convert selected columns to float
    if to_float != None:
        for i in to_float: data_frame[i] = data_frame[i].astype(float)

    # Convert selected columns to int
    if to_int != None:
        for j in to_int: data_frame[j] = data_frame[j].astype(int)

    master_dict = dict.fromkeys(data_frame[nest_col_a].astype(str).str.upper().unique())
    for k in master_dict.keys():
        slice = data_frame[data_frame[nest_col_a] == k]
        master_dict[k] = dict(zip(slice[nest_col_b].astype(str), slice[nest_col_c]))

    return master_dict

def strlist_to_list(to_parse):
    """

    Eval() work around for: "[1992, '221-21', 2102, 'apples']" --> ['1992', '221-21', '2102', 'apples']

    :param to_parse:
    :return:
    """
    return [i.strip().replace("'", "") for i in [j.split(",") for j in [to_parse.replace("[", "").replace("]", "")]][0]]

def alpha2_to_alpha2_unpack(pandas_series, unpack_dict):
    """

    :param pandas_series:
    :param unpack_dict:
    :return:
    """

    # Hacking the living daylights out of the pandas API
    return pandas_series.replace(unpack_dict).map(lambda x: np.NaN if 'nan' in str(x) else strlist_to_list(str(x)))

def _dict_key_remove(input_dict, to_remove = np.nan, wrt = 'both'):
    """

    :param input_dict:
    :param to_remove:
    :return:
    """

    if wrt in ['key', 'value']:
        return {k: v for k, v in input_dict.items() if str((k if wrt == 'key' else v)) != str(to_remove)}
    elif wrt == 'both':
        return {k: v for k, v in input_dict.items() if (str(k) != str(to_remove) and str(v) != str(to_remove))}

def remove_from_dict(input_dict, to_remove = [np.nan], wrt = 'both'):
    """

    :param input_dict:
    :param to_remove:
    :param wrt:
    :return:
    """

    for r in to_remove:
        input_dict = _dict_key_remove(input_dict, r, wrt)

    return input_dict

def key_value_flip(dictionary):
    """

    :param dictionary:
    :return:
    """
    return dict([(v, k) for k, v in dictionary.items()])

def money_printer(money, round_to):
    """

    :param money:
    :return:
    """

    money_to_handle = str(round(floater(money), round_to))
    split_money = money_to_handle.split(".")

    if len(split_money[1]) == 1:
        return money_to_handle + "0"
    elif len(split_money[1]) == 2:
        return money_to_handle
    elif len(split_money[1]) > 2:
        return ".".join([split_money[0], str(round(float(split_money[1]), -3))[:2]])
    else:
        raise ValueError("Invalid money conversion requested.")

def min_max(input_list):
    """

    Gets min and max of a list.
    Obviously, each of these are O(n).

    :param input_list:
    :return:
    """
    if not isinstance(input_list, list):
        raise ValueError("input_list must be a list.")
    try:
        return [min(input_list), max(input_list)]
    except:
        return [np.NaN, np.NaN]

def str_to_datetime(list_of_dates, date_format = "%Y-%m-%d"):
    """

    :param list_of_dates:
    :param date_format:
    :return:
    """
    return [datetime.datetime.strptime(d, date_format) for d in list_of_dates]

def datetime_to_str(list_of_dates, date_format = "%Y-%m-%d"):
    """

    :param list_of_dates:
    :param date_format:
    :return:
    """
    return [d.strftime(date_format) for d in list_of_dates]

def pandas_print_full(pd_df, full_rows = True, full_cols = True):
    """

    :param pd_df:
    :return:
    """

    if full_rows:
        pd.set_option('display.max_rows', len(pd_df))
    if full_cols:
        pd.set_option('expand_frame_repr', False)

    # Print the data frame
    print(pd_df)

    if full_rows:
        pd.reset_option('display.max_rows')
    if full_cols:
        pd.set_option('expand_frame_repr', True)

def _floor_or_ceiling_date(year, dtype = 'floor'):
    """

    :param year:
    :param dtype:
    :return:
    """
    if not floater(year, just_check = True) or not len(year) == 4:
        return year
    if dtype == 'floor':
        return year + "-01-01"
    elif dtype == 'ceiling':
        return year + "-12-31"

def date_bounds_floor(date_ranges):
    """

    This function rounds dates to their poles, i.e., max: YYYY --> YYYY-12-31; min: YYYY --> YYYY-01-01.
    and finds the floors maximum minimum date as well as the minimum maximum date (see date_ranges description).

    :param date_ranges: format: [[minimum, maximum], [minimum, maximum], ...]
    :return:
    """

    # Check for Nones and NaNs
    if True in [str(i) in ['None', 'nan'] for i in date_ranges]:
        return np.NaN

    # Checks that date_ranges is a list of lists (not perfect, but should catch 99% of cases).
    if False in [isinstance(i, list) for i in date_ranges] or \
        True in [item for s in [[isinstance(j, list) for j in i] for i in date_ranges] for item in s]:
        raise ValueError('date_ranges must be a list of lists.')

    # Check all sublists in date_range are the same length
    if len(set([len(l) for l in date_ranges])) != 1:
        raise ValueError('All sublists in date_ranges must be of the same length')

    # Convert date_ranges to a numpy array
    dates = np.array(date_ranges)

    # Round dates to their poles.
    rounded_dates = [[_floor_or_ceiling_date(i, dtype = j[1]) for i in dates[:,j[0]]] for j in [[0, 'floor'], [1, 'ceiling']]]

    # Compute the floors and return
    return [max(rounded_dates[0]), min(rounded_dates[1])]


















































