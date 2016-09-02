"""

    Unit Testing for EasyMoney
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Import the tool
import sys
import unittest
import pandas as pd
import pkg_resources



# Import the tool
from easymoney.money import Currency


class EasyMoneyTests(unittest.TestCase):
    """


    """

    def __init__(self, *args, **kwargs):
        super(EasyMoneyTests, self).__init__(*args, **kwargs)
        self.curr = Currency()

    def test_options_list(self):
        """
        General: test the money module's Currency().options() method.
        Specific: test rformat = 'list'.
        """
        self.exchange_options_list = self.curr.options(info = "exchange", rformat = 'list', pretty_print = False)
        self.assertEqual(isinstance(self.exchange_options_list), list)
        self.assertEqual(len(self.exchange_options_list) > 0, True)

        # Request
        self.inflation_options_list = self.curr.options(info = "inflation", rformat = 'list', pretty_print = False)

        # Assert inflation_options_list is, in fact, a list
        self.assertEqual(isinstance(self.inflation_options_list), list)

        # Assert inflation_options_list is of nontrivial (math-babble for nonzero) length.
        self.assertEqual(len(self.inflation_options_list) > 0, True)

    def test_options_df_exchange(self):
        """
        General: test the money module's Currency().options() method.
        Specific: test rformat = 'table'.
        """
        self.exchange_options_df = self.curr.options(info = "exchange", rformat = 'table', pretty_print = False)

        # Assert exchange_options_df is a Pandas DataFrame
        self.assertEqual(isinstance(self.exchange_options_df), pd.DataFrame)

        # Assert the number of rows in exchange_options_df is > 0.
        self.assertEqual(self.exchange_options_df.shape[0] > 0, True)

    def test_options_df_inflation(self):
        """
        General: test the money module's Currency().options() method.
        Specific: test rformat = 'table'.
        """
        self.inflation_options_df = self.curr.options(info="inflation", rformat='table', pretty_print=False)

        # Assert exchange_options_df is a Pandas DataFrame
        self.assertEqual(isinstance(self.inflation_options_df), pd.DataFrame)

        # Assert the number of rows in exchange_options_df is > 0.
        self.assertEqual(self.inflation_options_df.shape[0] > 0, True)

    def test_options_df_exchange(self):
        """
        General: test the money module's Currency().options() method.
        Specific: test rformat = 'table'.
        """
        self.exchange_options_df = self.curr.options(info="exchange", rformat='table', pretty_print=False)

        # Assert exchange_options_df is a Pandas DataFrame
        self.assertEqual(isinstance(self.exchange_options_df), pd.DataFrame)

        # Assert the number of rows in exchange_options_df is > 0.
        self.assertEqual(self.exchange_options_df.shape[0] > 0, True)


    def test_currency_converter_all(self):
        """
        General: Test the money module's Currency().currency_converter() method.
        Specific: testing that all curriency1 --> curriency2 possibilities return numeric results.
        """
        # Get the Exchange options
        exchange_options = self.curr.options(info = "exchange", rformat = 'list', pretty_print = False)

        # LCU --> EUR
        for c in exchange_options:
            lcu_to_eur = self.curr.currency_converter(100, c, 'EUR', date = 'latest')
            self.assertEqual(isinstance(lcu_to_eur, (float, int)), True)

        # EUR --> LCU
        for c in exchange_options:
            lcu_to_eur = self.curr.currency_converter(100, 'EUR', c, date = 'latest')
            self.assertEqual(isinstance(lcu_to_eur, (float, int)), True)

    def test_currency_converter_EUR_USD(self):
        """
        General: Test the money module's Currency().currency_converter() method.
        Specific: Test Converting between USD and EUR against a known value.
        """

        # As of Sept 2, 2016, 100 EUR = 111.93 USD (based on ECB data).
        sept2_2016_eur_to_usd = self.curr.currency_converter(100, 'EUR', "USD", date = "2016-09-02")
        self.assertEqual(sept2_2016_eur_to_usd, 111.93)

        # As of Sept 2, 2016, 100 USD = 89.34 EUR (based on ECB data).
        sept2_2016_usd_to_eur = self.curr.currency_converter(100, 'USD', "EUR", date = "2016-09-02")
        self.assertEqual(sept2_2016_usd_to_eur, 89.34)

    def test_inflation_calculator(self):
        """

        """
        self.assertEqual(1, 1)

    def test_inflation_rate(self):
        """

        """
        self.assertEqual(1, 1)

    def test_normalize(self):
        """

        """
        self.assertEqual(1, 1)

# Run
unittest.main()





































































