#!/usr/bin/env python3

"""

Tools for Obtaining European Central Bank Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.5

"""

# Modules #
import re
import urllib.request
from bs4 import BeautifulSoup
from easy_money.support_money import floater

def _soup_from_url(url, parser = 'lxml'):
    """

    :param xmlpath:
    :return:
    """
    return BeautifulSoup(urllib.request.urlopen(url), parser)

def _ecb_exchange_data(return_as = 'dict', xmlpath = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"):
    """

    NOTE:
    THIS GOES OUT TO THE EROPEAN CENTRAL BANK via THEIR GENEROUSLY PROVIDED API.
    DO *NOT* WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param xmlpath: URL9 to the exchange XML
    :param return_as: dict for dictionary (nested); df for pandas dataframe
    :return: exchangerate w.r.t. EURO as the base-currency
    :rtype: dict or pandas dataframe
    """

    # Parse with beautifulsoup
    soup = _soup_from_url(xmlpath).find("gesmes:envelope")
    soup = soup.find("cube")

    # Convert to string
    ecb_hist_xml = str(soup.find_all("cube", attrs={"time":True})).split(",")

    # Get all Dates
    exchange_rate_db = dict.fromkeys([re.findall(r'time="(.*?)">', i)[0] for i in ecb_hist_xml])

    # Extract time, currency and rate information
    for j in ecb_hist_xml:
        date = re.findall(r'time="(.*?)">', j)[0]
        alpha3 = re.findall(r'currency="(.*?)" rate=', j)
        rate = re.findall(r'rate="(.*?)">', j)
        exchange_rate_db[date] = dict(zip(alpha3, [floater(x) for x in rate]))

    # return as dict
    if return_as == 'dict':
        return exchange_rate_db

    # return as pandas df
    elif return_as == 'df':

        # Convert to pandas dataframe, convert date --> column and reindex
        df = pd.DataFrame.from_dict(exchange_rate_db, orient = 'index')
        df['date'] = df.index
        df.index = range(df.shape[0])

        # Melt the dataframe
        df = pd.melt(df, id_vars=['date'], value_vars = [d for d in df.columns if d != 'date'] )
        df.rename(columns = {"variable" : "alpha3", "value" : "rate"}, inplace = True)

        # Convert data column --> datetime
        df.date = pd.to_datetime(df.date, infer_datetime_format=True)

        return df





