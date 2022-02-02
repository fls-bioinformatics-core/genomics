#######################################################################
# Tests for cmpdirs.py
#######################################################################

import unittest
import os
import tempfile
import shutil
from bcftbx.Md5sum import Md5Checker
from bcftbx.test.mock_data import TestUtils,ExampleDirLanguages
from cmpdirs import yield_filepairs
from cmpdirs import cmp_filepair
from cmpdirs import cmp_dirs

class TestYieldFilepairs(unittest.TestCase):
    def setUp(self):
        # Create example directory structure which
        # includes files and links
        self.d = ExampleDirLanguages()
        self.d.create_directory()
    def tearDown(self):
        # Delete example directory structure
        self.d.delete_directory()
    def test_yield_filepairs(self):
        """yield_filepairs returns correct set of files and links
        """
        # Get all files, links and directories in the example directory
        expected = self.d.filelist(include_links=True,include_dirs=True)
        # Remove any (non-link) directories from the expected list
        expected = filter(lambda x: os.path.islink(x) or not os.path.isdir(x),
                          expected)
        print("Expected = %s" % expected)
        # Get all file pairs from the example dir and a
        # dummy target directory name
        for pair in yield_filepairs(self.d.dirn,'/dummy/dir'):
            p1,p2 = pair
            self.assertTrue(p1 in expected,"%s not expected" % p1)
            # Remove from the list
            expected.remove(p1)
            # Check target file is as expected
            p2_expected = os.path.join('/dummy/dir',
                                       os.path.relpath(p1,self.d.dirn))
            self.assertEqual(p2,p2_expected,
                             "Expected '%s', got '%s'" % (p2,p2_expected))
        # List should be empty at the end
        self.assertEqual(len(expected),0,
                         "Some paths not returned: %s" % expected)

class TestCmpFilepair(unittest.TestCase):
    def setUp(self):
        # Create working directory for test files etc
        self.wd = TestUtils.make_dir()
    def tearDown(self):
        # Remove the container dir
        TestUtils.remove_dir(self.wd)
    def test_cmp_filepair_identical_files(self):
        """cmp_filepair matches identical files
        """
        # Make two identical files and compare them
        f1 = TestUtils.make_file('test_file1',"Lorum ipsum",basedir=self.wd)
        f2 = TestUtils.make_file('test_file2',"Lorum ipsum",basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.MD5_OK)
    def test_cmp_filepair_different_files(self):
        """cmp_filepair flags mismatch between differing files
        """
        # Make two different files and compare them
        f1 = TestUtils.make_file('test_file1',"Lorum ipsum",basedir=self.wd)
        f2 = TestUtils.make_file('test_file2',"lorum ipsum",basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.MD5_FAILED)
    def test_cmp_filepair_identical_links(self):
        """cmp_filepair matches identical links
        """
        # Make two identical symlinks and compare them
        f1 = TestUtils.make_sym_link('/dummy/file',link_name='test_link1',basedir=self.wd)
        f2 = TestUtils.make_sym_link('/dummy/file',link_name='test_link2',basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.LINKS_SAME)
    def test_cmp_filepair_different_links(self):
        """cmp_filepair flags mismatch between differing links
        """
        # Make two identical symlinks and compare them
        f1 = TestUtils.make_sym_link('/dummy/file1',link_name='test_link1',basedir=self.wd)
        f2 = TestUtils.make_sym_link('/dummy/file2',link_name='test_link2',basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.LINKS_DIFFER)
    def test_cmp_filepair_file_to_link(self):
        """cmp_file flags mismatch between file and link
        """
        # Make file and link
        f1 = TestUtils.make_file('test_file1',"Lorum ipsum",basedir=self.wd)
        f2 = TestUtils.make_sym_link('/dummy/file',link_name='test_link2',basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.MD5_ERROR)
    def test_cmp_filepair_link_to_file(self):
        """cmp_file flags mismatch between link and file
        """
        # Make file and link
        f1 = TestUtils.make_sym_link('/dummy/file',link_name='test_link1',basedir=self.wd)
        f2 = TestUtils.make_file('test_file2',"Lorum ipsum",basedir=self.wd)
        result = cmp_filepair((f1,f2))
        self.assertEqual(result.status,Md5Checker.TYPES_DIFFER)

class TestCmpDirs(unittest.TestCase):
    def setUp(self):
        # Create reference example directory structure which
        # includes files and links
        self.dref = ExampleDirLanguages()
        self.dref.create_directory()
        # Create copy of reference dir
        self.dcpy = ExampleDirLanguages()
        self.dcpy.create_directory()
    def tearDown(self):
        # Delete example directory structures
        self.dref.delete_directory()
        self.dcpy.delete_directory()
    def test_cmp_dirs_identical_dirs(self):
        """cmp_dirs works for identical directories
        """
        # Compare dirs
        count = cmp_dirs(self.dref.dirn,self.dcpy.dirn)
        self.assertEqual(count[Md5Checker.MD5_OK],7)
        self.assertEqual(count[Md5Checker.LINKS_SAME],6)
    def test_cmp_dirs_different_dirs(self):
        """cmp_dirs works for different directories
        """
        # Add more files and links to reference
        self.dref.add_file("extra","Additional file")
        self.dref.add_link("destination","place/you/want/to/go")
        # Add differing files and links
        self.dref.add_file("more","Yet another file")
        self.dcpy.add_file("more","Yet another file, again")
        self.dref.add_link("where_to","somewhere")
        self.dcpy.add_link("where_to","somewhere/else")
        # Compare dirs
        count = cmp_dirs(self.dref.dirn,self.dcpy.dirn)
        self.assertEqual(count[Md5Checker.MD5_OK],7)
        self.assertEqual(count[Md5Checker.LINKS_SAME],6)
        self.assertEqual(count[Md5Checker.MD5_FAILED],1)
        self.assertEqual(count[Md5Checker.LINKS_DIFFER],1)

