#!/usr/bin/env python
#
#     utils.py: utility classes & functions specific to NGS applications
#     Copyright (C) University of Manchester 2017 Peter Briggs
#
########################################################################
#
# ngsutils.py
#
#########################################################################

"""
Legacy module providing utility classes and functions specific to NGS
applications.

Extracting reads from Fastq, cfasta and qual files:

- getreads: fetch reads one-by-one from Fastq, cfasta or qual file
- getreads_subset: fetch subset of reads specified by index
- getreads_regex: fetch subset of reads matching regular expression

"""

#######################################################################
# Imports
#######################################################################

from .utils.ngs import getreads
from .utils.ngs import getreads_subset
from .utils.ngs import getreads_regex
