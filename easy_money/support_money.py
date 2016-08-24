#!/usr/bin/env python3

"""

Support Tools
~~~~~~~~~~~~~

Python 3.5

"""

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

def dict_key_remove(input_dict, to_remove = np.nan, wrt = 'both'):
    """

    :param input_dict:
    :param to_remove:
    :return:
    """
    if wrt in ['key', 'value']:
        return {k: v for k, v in input_dict.items() if (k if wrt == 'key' else v) is not to_remove}
    elif wrt == 'both':
        return {k: v for k, v in input_dict.items() if (k is not to_remove and v is not to_remove)}


# def _best_date_match(date):
#     """
#
#     :param date: YYYY-MM-DD
#     :return:
#     """
#
#     if date in sorted_exchange_dates:
#         return date
#
#     # Convert date str to datetime
#     tstamp = datetime.datetime.strptime(date, "%Y-%m-%d")
#
#     # Restrict by year, month
#     close_dates = [d for d in sorted_exchange_dates if (d.year == tstamp.year) and (d.month == tstamp.month) ]
#
#     # Closest Date to the one supplied by the user
#     nearest_day = min([d.day for d in close_dates], key = lambda x: abs(x - tstamp.day))
#
#     return [d for d in close_dates if d.day == nearest_day][0].strftime('%Y-%m-%d')
