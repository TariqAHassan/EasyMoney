EasyMoney
=========

|Build Status|

Overview
~~~~~~~~

Project Summary
'''''''''''''''

This package is primarily intended to be used in the domain of Data Science to simplify
the process of analysing data sets which contain money information. Often, the financial information
within, and very often between, data sets is separated in time (inflation), currency (conversion)
as well as the ways in which these sources refer to the currency being used (e.g., country codes vs. currency codes).
Conventionally, this has required handcrafting a solution to control for these differences on a case-by-case basis.
EasyMoney is intended to streamline this process to make comparisons across these dimensions
extremely simple and straightforward.


Feature Summary
'''''''''''''''

-  Computing Inflation
-  Currency Conversion
-  Adjusting a given currency for Inflation
-  'Normalizing' a currency, i.e., adjust for inflation and then convert
   to a base currency.
-  Relating ISO Alpha2/3 Country Codes, Currency Codes as well as a
   Region's Name to one another.
-  This tool automatically obtains the latest inflation and
   exchange rate information from online databases.

**NOTICE: THIS TOOL IS FOR INFORMATION PURPOSES ONLY.**

--------------

Dependencies
~~~~~~~~~~~~

EasyMoney requires: `numpy <http://www.numpy.org>`__,
`pandas <http://pandas.pydata.org>`__,
`requests <http://docs.python-requests.org/en/master/>`__,
`pycountry <https://pypi.python.org/pypi/pycountry>`__ and
`wbdata <https://github.com/OliverSherouse/wbdata>`__\ †.

--------------

Installation
~~~~~~~~~~~~

Python Package Index:

.. code:: bash

    $ pip install easymoney

Latest Build:

.. code:: bash

    $ pip install git+git://github.com/TariqAHassan/EasyMoney@master

EasyMoney is compatible with Python 2.7 and 3.3+.

--------------

Examples
~~~~~~~~

Import the tool
'''''''''''''''

.. code:: python

    from easymoney.money import EasyPeasy

Create an instance of the EasyPeasy Class
'''''''''''''''''''''''''''''''''''''''''

The standard way to do this is as follows:

.. code:: python

    ep = EasyPeasy()

However, `fuzzy searching <https://github.com/seatgeek/fuzzywuzzy>`__
can also easily be enabled.

.. code:: python

    ep = EasyPeasy(fuzzy_threshold=True)

Prototypical Conversion Problems
''''''''''''''''''''''''''''''''

1. Currency Converter
'''''''''''''''''''''

.. code:: python

    ep.currency_converter(amount=100000, from_currency="USD", to_currency="EUR", pretty_print=True)

    # 94,553.71 EUR

2. Adjust for Inflation and Convert to a base currency
''''''''''''''''''''''''''''''''''''''''''''''''''''''

.. code:: python

    ep.normalize(amount=100000, region="CA", from_year=2010, to_year="latest", pretty_print=True)

    # 76,357.51 EUR

3. Convert Currency in a more Natural Way
'''''''''''''''''''''''''''''''''''''''''

.. code:: python

    ep.currency_converter(amount=100, from_currency="Canada", to_currency="Ireland", pretty_print=True)

    # 70.26 EUR

Handling Common Currencies
''''''''''''''''''''''''''

1. Currency Conversion:
'''''''''''''''''''''''

.. code:: python

    ep.currency_converter(amount=100, from_currency="France", to_currency="Germany", pretty_print=True)

    # 100.00 EUR

EasyMoney understands that these two nations share a common currency.

2. Normalization
''''''''''''''''

.. code:: python

    ep.normalize(amount=100, region="France", from_year=2010, to_year="latest", base_currency="USD", pretty_print=True)

    # 111.67 USD

.. code:: python

    ep.normalize(amount=100, region="Germany", from_year=2010, to_year="latest", base_currency="USD", pretty_print=True)

    # 113.06 USD

EasyMoney also understands that, while these two nations may share a
common currency, the rate of inflation in these regions could differ.

Region Information
''''''''''''''''''

EasyPeasy's ``region_map()`` method exposes some of the functionality
from the ``pycountries`` package in a streamlined manner.

.. code:: python

    ep.region_map('GB', map_to='alpha_3')

    # GBR

.. code:: python

    ep.region_map('GB', map_to='currency_alpha_3')

    # GBP

If fuzzy searching is enabled, the search term does not have to exactly
match those stored in the databases cached by an ``EasyPeasy`` instance.

For example, it is possible to find the ISO Alpha 2 country code for
'Germany' by passing 'German'.

.. code:: python

    ep.region_map('German', map_to='alpha_2')

    # DE

Options
'''''''

It's easy to explore the terminology understood by ``EasyPeasy``, as
well as the dates for which data is available.

.. code:: python

    ep.options()

+---------+-------+-------+----------+------------+-------------------+-------------------+
| Region  | Alpha | Alpha | Currenci | InflationD | ExchangeDates     | Overlap           |
|         | 2     | 3     | es       | ates       |                   |                   |
+=========+=======+=======+==========+============+===================+===================+
| Austral | AU    | AUS   | AUD      | [1960,     | [04/01/1999,      | [04/01/1999,      |
| ia      |       |       |          | 2015]      | 29/11/2016]       | 31/12/2015]       |
+---------+-------+-------+----------+------------+-------------------+-------------------+
| Austria | AT    | AUT   | EUR      | [1960,     | [04/01/1999,      | [04/01/1999,      |
|         |       |       |          | 2015]      | 29/11/2016]       | 31/12/2015]       |
+---------+-------+-------+----------+------------+-------------------+-------------------+
| Belgium | BE    | BEL   | EUR      | [1960,     | [04/01/1999,      | [04/01/1999,      |
|         |       |       |          | 2015]      | 29/11/2016]       | 31/12/2015]       |
+---------+-------+-------+----------+------------+-------------------+-------------------+
| ...     | ...   | ...   | ...      | ...        | ...               | ...               |
+---------+-------+-------+----------+------------+-------------------+-------------------+

Above, the 'InflationDates' and 'ExchangeDates' columns provide the
range of dates for which inflation and exchange rate information is
available, respectively. Additionally, all dates for which data is
available can be show by setting the ``range_table_dates`` parameter to
``False``. The 'Overlap' column shows the range of dates shared by the
'InflationDates' and 'ExchangeDates' columns.

--------------

License
~~~~~~~~~

This software is provided under a BSD License.

--------------

Resources
~~~~~~~~~

Indicators used:

1. `Consumer price index (2010 =
   100) <http://data.worldbank.org/indicator/FP.CPI.TOTL>`__

   -  Source: International Monetary Fund (IMF), International Financial
      Statistics.

      -  Notes:

         1. All inflation-related results obtained from easymoney
            (including, but not necessarily limited to, inflation rate
            and normalization) are the result of calculations based on
            IMF data. These results do not constitute a direct reporting
            of IMF-provided data.

2. `Euro foreign exchange reference rates - European Central
   Bank <https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html>`__

   -  Source: European Central Bank (ECB).

      -  Notes:

         1. The ECB data used here can be obtained directly from the
            link provided above.
         2. Rates are updated by the ECB around 16:00 CET.
         3. The ECB states, clearly, that usage of this data for
            transaction purposes is strongly discouraged. This sentiment
            is echoed here; as stated above, **this tool is for
            information purposes only**.
         4. All exchange rate-related results obtained from easymoney
            (including, but not necessarily limited to, currency
            conversion and normalization) are the result of calculations
            based on ECB data. These results do not constitute a direct
            reporting of ECB-provided data.

†Sherouse, Oliver (2014). Wbdata. Arlington, VA.

.. |Build Status| image:: https://travis-ci.org/TariqAHassan/EasyMoney.svg?branch=master
   :target: https://travis-ci.org/TariqAHassan/EasyMoney
