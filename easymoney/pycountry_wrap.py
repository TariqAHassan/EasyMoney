#!/usr/bin/env python3

"""

    EasyMoney Wrapper for Pycountry
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Import
import pycountry
from warnings import warn
from easymoney.sources.databases import currency_mapping_to_dict


class PycountryWrap(object):
    """

    Tools wrapping the `pycountry` module.

    :param fuzzy_match_threshold: a threshold for fuzzy matching confidence (requires the ``fuzzywuzzy`` package).
                                  For more, see ``EasyPeasy()`` in the `money` module.
    :type fuzzy_threshold: ``int`` or ``float``
    :param data_path: path to the database file(s). Defaults to ''.
    :type data_path: ``str``
    """


    def __init__(self, fuzzy_threshold=False, data_path=''):
        """

        Initialize the ``PycountryWrap()`` class.

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
                                  " - python 3: $ pip3 install fuzzywuzzy\n"
                                  "You may need to create a new Python instance for these changes to take effect.")


    def _country_extract(self, country, extract_type='alpha_2'):
        """

        Extract information from a given country in the `pycountry` database.

        :param country: a pycountry object to harvest `extract_type` from.
                        Recognized types of information: 'alpha_2', 'alpha_3', 'numeric', 'name' or 'official_name'.

        :type country: ``pycountry object``
        :param extract_type: The type of information to extract from `country`. Defaults to 'alpha_2'.
        :type extract_type: ``str``
        :return: a country's ISO alpha 2 code, ISO alpha 3 code, numeric code, name or official name.
        :rtype: ``str`` or ``None``
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

        Extract information from a given currency in the `pycountry` database.

        :param currency_name: a country.
        :type currency_name: ``str``
        :param extract_type: Defaults to 'currency_alpha_3'.
        :type extract_type: ``str``
        :return: an ISO Alpha 3 currency code.
        :rtype: ``pycountry object`` or ``None``
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
        
        Fuzzy Searching tool via the `fuzzywuzzy` module.

        :param term: a search term.
        :type term: ``str``
        :param options: an iterable of options to match on.
        :type options: ``iterable``
        :return: best match match quality is less than the threshold.
        :rtype: ``str``
        """
        rslt = self.extractOne(term, options)
        return rslt[0] if rslt[1] >= self.fuzzy_threshold else None


    def _region_lookup(self, region):
        """
        
        Tool to find a region's `pycountry` object.

        :param region: a region.
        :type region: ``str``
        :return: a `pycountry` object for `region`.
        :rtype: ``pycountry object`` or ``None``
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
            region: 'alpha_2', 'alpha_3', 'name' or 'official_name'.
            currency: 'currency_alpha_3', 'currency_numeric' or 'currency_name'.

        :param region: any region
        :type region: ``str``
        :param extract_type: the type of information about `region` to extract. Must be one of the types listed above.
        :type extract_type: ``str``
        :return: `extract_type` information.
        :rtype: ``str`` or ``None``
        """
        rslt = self._region_lookup(region)
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



















