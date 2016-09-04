"""

Database of which Nations use which Currency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note: quick script -- unlikely to ever be used again
...hence the use of messy 'shortcuts'.

Python 3.5

"""

# Imports #
import re
import os
import numpy as np
import pandas as pd


# Import Curency Codes
currency_codes = pd.read_csv("data_sources/CurrencyCodesDB.csv", encoding = "ISO-8859-1")
currency_codes['Locations'] = currency_codes['Locations'].astype(str).map(lambda x: re.sub(r"\s\s+", " ", str(x).strip()))

# Move to the data directory
os.chdir("data")

# Import Country Codes
country_codes = pd.read_csv("CountryAlpha2_and_3.csv", encoding = "ISO-8859-1", keep_default_na = False)

# Construct Dicts
country_codes_dict = dict(zip(country_codes['Alpha2'], country_codes['Alpha3']))
country_codes_dict2 = dict(zip(country_codes['CountryName'], country_codes['Alpha2']))

# Dict. for special cases in the currency_codes dataframe.
currency_codes_special_cases_dict = {
      "Democratic Republic of the Congo" : "CD"
    , "Cape Verde" : "CV"
    , "Egypt, auxiliary in Gaza Strip" : "EG"
    , "North Korea" : "KP"
    , "South Korea" : "KR"
    , "Laos" : "LA"
}

# Currency Codes --> Alpha2
alpha2_list = list()
for c in currency_codes['Locations'].tolist():
    if "(" not in c:
        region = [k for k in country_codes_dict2.keys() if c.upper() in k.upper()]
        if c in currency_codes_special_cases_dict.keys():
            alpha2_list.append(currency_codes_special_cases_dict[c])
        else:
            if len(region) > 1:
                region = [r for r in region if c.upper() == r.upper()]
            if len(region) == 1:
                alpha2 = [country_codes_dict2[region[0]]]
                if len(alpha2) == 1 and all(x not in [[x.strip() for x in alpha2]] for x in [np.nan, '']):
                    alpha2_list.append(alpha2)
                else:
                    alpha2_list.append(np.NaN)
            else:
                alpha2_list.append(np.NaN)
    else:
        multi = [x.replace(")", "").replace("(", "") for x in re.findall(r"\(\w+\)", c)]
        alpha2_list.append(multi[0]) if len(multi) == 1 else alpha2_list.append(multi)

# Clean up
alpha2_list = [np.NaN if isinstance(c, list) and len(c) == 0 else c for c in alpha2_list]
alpha2_list = [[c] if not isinstance(c, list) and isinstance(c, str) else c for c in alpha2_list]

# Correct for weird match...
alpha2_list = [['HK'] if i == ['HK', 'MO'] else i for i in alpha2_list]

# Add to the data frame
currency_codes['Alpha2'] = alpha2_list

# Remove all bracketed information from the Locations column
currency_codes['Locations'] = currency_codes['Locations'].map(lambda x: re.sub(r"\s\s+", "", re.sub(r"\(.*\)", "", x)).strip())

# Remove rows with Alpha2 == nan
currency_codes = currency_codes[pd.notnull(currency_codes["Alpha2"])]
currency_codes.index = range(currency_codes.shape[0])

# Get Alpha3 code
alpha3_list = list()
for cc in currency_codes.Alpha2.tolist():
    alpha3_list.append([country_codes_dict[c] for c in cc])

# Add Alpha3 Column
currency_codes['Alpha3'] = alpha3_list

# Drop the Locations Column
currency_codes.drop('Locations', axis = 1, inplace = True)

# Reorder
currency_codes = currency_codes[['Currency', 'Code', 'Alpha2', 'Alpha3']]

# Rename column
currency_codes.rename(columns = {'Code': 'CurrencyCode'}, inplace = True)

# Save
currency_codes.to_pickle("CurrencyCodes_DB.p")




































