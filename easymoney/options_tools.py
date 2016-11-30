# coding: utf-8

"""

    Tools for EasyPeasy's options() Method
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Imports
import numpy as np
from datetime import datetime
from collections import defaultdict

from easymoney.support_tools import min_max
from easymoney.easy_pandas import items_null
from easymoney.support_tools import date_sort
from easymoney.support_tools import min_max_dates



def options_ranking(inflation, exchange):
    """

    Ranks ``options()`` table rows by their completeness.
    Rankings:
        3: inflation and exchange information
        2: exchange information
        1: inflation information
        0: neither inflation or exchange information

    :param inflation: date rage of data available for inflation data.
    :type inflation: ``list``
    :param exchange: date rage of data available for exchange data.
    :type exchange: ``list``
    :return: completeness of row
    :rtype: ``int``
    """
    if not items_null(inflation) and not items_null(exchange):
        return 3
    elif not items_null(exchange):
        return 2
    elif not items_null(inflation):
        return 1
    else:
        return 0


def year_date_overlap(years, full_dates, date_format="%d/%m/%Y"):
    """

    Get the overlap for a iterable of years and an iterable of full dates (as strings).

    :param range_a: years of the form (year_a, year_b).
    :type range_a: ``iterable``
    :param range_b: dates of the form (string_date_a, string_date_b).
    :type range_b: ``iterable``
    :return: date overlap.
    :rtype: ``list``
    """
    # Check inputs
    if any(items_null(i) for i in [years, full_dates]):
        return np.NaN

    # Convert input to datetimes
    year_datetimes = [datetime.strptime(dm + str(y), date_format) for y, dm in zip(min_max(years), ["01/01/", "31/12/"])]
    dates_datetimes = [datetime.strptime(d, date_format) for d in min_max_dates(full_dates, from_format=date_format)]

    # Get date floor
    date_floor = max([year_datetimes[0], dates_datetimes[0]])

    # Get date ceiling
    date_ceiling = min([year_datetimes[1], dates_datetimes[1]])

    # Return
    return [date_floor.strftime(date_format), date_ceiling.strftime(date_format)]


def alpha2_by_cpi_years(regions, cpi_dictionary):
    """

    Tool to construct a dictionary of the form:
    ``{CountryAlpha2: [Years for which CPI info is available]}``.

    :param regions: an iterable of ISO alpha 2 country codes.
    :type regions: ``iterable``
    :param cpi_dictionary: dictionary of CPI information as returned by ``world_bank_pull(return_as='dict')``.
    :param cpi_dictionary: ``dict``
    :return: dictionary of years for which CPI information is available for a given country.
    :rtype: ``dict``
    """
    # Note: not strictly for `EasyPeasy().options()` as this is also used in `EasyPeasy()._cpi_years()`.
    cpi_years_dict = defaultdict(list)
    for r in regions:
        for y in sorted(list(cpi_dictionary.keys()), reverse=True):
            if cpi_dictionary.get(y, None).get(r, None) != None:
                cpi_years_dict[r].append(y)

    return dict(cpi_years_dict)












