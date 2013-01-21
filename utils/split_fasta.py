#!/bin/env python
#
#     split_fasta.py: extract individual chromosome sequences from fasta file
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# split_fasta.py
#
#########################################################################
#
"""split_fasta.py

Split input FASTA file with multiple sequences into multiple files, each
containing sequences for a single chromosome.

The program is built around the FastaChromIterator class which reads
data chromosome-by-chromosome from a Fasta file.

"""
#######################################################################
# Module metadata
#######################################################################

__version__ = "0.1.0"

#######################################################################
# Import modules
#######################################################################

from collections import Iterator
import sys
import os
import optparse
import logging

#######################################################################
# Classes
#######################################################################

class FastaChromIterator(Iterator):
    """FastaChromIterator

    Class to loop over all chromosomes in a FASTA file, and returning a
    tuple of the form

    (name,seq)

    for each chromosome (where 'name' is the chromosome name given in the
    '>' record, and 'seq' is the associated sequence).

    Example looping over all chromosomes and echoing to stdout:
    >>> for chrom in FastaChromIterator(fasta_file):
    >>>    print ">%s\n%s" % (chrom[0],chrom[1])

    """

    def __init__(self,fasta=None,fp=None):
        """Create a new FastaChromIterator

        The input source can be specified either as a file name or
        as a file-like object opened for line reading.

        Arguments:
           fasta: name of the Fasta file to iterate through
           fp: file-like object to read Fasta data from

        """
        if fp is None:
            # Open input fasta file
            self._fasta = fasta
            self._fp = open(self._fasta,'rU')
        else:
            # File object already supplied
            self._fasta = None
            self._fp = fp
        # Internal: store last line read from file
        self.__line = None

    def next(self):
        """Return next chromosome from Fasta file as a (name,sequence) tuple
       
        """
        # Initialise line storage
        if self.__line is None:
            line = self._fp.readline()
        else:
            line = self.__line
        chrom = None
        seq = []
        # Loop over lines in file looking for start of chromosome
        while line != '':
            if line.startswith(">"):
                if chrom is None:
                    # Start of current chromosome, get name
                    chrom = line.strip()[1:]
                else:
                    # Start of next chromosome, finish
                    # Store line for next iteration
                    self.__line = line
                    # Return data
                    return (chrom,''.join(seq))
            elif chrom is not None:
                # Store sequence line
                seq.append(line)
            # Get next line
            line = self._fp.readline()
        # Reached end of file
        if chrom is not None:
            # Close input file?
            if self._fasta is not None:
                self._fp.close()
            # Flush remaining data
            self.__line = ''
            return (chrom,''.join(seq))
        else:
            # Finished iteration
            raise StopIteration

#######################################################################
# Functions
#######################################################################

def split_fasta(fasta):
    """
    """
    # Open input file and loop through sequences
    fp = open(fasta,'rU')
    chrom = None
    fp_chrom = None
    for line in fp:
        if line.startswith(">"):
            # New chromosome
            chrom_name = line.strip()[1:]
            if chrom != chrom_name:
                # Close current output file, if one is open
                if fp_chrom is not None:
                    fp_chrom.close()
                    fp_chrom = None
                # Open new output file
                print "Opening output file for chromosome %s" % chrom_name
                chrom_fasta = "%s.fa" % chrom_name
                fp_chrom = open(chrom_fasta,'w')
        if fp_chrom is not None:
            fp_chrom.write(line)
    # Finished, tidy up loose ends
    if fp_chrom is not None:
        fp_chrom.close()

#######################################################################
# Tests
#######################################################################

import unittest
import cStringIO

# Test data
class TestData:
    """Set up example data to use in unit test classes

    """
    def __init__(self):
        # Data for individual example chromosomes
        self.chrom = []
        self.chrom.append(("chr1","""CCACACCACACCCACACACCCACACACCACACCACACACCACACCACACCCACACACACA
CATCCTAACACTACCCTAACACAGCCCTAATCTAACCCTGGCCAACCTGTCTCTCAACTT
"""))
        self.chrom.append(("chr2","""AAATAGCCCTCATGTACGTCTCCTCCAAGCCCTGTTGTCTCTTACCCGGATGTTCAACCA
AAAGCTACTTACTACCTTTATTTTATGTTTACTTTTTATAGGTTGTCTTTTTATCCCACT
"""))
        self.chrom.append(("chr3","""CCCACACACCACACCCACACCACACCCACACACCACACACACCACACCCACACACCCACA
CCACACCACACCCACACCACACCCACACACCCACACCCACACACCACACCCACACACACC
"""))
        # Build example fasta from chromosomes
        self.fasta = []
        for chrom in self.chrom:
            self.fasta.append(">%s\n%s" % (chrom[0],chrom[1]))
        self.fasta = ''.join(self.fasta)

class TestFastaChromIterator(unittest.TestCase):
    """Tests for the FastaChromIterator class

    """
    def setUp(self):
        # Instantiate test data
        self.test_data = TestData()

    def test_loop_over_chromosomes(self):
        """Test that example Fasta file deconvolutes into individual chromosomes

        """
        fp = cStringIO.StringIO(self.test_data.fasta)
        i = 0
        for chrom in FastaChromIterator(fp=fp):
            self.assertEqual(chrom,self.test_data.chrom[i])
            i += 1

def run_tests():
    """Run the tests
    """
    suite = unittest.TestSuite(unittest.TestLoader().\
                                   discover(os.path.dirname(sys.argv[0]), \
                                                pattern=os.path.basename(sys.argv[0])))
    unittest.TextTestRunner(verbosity=2).run(suite)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Process the command line
    p = optparse.OptionParser(usage="%prog OPTIONS fasta_file",
                              version="%prog "+__version__,
                              description="Split input FASTA file with multiple sequences "
                              "into multiple files each containing sequences for a single "
                              "chromosome.")
    p.add_option("--tests",action="store_true",dest="run_tests",default=False,
                 help="Run unit tests")
    options,arguments = p.parse_args()
    # Run unit tests option
    if options.run_tests:
        print "Running unit tests"
        run_tests()
        print "Tests finished"
        sys.exit()
    # Expects single Fasta file as input
    if len(arguments) != 1:
        p.error("Expects exactly one fasta file as input")
    # Loop over chromosomes and output each one to a separate file
    for chrom in FastaChromIterator(arguments[0]):
        name = chrom[0]
        seq = chrom[1]
        print "Outputting '%s'" % name
        fasta = "%s.fa" % name
        open(fasta,'w').write(">%s\n%s" % (name,seq))

