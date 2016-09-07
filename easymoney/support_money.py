#!/usr/bin/env python3

"""

    Support Tools
    ~~~~~~~~~~~~~

A collection of handy little tools.

"""

# Modules #
import copy
import warnings
import datetime
import numpy as np
import pandas as pd
import pkg_resources


# TO DO: Functions need to be better organized.


def floater(input_to_process, just_check = False, override_to_int = False):
    """

    *Private Method*
    Check if input can be converted to a floating point number.

    :param input_to_process: object.
    :type input_to_process: any
    :param just_check: if string can be converted to a float. Defaults to False.
    :type just_check: bool
    :param override_to_int: override output to be an int. Defaults to False.
    :type override_to_int: bool
    :return: input_to_process as a float, int or boolean (if just_check is True).
    :rtype: float or int
    """
    try:
        float(input_to_process)
        return (int(float(input_to_process)) if override_to_int else float(input_to_process)) if not just_check else True
    except:
        return np.NaN if not just_check else False

def _standard_pd_nester(data_frame, nest_col_a, nest_col_b, nest_col_c, keys_to_str = True):
    """

    *Private Method*
    Method to produce a nested dict from a large pandas dataframe.
    Reliable technique (although slow with large DataFrames).

    :param data_frame: see ``twoD_nested_dict()``.
    :type data_frame: Pandas DataFrame
    :param nest_col_a: see ``twoD_nested_dict()``.
    :type nest_col_a: str
    :param nest_col_b: see ``twoD_nested_dict()``.
    :type nest_col_b: str
    :param nest_col_c: see ``twoD_nested_dict()``.
    :type nest_col_c: str
    :param keys_to_str: see ``twoD_nested_dict()``.
    :type keys_to_str: bool
    :return: nested dict of the form {nest_col_a: {nest_col_b: nest_col_c}.
    :rtype: dict
    """
    # Initialize
    df_slice = None

    # Make columns that are to become keys strings.
    if keys_to_str:
        data_frame[nest_col_a] = data_frame[nest_col_a].astype(str).str.upper()
        data_frame[nest_col_b] = data_frame[nest_col_b].astype(str)

    # Create a dict from keys()
    nested_dict = dict.fromkeys(data_frame[nest_col_a].unique())
    for k in nested_dict.keys():
        df_slice = data_frame[data_frame[nest_col_a] == k]
        nested_dict[k] = dict(zip(df_slice[nest_col_b], df_slice[nest_col_c]))

    return nested_dict

def _fast_pd_nester(data_frame, nest_col_a, nest_col_b, nest_col_c, keys_to_str = True):
    """

    | *Private Method*
    | This is a *VERY* fast way to produce a nested dict from a large Pandas DataFrames.
    | Can handle DataFrames with several nest_col_a entries that are the same,
    | e.g.,
    |         nest_col_a    nest_col_b  nest_col_c
    | 0       1999-01-04      AUD          0
    | 1       1999-01-04      CAD          1
    | 2       1999-01-05      CHF          2
    | 3       1999-01-05      CYP          3
    |
    | WARNING: Not well-tested.

    :param data_frame: see ``twoD_nested_dict()``.
    :type data_frame: Pandas DataFrame
    :param nest_col_a: see ``twoD_nested_dict()``.
    :type nest_col_a: str
    :param nest_col_b: see ``twoD_nested_dict()``.
    :type nest_col_b: str
    :param nest_col_c: see ``twoD_nested_dict()``.
    :type nest_col_c: str
    :param keys_to_str: see ``twoD_nested_dict()``.
    :type keys_to_str: bool
    :return: nested dict of the form {nest_col_a: {nest_col_b: nest_col_c}.
    :rtype: dict
    """
    # Group nest_col_b and nest_col_c by nest_col_a
    col_b_groupby = data_frame.groupby(nest_col_a)[nest_col_b].apply(lambda x: x.tolist()).reset_index()
    col_c_groupby = data_frame.groupby(nest_col_a)[nest_col_c].apply(lambda x: x.tolist()).reset_index()

    # Merge on nest_col_a
    grouped_data_frame = pd.merge(col_b_groupby, col_c_groupby, on = nest_col_a, how = 'outer')

    # Convert columns that will become keys to a string
    if keys_to_str:
        grouped_data_frame[nest_col_a] = grouped_data_frame[nest_col_a].astype(str)
        grouped_data_frame[nest_col_b] = grouped_data_frame[nest_col_b].map(lambda x: [str(i) for i in x])

    # Generate a dictionary by zipping the nest_col_b and nest_col_c columns
    grouped_data_frame['dict_zipped'] = grouped_data_frame[[nest_col_b, nest_col_c]].apply(
                                                                    lambda x: dict(zip(x[0], x[1])), axis = 1)

    # Return as a nested dict
    return dict(zip(grouped_data_frame[nest_col_a], grouped_data_frame['dict_zipped']))

def twoD_nested_dict(data_frame
                     , nest_col_a = None
                     , nest_col_b = None
                     , nest_col_c = None
                     , to_float = None
                     , to_int = None
                     , keys_to_str = True
                     , engine = 'standard'):
    """

    *Private Method*
    Generate a nested dictionary from the columns of a pandas dataframe.
    Defaults to using the first 3 columns.

    :param data_frame: a pandas dataframe.
    :type data_frame: DateFrame
    :param nest_col_a: reference to column in the dataframe; to become the master key in dict.
                       Defaults to None (i.e., col 1).
    :type nest_col_a: str
    :param nest_col_b: reference to column in the dataframe; to become the sub-key.
                       Defaults to None (i.e., col 2).
    :type nest_col_b: str
    :param nest_col_c: reference to column in the dataframe; to become the value to corresponding to the sub-key.
                       Defaults to None (i.e., col 3).
    :type nest_col_c: str
    :param to_float: a list items to float. Defaults to None.
    :type to_float: str
    :param to_int: a list of the lists to convert to ints. Defaults to None.
    :type to_int: str
    :param keys_to_str: Convert the columns that will become keys to strings. Default to True.
                        WARNING: will OVERRIDE *to_float* and *to_int* if they reference nest_col_a or nest_col_b.
    :param engine: 'standard' for a slower (but better tested) method of generating a nested dict;
                   'fast' to employ a very speedy (but not well tested) method for generating a nested dict.
                    Default to 'standard'.
    :type engine: str
    :return: nested dict of the form {nest_col_a: {nest_col_b: nest_col_c}.
    :rtype: dict
    """
    if all(v is None for v in [nest_col_a, nest_col_b, nest_col_c]):
        nest_col_a = data_frame.columns[0]
        nest_col_b = data_frame.columns[1]
        nest_col_c = data_frame.columns[2]

    # Convert selected columns to float
    if to_float != None:
        for i in to_float: data_frame[i] = data_frame[i].astype(float)

    # Convert selected columns to int
    if to_int != None:
        for j in to_int: data_frame[j] = data_frame[j].astype(int)

    # Use one of two engines to generate the nested dict
    if engine == 'standard':
        return _standard_pd_nester(data_frame, nest_col_a, nest_col_b, nest_col_c, keys_to_str)

    elif engine == 'fast':
        return _fast_pd_nester(data_frame, nest_col_a, nest_col_b, nest_col_c, keys_to_str)

def strlist_to_list(to_parse, convert_to_str_first = False):
    """

    *Private Method*
    Eval() work around for str(list) --> list.
    For example: "[1992, '221-21', 2102, 'apples']" --> ['1992', '221-21', '2102', 'apples'].

    :param to_parse: a string of a list.
    :type to_parse: str
    :param convert_to_str_first: convert to a string first (as a precaution). Defaults to False.
    :type convert_to_str_first: bool
    :return: string of a list to an actual list.
    :return: list
    """
    str_list = str(to_parse) if convert_to_str_first else to_parse
    return [i.strip().replace("'", "") for i in [j.split(",") for j in [str_list.replace("[", "").replace("]", "")]][0]]

def pandas_dictkey_to_key_unpack(pandas_series, unpack_dict):
    """

    *Private Method*
    Unpacks ISO Alpha2 --> Alpha2 ISO code Pandas Series.

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

    *Private Method*
    Remove a single item from a list.

    :param input_dict: any dictionary.
    :type input_dict: dict
    :param to_remove: object to remove.
    :type to_remove: any
    :param wrt: with respect to: 'key' for dict keys, 'value' for dict values, 'both' for both key and value. Defaults to 'both'.
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

    *Private Method*
    Remove a list of items from a dict; _dict_key_remove() wrapper.

    :param input_dict: any dictionary.
    :type input_dict: dict
    :param to_remove: a list of items to remove. Default to [np.nan].
    :type to_remove: list
    :param wrt: with respect to: 'key' for dict keys, 'value' for dict values, 'both' for both key and value. Defaults to 'both'.
    :type wrt: str
    :return: dictionary with the to_remove items eliminated.
    :rtype: dict
    """
    for r in to_remove:
        input_dict = _dict_key_remove(input_dict, r, wrt)

    return input_dict

def key_value_flip(dictionary):
    """

    *Private Method*
    Reverse the keys and values in a dictionary.

    :param dictionary: any dictionary (cannot be nested).
    :type dictionary: dict
    :return: reveresed dict.
    :rtype: dict
    """
    return dict([(v, k) for k, v in dictionary.items()])

def dict_list_unpack(dictionary):
    """

    Flips keys and values when values are lists.

    :param dictionary: {key1: ['a','b'], key2: ['c', 'd']...}
    :type dictionary: dict
    :return: {'a': key1, 'b': key1, 'c': key2, 'd': key2}
    """

    # Create alpha2_to_currency dict and populate using the currency_to_alpha2 dict.
    # If the below code seems dense, it's the same result as produced by this:
    # alpha2_to_currency = dict()
    # for k, v in currency_to_alpha2.items():
    #     for i in v: alpha2_to_currency[i] = k
    # ...but more fun!

    return dict([item for s in [[(i, k) for i in v] for k, v in dictionary.items()] for item in s])

def money_printer(money, currency = None, year = None, round_to = 2):
    """

    *Private Method*
    Pretty Prints an Amount of Money.

    :param money: a numeric amount.
    :type money: float or int
    :param round_to: places to round to after the desimal.
    :type round_to: int
    """
    # Initialize
    money_to_handle = str(round(floater(money), round_to))
    split_money = money_to_handle.split(".")
    to_return = None

    if len(split_money[1]) == 1:
        to_return = money_to_handle + "0"
    elif len(split_money[1]) == 2:
        to_return =  money_to_handle
    elif len(split_money[1]) > 2:
        to_return =  ".".join([split_money[0], str(round(float(split_money[1]), -3))[:2]])
    else:
        raise ValueError("Invalid money conversion requested.")

    if currency != None or year != None:
        tail = (str(year) if year != None else '')  + \
               (" " if isinstance(currency, str) and year != None else '') + \
               (str(currency) if isinstance(currency, str) else '')
        return to_return + (" " + tail if isinstance(currency, str) and year == None else " (" + tail + ")")
    else:
        return to_return

def min_max(input_list):
    """

    *Private Method*
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

    *Private Method*
    Converts a string to a datetime object.

    :param list_of_dates: a list of strings (dates).
    :type list_of_dates: list
    :param date_format: a date format; defaults to '%Y-%m-%d'.
    :type date_format: str
    :return: a list of datetimes.
    :rtype: list
    """
    date_str = datetime.datetime.strptime
    datetimes = [date_str(d, date_format) for d in ([list_of_dates] if isinstance(list_of_dates, str) else list_of_dates)]
    return datetimes[0] if isinstance(list_of_dates, str) else datetimes

def datetime_to_str(list_of_dates, date_format = "%Y-%m-%d"):
    """

    *Private Method*
    Convert a datetime.datetime object to a string.

    :param list_of_dates: a list of datetimes.
    :type list_of_dates: list
    :param date_format: a date format; defaults to '%Y-%m-%d'.
    :type date_format: str
    :return: a string of the date, formatted according to date_format.
    :rtype: str
    """
    datetimes = [d.strftime(date_format) for d in ([list_of_dates] if isinstance(list_of_dates, datetime.datetime) else list_of_dates)]
    return datetimes[0] if isinstance(list_of_dates, str) else datetimes

def pandas_print_full(pd_df, full_rows = True, full_cols = True):
    """

    *Private Method*
    Print *all* of a Pandas DataFrame.

    :param pd_df: DataFrame to printed in its entirety.
    :type pd_df: Pandas DataFrame
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

    *Private Method*
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

    *Private Method*
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

def prettify_list_of_strings(input_list, final_join = "and", all_commas_override = False):
    """

    Convert a list of strings into a sentence-like format.

    :param input_list: a list of strings.
    :type input_list: str
    :param final_join: string to join the final list items when then length of the input list is greater than one.
    :type final_join: str
    :param all_commas_override: join the list on commas.
    :type all_commas_override: bool
    :return: a joined list.
    :rtype: str
    """
    # Initialize
    final_join_with_tails = " " + final_join + " "

    # Error Handling
    if not isinstance(input_list, list):
        raise ValueError('input_list must be a list')
    if len(input_list) == 0:
        raise ValueError("input_list is empty.")

    # Combine into a single string
    if len(input_list) == 1:
        return input_list[0]
    elif all_commas_override:
        return ", ".join(input_list)
    elif len(input_list) == 2:
        return final_join_with_tails.join(input_list)
    elif len(input_list) > 2:
        return ", ".join(input_list[:-1]) + final_join_with_tails + input_list[-1]

def dict_merge(first_dict, second_dict):
    """

    Merge two dictionaries.

    :param first_dict: any dict.
    :type first_dict: dict
    :param second_dict: any dict.
    :type second_dict: dict
    :return: a merged dict.
    :rtype: dict
    """

    # Create deepcopies of the input
    new_dict = copy.deepcopy(first_dict)
    dict2 = copy.deepcopy(second_dict)

    # Merge
    new_dict.update(dict2)

    # Return
    return new_dict

def pandas_list_column_to_str(data_frame, columns):
    """

    Tool for converting the columns in a Pandas DataFrame
    from pd.Series of lists into comma-seperated strings.

    :param data_frame: any DataFrame
    :type data_frame: Pandas DataFrame
    :param columns: a list of columns in the DataFrame
    :type columns: list
    :return: a DataFrame with the columns altered in the manner described above.
    :rtype: Pandas DataFrame
    """
    data_frame = copy.deepcopy(data_frame)
    for col in columns:
        data_frame[col] = data_frame[col].map(lambda x: ", ".join([str(i) if not isinstance(i, str) else i for i in x]))

    return data_frame

def pandas_str_column_to_list(data_frame, columns):
    """

    Tool for converting the columns in a Pandas DataFrame
    from comma-seperated strings into a pd.Series of lists.

    :param data_frame: any DataFrame
    :type data_frame: Pandas DataFrame
    :param columns: a list of columns in the DataFrame
    :type columns: list
    :return: a DataFrame with the columns altered in the manner described above.
    :rtype: Pandas DataFrame
    """
    data_frame = copy.deepcopy(data_frame)
    for col in columns:
        data_frame[col] = data_frame[col].astype(str).map(lambda x: [i.strip() for i in x.split(",")])

    return data_frame










