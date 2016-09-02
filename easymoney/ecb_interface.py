#!/usr/bin/env python3


"""

    Tools for Obtaining Data from the European Central Bank
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

# Modules #
import re
import sys
import pandas as pd
from bs4 import BeautifulSoup
from easymoney.support_money import floater

if sys.version_info.major == 3:
    import urllib.request
elif sys.version_info.major == 2 and sys.version_info.minor >= 7:
    import urllib2
else:
    raise ImportError("Your Version of Python is too old. Please Consider upgrading to --at least-- Python 2.7.\n"
                      "Python 3.5 is preferable.")

def _soup_from_url(url, parser = 'lxml'):
    """

    *Private Method*
    Parses a URL with bs4's BeautifulSoup() method.

    :param url: URL to parse with BeautifulSoup().
    :type url: str
    :param parser: the parser to be used by BeautifulSoup(). Defaults to 'lxml'.
    :type parser: str
    :return: BeautifulSoup
    :rtype: bs4 obj
    """
    if sys.version_info.major == 3:
        return BeautifulSoup(urllib.request.urlopen(url), parser)
    else:
        return BeautifulSoup(urllib2.Request(url), parser)

def ecb_exchange_data(return_as = 'dict', ecb_extension = "/stats/eurofxref/eurofxref-hist.xml"):
    """

    | This tool goes out to the European Central Bank via their generously provided API
    | and coerces XML data into a dictionary. Expects 'time', 'currency', 'rate' in the XML data.
    | Returns a nested dictionary of the form: {time: {currency: rate}}.
    | DO NOT WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param return_as: 'dict' for dictionary (nested); 'df' for pandas dataframe.
    :type return_as: str
    :param ecb_extension: URL to the exchange rate XML data on "http://www.ecb.europa.eu".
                          Defaults to '/stats/eurofxref/eurofxref-hist.xml'.
    :type ecb_extension: str
    :return: exchange rate with EUR as the base-currency.
    :rtype: dict or Pandas DataFrame
    """
    # Initialize
    all_currency_codes = list()

    # Constuct the URL to the XML data on the ECB's website.
    xmlpath = "http://www.ecb.europa.eu" + ecb_extension

    # Parse with BeautifulSoup
    soup = _soup_from_url(xmlpath)

    # Convert to string
    ecb_hist_xml = str(soup.find_all("cube", attrs = {"time": True})).split(",")

    # Get all Dates
    exchange_rate_db = dict()

    # Extract time, currency and rate information
    for j in ecb_hist_xml:
        date = re.findall(r'time="(.*?)">', j)[0]
        ccodes = re.findall(r'currency="(.*?)" rate=', j)
        rates = re.findall(r'rate="(.*?)">', j)
        exchange_rate_db[date] = dict(zip(ccodes, [floater(x) for x in rates]))
        all_currency_codes += [c for c in ccodes if c not in all_currency_codes]

    # return as dict
    if return_as == 'dict':
        return exchange_rate_db, all_currency_codes

    # return as pandas df
    elif return_as == 'df':
        # Convert to pandas dataframe, convert date --> column and reindex
        df = pd.DataFrame.from_dict(exchange_rate_db, orient = 'index')
        df['date'] = df.index
        df.index = range(df.shape[0])

        # Melt the dataframe
        df = pd.melt(df, id_vars = ['date'], value_vars = [d for d in df.columns if d != 'date'])
        df.rename(columns = {"variable" : "currency", "value" : "rate"}, inplace = True)

        # Convert date column --> datetime
        df.date = pd.to_datetime(df.date, infer_datetime_format = True)

        # Sort by currency code
        df.sort_values(['date', 'currency'], ascending = [1, 1], inplace = True)

        # Refresh index
        df.index = range(df.shape[0])

        return df, all_currency_codes

ecb_currency_to_alpha2_dict = {   "CYP": "CY"
                                , "EEK": "EE"
                                , "LTL": "LT"
                                , "LVL": "LV"
                                , "MTL": "MT"
                                , "ROL": "RO"
                                , "SIT": "SI"
                                , "SKK": "SK"
                                , "TRL": "TR"
}
