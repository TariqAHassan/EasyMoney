import os
from setuptools import setup, find_packages


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return 'Please see: https://github.com/TariqAHassan/EasyMoney.'


setup(
    name = "easymoney",
    version = "1.5.0",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Data Science Tools for Monetary Information and Conversions."),
    long_description = read('docs/README.rst'),
    license = "BSD",
    keywords = 'economics, finance, inflation, currency converter, data analysis, data science',
    url = "https://github.com/TariqAHassan/EasyMoney.git",
    download_url='https://github.com/TariqAHassan/EasyMoney/archive/1.5.0.tar.gz',
    packages = find_packages(exclude = ["tests.*"
                                        , "tests"
                                        , "sources/single_use.*"
                                        , "sources/single_use"
                                        ]),
    package_data = {'easymoney': ['sources/data/*.csv'],},
    data_files = [('', ["LICENSE.txt"])],
    install_requires = ['numpy', 'pandas', 'pycountry', 'requests', 'wbdata'],
    classifiers = ["Development Status :: 5 - Production/Stable"
                   , "Natural Language :: English"
                   , "Intended Audience :: Science/Research"
                   , "Intended Audience :: Financial and Insurance Industry"
                   , "Programming Language :: Python :: 2.7"
                   , "Programming Language :: Python :: 3.3"
                   , "Programming Language :: Python :: 3.4"
                   , "Programming Language :: Python :: 3.5"
                   , "License :: OSI Approved :: BSD License"
    ],
    include_package_data = True
)


