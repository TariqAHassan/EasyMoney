#!/usr/bin/env python3

"""

    General Support Tools
    ~~~~~~~~~~~~~~~~~~~~~

"""

# modules
import re

def cln(i, extent = 1):
    """
    String white space 'cleaner'.
    :param i:
    :param extent: 1 --> all white space reduced to length 1; 2 --> removal of all white space.
    :return:
    """

    if isinstance(i, str) and i != "":
        if extent == 1:
            return re.sub(r"\s\s+", " ", i)
        elif extent == 2:
            return re.sub(r"\s+", "", i)
    else:
        return i