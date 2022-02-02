#!/usr/bin/env python
#
#     split_fasta.py: extract individual chromosome sequences from fasta file
#     Copyright (C) University of Manchester 2013-2022 Peter Briggs
#

"""
split_fasta.py

Split input FASTA file with multiple sequences into multiple files, each
containing sequences for a single chromosome.
"""

#######################################################################
# Import modules
#######################################################################

import sys
import os
import io
import argparse
import logging
from ..fasta import FastaChromIterator
from .. import get_version

#######################################################################
# Main program
#######################################################################

def main():
    # Process the command line
    p = argparse.ArgumentParser(
        description="Split input FASTA file with multiple sequences "
        "into multiple files each containing sequences for a single "
        "chromosome.")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument('fasta_file',nargs='?',
                   help="input FASTA file to split")
    arguments = p.parse_args()
    if not arguments.fasta_file:
        p.error("Need to supply FASTA file as input")
    # Keep a record of file names from chromosome names
    file_names = []
    # Loop over chromosomes and output each one to a separate file
    for chrom in FastaChromIterator(arguments.fasta_file):
        name = chrom[0]
        seq = chrom[1]
        # Make a file name from chromosome description
        # Split on spaces and escape special characters
        fname = name.split()[0].replace('|','_').strip('_')
        # Check that the name hasn't already been used
        n = 0
        while fname in file_names:
            if n:
                fname = '.'.join(fname.split('.')[0:-1])
            n += 1
            fname += ".%d" % n
        file_names.append(fname)
        fasta = "%s.fa" % fname
        # Report what's happening
        print("Outputting '%s' to %s" % (name,fasta))
        if os.path.isfile(fasta):
            sys.stderr.write("WARNING '%s' already exists, overwriting\n" % fasta)
        with io.open(fasta,'wt') as fp:
            fp.write(">%s\n%s\n" % (name,seq))
