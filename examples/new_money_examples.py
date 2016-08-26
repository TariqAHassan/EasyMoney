# Import the tool #
from easymoney.money import Currency

# Create an instance of the Currency Class
curr = Currency()
# Note: this may take a moment, depending on the speed of your internet connection.

# Prototypical Conversion Problems #

# Currency Converter
curr.currency_converter(amount = 100, from_currency = "USD", to_currency = "EUR", pretty_print = True)

# Adjust for Inflation and Convert
curr.normalize(amount = 100, currency = "USD", from_year = 2010, to_year = "most_recent", base_currency = "CAD", pretty_print = True)


# Convert Currency in a more Natural Way
curr.currency_converter(amount = 100, from_currency = "Canada", to_currency = "Ireland", pretty_print = True)

# Handling Common Currencies #

# 1. Currency Conversion:
curr.currency_converter(amount = 100, from_currency = "France", to_currency = "Germany", pretty_print = True)

# EasyMoney understands that these two nations share a common currency.

# 2. Normalization
curr.normalize(amount = 100, currency = "France", from_year = 2010, to_year = "most_recent", base_currency = "USD", pretty_print = True)
curr.normalize(amount = 100, currency = "Germany", from_year = 2010, to_year = "most_recent", base_currency = "USD", pretty_print = True)

# EasyMoney also understands that, while these two nations may share a common currency, inflation may differ.



