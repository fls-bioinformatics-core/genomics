#######################################################################
# Tests for utils/path.py module
#######################################################################


import unittest
from bcftbx.utils.path import commonprefix


class TestCommonPrefixFunction(unittest.TestCase):

    def test_commonprefix(self):
        """
        utils.path.commonprefix: check correct prefix is returned
        """
        self.assertEqual('/mnt/stuff',commonprefix('/mnt/stuff/dir1',
                                                   '/mnt/stuff/dir2'))
        self.assertEqual('',commonprefix('/mnt1/stuff/dir1',
                                         '/mnt2/stuff/dir2'))