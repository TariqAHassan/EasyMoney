from setuptools import setup, find_packages

setup(
    name = "easymoney",
    version = "0.9",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Tools for common monetary problems."),
    long_description = open('README.md', 'r').read(),
    license = "BSD",
    keywords = 'economics, finance',
    url = "https://github.com/TariqAHassan/NewMoney.git",
    packages = find_packages(),
    package_data = {'': ['*.csv', '*.p'],},
    data_files = [('', ["LICENSE.txt"])],
    install_requires = ['numpy', 'pandas', 'wbdata', 'bs4', 'setuptools-git'],
    classifiers = [  "Development Status :: 4 - Beta"
                   , "Natural Language :: English"
                   , "Intended Audience :: Financial and Insurance Industry"
                   , "Intended Audience :: Science/Research"
                   , "Programming Language :: Python :: 3.5"
                   , "Environment :: MacOS X"
                   , "License :: OSI Approved :: BSD License"
    ],
    include_package_data = True
)


