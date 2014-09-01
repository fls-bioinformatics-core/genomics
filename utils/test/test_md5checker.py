#######################################################################
# Tests for md5checker.py
#######################################################################

import unittest
import os
import tempfile
import shutil
from bcftbx.test.mock_data import TestUtils,ExampleDirScooby
from md5checker import diff_directories
from md5checker import diff_files
from md5checker import compute_md5sum_for_file
from md5checker import compute_md5sums
from md5checker import verify_md5sums

class TestMd5sums(unittest.TestCase):
    """Test computing and verifying MD5 sums via files

    """
    def setUp(self):
        # Create and populate test directory
        self.dir = ExampleDirScooby()
        self.dir.create_directory()
        # Make temporary area for input/ouput checksum files
        self.md5sum_dir = tempfile.mkdtemp()
        self.checksum_file = os.path.join(self.md5sum_dir,"checksums")
        # Reference checksums for test directory
        self.reference_checksums = []
        for f in self.dir.filelist(full_path=False):
            self.reference_checksums.append("%s  %s" % (self.dir.checksum_for_file(f),f))
        self.reference_checksums.append('')
        self.reference_checksums = '\n'.join(self.reference_checksums)
        # Store current dir and move to top level of test directory
        self.pwd = os.getcwd()
        os.chdir(self.dir.dirn)

    def tearDown(self):
        # Move back to original directory
        os.chdir(self.pwd)
        # Clean up test directory and checksum file
        self.dir.delete_directory()
        shutil.rmtree(self.md5sum_dir)

    def test_compute_md5sums(self):
        """compute_md5sums make md5sum file for test directory
        """
        compute_md5sums('.',output_file=self.checksum_file,relative=True)
        checksums = open(self.checksum_file,'r').read()
        reference_checksums = self.reference_checksums.split('\n')
        reference_checksums.sort()
        checksums = checksums.split('\n')
        checksums.sort()
        print str(checksums)
        for l1,l2 in zip(reference_checksums,checksums):
            self.assertEqual(l1,l2)

    def test_verify_md5sums(self):
        # Verify md5sums for test directory
        fp = open(self.checksum_file,'w')
        fp.write(self.reference_checksums)
        fp.close()
        self.assertEqual(verify_md5sums(self.checksum_file),0)

    def test_compute_md5sum_for_file(self):
        # Compute md5sum for a single file
        compute_md5sum_for_file('test.txt',output_file=self.checksum_file)
        checksum = open(self.checksum_file,'r').read()
        self.assertEqual("0b26e313ed4a7ca6904b0e9369e5b957  test.txt\n",checksum)

    def test_broken_links(self):
        """compute_md5sums make md5sum file for test directory with broken links
        """
        # Add broken link to test dir
        self.dir.add_link("broken","missing.txt")
        compute_md5sums('.',output_file=self.checksum_file,relative=True)

class TestDiffFilesFunction(unittest.TestCase):
    """Test checking pairs of files (diff_files)

    """
    def setUp(self):
        # Create a set of files to compare
        self.file1 = TestUtils.make_file(None,"This is a test file")
        self.file2 = TestUtils.make_file(None,"This is a test file")
        self.file3 = TestUtils.make_file(None,"This is another test file")

    def tearDown(self):
        # Delete the test files
        os.remove(self.file1)
        os.remove(self.file2)
        os.remove(self.file3)

    def test_same_file(self):
        """diff_files: distinct identical files have same checksums

        """
        self.assertEqual(diff_files(self.file1,self.file2),0)

    def test_different_files(self):
        """diff_files: different files have different values checksums

        """
        self.assertNotEqual(diff_files(self.file1,self.file3),0)

class TestDiffDirectoriesFunction(unittest.TestCase):
    """Test checking pairs of directories (diff_directories)

    """

    def setUp(self):
        # Make test directories
        self.empty_dir1 = TestUtils.make_dir()
        self.empty_dir2 = TestUtils.make_dir()
        self.dir1 = ExampleDirScooby()
        self.dir2 = ExampleDirScooby()
        self.dir1.create_directory()
        self.dir2.create_directory()

    def tearDown(self):
        # Remove test directories
        shutil.rmtree(self.empty_dir1)
        shutil.rmtree(self.empty_dir2)
        self.dir1.delete_directory()
        self.dir2.delete_directory()

    def test_same_dirs(self):
        """diff_directories: identical directories are identified as identical

        """
        self.assertEqual(diff_directories(self.empty_dir1,self.empty_dir2),0)
        self.assertEqual(diff_directories(self.dir1.dirn,self.dir2.dirn),0)

    def test_extra_file(self):
        """diff_directories: target directory contains extra file
        
        """
        # Add extra file to a directory
        self.dir2.add_file("extra.txt","This is an extra test file")
        self.assertEqual(diff_directories(self.dir1.dirn,self.dir2.dirn),0)
        self.assertNotEqual(diff_directories(self.dir2.dirn,self.dir1.dirn),0)

    def test_different_file(self):
        """diff_directories: file differs between directories

        """
        # Add different versions of a file to each directory
        self.dir1.add_file("diff.txt","This is one version of the file")
        self.dir2.add_file("diff.txt","This is another version of the file")
        self.assertNotEqual(diff_directories(self.dir1.dirn,
                                             self.dir2.dirn),0)
        self.assertNotEqual(diff_directories(self.dir2.dirn,
                                             self.dir1.dirn),0)

    def test_broken_links(self):
        """diff_directories: handle broken links

        """
        # Add broken link
        self.dir1.add_link("broken","missing.txt")
        self.assertNotEqual(diff_directories(self.dir1.dirn,
                                             self.dir2.dirn),0)
        self.assertEqual(diff_directories(self.dir2.dirn,
                                          self.dir1.dirn),0)
