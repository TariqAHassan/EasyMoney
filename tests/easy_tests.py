#!/usr/bin/env python3

"""

    Public API Unit Testing for EasyMoney
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""
# Imports
import os
import sys
import unittest
import pandas as pd

# Allow access to modules
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../"))

# Import the tool
from easymoney.money import EasyPeasy
from easymoney.easy_pandas import items_null

# Set the Data Path
data_path = str(os.getcwd()).split("/tests")[0] + "/easymoney/sources/data"

# Create an instance of the tool
ep = EasyPeasy(fuzzy_threshold=85, data_path=data_path)



class OptionTests(unittest.TestCase):
    """

    Test Battery for EasyMoney/money"s EasyPeasy().options() method.

    """


    def test_options_list(self):
        """
        General: test the EasyPeasy().options() method.
        Specific: test rformat = "list".
        """
        # Request a list of nations for which there is exchange rate information.
        exchange_options_list = ep.options(info="exchange", rformat="list", pretty_print=False)

        # Assert exchange_options_list is, in fact, a list
        self.assertEqual(isinstance(exchange_options_list, list), True)

        # Assert that the length of exchange_options_list is nontrivial.
        self.assertEqual(len(exchange_options_list) > 0, True)

        # Request a list of nations for which there is inflation information.
        inflation_options_list = ep.options(info="inflation", rformat="list", pretty_print=False)

        # Assert inflation_options_list is, in fact, a list
        self.assertEqual(isinstance(inflation_options_list, list), True)

        # Assert that the length of inflation_options_list is nontrivial.
        self.assertEqual(len(inflation_options_list) > 0, True)


    def test_options_df_exchange(self):
        """
        General: test the EasyPeasy().options() method.
        Specific: test rformat = "table".
        """
        exchange_options_df = ep.options(info="exchange", rformat="table", pretty_print=False)

        # Assert exchange_options_df is a Pandas DataFrame
        self.assertEqual(isinstance(exchange_options_df, pd.DataFrame), True)

        # Assert the number of rows in exchange_options_df is > 0.
        self.assertEqual(exchange_options_df.shape[0] > 0, True)


    def test_options_df_inflation(self):
        """
        General: test the EasyPeasy().options() method.
        Specific: test rformat = "table".
        """
        # Request a Pandas DataFrame with all information information.
        inflation_options_df = ep.options(info="inflation", rformat="table", pretty_print=False)

        # Assert inflation_options_list is a Pandas DataFrame
        self.assertEqual(isinstance(inflation_options_df, pd.DataFrame), True)

        # Assert the number of rows in inflation_options_list is > 0.
        self.assertEqual(inflation_options_df.shape[0] > 0, True)


    def test_options_df_overlap(self):
        """
        General: test the EasyPeasy().options() method.
        Specific: test rformat = "table".
        """
        # Request a Pandas DataFrame with all overlap information (between exchange rate and inflation).
        overlap_options_df = ep.options(rformat='table', table_overlap_only=True, pretty_print=False)

        # Assert overlap_options_df is a Pandas DataFrame
        self.assertEqual(isinstance(overlap_options_df, pd.DataFrame), True)

        # Assert the number of rows in overlap_options_df is > 0.
        self.assertEqual(overlap_options_df.shape[0] > 0, True)


    def test_options_df_all_dates(self):
        """
        General: test the EasyPeasy().options() method.
        Specific: test range_table_dates = False.
        """
        # Request a Pandas DataFrame with all data information
        all_dates_options_df = ep.options(pretty_print=False, range_table_dates=False)

        # Assert there are more than lists of two (i.e, [min, max] in the InflationRange column
        self.assertEqual(max([len(l) for l in all_dates_options_df["InflationDates"] if isinstance(l, list)]) > 2, True)

        # Assert there are more than lists of two (i.e, [min, max] in the ExchangeRange column
        self.assertEqual(max([len(l) for l in all_dates_options_df["ExchangeDates"] if isinstance(l, list)]) > 2, True)



class FunctionalityTests(unittest.TestCase):
    """

    Test Battery for all Public Methods in EasyMoney/money"s EasyPeasy() Class, excluding options().

    """


    def __init__(self, *args, **kwargs):
        """

        Thanks to karthikr on SO: http://stackoverflow.com/a/17353262/4898004.
        Very helpful workaround.

        """
        super(FunctionalityTests, self).__init__(*args, **kwargs)

        # Request a list of nations for which there is exchange rate information.
        self.exchange_options_list = ep.options(info="exchange", rformat="list", pretty_print=False)

        # Request a list of nations for which there is inflation information.
        self.inflation_options_list = ep.options(info="inflation", rformat="list", pretty_print=False)

        # Request a Pandas DataFrame with all inflation information.
        self.inflation_options_df = ep.options(info="inflation", rformat="table", pretty_print=False)

        # Construct a {Alpha2: [min(inflation_data), max(inflation_data)]} dict w.r.t. the inflation_options_df.
        self.inflation_dict = dict(zip(self.inflation_options_df["Alpha2"], self.inflation_options_df["InflationDates"]))

        # Request a Pandas DataFrame with all overlap information (between exchange rate and inflation).
        self.overlap_options_df = ep.options(info="all", rformat="table", table_overlap_only=True, pretty_print=False)

        # Construct a {Alpha2: [min(inflation_data), max(inflation_data)]} dict  w.r.t. the overlap_options_df.
        self.overlap_dict = dict(zip(self.overlap_options_df["Alpha2"], self.overlap_options_df["InflationDates"]))


    def test_region_map(self):
        """
        General: Test the EasyPeasy().region_map() method.
        Specific:
                  (a) CAD --> Alpha2
                  (b) CAD --> Alpha3
                  (c) FR  --> Currency
                  (c) FR  --> Natural
        """

        # (1) Request "CAN" be mapped to its ISO ALpha2 Code.
        CAD_alpha2 = ep.region_map(region="CAN", map_to="alpha_2")

        # Assert (1) is "CA"
        self.assertEqual(CAD_alpha2, "CA")

        # (2) Request "CAN" be mapped to its ISO ALpha3 Code.
        CAD_alpah3 = ep.region_map(region="CAN", map_to="alpha_3")

        # Assert (2) is "CAN"
        self.assertEqual(CAD_alpah3, "CAN")

        # (3) Request "FR" be mapped to its Currency Code.
        FR_currency = ep.region_map(region="FR", map_to="name")

        # Assert (3) is "France"
        self.assertEqual(FR_currency, "France")


    def test_currency_converter_all(self):
        """
        General: Test the EasyPeasy().currency_converter() method.
        Specific: testing that all curriency1 --> curriency2 possibilities return numeric results.
        """
        # LCU --> EUR and EUR --> LCU
        for c in self.exchange_options_list:
            lcu_to_eur = ep.currency_converter(100, c, "EUR", date="latest")
            eur_to_lcu = ep.currency_converter(100, "EUR", c, date="latest")


    def test_currency_converter_EUR_USD(self):
        """
        General: Test the EasyPeasy().currency_converter() method.
        Specific: Test Converting between USD and EUR against a known value.
        """
        # (1) On Sept 2, 2016, 100 EUR = 111.93 USD (based on ECB data).
        sept2_2016_eur_to_usd = ep.currency_converter(100, "EUR", "USD", date="02/09/2016")

        # Assert (1) is True.
        self.assertEqual(sept2_2016_eur_to_usd, 111.93)

        # (2) On Sept 2, 2016, 100 USD = 89.34 EUR (based on ECB data).
        sept2_2016_usd_to_eur = ep.currency_converter(100, "USD", "EUR", date="02/09/2016")

        # Assert (2) is True.
        self.assertEqual(sept2_2016_usd_to_eur, 89.34)


    def test_inflation_rate(self):
        """
        General: test the EasyPeasy().inflation_rate() method.
        Specific: test that all region referenced in options have:
                      (a) (numeric) inflation rate information.
                      (b) A dictionary of CPI information for each region can be returned.
                         (i)  that this dictionary has the same number of keys as years provided.
                         (ii) that all values in this dictionary are numeric.
        """
        # Initialize
        rate = None
        rate_dict = None

        # Iterate though the inflation_dict dict.
        for region, drange in self.inflation_dict.items():
            if not items_null(drange):
                # Reqest the inflation rate for all possible regions.
                rate = ep.inflation(region, int(drange[0]), int(drange[1]))

                # Assert the returned result is numeric.
                self.assertEqual(isinstance(rate, (int, float)), True)

                # Request a dictionary of CPI information.
                rate_dict = ep.inflation(region, int(drange[0]), int(drange[1]), return_raw_cpi_dict=True)

                # Asser rate_dict is, in fact, a dictionary.
                self.assertEqual(isinstance(rate_dict, dict), True)

                # Assert the number of keys is equal to the number of years provided.
                self.assertEqual(len(rate_dict.keys()), len(set(drange)))

                # Assert that the values in rate_dict are numeric.
                self.assertEqual(all([isinstance(i, (float, int)) for i in rate_dict.values()]), True)


    def test_inflation_calculator(self):
        """
        General: Test the EasyPeasy().inflation_calculator() method.
        Specific: Check that 100 dollars can be adjusted for inflation on the range indicated in options().
        """
        # Initialize
        real_dollars = None

        # Iterate though the inflation_dict dict.
        for region, drange in self.inflation_dict.items():
            if not items_null(drange):
                real_dollars = ep.inflation_calculator(100, region, int(drange[0]), int(drange[1]))
                self.assertEqual(isinstance(real_dollars, (int, float)), True)

        # (1) 100 (1990 USD) =~= 181.40 (2015 USD).
        # Similar result obtained at: http://www.bls.gov/data/inflation_calculator.htm).
        US_inflation_1990_to_2015 = ep.inflation_calculator(100, "US", 1990, 2015)

        # Assert (1) is True.
        self.assertEqual(US_inflation_1990_to_2015, 181.4)

        # (2) 100 (1990 CAD) =~= 161.56 (2015 CAD).
        # Similar answer obtained at: http://www.bankofcanada.ca/rates/related/inflation-calculator/.
        CA_inflation_1990_to_2015 = ep.inflation_calculator(100, "CA", 1990, 2015)

        # Assert (2) is True.
        self.assertEqual(CA_inflation_1990_to_2015, 161.56)


    def test_normalize(self):
        """
        General: test the EasyPeasy().normalize() method.
        Specific:
                (a) many different combinations of region, from_year and base requests.
                (b) USD to EUR; inlfation: 2010 --> 2015; exchange_date = 2015-12-01.
                (c) CAD to USD; inlfation: 2005 --> 2012; exchange_date = 30/11/2012.
        """
        # Initialize
        normalized_amount = None

        # Systematic attempt to break the normalize() method.
        for base in self.overlap_options_df.Alpha3.tolist():
            for region, drange in self.overlap_dict.items():
                if not items_null(drange):
                    for d in drange:
                        normalized_amount = ep.normalize(100, region, int(d), base_currency=base)

                        # Assert normalized_amount is numeric.
                        self.assertEqual(isinstance(normalized_amount, (float, int)), True)

        # (1) 100 (2010 USD) =~= 108.70 (2015 USD) =~= 102.55 (01/12/2015 EUR).
        norm_USD_to_EUR = ep.normalize(100, region="US"
                                           , from_year=2010
                                           , to_year=2015
                                           , base_currency="EUR"
                                           , exchange_date="01/12/2015")

        # Assert (1) is True.
        self.assertEqual(norm_USD_to_EUR, 102.55)

        # (2) 100 (2005 CAD) =~= 113.74 (2012 CAD) =~= 114.46 (30/11/2012 USD).
        norm_CAD_to_USD = ep.normalize(100, region="CA"
                                           , from_year=2005
                                           , to_year=2012
                                           , base_currency="USD"
                                           , exchange_date="30/11/2012")

        # Assert (2) is True.
        self.assertEqual(norm_CAD_to_USD, 114.46)

        # Notes:
        #   For (1), a similar exchange rate calculation can be obtained at (i); similarly for (2) at (ii).
        #   For both (1) and (2) a similar exchange rate calculation result can be obtained at (iii).
        #       (i)   http://www.bls.gov/data/inflation_calculator.htm
        #       (ii)  http://www.bankofcanada.ca/rates/related/inflation-calculator/
        #       (iii) http://www.bankofcanada.ca/rates/exchange/10-year-converter/


    def test_fuzzy_search(self):
        """
        General: Test Fuzzy Search instance of EasyPeasy().
        Specific: test EasyPeasy().normalize() method.
        """
        # (2) 100 (2005 CAD) =~= 113.74 (2012 CAD) =~= 114.46 (2012-11-30 USD).
        #     Use "Canadian" as a subsitue for "CAD".
        norm_CAD_to_USD = ep.normalize(100, region="Canadian"
                                           , from_year=2005
                                           , to_year=2012
                                           , base_currency="USD"
                                           , exchange_date="30/11/2012")

        # Assert (2) is True.
        self.assertEqual(norm_CAD_to_USD, 114.46)



# Run Tests
unittest.main()














