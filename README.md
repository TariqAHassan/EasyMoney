NewMoney
========

**Overview**

NewMoney is a set of tools for:
- computing inflation
- adjusting a given currency for inflation
- converting one currency into another based on averaged, historical data.
- 'normalizing' a currency.<sup>1</sup>

*A small, but convenient feature of this tool is that one need not 
know a country's currency code*

*Data*
Finance data is obtained from the World Bank Group's 
Application Programming Interface (API).

<sup>1</sup>Adjust for inflation and convert to USD.

Note: *NewMoney is in Alpha and very much under development*

------------------------------------------------------------------------

**Dependencies**

NewMoney requires: [numpy], [pandas] and [wbdata]<sup>†</sup>.

<sup>†</sup> Sherouse, Oliver (2014). Wbdata. Arlington, VA. 

------------------------------------------------------------------------

**Installation**

`$ pip3 install git+git://github.com/TariqAHassan/NewMoney@master`

*Note*: only for use with Python 3.5.

------------------------------------------------------------------------

**Examples**

***Setup***
```python
# Import
from new_money.money import Currency

# Create an instance of the currency class
curr = Currency()
```

***Get Inflation Rate***
```python
inf = curr.inflation_rate('Germany', '2014', '2015')
print(inf)
```

***Normalize Currency***
```python
# Normalize 10 of 'Germany' (i.e., EUR) to USD
norm = curr.currency_normalizer(10, "Germany", 2000, 2015)
print(norm)
```


------------------------------------------------------------------------

**License**


This software is provided under a BSD License.

------------------------------------------------------------------------

**References**

Indicators used:

1. [Consumer price index (2010 = 100)]
       * Source: International Monetary Fund, International Financial Statistics.
2. [Official exchange rate (LCU per US$, period average)]
       * Source: International Monetary Fund, International Financial Statistics.


  [Consumer price index (2010 = 100)]: http://data.worldbank.org/indicator/FP.CPI.TOTL
  [Official exchange rate (LCU per US$, period average)]: http://data.worldbank.org/indicator/PA.NUS.FCRF
  [numpy]: http://www.numpy.org
  [pandas]: http://pandas.pydata.org
  [wbdata]: https://github.com/OliverSherouse/wbdata
  
