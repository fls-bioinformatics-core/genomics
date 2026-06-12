#!/usr/bin/env python
#
#     Md5sum.py: classes and functions for md5 checksum operations
#     Copyright (C) University of Manchester 2012-2022 Peter Briggs
#
########################################################################
#
# Md5sum.py
#
#########################################################################

"""Md5sum

Classes and functions for performing various MD5 checksum operations.

The code function is the 'md5sum' function, which computes the MD5 hash for
a file and is based on examples at:

http://www.python.org/getit/releases/2.0.1/md5sum.py

and
    
http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python

Usage:

>>> import Md5sum
>>> Md5Sum.md5sum("myfile.txt")
... eacc9c036025f0e64fb724cacaadd8b4

This module implements two methods for generating the md5 digest of a file:
the first uses a method based on the hashlib module, while the second (used
as a fallback for pre-2.5 Python) uses the now deprecated md5 module. Note
however that the md5sum function determines itself which method to use.

There is also a high-level class 'Md5Checker' which implements various
class methods for running MD5 checks across all files in a directory, and
a wrapper class 'Md5Reporter' which

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from .utils.checksums import Md5Checker
from .utils.checksums import Md5CheckReporter
from .utils.checksums import md5sum
