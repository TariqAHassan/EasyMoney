EasyMoney
========

**Overview**

EasyMoney is a set of tools for:
- computing inflation
- adjusting a given currency for inflation
- converting one currency into another based on averaged, historical data.
- 'normalizing' a currency.<sup>1</sup>

*Data*
Finance data is obtained from the World Bank Group's 
Application Programming Interface (API).

<sup>1</sup>Adjust for inflation and convert to USD.

Note: *EasyMoney is in Alpha and very much under development*

------------------------------------------------------------------------

**Dependencies**

EasyMoney requires: [numpy], [pandas] and [wbdata]<sup>†</sup>.

<sup>†</sup> Sherouse, Oliver (2014). Wbdata. Arlington, VA. 

------------------------------------------------------------------------

**Installation**

`$ pip3 install git+git://github.com/TariqAHassan/EasyMoney@master`

*Note*: only known to be stable with Python 3.5.

------------------------------------------------------------------------

**Examples**

Coming Soon...

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
  
