#######################################################################
# Tests for io.fasta.py module
#######################################################################


import unittest
from io import StringIO
from bcftbx.fasta import FastaChromIterator


# Test data
FASTA_DATA = """>chr2L
Cgacaatgcacgacagagga
agcagCTCAAGATAccttct
>chr2R
CTCAAGATAccttctacaga
Cgacaatgcacgacagagga
"""


class TestFastaChromIterator(unittest.TestCase):
    """
    Tests of the FastaChromIterator class
    """
    def test_fastachromiterator(self):
        """
        FastaChromIterator: iteration over small FASTA file
        """
        fp = StringIO(FASTA_DATA)
        fasta = FastaChromIterator(fp=fp)
        expected = (
            ("chr2L", "Cgacaatgcacgacagagga\nagcagCTCAAGATAccttct"),
            ("chr2R", "CTCAAGATAccttctacaga\nCgacaatgcacgacagagga"),
        )
        nchroms = 0
        for chrom,expt in zip(fasta,expected):
            nchroms += 1
            self.assertEqual(chrom,expt)
        self.assertEqual(nchroms, len(expected))