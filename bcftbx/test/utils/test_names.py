#######################################################################
# Tests for utils/names.py module
#######################################################################


import unittest


from bcftbx.utils.names import extract_initials
from bcftbx.utils.names import extract_prefix
from bcftbx.utils.names import extract_index_as_string
from bcftbx.utils.names import extract_index
from bcftbx.utils.names import pretty_print_names
from bcftbx.utils.names import name_matches


class TestNameFunctions(unittest.TestCase):
    """
    Unit tests for name handling utility functions
    """

    def test_extract_initials(self):
        """
        utils.names.extract_initials: check extraction
        """
        self.assertEqual('DR',extract_initials('DR1'))
        self.assertEqual('EP',extract_initials('EP_NCYC2669'))
        self.assertEqual('CW',extract_initials('CW_TI'))

    def test_extract_prefix(self):
        """
        utils.names.extract_prefix: check extraction
        """
        self.assertEqual('LD_C',extract_prefix('LD_C1'))

    def test_extract_index_as_string(self):
        """
        utils.names.extract_index_as_string: check extraction
        """
        self.assertEqual('1',extract_index_as_string('LD_C1'))
        self.assertEqual('07',extract_index_as_string('DR07'))
        self.assertEqual('',extract_index_as_string('DROHSEVEN'))

    def test_extract_index(self):
        """
        utils.names.extract_index: check extraction
        """
        self.assertEqual(1,extract_index('LD_C1'))
        self.assertEqual(7,extract_index('DR07'))
        self.assertEqual(None,extract_index('DROHSEVEN'))
        self.assertEqual(0,extract_index('HUES1A0'))

    def test_pretty_print_names(self):
        """
        utils.names.pretty_print_names: output is correct
        """
        self.assertEqual('JC_SEQ26-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ27',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26',pretty_print_names(('JC_SEQ26',)))
        self.assertEqual('JC_SEQ26, JC_SEQ28-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26, JC_SEQ28, JC_SEQ30',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ30')))
        self.assertEqual('ML1, Mmyr2',pretty_print_names(('ML1','Mmyr2')))

    def test_name_matches(self):
        """
        utils.names.name_matches: check matching is correct
        """
        # Cases which should match
        self.assertTrue(name_matches('PJB','PJB'))
        self.assertTrue(name_matches('PJB','PJB*'))
        self.assertTrue(name_matches('PJB123','PJB*'))
        self.assertTrue(name_matches('PJB456','PJB*'))
        self.assertTrue(name_matches('PJB','*'))
        # Cases which shouldn't match
        self.assertFalse(name_matches('PJB123','PJB'))
        self.assertFalse(name_matches('PJB','IDJ'))
        # Cases with multiple matches
        self.assertTrue(name_matches('PJB','PJB,IJD'))
        self.assertTrue(name_matches('IJD','PJB,IJD'))
        self.assertFalse(name_matches('LJZ','PJB,IJD'))