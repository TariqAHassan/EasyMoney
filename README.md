EasyMoney
=========

[![Build Status](https://travis-ci.org/TariqAHassan/EasyMoney.svg?branch=master)](https://travis-ci.org/TariqAHassan/EasyMoney)

###Overview

EasyMoney is a set of tools for:

- computing inflation
- currency conversions
- adjusting a given currency for inflation
- 'normalizing' a currency, i.e., adjust for inflation and then convert to a base currency.
- doing all of the above without having to memorize currency codes!

**NOTICE: THIS TOOL IS FOR INFORMATION PURPOSES ONLY.**

------------------------------------------------------------------------

###Dependencies

EasyMoney requires: [numpy], [pandas], [requests] and [wbdata]<sup>†</sup>.

Internet access is required to create an instance of the main `EasyPeasy()` class.
However, once EasyMoney has cached the latest data from online databases (see below), internet
access is no longer required.

------------------------------------------------------------------------

###Installation

`$ pip3 install git+git://github.com/TariqAHassan/EasyMoney@master`

*Note*: EasyMoney requires Python 3.4 or later.

------------------------------------------------------------------------

###Examples

#####Import the tool
```python
from easymoney.money import EasyPeasy
```

#####Create an instance of the EasyPeasy Class
```python
ep = EasyPeasy()
```
Note: this may take a moment, depending on the speed of your internet connection.

####Prototypical Conversion Problems

#####Currency Converter
```python
ep.currency_converter(amount = 100, from_currency = "USD", to_currency = "EUR", pretty_print = True)

# 88.75 EUR
```

#####Adjust for Inflation and Convert
```python
ep.normalize(amount = 100, currency = "USD", from_year = 2010, to_year = "latest", base_currency = "CAD", pretty_print = True)

# 140.66 CAD
```

#####Convert Currency in a more Natural Way
```python
ep.currency_converter(amount = 100, from_currency = "Canada", to_currency = "Ireland", pretty_print = True)

# 68.58 EUR
```

####Handling Common Currencies

#####1. Currency Conversion:
```python
ep.currency_converter(amount = 100, from_currency = "France", to_currency = "Germany", pretty_print = True)

# 100.00 EUR
```
EasyMoney understands that these two nations share a common currency.

#####2. Normalization

```python
ep.normalize(amount = 100, currency = "France", from_year = 2010, to_year = "latest", base_currency = "USD", pretty_print = True)

# 118.98 USD
```

```python
ep.normalize(amount = 100, currency = "Germany", from_year = 2010, to_year = "latest", base_currency = "USD", pretty_print = True)

# 120.45 USD
```

EasyMoney also understands that, while these two nations may share a common currency, inflation may differ.

####Options

It's easy to explore the terminology EasyMoney understands.

The following can be used interchangeably:

- Region Names (as they appear in `options()`)
- ISO Alpha2 Codes
- ISO Alpha3 Codes
- Currency Codes*

*This may fail when attempting to obtain inflation information about a country that uses a common currency. 

```python
ep.options(info = 'all', pretty_print = True, overlap_only = True)
```

|   Region  | Currency | Alpha2 | Alpha3 | InflationRange |      CurrencyRange       |       Overlap            |CurrencyTransition |
|:---------:|:--------:|:------:|:------:|:--------------:|:------------------------:|:------------------------:|:-----------------:|
| Australia |  AUD     | AU     | AUS    |  [1960, 2015]  | [1999-01-04, 2016-08-29] | [1999-01-04, 2015-12-31] |                   |
| Canada    |  CAD     | CA     | CAN    |  [1960, 2015]  | [1999-01-04, 2016-08-29] | [1999-01-04, 2015-12-31] |                   |
| Cyprus    |  EUR     | CY     | CYP    |  [1960, 2015]  | [1999-01-04, 2007-12-31] | [1999-01-04, 2007-12-31] |              2008 |
|   ...     |  ...     | ...    | ...    |      ...       |           ...            |           ...            |               ... |  

As can be seen above, the date ranges for which Inflation (InflationRange) and Exchange Rate (CurrencyRange) data is available 
(as well as when these two overlap) are provided. Additionally, the dates of (some) transitions from one currency to another 
(CurrencyTransition) are noted.

One can also gain access to *currency* and *inflation* information separately.
```python
# Currency Information Alone
ep.options(info = 'exchange', pretty_print = True)

# Inflation Infomation Alone
ep.options(info = 'inflation', pretty_print = True)
```

Additionally, instead of printing a given data table, it can be returned as Pandas DataFrame.
```python
inflation_df = ep.options(info = 'inflation', pretty_print = False)
```

It is also possible to simply obtain a list of regions for which inflation information is available.
```python
inflation_list = ep.options(info = 'inflation', rformat = 'list', pretty_print = False)
```
This can also be done for exchange rate information.
```python
currency_list = ep.options(info = 'exchange', rformat = 'list', pretty_print = False)
```

*Note*: Errors may emerge when converting across currency transitions, e.g., CY (2005) → CY (2010).

####Databases

It's also straightforward to gain access to the databases used
by ``EasyPeasy()``.

To see all of the International Organization for Standardization (ISO) Alpha2
codes currently cached:
```python
ep.ISOAlphaCodesDB
```

To see all of the known transitions from one currency to another:
```python
ep.CurrencyTransitionDB
```

To see the raw Exchange Rate information currently cached:
```python
ep.ExchangeRatesDB
```

To see the raw Consumer Price Index (CPI) information currently cached:
```python
ep.ConsumerPriceIndexDB
```

Finally, to see the relationships between Country Names, ISO Alpha2/3 Codes
and Currency Codes currently understood by ``EasyPeasy()``:
```python
ep.ConsumerPriceIndexDB
```

It's also easy to save these databases to disk so they can be used offline
or modified. One can simply pass a directory when creating an instance of the class.
```python
ep = EasyPeasy('/path/of/your/choosing')
```

If this directory does not contain all of the required DataBases, it will 
be populate it with them.

If the directory already contains some of the required databases, ``EasyPeasy()``
will automagically read in the existing databases and generate only those
databases that are missing. 

------------------------------------------------------------------------

##Documentation

For complete documentation, please click [here].

------------------------------------------------------------------------

##License

This software is provided under a BSD License.

------------------------------------------------------------------------

##Resources

Indicators used:

1. [Consumer price index (2010 = 100)]
       * Source: International Monetary Fund, International Financial Statistics.
2. [Euro foreign exchange reference rates - European Central Bank]
       * Source: European Central Bank (ECB).
       	* Notes:
       		1. The ECB data used here can be obtained directly from the link provided above.
       		2. Rates are updated by the ECB around 16:00 CET.
       		3. The ECB states, clearly, that usage for transaction purposes is strongly discouraged. 
       		   This sentiment is echoed here; ***as stated above, this tool is intended to be for information purposes only***.
       		4. ALL EXCHANGE RESULTS OBTAINED FROM EASYMONEY ARE THE RESULT OF CALCULATIONS BASED ON ECB DATA. THAT IS, THESE RESULTS ARE NOT A DIRECT REPORTING OF ECB-PROVIDED DATA.
    
<sup>†</sup>Sherouse, Oliver (2014). Wbdata. Arlington, VA. 

  [Consumer price index (2010 = 100)]: http://data.worldbank.org/indicator/FP.CPI.TOTL
  [Euro foreign exchange reference rates - European Central Bank]: https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html
  [numpy]: http://www.numpy.org
  [pandas]: http://pandas.pydata.org
  [requests]: http://docs.python-requests.org/en/master/
  [wbdata]: https://github.com/OliverSherouse/wbdata
  [here]: https://tariqahassan.github.io/EasyMoney/index.html