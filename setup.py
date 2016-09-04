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
    version = "0.9",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Tools for common monetary problems."),
    long_description = markdown_reader('README.md'),
    license = "BSD",
    keywords = 'economics, finance',
    url = "https://github.com/TariqAHassan/EasyMoney.git",
    packages = find_packages(),
    package_data = {'': ['*.csv', '*.p'],},
    data_files = [('', ["LICENSE.txt"])],
    install_requires = ['numpy', 'pandas', 'wbdata'],
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




