#!/usr/bin/env python3

"""

    Tools for Obtaining Data from the European Central Bank
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

# Modules
import re
import requests
import pandas as pd

from easymoney.support_tools import date_reformat

def ecb_xml_exchange_data(return_as = 'dict', ecb_extension = "/stats/eurofxref/eurofxref-hist.xml"):
    """

    *Private Method*
    | This tool goes out to the European Central Bank via their generously provided API
    | and coerces XML data into a dictionary.
    | Expects 'time', 'currency', 'rate' in the XML data.
    | Returns a nested dictionary of the form: ``{time: {currency: rate}}``.
    | DO NOT WRITE PROCEDURES THAT SLAM THEIR SERVERS.

    :param return_as: 'dict' for dictionary (nested); 'df' for Pandas DataFrame OR 'both' for both a dict and DataFrame.
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

    # Request the data from the sever.
    url_request = requests.get(xmlpath)

    # Convert the XML to str, split on 'Cube><Cube' and remove the first element.
    parsed_xml = str(url_request.content).split("Cube><Cube")[1:]

    # Initialize the exchange rate dict
    exchange_rate_db = dict()

    # Iterate though the parsed XML
    for j in parsed_xml:
        date = re.findall(r'time="(.*?)"', j)[0]
        ccodes = re.findall(r'currency="(.*?)" rate=', j)
        rates = re.findall(r'rate="(.*?)"', j)
        exchange_rate_db[date_reformat(date, from_format="%Y-%m-%d")] = dict(zip(ccodes, [float(x) for x in rates]))
        all_currency_codes += [c for c in ccodes if c not in all_currency_codes]

    # return as dict
    if return_as == 'dict':
        return exchange_rate_db, all_currency_codes

    # return as pandas df
    elif return_as == 'data_frame' or return_as == 'both':
        # Convert to pandas dataframe
        df = pd.DataFrame.from_dict(exchange_rate_db, orient = 'index')

        # convert date index --> column
        df['Date'] = df.index
        df.index = range(df.shape[0])

        # Melt the dataframe
        df = pd.melt(df, id_vars = ['Date'], value_vars = [d for d in df.columns if d != 'Date'])
        df.rename(columns = {"variable" : "Currency", "value" : "Rate"}, inplace = True)

        # Drop NaNs
        df = df[pd.notnull(df['Rate'])]

        # Add Temp. Date Column
        df['DateTemp'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

        # Sort by currency code
        df.sort_values(['DateTemp', 'Currency'], ascending = [1, 1], inplace = True)

        # Drop DateTemp
        del df['DateTemp']

        # Refresh index
        df = df.reset_index(drop=True)

        if return_as == 'data_frame':
            return df, all_currency_codes
        elif return_as == 'both':
            return exchange_rate_db, df, all_currency_codes

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

