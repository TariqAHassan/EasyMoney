#!/usr/bin/env python3

"""

    Main API Functionality
    ~~~~~~~~~~~~~~~~~~~~~~

"""

# Functionality
# Region Type
# Inflation
# Currency Conversion


# _closest_date
# _currency_transition_handler
# region_map
# inflation_rate
# inflation_calculator
# currency_converter
# normalize
# options

# imports
import pycountry
from easymoney.pycountry_wrap import map_to_type


class EasyPeasy(object):
    """

    """
    def __init__(self):
        self.rl = RegionLookup()
        self.rl_methods = [f for f in dir(rl) if callable(getattr(rl, f)) and not f.startswith("__")]


def region_map(region, map_to='alpha_2', return_region_type=False):
    """

    Map a 'region' to any one of: ISO Alpha2, ISO Alpha3 or Currency Code as well as its Natural Name.

        Examples Converting From Currency:
            - ``EasyPeasy().region_map(region='CAD', map_to='alpha2')``   :math:`=` 'CA'
            - ``EasyPeasy().region_map(region='CAD', map_to='alpha3')``   :math:`=` 'CAN'

        Examples Converting From Alpha2:
            - ``EasyPeasy().region_map(region='FR', map_to='currency')`` :math:`=` 'EUR'
            - ``EasyPeasy().region_map(region='FR', map_to='natural')``  :math:`=` 'France'

    :param region: a 'region' in the format of a ISO Alpha2, ISO Alpha3 or currency code, as well as natural name.
    :type region: str
    :param map_to: 'alpha_2', 'alpha_3' 'name' or 'offical_name'. Defaults to 'alpha_2'.
    :type map_to: str
    :return: the desired mapping from region to ISO Alpha2.
    :rtype: ``str`` or ``tuple``

    .. warning::
        Attempts to map common currencies to a single nation will fail.


        For instance, ``EasyPeasy().region_map(region = 'EUR', map_to = 'alpha2')`` will fail because the Euro (EUR)
        is used in several nations and thus a request to map it to a single ISO Alpha2 country code creates
        insurmountable ambiguity.
    """
    return map_to_type(region=region, extract_type=map_to)












































































































































































