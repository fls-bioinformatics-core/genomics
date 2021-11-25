#######################################################################
# Tests
#######################################################################

import unittest
import io
from bcftbx.cli.split_fasta import FastaChromIterator

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
            self.fasta.append(u">%s\n%s" % (chrom[0],chrom[1]))
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
        fp = io.StringIO(self.test_data.fasta)
        i = 0
        for chrom in FastaChromIterator(fp=fp):
            self.assertEqual(chrom,self.test_data.chrom[i])
            i += 1
