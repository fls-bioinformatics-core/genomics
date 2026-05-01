#######################################################################
# Tests for utils/path.py module
#######################################################################


import unittest
from bcftbx.utils.path import commonprefix
from bcftbx.utils.path import rootname
from bcftbx.utils.path import strip_ext


class TestCommonPrefixFunction(unittest.TestCase):

    def test_commonprefix(self):
        """
        utils.path.commonprefix: check correct prefix is returned
        """
        self.assertEqual('/mnt/stuff',commonprefix('/mnt/stuff/dir1',
                                                   '/mnt/stuff/dir2'))
        self.assertEqual('',commonprefix('/mnt1/stuff/dir1',
                                         '/mnt2/stuff/dir2'))


class TestRootnameFunction(unittest.TestCase):

    def test_rootname(self):
        """
        utils.path.rootname: check correct root name is returned
        """
        self.assertEqual('name',rootname('name'))
        self.assertEqual('name',rootname('name.fastq'))
        self.assertEqual('name',rootname('name.fastq.gz'))
        self.assertEqual('/path/to/name',rootname('/path/to/name.fastq.gz'))


class TestStripExtFunction(unittest.TestCase):

    def test_strip_ext(self):
        """
        utils.path.strip_ext: check correct name is returned
        """
        self.assertEqual('name',strip_ext('name'))
        self.assertEqual('name',strip_ext('name.fastq','fastq'))
        self.assertEqual('name',strip_ext('name.fastq','.fastq'))
        self.assertEqual('name.fastq',strip_ext('name.fastq','gz'))
        self.assertEqual('name.fastq',strip_ext('name.fastq.gz','gz'))
        self.assertEqual('name.fastq',strip_ext('name.fastq','fastq.gz'))
        self.assertEqual('name',strip_ext('name.fastq.gz','fastq.gz'))
        self.assertEqual('name.gz',strip_ext('name.gz','fastq.gz'))
        self.assertEqual('name',strip_ext('name.fastq'))
        self.assertEqual('name.fastq',strip_ext('name.fastq.gz'))