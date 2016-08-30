#!/usr/bin/env python3

"""

Tools for Obtaining European Central Bank Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

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
    raise ImportError("Your Version of Python is too old. Please Consider upgrading to --at least-- Python 2.7.")

def _soup_from_url(url, parser = 'lxml'):
    """

    :param xmlpath:
    :return:
    """
    if sys.version_info.major == 3:
        return BeautifulSoup(urllib.request.urlopen(url), parser)
    else:
        return BeautifulSoup(urllib2.Request(url), parser)

def _ecb_exchange_data(return_as = 'dict', xmlpath = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"):
    """

    NOTE:
    THIS GOES OUT TO THE EROPEAN CENTRAL BANK via THEIR GENEROUSLY PROVIDED API.
    DO *NOT* WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param return_as: 'dict' for dictionary (nested); 'df' for pandas dataframe.
    :param xmlpath: URL to the exchange XML
    :return: exchangerate w.r.t. EURO as the base-currency
    :rtype: dict or pandas dataframe
    """

    # Parse with beautifulsoup
    soup = _soup_from_url(xmlpath)

    # Convert to string
    ecb_hist_xml = str(soup.find_all("cube", attrs = {"time" : True})).split(",")

    # Get all Dates
    exchange_rate_db = dict.fromkeys([re.findall(r'time="(.*?)">', i)[0] for i in ecb_hist_xml])

    # Extract time, currency and rate information
    for j in ecb_hist_xml:
        date = re.findall(r'time="(.*?)">', j)[0]
        ccode = re.findall(r'currency="(.*?)" rate=', j)
        rate = re.findall(r'rate="(.*?)">', j)
        exchange_rate_db[date] = dict(zip(ccode, [floater(x) for x in rate]))

    # return as dict
    if return_as == 'dict':
        return exchange_rate_db, ccode

    # return as pandas df
    elif return_as == 'df':

        # Convert to pandas dataframe, convert date --> column and reindex
        df = pd.DataFrame.from_dict(exchange_rate_db, orient = 'index')
        df['date'] = df.index
        df.index = range(df.shape[0])

        # Melt the dataframe
        df = pd.melt(df, id_vars = ['date'], value_vars = [d for d in df.columns if d != 'date'])
        df.rename(columns = {"variable" : "ccode", "value" : "rate"}, inplace = True)

        # Convert data column --> datetime
        df.date = pd.to_datetime(df.date, infer_datetime_format = True)

        return df, ccode

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



