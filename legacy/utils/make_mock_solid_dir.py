#!/usr/bin/env python
#
#     make_mock_solid_dir.py: make mock SOLiD directory for test purposes
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# make_mock_solid_dir.py
#
#########################################################################

"""make_mock_solid_dir.py

Makes a mock SOLiD run directory with run_definition and barcode statistic
files plus mock csfasta and qual files, which can be used to test other
programs and scrips with.

It uses the TestUtils class from the SolidData module to build and populate
the mock directory structure.

Usage: make_mock_solid_dir.py
"""

#######################################################################
# Import modules that this module depends on
#######################################################################
#
import os
import sys
# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
try:
    from bcftbx.test.test_SolidData import TestUtils
except ImportError as ex:
    print("Error importing modules: %s" % ex)

if __name__ == "__main__":
    paired_end = False
    if '--paired-end' in sys.argv:
        paired_end = True
    elif len(sys.argv) > 1:
        print("Usage: %s [--paired-end]" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    # Make mock solid directory
    if paired_end:
        solid_dir = TestUtils().make_solid_dir_paired_end('solid0123_20111014_PE_BC')
    else:
        solid_dir = TestUtils().make_solid_dir('solid0123_20111014_FRAG_BC')
    print("Constructed mock dir: %s" % solid_dir)
