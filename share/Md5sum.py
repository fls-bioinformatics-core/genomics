#!/usr/bin/env python
#
#     Md5sum.py: functions for generating md5 checksums
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# Md5sum.py
#
#########################################################################

"""Md5sum

Functions for generating MD5 checksums for files

Code based on examples at:

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
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

try:
    # Preferentially use hashlib module
    import hashlib
except ImportError:
    # hashlib not available, use deprecated md5 module
    import md5

#######################################################################
# Modules constants
#######################################################################

BLOCKSIZE = 1024*1024

#######################################################################
# Functions
#######################################################################

def hexify(s):
    """Return the hex representation of a string
    """
    return ("%02x"*len(s)) % tuple(map(ord, s))

def md5sum(filen):
    """Return md5sum digest for a file
    
    This implements the md5sum checksum generation using both
    the hashlib module (which should be available in Python 2.5) and
    the deprecated md5 module (which will be used if hashlib is
    unavailable, as is the case for Python 2.4 and earlier).

    The choice of hashlib versus md5 is made automatically and there
    is no need for the invoking subprogram to decide: the resulting
    checksums are the same using either library regardless.

    Arguments:
      filen: name of the file to generate the checksum from
        
    Returns:
      Md5sum digest for the named file.
    """
    # Initialise checksum using whatever is available
    try:
        chksum = hashlib.md5()
    except NameError:
        chksum = md5.new()
    # Generate checksum
    with open(filen, "rb") as f:
        for block in iter(lambda: f.read(BLOCKSIZE), ''):
            chksum.update(block)
    return hexify(chksum.digest())

#######################################################################
# Tests
#######################################################################

import unittest
import os
import tempfile

test_text = """Md5sum is a Python module with functions for generating
MD5 checksums for files."""

class TestHexify(unittest.TestCase):

    def test_hexify(self):
        """Test hexify function
        """
        self.assertEqual(hexify("hello!"),'68656c6c6f21')
        self.assertEqual(hexify("goodbye"),'676f6f64627965')

class TestMd5sum(unittest.TestCase):

    def setUp(self):
        # mkstemp returns a tuple
        tmpfile = tempfile.mkstemp()
        self.filen = tmpfile[1]
        fp = open(self.filen,'w')
        fp.write(test_text)
        fp.close()

    def tearDown(self):
        os.remove(self.filen)

    def test_md5sum(self):
        """Test generation of md5sum
        """
        self.assertEqual(md5sum(self.filen),
                         '08a6facee51e5435b9ef3744bd4dd5dc')

    def test_no_file_name(self):
        """Test handling of file name 'None'
        """
        self.assertRaises(Exception,md5sum,None)
        
########################################################################
# Main: test runner
#########################################################################
if __name__ == "__main__":
    # Run tests
    unittest.main()


