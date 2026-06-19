#!/usr/bin/env python
#
#     fasta.py: classes and functions for handling FASTA files
#     Copyright (C) University of Manchester 2022-2026 Peter Briggs
#

"""
Legacy module providing utilities for reading through FASTA files.

The core functionality has been reimplemented in the ``io.fasta`` module;
the code in this module is now deprecated and only maintained for
backwards compatibility; they will be removed in a future release.

The legacy classes and functions are:

* FastaChromIterator: enables looping through chromosomes in FASTA file
"""

#######################################################################
# Import modules
#######################################################################

from .io.fasta import FastaChromIterator
