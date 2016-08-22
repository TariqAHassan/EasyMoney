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

EasyMoney requires: [numpy], [pandas], [bs4] and [wbdata]<sup>†</sup>.

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
2. [Euro foreign exchange reference rates - European Central Bank]
       * Source: European Central Bank (ECB).
       	* Notes:
       		1. The ECB data used here can be obtained directly from the link provided above.
       		2. Rates are updated by the ECB around 16:00 CET.
       		3. The ECB states, clearly, that usage for transaction purposes is strongly discouraged. This sentiment is echoed here; ***this tool is intended to be for information-purposes only***.
       		4. ALL RESULTS OBTAINED FROM EASYMONEY ARE THE RESULT OF CALCULATIONS *BASED* ON ECB DATA. THAT IS, THESE RESULTS ARE NOT A DIRECT REPORTING OF ECB-PROVIDED DATA.
       		

  [Consumer price index (2010 = 100)]: http://data.worldbank.org/indicator/FP.CPI.TOTL
  [Euro foreign exchange reference rates - European Central Bank]: https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html
  [numpy]: http://www.numpy.org
  [pandas]: http://pandas.pydata.org
  [bs4]: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  [wbdata]: https://github.com/OliverSherouse/wbdata
