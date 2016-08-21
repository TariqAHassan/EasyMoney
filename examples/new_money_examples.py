"""

Demo of NewMoney
~~~~~~~~~~~~~~~~

"""

# Import
from new_money.money import Currency

# Demo

# Create an instance of the money class
curr = Currency()

# Normalize 10 of --whatever the currency in Gemany was-- in 2000 to 2015 USD.
# Will Adjust for inflation
norm = curr.currency_normalizer(10, "Germany", 2000, 2015)
print(norm)



