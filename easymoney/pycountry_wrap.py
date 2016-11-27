#!/usr/bin/env python3

"""

    Wrapper for `pycountry`
    ~~~~~~~~~~~~~~~~~~~~~~

"""
# Import
import pycountry
import pandas as pd

from warnings import warn
from collections import defaultdict
from easymoney.support_tools import cln
from easymoney.sources.databases import currency_mapping_to_dict


class PycountryWrap():
    """

    """

    def __init__(self, curr_path=''):
        # Compute the dict mapping alpha2 codes to currencies
        self.alpha3_currency_dict = currency_mapping_to_dict(curr_path)  # move out of here.

    def _country_extract(self, country, extract_type='alpha_2'):
        """

        :param country: a pycountry object
        :param extract_type:
        :return:
        """
        if extract_type == 'alpha_2':
            try:
                return country.alpha_2
            except:
                return None
        elif extract_type == 'alpha_3':
            try:
                return country.alpha_3
            except:
                return None
        elif extract_type == 'numeric':
            try:
                return country.numeric
            except:
                return None
        elif extract_type == 'name':
            try:
                return country.name
            except:
                return None
        elif extract_type == 'official_name':
            try:
                return country.official_name
            except:
                try:
                    return country.name
                except:
                    return None
        else:
            raise ValueError("invalid extract_type supplied")

    def _currency_extract(self, currency_name, extract_type='currency_alpha_3'):
        """

        :param currency_name:
        :param extract_type:
        :return:
        """

        if extract_type == 'currency_alpha_3':
            try:
                return pycountry.currencies.get(alpha_3=currency_name).alpha_3
            except:
                return None
        elif extract_type == 'currency_numeric':
            try:
                return pycountry.currencies.get(alpha_3=currency_name).numeric
            except:
                return None

        elif extract_type == 'currency_name':
            try:
                return pycountry.currencies.get(alpha_3=currency_name).name
            except:
                return None
        else:
            raise ValueError("invalid extract_type supplied")

    def map_region_to_type(self, region, extract_type='alpha_2', curr_path=''):
        """

        Maps the input region to:
            region: alpha_2, alpha_3, name, official_name
            currency: currency_alpha_3, currency_numeric, currency_name

        :param region: any region
        :param extract_type:
        :return:
        """
        try:
            rslt = pycountry.countries.lookup(region)

            if 'currency_' not in extract_type.lower():
                return self._country_extract(rslt, extract_type.lower())

            else:
                # Get the alpha_3 country code
                alpha_3 = self._country_extract(rslt, 'alpha_3')

                # Look up
                currencies = self.alpha3_currency_dict[alpha_3]

                #
                if len(currencies):
                    if len(currencies) > 1:
                        warn("Multiple currencies are used in %s, including: %s.\n"
                             "%s has been selected by default." % (region, ", ".join(currencies), currencies[0]))
                    return self._currency_extract(currencies[0], extract_type)
                else:
                    return None
        except:
            return None


































































