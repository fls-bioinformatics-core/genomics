#######################################################################
# Tests for fasta.py module
#######################################################################

from bcftbx.fasta import *
import unittest

fasta_data = """>chr2L
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
        fp = io.StringIO(fasta_data)
        fasta = FastaChromIterator(fp=fp)
        expected = (
            ("chr2L","Cgacaatgcacgacagagga\nagcagCTCAAGATAccttct"),
            ("chr2R","CTCAAGATAccttctacaga\nCgacaatgcacgacagagga"),
        )
        nchroms = 0
        for chrom,expt in zip(fasta,expected):
            nchroms += 1
            self.assertEqual(chrom,expt)
        self.assertEqual(nchroms,len(expected))
