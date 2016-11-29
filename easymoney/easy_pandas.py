# coding: utf-8

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


def pstr(s):
    """

    Convert to any obect to a string using pandas.

    :param s: item to be converted to a string.
    :type s: ``any``
    :return: a string
    :rtype: ``str``
    """
    return pd.Series([s]).astype('unicode')[0]


def strlist_to_list(to_parse, convert_to_str_first=False):
    """

    Work around for using ``eval()`` for the following conversion: ``str(list)`` → ``list``.

    For example: ``"[1992, '221-21', 2102, 'apples']"`` → ``['1992', '221-21', '2102', 'apples']``.

    :param to_parse: a string of a list.
    :type to_parse: ``str``
    :param convert_to_str_first: convert to a string first (as a precaution). Defaults to False.
    :type convert_to_str_first: ``bool``
    :return: string of a list to an actual list.
    :return: ``list``
    """
    str_list = pstr(to_parse) if convert_to_str_first else to_parse
    return [i.strip().replace("'", "") for i in [j.split(",") for j in [str_list.replace("[", "").replace("]", "")]][0]]


def _pandas_dictkey_to_key_unpack(pandas_series, unpack_dict, convert_values_to_str = False):
    """

    Used to unpack ISO Alpha2 --> Alpha2 ISO code Pandas Series.

    :param pandas_series: a Series to replace the alpha2 codes with another set.
    :type pandas_series: ``Pandas Series``
    :param convert_values_to_str: convert the values to string (precaution).
    :type convert_values_to_str: ``bool``
    :param unpack_dict: a dict with the values coerced into strings.
    :type unpack_dict: ``dict``
    :return: a pandas series with the alpha2 values replaced with unpack_dict.values().
             ``NaN`` is used if a match cannot be found.
    :rtype: ``Pandas Series``
    """
    if convert_values_to_str:
        unpack_dict = {k: pstr(v) for k, v in unpack_dict.items()}

    return pandas_series.replace(unpack_dict).map(lambda x: np.NaN if 'nan' in pstr(x) else strlist_to_list(pstr(x)))


def _standard_pd_nester(data_frame, nest_col_a, nest_col_b, nest_col_c, keys_to_str = True):
    """

    Method to produce a nested dict from a large pandas dataframe.
    Reliable technique (although slow with large DataFrames).

    :param data_frame: see ``twoD_nested_dict()``.
    :type data_frame: ``Pandas DataFrame``
    :param nest_col_a: see ``twoD_nested_dict()``.
    :type nest_col_a: ``str``
    :param nest_col_b: see ``twoD_nested_dict()``.
    :type nest_col_b: ``str``
    :param nest_col_c: see ``twoD_nested_dict()``.
    :type nest_col_c: ``str``
    :param keys_to_str: see ``twoD_nested_dict()``.
    :type keys_to_str: ``bool``
    :return: nested dict of the form: ``{nest_col_a: {nest_col_b: nest_col_c}}``.
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

    | This is a fast way to produce a nested dict from a large Pandas DataFrames.
    | Can handle DataFrames with several nest_col_a entries that are the same,
    | e.g.,
    |         nest_col_a    nest_col_b  nest_col_c
    | 0       1999-01-04      AUD          0
    | 1       1999-01-04      CAD          1
    | 2       1999-01-05      CHF          2
    | 3       1999-01-05      CYP          3
    |
    | WARNING: Not well-tested. This procedure may produce inaccuracies.

    :param data_frame: see ``twoD_nested_dict()``.
    :type data_frame: Pandas DataFrame
    :param nest_col_a: see ``twoD_nested_dict()``.
    :type nest_col_a: str
    :param nest_col_b: see ``twoD_nested_dict()``.
    :type nest_col_b: str
    :param nest_col_c: see ``twoD_nested_dict()``.
    :type nest_col_c: str
    :param keys_to_str: see ``twoD_nested_dict()``.
    :type keys_to_str: ``bool``
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
        grouped_data_frame[nest_col_b] = grouped_data_frame[nest_col_b].map(lambda x: [pstr(i) for i in x])

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

    Generate a nested dictionary from the columns of a pandas dataframe.
    Defaults to using the first 3 columns.

    :param data_frame: a pandas dataframe.
    :type data_frame: ``Pandas DateFrame``
    :param nest_col_a: reference to column in the dataframe; to become the master key in dict.
                       Defaults to None (i.e., col 1).
    :type nest_col_a: ``str``
    :param nest_col_b: reference to column in the dataframe; to become the sub-key.
                       Defaults to None (i.e., col 2).
    :type nest_col_b: ``str``
    :param nest_col_c: reference to column in the dataframe; to become the value to corresponding to the sub-key.
                       Defaults to None (i.e., col 3).
    :type nest_col_c: ``str``
    :param to_float: a list items to float. Defaults to None.
    :type to_float: ``str``
    :param to_int: a list of the lists to convert to ints. Defaults to None.
    :type to_int: ``str``
    :param keys_to_str: Convert the columns that will become keys to strings. Default to True.
                        WARNING: will OVERRIDE *to_float* and *to_int* if they reference nest_col_a or nest_col_b.
    :type keys_to_str: ``bool``
    :param engine: 'standard' for a slower (but well-tested) method of generating a nested dict; 'fast' to employ a
                    speedy (but *not well-tested*) method for generating a nested dict. Default to 'standard'.
    :type engine: ``str``
    :return: nested dict of the form: ``{nest_col_a: {nest_col_b: nest_col_c}``.
    :rtype: ``dict``
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


def pandas_list_column_to_str(data_frame, columns, join_on = ", ", bracket_wrap = False):
    """

    Tool for converting the columns in a Pandas DataFrame
    from pd.Series of lists into comma-seperated strings.

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param columns: a list of columns in the DataFrame
    :type columns: ``list``
    :param join_on: a string to join on. Defaults to ", ".
    :type join_on: ``str``
    :return: a dataframe with the columns altered in the manner described above.
    :rtype: ``Pandas DataFrame``
    """
    df = copy.deepcopy(data_frame)
    for col in columns:
        df[col] = df[col].map(lambda x: join_on.join(x) if pstr(x) != 'nan' else x)
        if bracket_wrap:
            df[col] = df[col].map(lambda x: "[" + pstr(x) + "]" if pstr(x) != 'nan' else x)

    return df


def pandas_str_column_to_list(data_frame, columns):
    """

    Tool for converting the columns in a Pandas DataFrame
    from comma-seperated strings into a pd.Series of lists.

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param columns: a list of columns in the dataframe.
    :type columns: ``list``
    :return: a dataframe with the columns altered in the manner described above.
    :rtype: ``Pandas DataFrame``
    """
    data_frame = copy.deepcopy(data_frame)
    for col in columns:
        data_frame[col] = data_frame[col].astype(str).map(lambda x: [i.strip() for i in x.split(",")])
    return data_frame


def type_in_series(series):
    """

    Return the types of objects in a Pandas Series.

    :param series: a series.
    :type series: ``Pandas Series``
    :return: list of the types in a series.
    :rtype: ``list``
    """
    return list(set([type(i).__name__ if pstr(i).strip() not in ['nan', ''] else 'nan' for i in series]))


def prettify_all_pandas_list_cols(data_frame, join_on = ", ", allow_nan = True, exclude = [], bracket_wrap = False):
    """

    Converts all columns with only lists to list-seperated-strings.

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param nan: allow nans
    :type nan: ``bool``
    :param join_on: a string to join on. Defaults to ", ".
    :type join_on: ``str``
    :param exclude: columns to exclude Defaults to an empty list (``[]``).
    :type exclude: ``list``
    :param bracket_wrap: wrap in brackets.
    :type bracket_wrap: ``bool``
    :return: dataframe with columns lists converted to strings.
    :rtype: ``Pandas DataFrame``
    """
    allowed = [['list'], ['list', 'nan']] if allow_nan else [['list']]

    # Find allowed columns
    cols_to_prettify = \
        [c for c in data_frame.columns if sorted(type_in_series(data_frame[c])) in allowed and c not in exclude]

    if len(cols_to_prettify) == 0:
        return data_frame
    else:
        return pandas_list_column_to_str(data_frame, cols_to_prettify, join_on, bracket_wrap)


def items_null(element):
    """

    Check if an object is a NaN, including all the elements in an iterable.

    :param element: a python object.
    :type element: ``any``
    :return: assessment of whether or not `element` is a NaN.
    :rtype: ``bool``
    """
    if isinstance(element, (list, tuple, type(np.array))):
        return True if all(pd.isnull(i) for i in element) else False
    else:
        return pd.isnull(element)


def pandas_null_drop(data_frame, subset=None):
    """

    Drop rows with NaNs of all, or a subset of, the dataframe's columns.
    (Can handle iterables which only contain NaNs).

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param subset: a subset of columns. Defaults to None, which will apply to all columns.
    :type subset: ``iterable``
    :return: dataframe with NaN dropped.
    :rtype: ``Pandas DataFrame``
    """
    # Fill Empty cells with nans
    data_frame = data_frame.fillna(np.NaN)

    if subset is None:
        data_frame = data_frame.dropna()
    else:
        for c in subset:
            data_frame = data_frame[~data_frame[c].map(items_null)]

    return data_frame.reset_index(drop=True)

# ----------------------------------------------------------------------------------------------------------
# Printing Suit
# ----------------------------------------------------------------------------------------------------------

def _padding(s, amount, justify):
    """

    Add padding to a string.

    :param s: a string.
    :type s: ``str``
    :param amount: the amount of white space to add.
    :type amount: ``float`` or ``int``
    :param justify: the justification of the resultant text. Must be one of: 'left' or 'center'.
    :type justify: ``str``
    :return: `s` justified, or as passed if `justify` is not one of: 'left' or 'center'.
    :rtype: ``str``
    """
    pad = ' ' * amount
    if justify == 'left':
        return "%s%s" % (pstr(s), pad)
    elif justify == 'center':
        return "%s%s%s" % (pad[:int(amount/2)], pstr(s), pad[int(amount/2):])
    else:
        return s

def _pandas_series_alignment(pandas_series, justify):
    """

    Align all items in a pandas series.

    :param pandas_series: a pandas series.
    :type pandas_series: ``Pandas Series``
    :param justify: the justification of the resultant text. Must be one of: 'left', 'right' or 'center'.
    :type justify: ``str``
    :return: aligned series
    :rtype: ``str``
    """
    if justify == 'right':
        return pandas_series
    longest_string = max([len(s) for s in pandas_series.astype('unicode')])
    return [_padding(s, longest_string - len(s), justify) if not items_null(s) else s for s in pandas_series]


def align_pandas(data_frame, to_align='right'):
    """

    Align the columns of a Pandas DataFrame by adding whitespace.

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param to_align: 'left', 'right', 'center' or a dictionary of the form: ``{'Column': 'Alignment'}``.
    :type to_align: ``str``
    :return: dataframe with aligned columns.
    :rtype: ``Pandas DataFrame``
    """
    if isinstance(to_align, dict):
        alignment_dict = to_align
    elif to_align.lower() in ['left', 'right', 'center']:
        alignment_dict = dict.fromkeys(data_frame.columns, to_align.lower())
    else:
        raise ValueError("to_align must be either 'left', 'right', 'center', or a dict.")

    for col, justification in alignment_dict.items():
        data_frame[col] = _pandas_series_alignment(data_frame[col], justification)

    return data_frame


def pandas_print_full(pd_df, full_rows = True, full_cols = True):
    """

    Print *all* of a Pandas DataFrame.

    :param pd_df: DataFrame to printed in its entirety.
    :type pd_df: ``Pandas DataFrame``
    :param full_rows: print all rows if True. Defaults to True.
    :type full_rows: ``bool``
    :param full_cols: print all columns side-by-side if True. Defaults to True.
    :type full_cols: ``bool``
    """
    if full_rows: pd.set_option('display.max_rows', len(pd_df))
    if full_cols: pd.set_option('expand_frame_repr', False)

    # Print the data frame
    print(pd_df)

    if full_rows: pd.reset_option('display.max_rows')
    if full_cols: pd.set_option('expand_frame_repr', True)


def pandas_pretty_print(data_frame, col_align='right', header_align='center', full_rows=True, full_cols=True):
    """

    Pretty Print a Pandas DataFrame.

    :param data_frame: a dataframe.
    :type data_frame: ``Pandas DataFrame``
    :param col_align: 'left', 'right', 'center'' or a dictionary of the form: ``{'Column': 'Alignment'}``.
    :type col_align: ``str`` or ``dict``
    :param header_align: alignment of headers. Must be one of: 'left', 'right', 'center'.
    :type header_align: ``str`` or ``dict``
    :param full_rows: print all rows.
    :type full_rows: ``bool``
    :param full_cols: print all columns.
    :type full_cols: ``bool``
    """
    aligned_df = align_pandas(data_frame, col_align)
    pd.set_option('colheader_justify', header_align)
    pandas_print_full(aligned_df.fillna(""), full_rows, full_cols)
    pd.set_option('colheader_justify', 'right')



















