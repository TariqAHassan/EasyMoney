#!/usr/bin/env python3

"""

    Supporting Pandas Tools
    ~~~~~~~~~~~~~~~~~~~~~~~

"""

# Modules #
import copy
import warnings
import datetime
import numpy as np
import pandas as pd


from easymoney.support_money import strlist_to_list


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

def pandas_dictkey_to_key_unpack(pandas_series, unpack_dict):
    """

    *Private Method*
    Used to unpack ISO Alpha2 --> Alpha2 ISO code Pandas Series.

    :param pandas_series: a Series to replace the alpha2 codes with another set.
    :type pandas_series: Pandas Series
    :param unpack_dict: a dict with the values coerced into strings.
    :type unpack_dict: dict
    :return: a pandas series with the alpha2 values replaced with unpack_dict.values(). NaNs are used if a match cannot be found.
    :rtype: Pandas Series
    """
    # Hacking the living daylights out of the pandas API
    return pandas_series.replace(unpack_dict).map(lambda x: np.NaN if 'nan' in str(x) else strlist_to_list(str(x)))

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









