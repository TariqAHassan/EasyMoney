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


class PycountryWrap(object):
    """


    :param fuzzy_threshold:
    :param data_path:
    """

    def __init__(self, fuzzy_threshold=False, data_path=''):
        """

        :param fuzzy_threshold:
        :param data_path:
        """
        # Compute the dict mapping alpha2 codes to currencies
        self.alpha2_currency_dict = currency_mapping_to_dict(data_path)

        # Get a list of country names
        self.countries = [c.name for c in list(pycountry.countries)]

        # FuzzyWuzzy Settings
        self.fuzzy_threshold = fuzzy_threshold

        if fuzzy_threshold != False:
            try:
                from fuzzywuzzy import process
                self.extractOne = process.extractOne
            except:
                raise ImportError("To use `fuzzy_threshold` please install `fuzzywuzzy`.\n"
                                  " - python 2: $ pip install fuzzywuzzy\n"
                                  " - python 3: $ pip3 install fuzzywuzzy")

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

    def _fuzzy_search(self, term, options):
        """

        :param term:
        :param options:
        :return:
        """
        rslt = self.extractOne(term, options)
        return rslt[0] if rslt[1] >= self.fuzzy_threshold else None

    def _country_lookup(self, region):
        """

        :param region:
        :return:
        """
        fuzzy_match = None
        try:
            return pycountry.countries.lookup(region)
        except:
            if self.fuzzy_threshold != False:
                fuzzy_match = self._fuzzy_search(region, self.countries)
                if fuzzy_match is not None:
                    return pycountry.countries.lookup(fuzzy_match)
                else:
                    return None
            else:
                return None

    def map_region_to_type(self, region, extract_type='alpha_2'):
        """

        Maps the input region to:
            region: alpha_2, alpha_3, name, official_name
            currency: currency_alpha_3, currency_numeric, currency_name

        :param region: any region
        :param extract_type:
        :return:
        """
        rslt = self._country_lookup(region)
        if rslt is None:
            return None

        try:
            if 'currency_' not in extract_type.lower():
                return self._country_extract(rslt, extract_type.lower())

            else:
                # Get the alpha_3 country code
                alpha_2 = self._country_extract(rslt, 'alpha_2')

                # Look up
                currencies = self.alpha2_currency_dict[alpha_2]

                # Extract
                if len(currencies):
                    if len(currencies) > 1:
                        warn("Multiple currencies are used in %s, including: %s.\n"
                             "%s has been selected by default." % (region, ", ".join(currencies), currencies[0]))
                    return self._currency_extract(currencies[0], extract_type)
                else:
                    return None
        except:
            return None



















