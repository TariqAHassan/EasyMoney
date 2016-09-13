EasyMoney
=========

Overview
~~~~~~~~

Project Summary
'''''''''''''''

This package is primarily intended to be used in the domain of Data Science to simplify
the process of analysing data sets which contain money information. Often, the financial information
within, or often between, data sets is be separated in time (inflation), currency (conversion)
and/or the ways in which these sources refer to the currency being used (e.g., ISO Alpha2 Codes vs. Currency Codes).
Conventionally, this has required handcrafting a patchwork of techniques and tools to control for these differences on a
case-by-case basis. EasyMoney is intended to streamline this process to make comparisons across these dimensions
extremely simple and straightforward.

Feature Summary
'''''''''''''''

- Computing Inflation
- Currency Conversion
- Adjusting a given currency for Inflation
- 'Normalizing' a currency, i.e., adjust for inflation and then convert to a base currency.
- Relating ISO Alpha2/3 Codes, Currency Codes and a region's Natural Name.

**NOTICE: THIS TOOL IS FOR INFORMATION PURPOSES ONLY.**

--------------

Dependencies
~~~~~~~~~~~~

EasyMoney requires: `numpy <http://www.numpy.org>`__,
`pandas <http://pandas.pydata.org>`__,
`requests <http://docs.python-requests.org/en/master/>`__ and
`wbdata <https://github.com/OliverSherouse/wbdata>`__\ :sup:`†`.

--------------

Installation
~~~~~~~~~~~~

``$ pip3 install git+git://github.com/TariqAHassan/EasyMoney@master``

*Note*: EasyMoney requires Python 3.4 or later.

--------------

Examples
~~~~~~~~

Import the tool
'''''''''''''''

.. code:: python

    from easymoney.money import EasyPeasy

Create an instance of the EasyPeasy Class
'''''''''''''''''''''''''''''''''''''''''

.. code:: python

    ep = EasyPeasy()

Note: this may take a moment, depending on the speed of your internet
connection.

Prototypical Conversion Problems
''''''''''''''''''''''''''''''''

Currency Converter
''''''''''''''''''

.. code:: python

    ep.currency_converter(amount = 100, from_currency = "USD", to_currency = "EUR", pretty_print = True)

    # 88.75 EUR

Adjust for Inflation and Convert
''''''''''''''''''''''''''''''''

.. code:: python

    ep.normalize(amount = 100, currency = "USD", from_year = 2010, to_year = "latest", base_currency = "CAD", pretty_print = True)

    # 140.66 CAD

Convert Currency in a more Natural Way
''''''''''''''''''''''''''''''''''''''

.. code:: python

    ep.currency_converter(amount = 100, from_currency = "Canada", to_currency = "Ireland", pretty_print = True)

    # 68.58 EUR

Handling Common Currencies
''''''''''''''''''''''''''

Currency Conversion:
''''''''''''''''''''

.. code:: python

    ep.currency_converter(amount = 100, from_currency = "France", to_currency = "Germany", pretty_print = True)

    # 100.00 EUR

EasyMoney understands that these two nations share a common currency.

Normalization
'''''''''''''

.. code:: python

    ep.normalize(amount = 100, currency = "France", from_year = 2010, to_year = "latest", base_currency = "USD", pretty_print = True)

    # 118.98 USD

.. code:: python

    ep.normalize(amount = 100, currency = "Germany", from_year = 2010, to_year = "latest", base_currency = "USD", pretty_print = True)

    # 120.45 USD

EasyMoney also understands that, while these two nations may share a
common currency, inflation may differ.

Options
'''''''

It's easy to explore the terminology EasyMoney understands.

The following can be used interchangeably:

-  Region Names (as they appear in ``options()``)
-  ISO Alpha2 Codes
-  ISO Alpha3 Codes
-  Currency Codes

.. code:: python

    ep.options(info = 'all', pretty_print = True, overlap_only = True)

+-----------+----------+--------+--------+-----------+-----------------+-----------------+-------------+
| Region    | Currency | Alpha2 | Alpha3 | Inflation | Exchange        | Overlap         | Transitions |
|           |          |        |        | Range     | Range           |                 |             |
+===========+==========+========+========+===========+=================+=================+=============+
| Australia | AUD      | AU     | AUS    | [1960,    | [1999-01-04 :   | [1999-01-04 :   |             |
|           |          |        |        | 2015]     | 2016-09-12]     | 2015-12-31]     |             |
+-----------+----------+--------+--------+-----------+-----------------+-----------------+-------------+
| Austria   | EUR      | AT     | AUT    | [1960,    | [1999-01-04 :   | [1999-01-04 :   | 1999 (ATS   |
|           |          |        |        | 2015]     | 2016-09-12]     | 2015-12-31]     | to EUR)     |
+-----------+----------+--------+--------+-----------+-----------------+-----------------+-------------+
| Belgium   | EUR      | BE     | BEL    | [1960,    | [1999-01-04 :   | [1999-01-04 :   | 1999 (BEF   |
|           |          |        |        | 2015]     | 2016-09-12]     | 2015-12-31]     | to EUR)     |
+-----------+----------+--------+--------+-----------+-----------------+-----------------+-------------+
| ...       | ...      | ...    | ...    | ...       | ...             | ...             | ...         |
+-----------+----------+--------+--------+-----------+-----------------+-----------------+-------------+

Above, the *InflationRange* and *ExchangeRange* columns provide the range of dates for
which inflation and exchange rate information is available, respectively. The *Overlap* column
shows the range of dates shared by these two columns.
Additionally, the dates of known transitions from one currency to another are also provided.

To gain access to a summary of the exchange data alone, 'exchange' can be passed to *info*.
Similarly, 'inflation' can be passed to inspect inflation information separately.

.. code:: python

    # Currency Information Alone
    ep.options(info = 'exchange', pretty_print = True)

    # Inflation Information Alone
    ep.options(info = 'inflation', pretty_print = True)

Changing ``pretty_print`` to False will return the information in ``options()`` as
a ``Pandas DataFrame``.

.. code:: python

    inflation_df = ep.options(info = 'inflation', pretty_print = False)

It is also possible to simply obtain a list of regions for which
inflation information is available.

.. code:: python

    inflation_list = ep.options(info = 'inflation', rformat = 'list', pretty_print = False)

This can also be done for exchange rate information.

.. code:: python

    currency_list = ep.options(info = 'exchange', rformat = 'list', pretty_print = False)


Databases
'''''''''

It's also straightforward to gain access to the databases used by
``EasyPeasy()``.

To see all of the International Organization for Standardization (ISO)
Alpha2 and Alpha3 codes (along with a region's natural name) currently cached:

.. code:: python

    ep.ISOAlphaCodesDB

To see all of the known transitions from one currency to another:

.. code:: python

    ep.CurrencyTransitionDB

To see the raw Exchange Rate information currently cached:

.. code:: python

    ep.ExchangeRatesDB

To see the raw Consumer Price Index (CPI) information currently cached:

.. code:: python

    ep.ConsumerPriceIndexDB

Finally, to see the relationships between Country Names, ISO Alpha2/3
Codes and Currency Codes currently understood by ``EasyPeasy()``:

.. code:: python

    ep.ConsumerPriceIndexDB

It's also easy to save these databases to disk so they can be used
offline or modified. To do so, one can simply pass a directory when creating an
instance of the ``EasyPeasy()`` class.

.. code:: python

    ep = EasyPeasy('/path/of/your/choosing')

If this directory does not contain all of the required databases, it
will be populated with them. Conversely, if the the directory already contains
some of the required databases, ``EasyPeasy()`` will automagically
read in the existing databases and generate only those databases that are missing.

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

   -  Source: International Monetary Fund, International Financial
      Statistics.

2. `Euro foreign exchange reference rates - European Central
   Bank <https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html>`__

   -  Source: European Central Bank (ECB).

      -  Notes:

         1. The ECB data used here can be obtained directly from the
            link provided above.
         2. Rates are updated by the ECB around 16:00 CET.
         3. The ECB states, clearly, that usage for transaction purposes
            is strongly discouraged. This sentiment is echoed here;
            **as stated above, this tool is intended to be for
            information purposes only**.
         4. ALL EXCHANGE RESULTS OBTAINED FROM EASYMONEY ARE THE RESULT
            OF CALCULATIONS BASED ON ECB DATA. THAT IS, THESE RESULTS
            ARE NOT A DIRECT REPORTING OF ECB-PROVIDED DATA.

:sup:`†` Sherouse, Oliver (2014). Wbdata. Arlington, VA.
