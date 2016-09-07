#!/usr/bin/env python3

"""

    Database of which Nations use which Currency
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

# Modules #
import os
import re
import copy
import numpy as np
import pandas as pd
import pkg_resources


from easymoney.support_money import DEFAULT_DATA_PATH
from easymoney.support_money import pandas_list_column_to_str


DEFAULT_DATA_PATH = pkg_resources.resource_filename('sources', 'data')
SINGLE_USE_PATH = pkg_resources.resource_filename('sources', 'single_use')


# Dict. for special cases in the self.currency_codes dataframe.
known_special_cases_dict = {
      "Democratic Republic of the Congo" : "CD"
    , "Cape Verde" : "CV"
    , "Egypt, auxiliary in Gaza Strip" : "EG"
    , "North Korea" : "KP"
    , "South Korea" : "KR"
    , "Laos" : "LA"
}


class CurrencyRelationships(object):
    """

    *SPECIFIC* set of tools for interacting with the included CurrencyCodesDB.csv and ISOAlphaCodesDB.csv databases.

    :param path_to_databases: an alterative path to the database files.
                              See ``easymoney.money.EasyPeasy(path_to_databases)`` for more.
    :type path_to_databases: str
    """


    def __init__(self, currency_codes_db = None, iso_alpha_codes_db = None):
        """
        Initialize the ``CurrencyRelationships()`` class.

        """
        # Initalize
        string_strip = lambda x: re.sub(r"\s\s+", " ", str(x).strip())

        # Import Currency Code Database.
        if currency_codes_db == None:
            self.currency_codes = pd.read_csv(SINGLE_USE_PATH + "/CurrencyCodesDB.csv", encoding = "ISO-8859-1")
        else:
            self.currency_codes = copy.deepcopy(currency_codes_db)

        # Clean the Locations column.
        self.currency_codes['Locations'] = self.currency_codes['Locations'].astype(str).map(string_strip)

        # Import Country Codes Database.
        if iso_alpha_codes_db == None:
            self.country_codes = pd.read_csv(DEFAULT_DATA_PATH + "/ISOAlphaCodesDB.csv", encoding = "ISO-8859-1", keep_default_na = False)
        else:
            self.country_codes = copy.deepcopy(iso_alpha_codes_db)

        # Dict relating alpha2 to alpha3.
        self.alpha2_to_alpha3_dict = dict(zip(self.country_codes['Alpha2'], self.country_codes['Alpha3']))

        # Dict relating a country's natural name (e.g., Canada) to its alpha2 code.
        self.name_to_alpha2_dict = dict(zip(self.country_codes['CountryName'], self.country_codes['Alpha2']))

    def alpha2_from_natural_name(self):
        """

        Parses lists that contain Natural Names (some of which *may* also have Alpha2 Codes in braces),
        e.g., Canada (CA)
              Cambodia
              China (CN)
                ...

        :return: see above description
        :rtype: list
        """
        # Note: this 'code soup' should be refactored in time.

        # Initialize
        region = None
        alpha2 = None
        alpha2_list = list()

        # Iterate through natural names
        for c in self.currency_codes['Locations'].tolist():
            if "(" not in c:
                region = [k for k in self.name_to_alpha2_dict.keys() if c.upper() in k.upper()]
                if c in known_special_cases_dict.keys():
                    alpha2_list.append(known_special_cases_dict[c])
                else:
                    if len(region) > 1:
                        region = [r for r in region if c.upper() == r.upper()]
                    if len(region) == 1:
                        alpha2 = [self.name_to_alpha2_dict[region[0]]]
                        if len(alpha2) == 1 and all(x not in [[x.strip() for x in alpha2]] for x in [np.nan, '']):
                            alpha2_list.append(alpha2)
                        else:
                            alpha2_list.append(np.NaN)
                    else:
                        alpha2_list.append(np.NaN)
            else:
                # Extract alpha2 codes from braces, e.g., 'Curacao (CW), Sint Maarten (SX)'.
                multi_codes = [x.replace(")", "").replace("(", "") for x in re.findall(r"\(\w+\)", c)]

                # Append
                alpha2_list.append(multi_codes[0]) if len(multi_codes) == 1 else alpha2_list.append(multi_codes)

        return alpha2_list

    def pandas_series_of_lists_cleanup(self, input_list):
        """

        Clean a list to allow it to be a Pandas series of lists.

        :param input_list: a list
        :type input_list: list
        :return: list of lists
        :rtype: list
        """
        # Clean up
        nan_replace_empty_list = [np.NaN if isinstance(c, list) and len(c) == 0 else c for c in input_list]

        # put strings into lists, if present and return.
        return [[c] if not isinstance(c, list) and isinstance(c, str) else c for c in nan_replace_empty_list]

    def relate(self):
        """

        Construct Pandas frame that relates Natural Name, Alpha2, Alpha3 and Currency Code.

        :returns: Natural Name, Alpha2, Alpha3 and Currency Code relationships.
        :rtype: Pandas DataFrame
        """
        # Get the alpha2 codes from the natural names
        alpha2_list = self.alpha2_from_natural_name()

        # Convert to a pandas acceptable format
        pandas_format_alpha2 = self.pandas_series_of_lists_cleanup(alpha2_list)

        # Use the self.currency_codes database as a framework
        relation_db = copy.deepcopy(self.currency_codes)

        # Correct for possible weird match and add as the Alpha2 column.
        relation_db['Alpha2'] = [['HK'] if i == ['HK', 'MO'] else i for i in pandas_format_alpha2]

        # Remove all bracketed information from the Locations column
        relation_db['Locations'] = relation_db['Locations'].map(lambda x: re.sub(r"\s\s+", "", re.sub(r"\(.*\)", "", x)).strip())

        # Remove rows with Alpha2 == nan
        relation_db = relation_db[pd.notnull(relation_db["Alpha2"])]
        
        # Refresh index
        relation_db.index = range(relation_db.shape[0])
        
        # Get Alpha3 code
        alpha3_list = list()
        for cc in relation_db.Alpha2.tolist():
            alpha3_list.append([self.alpha2_to_alpha3_dict[c] for c in cc])

        # Add Alpha3 Column
        relation_db['Alpha3'] = alpha3_list

        # Drop the Locations Column
        relation_db.drop('Locations', axis = 1, inplace = True)

        # Reorder
        relation_db = relation_db[['Currency', 'Code', 'Alpha2', 'Alpha3']]

        # Rename column
        relation_db.rename(columns = {'Code': 'CurrencyCode'}, inplace = True)

        return relation_db

# Save to Disk
# pandas_list_column_to_str(CurrencyRelationships().relate(), ['Alpha2', 'Alpha3']).to_csv('CurrencyRelationshipsDB.csv', index = False)








