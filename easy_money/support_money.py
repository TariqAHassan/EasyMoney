#!/usr/bin/env python3

"""

Support Tools
~~~~~~~~~~~~~

Python 3.5

"""


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

