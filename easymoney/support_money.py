#!/usr/bin/env python3

"""

Support Tools
~~~~~~~~~~~~~


"""

# Modules #
import numpy as np
import pandas as pd
import datetime


def floater(input_to_process, just_check = False, override_to_int = False):
    """

    Check if input can be converted to a floating point number.

    :param input_to_process: object.
    :type input_to_process: any
    :param just_check: if string can be converted to a float. Defaults to False.
    :type just_check: bool
    :param override_to_int: override output to be an int. Defaults to False.
    :type override_to_int: bool
    :return:
    """
    try:
        float(input_to_process)
        return (int(float(input_to_process)) if override_to_int else float(input_to_process)) if not just_check else True
    except:
        return np.NaN if not just_check else False

def twoD_nested_dict(data_frame, nest_col_a, nest_col_b, nest_col_c, to_float = None, to_int = None):
    """

    Generate a nested dictionary from the columns of a pandas dataframe.

    :param data_frame: a pandas dataframe.
    :type data_frame: DateFrame
    :param nest_col_a: reference to column in the dataframe; to become the master key in dict.
    :type nest_col_a: str
    :param nest_col_b: reference to column in the dataframe; to become the sub-key.
    :type nest_col_b: str
    :param nest_col_c: reference to column in the dataframe; to become the value to corresponding to the sub-key.
    :type nest_col_c: str
    :param to_float: a list items to float. Defaults to None.
    :rtype to_float: str
    :param to_int: a list of the lists to convert to ints. Defaults to None.
    :rtype to_int: str
    :return: nested dict.
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

    Eval() work around for str(list) --> list.
    For example: "[1992, '221-21', 2102, 'apples']" --> ['1992', '221-21', '2102', 'apples']

    :param to_parse: a string of a list.
    :type to_parse: str
    :return: string of a list to an actual list.
    :return: list
    """
    return [i.strip().replace("'", "") for i in [j.split(",") for j in [to_parse.replace("[", "").replace("]", "")]][0]]

def alpha2_to_alpha2_unpack(pandas_series, unpack_dict):
    """

    Unpacks ISO Alpha2 --> Alpha2 ISO code Pandas Series
    (could be applied more generally, but the need has not emerged).

    :param pandas_series: a Series to replace the alpha2 codes with another set.
    :type pandas_series: Pandas Series
    :param unpack_dict: a dict with the values coerced into strings.
    :type unpack_dict: dict
    :return: a pandas series with the alpha2 values replaced with unpack_dict.values(). NaNs are used if a match cannot be found.
    :rtype: Pandas Series
    """
    # Hacking the living daylights out of the pandas API
    return pandas_series.replace(unpack_dict).map(lambda x: np.NaN if 'nan' in str(x) else strlist_to_list(str(x)))

def _dict_key_remove(input_dict, to_remove = np.nan, wrt = 'both'):
    """

    Remove a single item from a list.

    :param input_dict: any dictionary.
    :type input_dict: dict
    :param to_remove: object to remove.
    :type to_remove: any
    :param wrt: with respect to: 'key' for dict keys, 'value' for dict values, 'both' for both key and value. Defaults to both.
    :type wrt: str
    :return: a dictionary with the desired item removed.
    :rtype: dict
    """
    if wrt in ['key', 'value']:
        return {k: v for k, v in input_dict.items() if str((k if wrt == 'key' else v)) != str(to_remove)}
    elif wrt == 'both':
        return {k: v for k, v in input_dict.items() if (str(k) != str(to_remove) and str(v) != str(to_remove))}

def remove_from_dict(input_dict, to_remove = [np.nan], wrt = 'both'):
    """

    Remove a list of items from a dict; _dict_key_remove() wrapper.

    :param input_dict: any dictionary.
    :type input_dict: dict
    :param to_remove: a list of items to remove. Default to [np.nan].
    :type to_remove: list
    :param wrt: with respect to: 'key' for dict keys, 'value' for dict values, 'both' for both key and value. Defaults to both.
    :type wrt: str
    :return: dictionary with the to_remove items eliminated.
    :rtype: dict
    """
    for r in to_remove:
        input_dict = _dict_key_remove(input_dict, r, wrt)

    return input_dict

def key_value_flip(dictionary):
    """

    Reverse the keys and values in a dictionary.

    :param dictionary: any dictionary (cannot be nested).
    :type dictionary: dict
    :return: reveresed dict.
    :rtype: dict
    """
    return dict([(v, k) for k, v in dictionary.items()])

def money_printer(money, round_to):
    """

    Pretty Prints an Amount of Money.

    :param money: a numeric amount.
    :type money: float or int
    :param round_to: places to round to after the desimal.
    :type round_to: int
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

    :param input_list: a list of values.
    :type input_list: list
    :return: try: return the min and max value in the list ([min, max]); returns [nan, nan] on failure.
    :rtype: list
    """
    if not isinstance(input_list, list):
        raise ValueError("input_list must be a list.")
    try:
        return [min(input_list), max(input_list)]
    except:
        return [np.NaN, np.NaN]

def str_to_datetime(list_of_dates, date_format = "%Y-%m-%d"):
    """

    Converts a string to a datetime object.

    :param list_of_dates: a list of strings (dates).
    :type list_of_dates: list
    :param date_format: a date format; defaults to %Y-%m-%d.
    :type date_format: str
    :return: a list of datetimes.
    :rtype: list
    """
    return [datetime.datetime.strptime(d, date_format) for d in list_of_dates]

def datetime_to_str(list_of_dates, date_format = "%Y-%m-%d"):
    """

    Convert a datetime.datetime object to a string.

    :param list_of_dates: a list of datetimes.
    :type list_of_dates: list
    :param date_format: a date format; defaults to: %Y-%m-%d.
    :type date_format: str
    :return: a string of the date, formatted according to date_format.
    :rtype: str
    """
    return [d.strftime(date_format) for d in list_of_dates]

def pandas_print_full(pd_df, full_rows = True, full_cols = True):
    """

    Print *all* of a Pandas DataFrame.

    :param pd_df: Pandas DataFrame
    :param full_rows: print all rows if True. Defaults to True.
    :type full_rows: bool
    :param full_cols: print all columns side-by-side if True. Defaults to True.
    :type full_cols: bool
    """
    if full_rows: pd.set_option('display.max_rows', len(pd_df))
    if full_cols: pd.set_option('expand_frame_repr', False)

    # Print the data frame
    print(pd_df)

    if full_rows: pd.reset_option('display.max_rows')
    if full_cols: pd.set_option('expand_frame_repr', True)

def _floor_or_ceiling_date(year, dtype = 'floor'):
    """

    Floor (Jan 1) or Ceiling (Dec 31) a date.

    :param year: a year to convert to YYYY-MM-DD.
    :type year: int
    :param dtype: 'floor' to floor a date; 'ceiling' to ceiling a date. Defaults to 'floor'.
    :type dtype: str
    :return: a floored or ceilinged date.
    :rtype: str
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

    :param date_ranges: format: [[minimum, maximum], [minimum, maximum], ...].
    :type date_ranges: 2D list
    :return: min and max date.
    :rtype: list
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










