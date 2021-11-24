#!/usr/bin/env python
#
#     verify_paired.py: check R1 and R2 fastq files are consistent
#     Copyright (C) University of Manchester 2013-2021 Peter Briggs
#

"""
verify_paired.py

Checks that headers for R1 and R2 fastq files are in agreement, and that
the files form an R1/2 pair.
"""

#######################################################################
# Imports
#######################################################################

import os
import sys
import itertools
import argparse
import logging
logging.basicConfig(format="%(levelname)s %(message)s")
from ..FASTQFile import fastqs_are_pair
from .. import get_version

#######################################################################
# Main program
#######################################################################

def main():
    # Create command line parser
    p = argparse.ArgumentParser(
        description="Check that read headers for R1 and R2 fastq files "
        "are in agreement, and that the files form an R1/2 pair.")
    p.add_argument('--version',action='version',
                   version=("%%(prog)s %s" % get_version()))
    p.add_argument('fastq_file_r1',metavar="R1.fastq",
                   help="Fastq file with R1 reads")
    p.add_argument('fastq_file_r2',metavar="R2.fastq",
                   help="Fastq file with R2 reads to check against "
                   "R1 reads")
    # Parse command line
    args = p.parse_args()
    # Process the data
    if fastqs_are_pair(args.fastq_file_r1,args.fastq_file_r2):
        sys.exit(0)
    else:
        logging.error("Not R1/R2 pair")
        sys.exit(1)
        
