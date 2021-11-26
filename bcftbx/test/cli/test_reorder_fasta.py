#######################################################################
# Unit tests
#######################################################################

import unittest
from bcftbx.cli.reorder_fasta import split_chrom_name
from bcftbx.cli.reorder_fasta import cmp_chrom_names

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
