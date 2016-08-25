from setuptools import setup

setup(
    name = "easymoney",
    version = "0.1",
    author = "Tariq A. Hassan",
    author_email = "laterallattice@gmail.com",
    description = ("Tools for common monetary problems."),
    long_description = open('README.md', 'r').read(),
    license = "BSD",
    keywords = 'economics, finance',
    url = "https://github.com/TariqAHassan/NewMoney.git",
    packages = ['easy_money'],
    install_requires = ['numpy', 'pandas', 'wbdata', 'bs4'],
    package_data={'easymoney': ['easy_data/*.csv', 'easy_data/*.p']},
    classifiers=[  "Development Status :: 3 - Alpha"
                 , "Natural Language :: English"
                 , "Programming Language :: Python :: 3.5"
                 , "Environment :: MacOS X"
                 , "License :: OSI Approved :: BSD License"
    ],
    include_package_data = True
)
