#######################################################################
# Tests
#######################################################################

import unittest
from bcftbx.cli.annotate_probesets import get_probeset_extension

class TestProbesetAnnotation(unittest.TestCase):

    def test_get_basic_probeset_extension(self):
        """Check that the correct probeset extensions are identified
        """
        self.assertEqual(get_probeset_extension('123356_at'),'_at')
        self.assertEqual(get_probeset_extension('123356_st'),'_st')
        self.assertEqual(get_probeset_extension('123356_s_at'),'_s_at')
        self.assertEqual(get_probeset_extension('123356_a_at'),'_a_at')
        self.assertEqual(get_probeset_extension('123356_x_at'),'_x_at')
        self.assertEqual(get_probeset_extension('123356_g_at'),'_g_at')
        self.assertEqual(get_probeset_extension('123356_f_at'),'_f_at')
        self.assertEqual(get_probeset_extension('123356_i_at'),'_i_at')
        self.assertEqual(get_probeset_extension('123356_b_at'),'_b_at')
        self.assertEqual(get_probeset_extension('123356_l_at'),'_l_at')
        self.assertEqual(get_probeset_extension('123356'),None)

    def test_get_tricky_probeset_extension(self):
        """Check the correct extensions are identified in tricker cases
        """
        self.assertEqual(get_probeset_extension('123356b_at'),'_at')

    def test_get_probeset_extension_r(self):
        """Check that the _r_ component overrules other extensions
        """
        self.assertEqual(get_probeset_extension('123356_r_at'),'_r_')
