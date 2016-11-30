EasyMoney
=========

[![Build Status](https://travis-ci.org/TariqAHassan/EasyMoney.svg?branch=master)](https://travis-ci.org/TariqAHassan/EasyMoney)

###Overview

Feature Summary:

- Computing Inflation
- Currency Conversion
- Adjusting a given currency for Inflation
- 'Normalizing' a currency, i.e., adjust for inflation and then convert to a base currency.
- Relating ISO Alpha2/3 Country Codes, Currency Codes as well as a region's name to one another.
- Automatically obtains the latest inflation and currency exchange rate information though online APIs.

**NOTICE: THIS TOOL IS FOR INFORMATION PURPOSES ONLY.**

------------------------------------------------------------------------

###Dependencies

EasyMoney requires: [numpy], [pandas], [requests], [pycountry] and [wbdata]<sup>†</sup>.

------------------------------------------------------------------------

###Installation

Python Package Index:
```bash
$ pip install easymoney
```

Latest Build:
```bash
$ pip install git+git://github.com/TariqAHassan/EasyMoney@master
```

EasyMoney is compatible with Python 2.7 and 3.3+.

------------------------------------------------------------------------

###Examples

#####Import the tool
```python
from easymoney.money import EasyPeasy
```

#####Create an instance of the EasyPeasy Class

The standard way to do this is as follows:

```python
ep = EasyPeasy()
```

However, [fuzzy searching] can easily be enabled.

```python
ep = EasyPeasy(fuzzy_threshold=True)
```

####Prototypical Conversion Problems

#####1. Currency Converter
```python
ep.currency_converter(amount=100000, from_currency="USD", to_currency="EUR", pretty_print=True)

# 94,553.71 EUR
```

#####2. Adjust for Inflation and Convert to a base currency
```python
ep.normalize(amount=100000, region="CA", from_year=2010, to_year="latest", pretty_print=True)

# 76,357.51 EUR
```

#####3. Convert Currency in a more Natural Way
```python
ep.currency_converter(amount=100, from_currency="Canada", to_currency="Ireland", pretty_print=True)

# 70.26 EUR
```

####Handling Common Currencies

#####1. Currency Conversion:
```python
ep.currency_converter(amount=100, from_currency="France", to_currency="Germany", pretty_print=True)

# 100.00 EUR
```
EasyMoney understands that these two nations share a common currency.

#####2. Normalization

```python
ep.normalize(amount=100, region="France", from_year=2010, to_year="latest", base_currency="USD", pretty_print=True)

# 111.67 USD
```

```python
ep.normalize(amount=100, region="Germany", from_year=2010, to_year="latest", base_currency="USD", pretty_print=True)

# 113.06 USD
```

EasyMoney also understands that, while these two nations may share a common currency, the rate of inflation in these regions could differ.

####Region Information

EasyPeasy's `region_map()` method exposes some of the functionality from the `pycountries` package in 
a streamlined manner.


```python
ep.region_map('GB', map_to='alpha_3')

# GBR
```

```python
ep.region_map('GB', map_to='currency_alpha_3')

# GBP
```


If fuzzy searching is enabled, the search term does not have to exactly match
those stored in the databases cached by an `EasyPeasy` instance.

For example, it is possible to find the ISO Alpha 2 country code for 'Germany' by passing 'German'.

```python
ep.region_map('German', map_to='alpha_2')

# DE
```

####Options

It's easy to explore the terminology understood by `EasyPeasy`, as well as the dates for which
data is available, with `options()`.

```python
ep.options()
```

|   Region  | Alpha2 | Alpha3 | Currencies | InflationDates |      ExchangeDates        |         Overlap           |     
|:---------:|:------:|:------:|:----------:|:--------------:|:-------------------------:|:-------------------------:|
| Australia |   AU   |  AUS   |     AUD    |  [1960, 2015]  | [04/01/1999, 29/11/2016] | [04/01/1999, 31/12/2015]   |
|  Austria  |   AT   |  AUT   |     EUR    |  [1960, 2015]  | [04/01/1999, 29/11/2016] | [04/01/1999, 31/12/2015]   |
|  Belgium  |   BE   |  BEL   |     EUR    |  [1960, 2015]  | [04/01/1999, 29/11/2016] | [04/01/1999, 31/12/2015]   |
|   ...     |  ...   | ...    |     ...    |      ...       |           ...             |           ...             |

Above, the 'InflationDates' and 'ExchangeDates' columns provide the range of dates for which inflation and exchange rate information 
is available, respectively. Additionally, all dates for which data is available can be show by setting the 
`range_table_dates` parameter to `False`. The 'Overlap' column shows the range of dates shared by the 'InflationDates'
and 'ExchangeDates' columns.

------------------------------------------------------------------------

##Documentation

For complete documentation please click [here].

------------------------------------------------------------------------

##License

This software is provided under a BSD License.

------------------------------------------------------------------------

##Resources

Indicators used:

1. [Consumer price index (2010 = 100)]
       * Source: International Monetary Fund (IMF), International Financial Statistics.
       	* Notes:
       		1. All inflation-related results obtained from easymoney (including, but not necessarily limited to, inflation rate and normalization) are the result of calculations based on IMF data.
       		   These results do not constitute a direct reporting of IMF-provided data.
2. [Euro foreign exchange reference rates - European Central Bank]
       * Source: European Central Bank (ECB).
       	* Notes:
       		1. The ECB data used here can be obtained directly from the link provided above.
       		2. Rates are updated by the ECB around 16:00 CET.
       		3. The ECB states, clearly, that usage of this data for transaction purposes is strongly discouraged. 
       		   This sentiment is echoed here; as stated above, ***this tool is for information purposes only***.
       		4. All exchange rate-related results obtained from easymoney (including, but not necessarily limited to, currency conversion and normalization) are the result of calculations based on ECB data.
       		   These results do not constitute a direct reporting of ECB-provided data.
    
<sup>†</sup>Sherouse, Oliver (2014). Wbdata. Arlington, VA. 

  [Consumer price index (2010 = 100)]: http://data.worldbank.org/indicator/FP.CPI.TOTL
  [Euro foreign exchange reference rates - European Central Bank]: https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html
  [numpy]: http://www.numpy.org
  [pandas]: http://pandas.pydata.org
  [requests]: http://docs.python-requests.org/en/master/
  [pycountry]: https://pypi.python.org/pypi/pycountry
  [wbdata]: https://github.com/OliverSherouse/wbdata
  [fuzzy searching]: https://github.com/seatgeek/fuzzywuzzy 
  [here]: https://tariqahassan.github.io/EasyMoney/index.html