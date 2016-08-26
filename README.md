EasyMoney
=========

###Overview

EasyMoney is a set of tools for:

- computing inflation
- adjusting a given currency for inflation
- converting from one currency to another
- 'normalizing' a currency, i.e., adjust for inflation and then convert a base currency, e.g., USD.

**WARNING: Due to EasyMoney's Alpha Status, results are likely to contain inaccuracies.**

------------------------------------------------------------------------

###Dependencies

EasyMoney requires: [numpy], [pandas], [bs4] and [wbdata]<sup>†</sup>.

------------------------------------------------------------------------

###Installation

`$ pip3 install git+git://github.com/TariqAHassan/EasyMoney@master`

*Note*: EasyMoney requires Python 3 and will *not* work with Python 2.

------------------------------------------------------------------------

###Examples

#####Import the tool
```python
from easy_money.money import Currency
```

#####Create an instance of the Currency Class
```python
curr = Currency()
```

####Prototypical Conversion Problems

#####Currency Converter
```python
curr.currency_converter(amount = 100, from_currency = "USD", to_currency = "EUR", pretty_print = True)

# 88.75 EUR
```

#####Adjust for Inflation and Convert
```python
curr.normalize(amount = 100, currency = "USD", from_year = 2010, to_year = "most_recent", base_currency = "CAD", pretty_print = True)

# 140.66 CAD
```

#####Convert Currency in a more Natural Way
```python
curr.currency_converter(amount = 100, from_currency = "Canada", to_currency = "Ireland", pretty_print = True)

# 68.58 EUR
```

####Handling Common Curriences

#####1. Currency Conversion:
```python
curr.currency_converter(amount = 100, from_currency = "France", to_currency = "Germany", pretty_print = True)

# 100.00 EUR
```
EasyMoney understands that these two nations share a common currency.

#####2. Normalization

```python
curr.normalize(amount = 100, currency = "France", from_year = 2010, to_year = "most_recent", base_currency = "USD", pretty_print = True)

# 118.98 USD
```

```python
curr.normalize(amount = 100, currency = "Germany", from_year = 2010, to_year = "most_recent", base_currency = "USD", pretty_print = True)

# 120.45 USD
```

EasyMoney also understands that, while these two nations may share a common currency, inflation is not assured to be the in the two countries.

------------------------------------------------------------------------

##License

This software is provided under a BSD License.

------------------------------------------------------------------------

##References

Indicators used:

1. [Consumer price index (2010 = 100)]
       * Source: International Monetary Fund, International Financial Statistics.
2. [Euro foreign exchange reference rates - European Central Bank]
       * Source: European Central Bank (ECB).
       	* Notes:
       		1. The ECB data used here can be obtained directly from the link provided above.
       		2. Rates are updated by the ECB around 16:00 CET.
       		3. The ECB states, clearly, that usage for transaction purposes is strongly discouraged. This sentiment is echoed here; ***this tool is intended to be for information-purposes only***.
       		4. ALL RESULTS OBTAINED FROM EASYMONEY ARE THE RESULT OF CALCULATIONS *BASED* ON ECB DATA. THAT IS, THESE RESULTS ARE NOT A DIRECT REPORTING OF ECB-PROVIDED DATA.
    

<sup>†</sup>Sherouse, Oliver (2014). Wbdata. Arlington, VA. 

  [Consumer price index (2010 = 100)]: http://data.worldbank.org/indicator/FP.CPI.TOTL
  [Euro foreign exchange reference rates - European Central Bank]: https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html
  [numpy]: http://www.numpy.org
  [pandas]: http://pandas.pydata.org
  [bs4]: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  [wbdata]: https://github.com/OliverSherouse/wbdata
