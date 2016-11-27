import os

from setuptools import setup, find_packages
from warnings import warn

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return 'Please see: https://github.com/TariqAHassan/EasyMoney.'

setup(
    name = "easymoney",
    version = "1.0.0",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Tools for Monetary Information and Conversions."),
    long_description = read('docs/README.rst'),
    license = "BSD",
    keywords = 'economics, finance, inflation, currency converter, data analysis, data science',
    url = "https://github.com/TariqAHassan/EasyMoney.git",
    download_url='https://github.com/TariqAHassan/EasyMoney/archive/1.0.0.tar.gz',
    packages = find_packages(exclude = [  "tests.*"
                                        , "tests"
                                        , "sources/single_use.*"
                                        , "sources/single_use"
                                        ]),
    package_data = {'sources': ['data/*.csv'],},
    data_files = [('', ["LICENSE.txt"])],
    install_requires = ['numpy', 'pandas', 'wbdata', 'requests', 'pycountry'],
    classifiers = [  "Development Status :: 5 - Production/Stable"
                   , "Natural Language :: English"
                   , "Intended Audience :: Science/Research"
                   , "Intended Audience :: Financial and Insurance Industry"
                   , "Programming Language :: Python :: 3.4"
                   , "Programming Language :: Python :: 3.5"
                   , "Environment :: MacOS X"
                   , "License :: OSI Approved :: BSD License"
    ],
    include_package_data = True
)




