from setuptools import setup, find_packages
from warnings import warn

try:
    import pypandoc
    markdown_reader = lambda md: pypandoc.convert(md, 'rst')
except:
    warn("Could not convert README.md to README.rst.\n"
         "If you'd like to refer to a local copy of EasyMoney's README, please install 'pypandocs'.")
    markdown_reader = lambda md: open(md, 'r').read()

setup(
    name = "easymoney",
    version = "1.0.0",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Tools for Monetary Information and Conversions."),
    long_description = markdown_reader('README.md'),
    license = "BSD",
    keywords = 'economics, finance, inflation, currency converter, data analysis, data science',
    url = "https://github.com/TariqAHassan/EasyMoney.git",
    download_url='https://github.com/TariqAHassan/EasyMoney/archive/1.0.1.tar.gz',
    packages = find_packages(exclude = [  "tests.*"
                                        , "tests"
                                        , "sources/single_use.*"
                                        , "sources/single_use"
                                        ]),
    package_data = {'': ['*.csv', '*.p'],},
    data_files = [('', ["LICENSE.txt"])],
    install_requires = ['numpy', 'pandas', 'wbdata', 'requests'],
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




