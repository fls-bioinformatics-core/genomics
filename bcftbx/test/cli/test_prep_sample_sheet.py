#######################################################################
# Unit tests
#######################################################################

import unittest
from bcftbx.cli.prep_sample_sheet import truncate_barcode
from bcftbx.cli.prep_sample_sheet import reverse_complement

class TestTruncateBarcodeFunction(unittest.TestCase):
    """Tests for the 'truncate_barcode' function

    """
    def test_truncate_single_index_barcode(self):
        self.assertEqual(truncate_barcode('CGTACTAG',0),'')
        self.assertEqual(truncate_barcode('CGTACTAG',6),'CGTACT')
        self.assertEqual(truncate_barcode('CGTACTAG',8),'CGTACTAG')
        self.assertEqual(truncate_barcode('CGTACTAG',10),'CGTACTAG')
    def test_truncate_dual_index_barcode(self):
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',0),'')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',6),'AGGCAG')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',8),'AGGCAGAA')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',10),'AGGCAGAA-TA')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',16),'AGGCAGAA-TAGATCGC')

class TestReverseComplementFunction(unittest.TestCase):
    """Tests for the 'reverse_complement' function

    """
    def test_reverse_complement_sequence(self):
        self.assertEqual(reverse_complement('AGGCAGAA'),'TTCTGCCT')
        self.assertEqual(reverse_complement('TAGATCGC'),'GCGATCTA')
