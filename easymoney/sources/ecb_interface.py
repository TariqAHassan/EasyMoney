#!/usr/bin/env python3

"""

    European Central Bank Data
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
# Modules
import re
import requests
import pandas as pd

from collections import defaultdict
from easymoney.support_tools import date_sort
from easymoney.support_tools import date_reformat


def _ecb_data_frame(exchange_rate_dict):
    """

    Convert `exchange_rate_dict` into a Pandas DataFrame

    :param exchange_rate_dict: data harvest by `ecb_xml_exchange_data()`.
    :type exchange_rate_dict: ``dict``
    :return: dataframe of ECB exchange data.
    :rytpe: ``Pandas DataFrame``
    """
    # Convert to pandas dataframe
    df = pd.DataFrame.from_dict(exchange_rate_dict, orient='index')

    # convert date index --> column
    df['Date'] = df.index
    df.index = range(df.shape[0])

    # Melt the dataframe
    df = pd.melt(df, id_vars=['Date'], value_vars=[d for d in df.columns if d != 'Date'])
    df.rename(columns={"variable": "Currency", "value": "Rate"}, inplace=True)

    # Drop NaNs
    df = df[pd.notnull(df['Rate'])]

    # Add Temp. Date Column
    df['DateTemp'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    # Sort by currency code
    df.sort_values(['DateTemp', 'Currency'], ascending=[1, 1], inplace=True)

    # Drop DateTemp
    del df['DateTemp']

    # Refresh index and Return
    return df.reset_index(drop=True)


def ecb_xml_exchange_data(return_as='dict', ecb_extension="stats/eurofxref/eurofxref-hist.xml"):
    """

    | This tool harvests XML data European Central Bank via their generously provided API.
    | Expects the follwing in the XML data: 'time', 'currency' and 'rate'.
    | Returns either a Pandas DataFrame or nested dictionary of the form: ``{time: {currency: rate}}``.
    | Please do not write procedures that slam their servers.

    :param return_as: 'dict' for dictionary (nested); 'df' for Pandas DataFrame OR 'both' for both a dict and DataFrame.
    :type return_as: ``str``
    :param ecb_extension: URL to the exchange rate XML data on ``"http://www.ecb.europa.eu"``.
                          Defaults to ``'/stats/eurofxref/eurofxref-hist.xml'``.
    :type ecb_extension: ``str``
    :return: exchange rate with EUR as the base-currency.
    :rtype: ``dict`` or ``Pandas DataFrame``
    """
    # Currency Codes
    all_currency_codes = list()

    # Constuct the URL to the XML data on the ECB's website.
    xmlpath = "http://www.ecb.europa.eu/" + ecb_extension

    # Request the data from the sever.
    url_request = requests.get(xmlpath)

    # Convert the XML to str, split on 'Cube><Cube' and remove the first element.
    parsed_xml = str(url_request.content).split("Cube><Cube")[1:]

    # Initialize the exchange rate dict
    exchange_rate_dict = dict()

    # Initialize dict to track dates by currency
    currency_date_record = defaultdict(set)

    # Iterate though the parsed XML
    for j in parsed_xml:
        date = re.findall(r'time="(.*?)"', j)[0]
        ccodes = re.findall(r'currency="(.*?)" rate=', j)
        rates = re.findall(r'rate="(.*?)"', j)

        # Reformat Date
        reformatted_date = date_reformat(date, from_format="%Y-%m-%d")

        # Build Exchange Rate Dict
        exchange_rate_dict[reformatted_date] = dict(zip(ccodes, [float(x) for x in rates]))

        # Track Currency Codes
        all_currency_codes += [c for c in ccodes if c not in all_currency_codes]

        # Track Dates
        for c in ccodes:
            currency_date_record[c].add(reformatted_date)

    # Sort currency_date_record
    currency_date_record_sorted = {k: date_sort(v) for k, v in currency_date_record.items()}

    # return as dict
    if return_as == 'dict':
        return exchange_rate_dict, all_currency_codes, currency_date_record_sorted
    elif return_as == 'data_frame':
        return _ecb_data_frame(exchange_rate_dict), all_currency_codes
    elif return_as == 'both':
        return exchange_rate_dict, _ecb_data_frame(exchange_rate_dict), all_currency_codes, currency_date_record_sorted
    else:
        raise ValueError("`return_as` must be one of: 'dict', 'data_frame' or `both`.")

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








