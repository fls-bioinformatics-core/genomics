#######################################################################
# Tests for utils/os.py module
#######################################################################


import unittest
import os
import stat
import tempfile
import shutil


from bcftbx.utils.os import mkdir
from bcftbx.utils.os import mkdirs
from bcftbx.utils.os import mklink
from bcftbx.utils.os import chmod
from bcftbx.utils.os import touch


class TestMkdirFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mkdir(self):
        """
        utils.os.mkdir: make a single subdirectory
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        self.assertFalse(os.path.exists(new_dir))
        mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_mkdir_chmod(self):
        """
        utils.os.mkdir: make a subdirectory and set permissions
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        self.assertFalse(os.path.exists(new_dir))
        mkdir(new_dir,mode=0o644)
        self.assertTrue(os.path.exists(new_dir))
        self.assertEqual(stat.S_IMODE(os.lstat(new_dir).st_mode),0o644)

    def test_mkdir_dir_already_exists(self):
        """
        utils.os.mkdir: try to make a subdirectory that already exists
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        os.mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_mkdir_dir_recursive(self):
        """
        utils.os.mkdir: make a subdirectory recursively
        """
        new_dir = os.path.join(self.test_dir,"new_dir","subdir","test")
        self.assertFalse(os.path.exists(new_dir))
        mkdir(new_dir,recursive=True)
        self.assertTrue(os.path.exists(new_dir))


class TestMkdirsFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mkdir_dir_recursive(self):
        """
        utils.os.mkdirs: make a subdirectory recursively
        """
        new_dir = os.path.join(self.test_dir,"new_dir","subdir","test")
        self.assertFalse(os.path.exists(new_dir))
        mkdirs(new_dir)
        self.assertTrue(os.path.exists(new_dir))


class TestMkLinkFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mklink_for_file(self):
        """
        utils.os.mklink: link to a file
        """
        test_file = os.path.join(self.test_dir, "test")
        touch(test_file)
        lnk = os.path.join(self.test_dir, "test2")
        mklink(test_file, lnk)
        self.assertTrue(os.path.islink(lnk))

    def test_mklink_for_directory(self):
        """
        utils.os.mklink: link to a directory
        """
        test_dir = os.path.join(self.test_dir, "test")
        mkdir(test_dir)
        lnk = os.path.join(self.test_dir, "test2")
        mklink(test_dir, lnk)
        self.assertTrue(os.path.islink(lnk))


class TestChmodFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_chmod_for_file(self):
        """
        utils.os.chomd: check for file
        """
        test_file = os.path.join(self.test_dir,'test.txt')
        with open(test_file,'wt') as fp:
            fp.write(u"Some random text")
        chmod(test_file,0o644)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)
        chmod(test_file,0o755)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o755)

    def test_chmod_for_directory(self):
        """
        utils.os.chmod: check for directory
        """
        test_dir = os.path.join(self.test_dir,'test')
        os.mkdir(test_dir)
        chmod(test_dir,0o755)
        self.assertEqual(stat.S_IMODE(os.lstat(test_dir).st_mode),0o755)
        chmod(test_dir,0o777)
        self.assertEqual(stat.S_IMODE(os.lstat(test_dir).st_mode),0o777)

    def test_chmod_doesnt_follow_link(self):
        """
        utils.os.chmod: check doesn't follow symbolic links
        """
        test_file = os.path.join(self.test_dir,'test.txt')
        with open(test_file,'w') as fp:
            fp.write(u"Some random text")
        test_link = os.path.join(self.test_dir,'test.lnk')
        os.symlink(test_file,test_link)
        chmod(test_file,0o644)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)
        chmod(test_link,0o755)
        # Target should be unaffected
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)


class TestTouchFunction(unittest.TestCase):
    """
    Unit tests for the 'touch' function
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_touch(self):
        "utils.os.touch: touch a file"
        filen = os.path.join(self.test_dir,'touch.test')
        self.assertFalse(os.path.exists(filen))
        touch(filen)
        self.assertTrue(os.path.isfile(filen))