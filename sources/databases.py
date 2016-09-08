#!/usr/bin/env python3

"""

    Tools for Locating Required Databases
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

# Modules #
import os
import pandas as pd
import pkg_resources

from shutil import copyfile
from easymoney.easy_pandas import twoD_nested_dict
from sources.world_bank_interface import _world_bank_pull_wrapper
from sources.ecb_interface import _ecb_xml_exchange_data


def _exchange_rates_from_datafile(exchange_rate_df, convert_to_dict = True):
    """

    *Private Method*
    Correct the columns of the exchange_rate_df and return as a DataFrame or a nested Dict

    :param exchange_rate_df: ExchangeRatesDB
    :type exchange_rate_df: Pandas DataFrame
    :param convert_to_dict: if True, will convert the exchange_rate_df into a nested dict.
    :type convert_to_dict: bool
    :return: DataFrame or a nested Dict
    :rtype: dict or Pandas DataFrame
    """
    # Convert the columns to the correct type.
    exchange_rate_df['Date'] = exchange_rate_df['Date'].astype(str)
    exchange_rate_df['Currency'] = exchange_rate_df['Currency'].astype(str)
    exchange_rate_df['Rate'] = exchange_rate_df['Rate'].astype(float)

    # Get the Currency Codes
    currency_codes = exchange_rate_df['Currency'].unique().tolist()
    if convert_to_dict:
        DictExchangeRatesDB = twoD_nested_dict(exchange_rate_df, engine = 'fast')
        return DictExchangeRatesDB, currency_codes
    else:
        return exchange_rate_df, currency_codes

class DatabaseManagment(object):
    """

    | *Private Class*
    | Set of tools for managing Databases used by EasyMoney

    :param default_data_path: the default path to EasyMoney's included DataBases
    :type default_data_path: str
    :param database_path: an alternate default path to EasyMoney's included DataBases
    :type database_path: str
    """


    def __init__(self, database_path):
        """

        Initialize ``DatabaseManagment()`` Class.

        """
        self.default_data_path = pkg_resources.resource_filename('sources', 'data')
        self.database_path = database_path
        self.required_databases =  [  'ISOAlphaCodesDB.csv'          # Included with EasyMoney.
                                    , 'CurrencyTransitionDB.csv'     # Included with EasyMoney.
                                    , 'CurrencyRelationshipsDB.csv'  # Included with EasyMoney.
                                    , 'ExchangeRatesDB.csv'          # Obtained from Online API(s).
                                    , 'ConsumerPriceIndexDB.csv'     # Obtained from Online API(s).
        ]


    def _data_path_assessment(self):
        """

        | *Private Method*
        | Method to determine if required databases are present in a given directory.
        | If databases are missing, they their names are returned.

        :return: Boolean for if files need to be installed in database_path; path to the data files or list of files to make.
                 Tuple of form the form: (bool, str OR list).
                 False <---> Path to all needed databases.
                 True  <---> [list of files to generate].
        :rtype: tuple
        """
        # Initialize
        files_in_alterative_path = list()

        # If database_path is None, use the default databases that are included with EasyMoney.
        if self.database_path == None:
            return False, self.default_data_path
        elif isinstance(self.database_path, str):

            # List of required files, if any, in the database_path.
            files_in_alterative_path = [x in os.listdir(self.database_path) for x in self.required_databases]

            # All Databases Present in the self.database_path.
            if all(files_in_alterative_path):
                return False, self.database_path
            # Some Databases present in the database_path.
            elif any(files_in_alterative_path):
                return True, [x for x in self.required_databases if x not in os.listdir(self.database_path)]
            # No Databases present in the database_path.
            elif list(set(files_in_alterative_path)) == [False]:
                return True, self.required_databases
        else:
            raise ValueError("the alterative path to the databases must be either None or a valid path (string).")

    def _database_manager(self, data_path, missing_files):
        """

        | *Private Method*
        | This method will:
        |    (1) Populate a data_path any with missing database.
        |    (2) Import from the directory any present database.

        :param data_path: path to a directory with EasyMoney databases
        :type data_path: str
        :param missing_files: a list of database files that a re missing from data_path
        :type missing_files: list
        :return: ISOAlphaCodesDB, CurrencyTransitionDB, ExchangeRatesDB, currency_codes, ConsumerPriceIndexDB, CurrencyRelationshipsDB
        :rtype: tuple
        """
        # Initialize
        ExchangeRatesDB = None
        ConsumerPriceIndexDB = None
        ISOAlphaCodesDB = None
        CurrencyTransitionDB = None
        currency_codes = None
        exchange_rate_df = None

        # Determine the databases that ship with EasyMoney that missing from database_path.
        missing_shipped_files = [x for x in self.required_databases[0:3] if x in missing_files]

        # Read in ISOAlphaCodesDB.
        if 'ISOAlphaCodesDB.csv' in missing_files:
            ISOAlphaCodesDB = pd.read_csv(self.default_data_path + "/ISOAlphaCodesDB.csv", keep_default_na = False)
        elif 'ISOAlphaCodesDB.csv' not in missing_files:
            ISOAlphaCodesDB = pd.read_csv(data_path + "/ISOAlphaCodesDB.csv", keep_default_na = False)

        # Read in CurrencyTransitionDB.
        if 'CurrencyTransitionDB.csv' in missing_files:
            CurrencyTransitionDB = pd.read_csv(self.default_data_path + "/CurrencyTransitionDB.csv")
        elif 'CurrencyTransitionDB.csv' not in missing_files:
            CurrencyTransitionDB = pd.read_csv(data_path + "/CurrencyTransitionDB.csv")

        # Copy missing databases from EasyMoney's cache to database_path. (dbc = database copy).
        if len(missing_shipped_files) > 0:
            for dbc in missing_shipped_files:
                copyfile(self.default_data_path + "/" + dbc, data_path + "/" + dbc)

        # Generate and Write ExchangeRatesDB, if needed.
        if data_path == self.default_data_path:

            # Generate if the default path is being used
            ExchangeRatesDB, currency_codes = _ecb_xml_exchange_data(return_as = 'df')

        elif 'ExchangeRatesDB.csv' in missing_files:

            # Obtain exchange data
            ExchangeRatesDB, currency_codes = _ecb_xml_exchange_data(return_as = 'df')

            # Save the ExchangeRatesDB to database_path
            ExchangeRatesDB.to_csv(data_path + "/ExchangeRatesDB.csv", index = False)

        else: # Read in from database_path, if not missing.
            ExchangeRatesDB, currency_codes = _exchange_rates_from_datafile(pd.read_csv(data_path + "/ExchangeRatesDB.csv"),  False)

        # Generate and Write ConsumerPriceIndexDB, if needed.
        if data_path == self.default_data_path:
            ConsumerPriceIndexDB, CurrencyRelationshipsDB = _world_bank_pull_wrapper("CPI", "FP.CPI.TOTL")

        elif 'ConsumerPriceIndexDB.csv' in missing_files:

            # Obtain CPI Data (will also look for 'CurrencyRelationshipsDB.csv' in database_path).
            ConsumerPriceIndexDB, CurrencyRelationshipsDB = _world_bank_pull_wrapper("CPI", "FP.CPI.TOTL", data_path = data_path)

            # Save the ConsumerPriceIndexDB to database_path
            ConsumerPriceIndexDB.to_csv(data_path + "/ConsumerPriceIndexDB.csv", index = False)

        else: # Read in from database_path, if not missing.
            ConsumerPriceIndexDB = pd.read_csv(data_path + "/ConsumerPriceIndexDB.csv")
            CurrencyRelationshipsDB = pd.read_csv(data_path + "/CurrencyRelationshipsDB.csv")

        return ISOAlphaCodesDB, CurrencyTransitionDB, ExchangeRatesDB, currency_codes, ConsumerPriceIndexDB, CurrencyRelationshipsDB

    def _database_wizard(self):
        """

        | *Private Method*
        | Method that oversees deployment of ``_database_manager()``.
        | Note: Manipulation of CurrencyRelationshipsDB not well-tested
          (not yet clear if manipulation produces actual changes).
        """

        # Assess what Files are needed
        database_assessment = self._data_path_assessment()

        # Need to Add Files is True
        if database_assessment[0]:
            return self._database_manager(data_path = self.database_path, missing_files = database_assessment[1])

        # Need to Add Files is False
        elif not database_assessment[0]:
            return self._database_manager(data_path = database_assessment[1], missing_files = [])















