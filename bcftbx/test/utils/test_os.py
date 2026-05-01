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
from bcftbx.utils.os import find_program
from bcftbx.utils.os import walk
from bcftbx.utils.os import list_dirs


from bcftbx.test import mock_data


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


class TestFindProgram(unittest.TestCase):
    """
    Unit tests for find_program function
    """
    def setUp(self):
        # Try and locate 'ls'
        # Can be in different locations for different OSes
        self.ls = None
        for d in ('/usr/bin','/bin'):
            ls = os.path.join(d,'ls')
            if os.path.exists(ls):
                self.ls = ls
                break
        if self.ls is None:
            self.fail("unable to locate ls program for test")

    def test_find_program_that_exists(self):
        """
        utils.os.find_program: find a program that exists
        """
        self.assertEqual(find_program('ls'), self.ls)

    def test_find_program_with_full_path(self):
        """
        utils.os.find_program: find a program from full path
        """
        self.assertEqual(find_program(self.ls), self.ls)

    def test_dont_find_program_that_does_exist(self):
        """
        utils.os.find_program: can't find program that doesn't exist
        """
        self.assertEqual(find_program('/this/doesnt/exist/ls'), None)


class TestWalkFunction(unittest.TestCase):
    """
    Unit tests for the 'walk' function
    """
    def setUp(self):
        # Make a test data directory structure
        self.example_dir = mock_data.ExampleDirLanguages()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        # Remove the test data directory
        self.example_dir.delete_directory()

    def test_walk(self):
        """
        utils.os.walk: traverses all files and directories
        """
        filelist = self.example_dir.filelist(include_dirs=True)
        filelist.append(self.wd)
        for f in walk(self.wd):
            self.assertTrue(f in filelist,"%s not expected" % f)
            filelist.remove(f)
        self.assertEqual(len(filelist),0,"Items not returned: %s" %
                         ','.join(filelist))

    def test_walk_no_directories(self):
        """
        utils.os.walk: traverses all files and ignores directories
        """
        filelist = self.example_dir.filelist(include_dirs=False)
        for f in walk(self.wd,include_dirs=False):
            self.assertTrue(f in filelist,"%s not expected" % f)
            filelist.remove(f)
        self.assertEqual(len(filelist),0,"Items not returned: %s" %
                         ','.join(filelist))

    def test_walk_includes_hidden_files_and_directories(self):
        """
        utils.os.walk: finds 'hidden' files and directories
        """
        self.example_dir.add_file(".hidden_file")
        self.example_dir.add_dir(".hidden_dir")
        self.example_dir.add_file(".hidden_dir/test")
        filelist = self.example_dir.filelist(include_dirs=True)
        filelist.append(self.wd)
        for f in walk(self.wd):
            self.assertTrue(f in filelist,"%s not expected" % f)
            filelist.remove(f)
        self.assertEqual(len(filelist),0,"Items not returned: %s" %
                         ','.join(filelist))


class TestListDirsFunction(unittest.TestCase):
    """T
    Tests for the list_dirs function
    """
    def setUp(self):
        self.parent_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.parent_dir)

    def __add_sub_dir(self,name):
        # Add a subdirectory
        os.mkdir(os.path.join(self.parent_dir, name))

    def __touch_file(self,name):
        # Add an empty file
        with open(os.path.join(self.parent_dir, name), 'wt') as fp:
            fp.write("")

    def test_empty_dir(self):
        """
        utils.os.list_dirs: returns empty list when listing empty directory
        """
        self.assertEqual(list_dirs(self.parent_dir),[])

    def test_gets_dirs(self):
        """
        utils.os.list_dirs: returns all subdirectories
        """
        self.__add_sub_dir('hello')
        self.assertEqual(list_dirs(self.parent_dir),['hello'])
        self.__add_sub_dir('goodbye')
        self.__add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir),['adios','goodbye','hello'])

    def test_ignores_files(self):
        """
        utils.os.list_dirs: ignores files and only returns subdirectories
        """
        self.__touch_file('hello')
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.__add_sub_dir('goodbye')
        self.__add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir),['adios','goodbye'])

    def test_gets_dir_using_matches(self):
        """
        utils.os.list_dirs: 'matches' argument returns a single directory
        """
        self.__touch_file('hello')
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.__add_sub_dir('goodbye')
        self.__add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir,matches='goodbye'),['goodbye'])
        self.assertEqual(list_dirs(self.parent_dir,matches='nothing'),[])

    def test_gets_dirs_using_startswith(self):
        """
        utils.os.list_dirs: 'startswith' argument returns matching subset of directories
        """
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.__add_sub_dir('hello')
        self.__add_sub_dir('helium')
        self.__add_sub_dir('helicopter')
        self.__add_sub_dir('hermes')
        self.__add_sub_dir('goodbye')
        self.__add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir,startswith='hel'),
                         ['helicopter','helium','hello'])
        self.assertEqual(list_dirs(self.parent_dir,startswith='her'),
                         ['hermes'])
        self.assertEqual(list_dirs(self.parent_dir,startswith='helio'),
                         [])