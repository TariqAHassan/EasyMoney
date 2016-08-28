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


def floater(input_to_process, just_check=False):
    """

    :param input_to_process:
    :param just_check: return boolean if string can be converted to a float.
    :return:
    """

    try:
        float(input_to_process)
        return float(input_to_process) if not just_check else True
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

def strlist_to_list(to_parse):
    """

    "[1992, '221-21', 2102, 'apples']" --> ['1992', '221-21', '2102', 'apples']

    Eval() work around.
    Mechanism of Action: Dark Magic.

    :param to_parse:
    :return:
    """
    return [i.strip().replace("'", "") for i in [j.split(",") for j in [to_parse.replace("[", "").replace("]", "")]][0]]



def pandas_print_full(pd_df):
    """

    :param pd_df:
    :return:
    """
    pd.set_option('display.max_rows', len(pd_df))
    print(x)
    pd.reset_option('display.max_rows')








