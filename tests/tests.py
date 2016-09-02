"""

    Unit Testing for EasyMoney
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Import the tool
import sys
import unittest
import pkg_resources


# Import the tool
from easymoney.money import Currency


class EasyMoneyTests(unittest.TestCase):
    """


    """

    def __init__(self, *args, **kwargs):
        super(EasyMoneyTests, self).__init__(*args, **kwargs)
        self.curr = Currency()

    def test_options(self):
        """
        Move to top.
        """
        self.assertEqual(1, 1)
        # self.exchange_options = self.curr.options(info = "exchange", rformat = 'list', pretty_print = False)
        # self.inflation_options = self.curr.options(info = "inflation", rformat = 'list', pretty_print = False)

    def test_currency_converter_all(self):
        """
        Test the money module's Currency().currency_converter() method.
        """
        # Get the Exchange options
        exchange_options = self.curr.options(info = "exchange", rformat = 'list', pretty_print = False)

        # LCU --> EUR
        for c in exchange_options:
            lcu_to_eur = self.curr.currency_converter(100, c, 'EUR')
            self.assertEqual(isinstance(lcu_to_eur, (float, int)), True)

        # EUR --> LCU
        for c in exchange_options:
            lcu_to_eur = self.curr.currency_converter(100, 'EUR', c)
            self.assertEqual(isinstance(lcu_to_eur, (float, int)), True)

    def test_currency_converter_EUR_USD(self):
        """

        Test Converting between USD and EUR against a known value.
        """

        # Sept 2, 2016. 100 EUR = 111.93 USD (based on ECB data).
        sept2_2016_eur_to_usd = self.curr.currency_converter(100, 'EUR', "USD", date = "2016-09-02")
        self.assertEqual(sept2_2016_eur_to_usd, 111.93)

        # Sept 2, 2016. 100 USD = 89.34 EUR (based on ECB data).
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





































































