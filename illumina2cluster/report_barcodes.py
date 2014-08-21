#!/bin/env python
#
#     report_barcodes.py: analyse barcode sequences from fastq files
#     Copyright (C) University of Manchester 2014 Peter Briggs
#
########################################################################
#
# report_barcodes.py
#
#########################################################################

"""report_barcodes.py

Count and report the barcode/index sequences (AKA tags) in one or more
Fastq file from an Illumina sequencer.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

__version__ = "0.0.2"

import sys
import optparse
import bcftbx.FASTQFile as FASTQFile

#######################################################################
# Class definitions
#######################################################################

class Barcodes:
    """Class for counting index sequences in Fastq files

    """
    def __init__(self):
        """Create a new Barcodes instance

        """
        self._counts = {}

    def load(self,fastq=None,fp=None):
        """Read in fastq data and collect index sequence info

        The input FASTQ can be either a text file or a compressed (gzipped)
        FASTQ, specified via a file name (using the 'fastq' argument), or a
        file-like object opened for line reading (using the 'fp' argument).

        Arguments:
           fastq_file: name of the FASTQ file to iterate through
           fp: file-like object opened for reading

        """
        for read in FASTQFile.FastqIterator(fastq_file=fastq,fp=fp):
            seq = read.seqid.index_sequence
            if seq not in self._counts:
                self._counts[seq] = 1
            else:
                self._counts[seq] += 1

    def sequences(self):
        """Return list of barcode sequences

        Returns a list with all the index sequences, sorted
        into alphabetical order.

        """
        unique = self._counts.keys()
        unique.sort()
        return unique

    def count_for(self,*seqs):
        """Return count for list of sequences

        If a single sequence is supplied then return the
        number of reads that have that sequence as the index.

        If more than one sequence is supplied then return
        the total number of reads for those index sequences
        i.e. the sum of the counts for each sequence, so that:

        b.count_for('ACG','ACC') == b.count_for('ACG') + b.count_for('ACC')

        """
        count = 0
        for s in seqs:
            try:
                count += self._counts[s]
            except KeyError:
                pass
        return count

    def group(self,seq,max_mismatches=1):
        """Return group of sequences which match the one supplied

        Given a sequence, find all sequences which match
        within the tolerance of allowed mismatches, and
        return as a list.

        """
        grp = []
        for s in self.sequences():
            if s not in grp and sequences_match(s,seq,max_mismatches):
                grp.append(s)
        grp.sort()
        return grp

#######################################################################
# Functions
#######################################################################

def sequences_match(seq1,seq2,max_mismatches=0):
    """Determine whether two sequences match with specified tolerance

    Returns True if sequences 'seq1' and 'seq2' are 
    consider to match, and False if not.

    By default sequences only match if they are identical.
    This condition can be loosen by specify a maximum number
    mismatched bases that are allowed.

    An 'N' in either (or both) sequences is automatically
    counted as a mismatched position, except for exact
    matches.

    """
    if max_mismatches == 0:
        return (seq1 == seq2)
    mismatches = 0
    for b1,b2 in zip(seq1,seq2):
        if b1 != b2 or b1 == 'N' or b2 == 'N':
            mismatches += 1
            if mismatches > max_mismatches:
                return False
    return True

def main(fastqs,cutoff):
    """Main program

    Arguments:
      fastqs: list of FASTQ files to read sequences from
      cutoff: set the minimum number of reads that a barcode must appear in
        before it is reported

    """
    barcodes = Barcodes()
    for fastq_file in fastqs:
        print "Reading in data from %s" % fastq_file
        barcodes.load(fastq=fastq_file)
    print "Total # barcode sequences: %d" % len(barcodes.sequences())
    print "Determining top barcode sequences"
    ordered_seqs = sorted(barcodes.sequences(),
                          cmp=lambda x,y: cmp(barcodes.count_for(y),
                                              barcodes.count_for(x)))
    print "Rank = position after sorting from most to least common"
    print "Index sequence = the barcode sequence"
    print "Count = number of reads with this exact index sequence"
    print "1 mismatch = number of reads which match this index when allowing 1 mismatch"
    print "2 mismatches = number of reads which match this index allowing 2 mismatches"
    print "Matching indices = list of higher ranked sequences matching this one (if any)"
    print "Rank\tIndex sequence\tCount\t1 mismatch\t2 mismatches\tMatching indices"
    for i,seq in enumerate(ordered_seqs):
        n_exact = barcodes.count_for(seq)
        n_1mismatch = barcodes.count_for(*barcodes.group(seq,1))
        n_2mismatch = barcodes.count_for(*barcodes.group(seq,2))
        match_seqs = []
        for i1,seq1 in enumerate(ordered_seqs[:i]):
            if sequences_match(seq,seq1,2):
                match_seqs.append("%d:'%s'" % (i1+1,seq1))
        print "%d\t%s\t%d\t%d\t%d\t[%s]" % (i+1,seq,
                                          n_exact,n_1mismatch,n_2mismatch,
                                          ','.join(match_seqs))
        if n_exact < cutoff:
            print "...remainder occur less than %d times (set by --cutoff)" % cutoff
            break

#######################################################################
# Tests
#######################################################################

import unittest
import cStringIO

class TestBarcodes(unittest.TestCase):
    def test_barcodes(self):
        fastq_data = cStringIO.StringIO(
"""@HWI-700511R:233:C446JACXX:6:1101:1241:2242 1:N:0:CCGTCCAT
GAAACGCGGCACAGA
+
<BBFFBFFBBFFF7B
@HWI-700511R:233:C446JACXX:6:1101:1280:2080 1:N:0:GTCNNCAT
CGAGCTCGAATTCAT
+
<0<<BFF<0BFFFII
@HWI-700511R:233:C446JACXX:6:1101:1241:2242 1:N:0:CCGTGCAT
GAAACGCGGCACAGA
+
<BBFFBFFBBFFF7B
""")
        b = Barcodes()
        b.load(fp=fastq_data)
        self.assertEqual(b.sequences(),['CCGTCCAT','CCGTGCAT','GTCNNCAT'])
        self.assertEqual(b.count_for('CCGTCCAT'),1)
        self.assertEqual(b.count_for('CCGTGCAT'),1)
        self.assertEqual(b.count_for('GTCNNCAT'),1)
        self.assertEqual(b.count_for('CCGTCCAT','CCGTGCAT'),2)
        self.assertEqual(b.count_for('ATCTGCAT'),0)
        self.assertEqual(b.group('CCGTCCAT'),['CCGTCCAT','CCGTGCAT'])
        self.assertEqual(b.group('GTCNNCAT'),[])
        self.assertEqual(b.group('GTCNNCAT',max_mismatches=2),['GTCNNCAT'])
        group = b.group('CCGTCCAT')
        self.assertEqual(b.count_for(*group),2)

class TestSequencesMatchFunction(unittest.TestCase):
    def test_sequences_match_exact(self):
        self.assertTrue(sequences_match('AGGTCTA','AGGTCTA'))
        self.assertFalse(sequences_match('AGGTCTA','ACGTCTA'))
    def test_sequences_match_different_lengths(self):
        self.assertFalse(sequences_match('AGGTCTA','AGGTC'))
    def test_sequences_match_one_mismatch(self):
        self.assertFalse(sequences_match('AGGTCTA','ACGTCTA'))
        self.assertTrue(sequences_match('AGGTCTA','ACGTCTA',max_mismatches=1))
    def test_sequences_match_two_mismatches(self):
        self.assertFalse(sequences_match('AGGTCTA','ACCTCTA'))
        self.assertFalse(sequences_match('AGGTCTA','ACCTCTA',max_mismatches=1))
        self.assertTrue(sequences_match('AGGTCTA','ACCTCTA',max_mismatches=2))
    def test_sequences_match_handle_ns(self):
        self.assertFalse(sequences_match('ACNTCTA','ACGTCTA'))
        self.assertTrue(sequences_match('ACNTCTA','ACGTCTA',max_mismatches=1))
        self.assertFalse(sequences_match('ANNTCTA','ACCTCTA'))
        self.assertFalse(sequences_match('ANNTCTA','ACCTCTA',max_mismatches=1))
        self.assertTrue(sequences_match('ANNTCTA','ACCTCTA',max_mismatches=2))
        # Special case: matching Ns with Ns
        self.assertTrue(sequences_match('ACNTCTA','ACNTCTA'))
        self.assertTrue(sequences_match('ACNTCTA','ACNTCTA',max_mismatches=1))

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    p = optparse.OptionParser(usage="%prog FASTQ [FASTQ...]",
                              version="%prog "+__version__,
                              description="Examine barcode sequences from one or more "
                              "Fastq files and report the most prevalent. Sequences will "
                              "be pooled from all specified Fastqs before being analysed.")
    p.add_option('--cutoff',action='store',dest='cutoff',default=1000000,type='int',
                 help="Minimum number of times a barcode sequence must appear to be "
                 "reported (default is 1000000)")
    options,args = p.parse_args()
    if len(args) == 0:
        p.error("Must supply at least one Fastq file")
    try:
        main(args,options.cutoff)
    except KeyboardInterrupt:
        print "Terminating following Ctrl-C"
        pass
