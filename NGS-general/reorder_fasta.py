#!/usr/bin/env python
#
#     reorder_fasta.py: reorder chromosomes in a FASTA file
#     Copyright (C) University of Manchester 2018-2019 Peter Briggs

"""
reorder_fasta.py

Reorders the chromosome records from a FASTA file into 'kayrotypic'
order, e.g.

chr1
chr2
...
chr10
chr11

Usage: reorder_fasta.py INFILE.fa

The output FASTA file will be called 'INFILE.karyotypic.fa'.
"""

#######################################################################
# Imports
#######################################################################

import sys
import os
import io
import argparse
import itertools
import tempfile
import logging
from future.moves.itertools import zip_longest

#######################################################################
# Module metadata
#######################################################################

__description__ = \
"""Reorder the chromosome records in a FASTA file into
karyotypic order."""

#######################################################################
# Functions
#######################################################################

def split_chrom_name(s):
    """
    Split chromosome name for comparison and sorting

    Splits a chromosome name into a list, to be
    used in comparison and sorting operations.

    For example:

    >>> split_chrom_name("chr1")
    ... [1]
    >>> split_chrom_name("chr17_gl000203_random")
    ... [17,"gl000203","random"]

    Arguments:
      s (str): chromosome name to split

    Returns:
      List: list representation of the name.
    """
    s0 = s.split('_')
    if s0[0].startswith('chr'):
        s0[0] = s0[0][3:]
        try:
            s0[0] = int(s0[0])
        except ValueError:
            pass
    return s0

def cmp_chrom_names(x,y):
    """
    Compare two chromosome names karyotypically

    Implements the 'cmp' function to compare two chromosomes
    names karyotypically.

    Arguments:
      x (str): first chromosome name
      y (str): second chromosome name

    Returns:
      Integer: negative if x < y, zero if x == y, positive if
        x > y.
    """
    for i,j in zip_longest(split_chrom_name(x),
                           split_chrom_name(y)):
        if i != j:
            if i is None:
                return -1
            elif j is None:
                return 1
            return ((i > j) - (i < j))
    return 0

#######################################################################
# Unit tests
#######################################################################

import unittest

class TestSplitChromName(unittest.TestCase):
    def test_split_chrom_name(self):
        self.assertEqual(split_chrom_name("chr1"),[1])
        self.assertEqual(split_chrom_name("chr10"),[10])
        self.assertEqual(split_chrom_name("chrX"),["X"])
        self.assertEqual(split_chrom_name("chr21_gl000210_random"),
                                          [21,"gl000210","random"])

class TestCmpChromNames(unittest.TestCase):
    def test_cmp_chrom_names_equal(self):
        self.assertTrue(cmp_chrom_names("chr1","chr1") == 0)
        self.assertTrue(cmp_chrom_names("chr10","chr10") == 0)
        self.assertTrue(cmp_chrom_names("chr17_gl000203_random",
                                        "chr17_gl000203_random") == 0)
    def test_cmp_chrom_names_lt(self):
        self.assertTrue(cmp_chrom_names("chr1","chr10") < 0)
        self.assertTrue(cmp_chrom_names("chr1",
                                        "chr17_gl000203_random") < 0)
        self.assertTrue(cmp_chrom_names("chr17",
                                        "chr17_gl000203_random") < 0)
    def test_cmp_chrom_names_gt(self):
        self.assertTrue(cmp_chrom_names("chr10","chr1") > 0)
        self.assertTrue(cmp_chrom_names("chr17_gl000203_random",
                                        "chr1") > 0)
        self.assertTrue(cmp_chrom_names("chr17_gl000203_random",
                                        "chr17") > 0)

#######################################################################
# Main
#######################################################################

def main(args=None):
    # Process command line
    if args is None:
        args = sys.argv[1:]
    p = argparse.ArgumentParser(description=__description__)
    p.add_argument("fasta",metavar="FASTA",
                   help="FASTA file to reorder")
    args = p.parse_args()
    fasta = os.path.abspath(args.fasta)
    if not os.path.exists(fasta):
        logging.critical("%s: file not found" % fasta)
        sys.exit(1)
    # Extract each chromosome to its own temporary file
    print("Extracting chromosomes...")
    chroms = list()
    wd = tempfile.mkdtemp()
    print("Using working dir %s" % wd)
    with io.open(fasta,'rt') as fp:
        chromfile = None
        for line in fp:
            if line.startswith(">"):
                # New chromosome encountered
                if chromfile is not None:
                    chromfile.close()
                # Extract chromosome name
                chrom = line.strip()[1:]
                print("\t%s" % chrom)
                if chrom in chroms:
                    logging.critical("%s: chromosome appears more "
                                     "than once" % chrom)
                    sys.exit(1)
                chroms.append(chrom)
                # Open a new file
                chromfile = io.open(os.path.join(wd,"%s.fa" % chrom),'wt')
            # Write chromosome data to temporary file
            chromfile.write(line)
    if chromfile is not None:
        chromfile.close()
    print("Found %d chromosomes" % len(chroms))
    chroms = sorted(chroms,cmp=cmp_chrom_names)
    # Assemble new fasta file in karyotypic order
    print("Reordering chromosomes...")
    fasta_reordered = "%s.%s%s" % (
        os.path.splitext(os.path.basename(fasta))[0],
        "karyotypic",
        os.path.splitext(os.path.basename(fasta))[1])
    with io.open(fasta_reordered,'wt') as fp:
        for chrom in chroms:
            chromfile = os.path.join(wd,"%s.fa" % chrom)
            print("\t%s (%s)" % (chrom,chromfile))
            with io.open(chromfile,'rt') as fpp:
                fp.write(fpp.read())
    print("Wrote reordered FASTA file to %s" % fasta_reordered)
    print("Finished")

if __name__ == "__main__":
    main()
