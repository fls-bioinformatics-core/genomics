#######################################################################
# Tests for bcf_utils.py module
#######################################################################
import unittest
import os
import io
import tempfile
import shutil
import gzip
import pickle
from . import mock_data
from .mock_data import ExampleDirSpiders
from bcftbx.utils import *

class TestAttributeDictionary(unittest.TestCase):
    """Tests for the AttributeDictionary class
    """

    def test_set_get_items(self):
        """AttributeDictionary 'set' and 'get' using dictionary notation
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        self.assertEqual(len(d),1)
        self.assertEqual(d["salutation"],"hello")

    def test_get_attrs(self):
        """AttributeDictionary 'get' using attribute notation
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        self.assertEqual(len(d),1)
        self.assertEqual(d.salutation,"hello")

    def test_init(self):
        """AttributeDictionary initialised like a standard dictionary
        """
        d = AttributeDictionary(salutation='hello',valediction='goodbye')
        self.assertEqual(len(d),2)
        self.assertEqual(d.salutation,"hello")
        self.assertEqual(d.valediction,"goodbye")

    def test_iter(self):
        """AttributeDictionary iteration over items
        """
        d = AttributeDictionary()
        self.assertEqual(len(d),0)
        d['salutation'] = 'hello'
        d['valediction'] = 'goodbye'
        self.assertEqual(len(d),2)
        self.assertEqual(d.salutation,"hello")
        self.assertEqual(d.valediction,"goodbye")
        for key in d:
            self.assertTrue(key in ('salutation','valediction'),
                            "%s not in list" % key)

    def test_can_pickle_attributedictionary(self):
        """AttributeDictionary can be pickled
        """
        d = AttributeDictionary(hello="world")
        self.assertEqual(d['hello'],"world")
        pickled = pickle.dumps(d)
        unpickled = pickle.loads(pickled)
        self.assertTrue(isinstance(unpickled,AttributeDictionary))
        self.assertEqual(unpickled['hello'],"world")
        self.assertEqual(unpickled.hello,"world")

class TestOrderedDictionary(unittest.TestCase):
    """Unit tests for the OrderedDictionary class
    """

    def test_get_and_set(self):
        """OrderedDictionary add and retrieve data
        """
        d = OrderedDictionary()
        self.assertEqual(len(d),0)
        d['hello'] = 'goodbye'
        self.assertEqual(d['hello'],'goodbye')

    def test_insert(self):
        """OrderedDictionary insert items
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        self.assertEqual(d.keys(),['hello'])
        self.assertEqual(len(d),1)
        # Insert at start of list
        d.insert(0,'stanley','fetcher')
        self.assertEqual(d.keys(),['stanley','hello'])
        self.assertEqual(len(d),2)
        self.assertEqual(d['stanley'],'fetcher')
        self.assertEqual(d['hello'],'goodbye')
        # Insert in middle
        d.insert(1,'monty','python')
        self.assertEqual(d.keys(),['stanley','monty','hello'])
        self.assertEqual(len(d),3)
        self.assertEqual(d['stanley'],'fetcher')
        self.assertEqual(d['monty'],'python')
        self.assertEqual(d['hello'],'goodbye')

    def test_keeps_things_in_order(self):
        """OrderedDictionary returns items in same order as added
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        d['stanley'] = 'fletcher'
        d['monty'] = 'python'
        self.assertEqual(d.keys(),['hello','stanley','monty'])

    def test_iteration_over_keys(self):
        """OrderedDictionary iterating over keys
        """
        d = OrderedDictionary()
        d['hello'] = 'goodbye'
        d['stanley'] = 'fletcher'
        d['monty'] = 'python'
        try:
            for i in d:
                pass
        except KeyError:
            self.fail("Iteration over OrderedDictionary failed")

class TestGetlinesFunction(unittest.TestCase):
    """Unit tests for the getlines function
    """
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.example_text = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
"""
    def tearDown(self):
        shutil.rmtree(self.wd)
    def test_getlines(self):
        """getlines: read lines from a file
        """
        # Make an example file
        example_file = os.path.join(self.wd,"example.txt")
        with io.open(example_file,'wt') as fp:
            fp.write(self.example_text)
        # Read lines
        lines = getlines(example_file)
        for l1,l2 in zip(self.example_text.split('\n'),lines):
            self.assertEqual(l1,l2)
    def test_getlines_from_gzipped_file(self):
        """getlines: read lines from a gzipped file
        """
        # Make an example gzipped file
        example_file = os.path.join(self.wd,"example.txt.gz")
        with gzip.open(example_file,'wt') as fp:
            fp.write(self.example_text)
        # Read lines
        lines = getlines(example_file)
        for l1,l2 in zip(self.example_text.split('\n'),lines):
            self.assertEqual(l1,l2)

class TestPathInfo(unittest.TestCase):
    """Unit tests for the PathInfo utility class

    """
    def setUp(self):
        """Build directory with test data

        """
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()
        self.example_dir.add_file("unreadable.txt")
        self.example_dir.add_file("group_unreadable.txt")
        self.example_dir.add_file("group_unwritable.txt")
        self.example_dir.add_file("program.exe")
        os.chmod(self.example_dir.path("spider.txt"),0o664)
        os.chmod(self.example_dir.path("web"),0o775)
        os.chmod(self.example_dir.path("unreadable.txt"),0o044)
        os.chmod(self.example_dir.path("group_unreadable.txt"),0o624)
        os.chmod(self.example_dir.path("group_unwritable.txt"),0o644)
        os.chmod(self.example_dir.path("program.exe"),0o755)
        self.example_dir.add_link("program","program.exe")

    def tearDown(self):
        """Remove directory with test data

        """
        os.chmod(self.example_dir.path("unreadable.txt"),0o644)
        os.chmod(self.example_dir.path("group_unreadable.txt"),0o644)
        os.chmod(self.example_dir.path("group_unwritable.txt"),0o644)
        os.chmod(self.example_dir.path("program.exe"),0o644)
        self.example_dir.delete_directory()

    def test_path(self):
        """PathInfo.path returns correct path

        """
        self.assertEqual(PathInfo("file1.txt").path,"file1.txt")
        self.assertEqual(PathInfo("/path/to/file1.txt").path,"/path/to/file1.txt")
        self.assertEqual(PathInfo("file1.txt",basedir="/path/to").path,"/path/to/file1.txt")

    def test_is_readable(self):
        """PathInfo.is_readable checks if file, directory and link is readable

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_readable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_readable)
        self.assertFalse(PathInfo(self.example_dir.path("unreadable.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unreadable.txt")).is_readable)

    def test_deepest_accessible_parent(self):
        """PathInfo.deepest_accessible_parent returns correct parent dir

        """
        d = self.example_dir
        self.assertEqual(PathInfo(d.path("spider.txt")).deepest_accessible_parent,d.dirn)
        self.assertEqual(PathInfo(d.path("web")).deepest_accessible_parent,d.dirn)

    def test_resolve_link_via_parent_dir(self):
        """PathInfo.resolve_link_via_parent resolves paths when parent directory is a symlink

        """
        d = self.example_dir
        self.assertEqual(PathInfo(d.path("web/parlour.txt")).resolve_link_via_parent,
                         d.path("web/parlour.txt"))
        self.assertEqual(PathInfo(d.path("web2/parlour.txt")).resolve_link_via_parent,
                         d.path("web/parlour.txt"))
        self.assertEqual(PathInfo(d.path("web/relative.txt")).resolve_link_via_parent,
                         d.path("spider.txt"))
        self.assertEqual(PathInfo(d.path("web/related.txt")).resolve_link_via_parent,
                         d.path("spider.txt"))
        self.assertEqual(PathInfo(d.path("broken.txt")).resolve_link_via_parent,
                         d.path("missing.txt"))

    def test_is_group_readable(self):
        """PathInfo.is_group_readable checks if file, directory and link is group readable

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("group_unreadable.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unwritable.txt")).is_group_readable)

    def test_is_group_writable(self):
        """PathInfo.is_group_writeable checks if file, directory and link is group writable

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_group_writable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unreadable.txt")).is_group_writable)
        self.assertFalse(PathInfo(self.example_dir.path("group_unwritable.txt")).is_group_writable)

    def test_uid(self):
        """PathInfo.uid returns correct UID (trivial test)

        """
        current_uid = os.getuid()
        self.assertNotEqual(None,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).uid,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).uid,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("web")).uid,current_uid)

    def test_user(self):
        """PathInfo.user returns correct user name (trivial test)

        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        self.assertNotEqual(None,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("web")).user,current_user)

    def test_gid(self):
        """PathInfo.gid returns correct GID (trivial test)

        """
        current_uid = os.getuid()
        current_gid = pwd.getpwnam(pwd.getpwuid(current_uid).pw_name).pw_gid
        self.assertNotEqual(None,current_uid)
        self.assertNotEqual(None,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).gid,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).gid,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("web")).gid,current_gid)

    def test_group(self):
        """PathInfo.group returns correct group name (trivial test)

        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        current_group = grp.getgrgid(pwd.getpwnam(current_user).pw_gid).gr_name
        self.assertNotEqual(None,current_user)
        self.assertNotEqual(None,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("web")).group,current_group)

    def test_exists(self):
        """PathInfo.exists correctly reports path existence

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("web")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("web2")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).exists)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).exists)

    def test_is_link(self):
        """PathInfo.is_link correctly identifies symbolic links

        """
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_link)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("web2")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_link)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_link)

    def test_is_file(self):
        """PathInfo.is_file correctly identifies files

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("web2")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("broken.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_file)

    def test_is_dir(self):
        """PathInfo.is_dir correctly identifies directories

        """
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_dir)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("web2")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("broken.txt")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_dir)

    def test_is_executable(self):
        """PathInfo.is_executable correctly identifies executable files

        """
        self.assertTrue(PathInfo(self.example_dir.path("program.exe")).is_executable)
        self.assertTrue(PathInfo(self.example_dir.path("program")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_executable)

    def test_relpath(self):
        """PathInfo.relpath returns expected relative paths

        """
        self.assertEqual(PathInfo("/a/test/path").relpath("/a/test/path"),".")
        self.assertEqual(PathInfo("/a/test/path").relpath("/a/test"),"path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/a"),"test/path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/"),"a/test/path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/b"),"../a/test/path")

    def test_chown_user(self):
        """PathInfo.chown can change user

        """
        path = PathInfo(self.example_dir.path("spider.txt"))
        # Ensure file can be removed by anyone i.e. write permission for all
        os.chmod(self.example_dir.path("spider.txt"),0o666)
        # Will always fail for non-root user?
        current_user = pwd.getpwuid(os.getuid()).pw_name
        if current_user != "root":
            raise unittest.SkipTest("always fails for non-root user")
        # Get a list of users
        users = [u.pw_uid for u in pwd.getpwall()]
        if len(users) < 2:
            raise unittest.SkipTest("must have at least two users on the system")
        # Get a second user
        new_uid = None
        for user in users:
            if user != path.uid:
                new_uid = user
                break
        print("Resetting owner to %s (%s)" % (new_uid,
                                              get_user_from_uid(new_uid)))
        self.assertNotEqual(new_uid,path.uid)
        # Reset the user
        path.chown(user=new_uid)
        self.assertEqual(path.uid,new_uid,"Failed to reset owner to %s (%s)" %
                         (new_uid,get_user_from_uid(new_uid)))

    def test_chown_group(self):
        """PathInfo.chown can change group

        """
        path = PathInfo(self.example_dir.path("spider.txt"))
        # Get a list of groups
        current_user = pwd.getpwuid(os.getuid()).pw_name
        groups = [g.gr_gid for g in grp.getgrall() if current_user in g.gr_mem]
        if len(groups) < 2:
            raise unittest.SkipTest("user '%s' must be in at least two groups" % current_user)
        # Get a second group
        new_gid = None
        for group in groups:
            if group != path.gid:
                new_gid = group
                break
        self.assertNotEqual(new_gid,path.gid)
        # Reset the group
        path.chown(group=new_gid)
        self.assertEqual(path.gid,new_gid,"Failed to reset group to %s (%s)" %
                         (new_gid,get_group_from_gid(new_gid)))

class TestUserAndGroupNameFunctions(unittest.TestCase):
    """Tests for the functions fetching user and group names and IDs

    """
    def test_get_user_from_uid(self):
        """get_user_from_uid gets 'root' from UID 0

        """
        self.assertEqual(get_user_from_uid(0),'root')

    def test_get_uid_from_user(self):
        """get_uid_from_user gets 0 from 'root'

        """
        self.assertEqual(get_uid_from_user('root'),0)

    def test_get_group_from_gid(self):
        """get_group_from_gid gets 'root' from UID 0

        """
        self.assertEqual(get_group_from_gid(0),'root')

    def test_get_gid_from_group(self):
        """get_gid_from_group gets 0 from 'root'

        """
        self.assertEqual(get_gid_from_group('root'),0)

    def test_user_and_group_functions_handle_string_ids(self):
        """get_user_from_uid, get_group_from_gid handle UID/GID supplied as strings

        """
        self.assertEqual(get_user_from_uid('0'),'root')
        self.assertEqual(get_group_from_gid('0'),'root')

    def test_user_and_group_functions_handle_nonexistent_users(self):
        """User/group name functions handle nonexistent users

        """
        self.assertEqual(get_user_from_uid(-999),None)
        self.assertEqual(get_uid_from_user(''),None)
        self.assertEqual(get_group_from_gid(-999),None)
        self.assertEqual(get_gid_from_group(''),None)

    def test_user_and_group_functions_handle_bad_inputs(self):
        """User/group name functions handle bad inputs

        """
        self.assertEqual(get_user_from_uid('root'),None)
        self.assertEqual(get_uid_from_user('0'),None)
        self.assertEqual(get_group_from_gid('root'),None)
        self.assertEqual(get_gid_from_group('0'),None)

class TestWalkFunction(unittest.TestCase):
    """Unit tests for the 'walk' function

    """
    def setUp(self):
        # Make a test data directory structure
        self.example_dir = mock_data.ExampleDirLanguages()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        # Remove the test data directory
        self.example_dir.delete_directory()

    def test_walk(self):
        """'walk' traverses all files and directories

        """
        filelist = self.example_dir.filelist(include_dirs=True)
        filelist.append(self.wd)
        for f in walk(self.wd):
            self.assertTrue(f in filelist,"%s not expected" % f)
            filelist.remove(f)
        self.assertEqual(len(filelist),0,"Items not returned: %s" %
                         ','.join(filelist))

    def test_walk_no_directories(self):
        """'walk' traverses all files and ignores directories

        """
        filelist = self.example_dir.filelist(include_dirs=False)
        for f in walk(self.wd,include_dirs=False):
            self.assertTrue(f in filelist,"%s not expected" % f)
            filelist.remove(f)
        self.assertEqual(len(filelist),0,"Items not returned: %s" %
                         ','.join(filelist))

    def test_walk_includes_hidden_files_and_directories(self):
        """'walk' finds 'hidden' files and directories

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
    """Tests for the list_dirs function

    """
    def setUp(self):
        self.parent_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.parent_dir)

    def add_sub_dir(self,name):
        # Add a subdirectory
        os.mkdir(os.path.join(self.parent_dir,name))

    def touch_file(self,name):
        # Add an empty file
        with io.open(os.path.join(self.parent_dir,name),'wt') as fp:
            fp.write(u'')

    def test_empty_dir(self):
        """list_dirs returns empty list when listing empty directory
        """
        self.assertEqual(list_dirs(self.parent_dir),[])

    def test_gets_dirs(self):
        """list_dirs returns all subdirectories
        """
        self.add_sub_dir('hello')
        self.assertEqual(list_dirs(self.parent_dir),['hello'])
        self.add_sub_dir('goodbye')
        self.add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir),['adios','goodbye','hello'])

    def test_ignores_files(self):
        """list_dirs ignores files and only returns subdirectories
        """
        self.touch_file('hello')
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.add_sub_dir('goodbye')
        self.add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir),['adios','goodbye'])

    def test_gets_dir_using_matches(self):
        """list_dirs 'matches' argument returns a single directory
        """
        self.touch_file('hello')
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.add_sub_dir('goodbye')
        self.add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir,matches='goodbye'),['goodbye'])
        self.assertEqual(list_dirs(self.parent_dir,matches='nothing'),[])

    def test_gets_dirs_using_startswith(self):
        """list_dirs 'startswith' argument returns matching subset of directories
        """
        self.assertEqual(list_dirs(self.parent_dir),[])
        self.add_sub_dir('hello')
        self.add_sub_dir('helium')
        self.add_sub_dir('helicopter')
        self.add_sub_dir('hermes')
        self.add_sub_dir('goodbye')
        self.add_sub_dir('adios')
        self.assertEqual(list_dirs(self.parent_dir,startswith='hel'),
                         ['helicopter','helium','hello'])
        self.assertEqual(list_dirs(self.parent_dir,startswith='her'),
                         ['hermes'])
        self.assertEqual(list_dirs(self.parent_dir,startswith='helio'),
                         [])

class TestFileSystemFunctions(unittest.TestCase):
    """Unit tests for file system wrapper and utility functions

    """

    def test_commonprefix(self):
        self.assertEqual('/mnt/stuff',commonprefix('/mnt/stuff/dir1',
                                                   '/mnt/stuff/dir2'))
        self.assertEqual('',commonprefix('/mnt1/stuff/dir1',
                                         '/mnt2/stuff/dir2'))

    def test_is_gzipped_file(self):
        self.assertTrue(is_gzipped_file('hello.gz'))
        self.assertTrue(is_gzipped_file('hello.tar.gz'))
        self.assertFalse(is_gzipped_file('hello'))
        self.assertFalse(is_gzipped_file('hello.txt'))
        self.assertFalse(is_gzipped_file('hello.gz.part'))
        self.assertFalse(is_gzipped_file('hellogz'))

    def test_rootname(self):
        self.assertEqual('name',rootname('name'))
        self.assertEqual('name',rootname('name.fastq'))
        self.assertEqual('name',rootname('name.fastq.gz'))
        self.assertEqual('/path/to/name',rootname('/path/to/name.fastq.gz'))

    def test_strip_ext(self):
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

class TestMkdirFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mkdir(self):
        """mkdir: make a single subdirectory
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        self.assertFalse(os.path.exists(new_dir))
        mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_mkdir_chmod(self):
        """mkdir: make a subdirectory and set permissions
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        self.assertFalse(os.path.exists(new_dir))
        mkdir(new_dir,mode=0o644)
        self.assertTrue(os.path.exists(new_dir))
        self.assertEqual(stat.S_IMODE(os.lstat(new_dir).st_mode),0o644)

    def test_mkdir_dir_already_exists(self):
        """mkdir: try to make a subdirectory that already exists
        """
        new_dir = os.path.join(self.test_dir,"new_dir")
        os.mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        mkdir(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_mkdir_dir_recursive(self):
        """mkdir: make a subdirectory recursively
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
        """mkdirs: make a subdirectory recursively
        """
        new_dir = os.path.join(self.test_dir,"new_dir","subdir","test")
        self.assertFalse(os.path.exists(new_dir))
        mkdirs(new_dir)
        self.assertTrue(os.path.exists(new_dir))

class TestChmodFunction(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_chmod_for_file(self):
        """Check chmod works on a file
        """
        test_file = os.path.join(self.test_dir,'test.txt')
        with io.open(test_file,'wt') as fp:
            fp.write(u"Some random text")
        chmod(test_file,0o644)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)
        chmod(test_file,0o755)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o755)

    def test_chmod_for_directory(self):
        """Check chmod works on a directory
        """
        test_dir = os.path.join(self.test_dir,'test')
        os.mkdir(test_dir)
        chmod(test_dir,0o755)
        self.assertEqual(stat.S_IMODE(os.lstat(test_dir).st_mode),0o755)
        chmod(test_dir,0o777)
        self.assertEqual(stat.S_IMODE(os.lstat(test_dir).st_mode),0o777)

    def test_chmod_doesnt_follow_link(self):
        """Check chmod doesn't follow symbolic links
        """
        test_file = os.path.join(self.test_dir,'test.txt')
        with io.open(test_file,'w') as fp:
            fp.write(u"Some random text")
        test_link = os.path.join(self.test_dir,'test.lnk')
        os.symlink(test_file,test_link)
        chmod(test_file,0o644)
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)
        chmod(test_link,0o755)
        # Target should be unaffected
        self.assertEqual(stat.S_IMODE(os.lstat(test_file).st_mode),0o644)

class TestTouchFunction(unittest.TestCase):
    """Unit tests for the 'touch' function

    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_touch(self):
        filen = os.path.join(self.test_dir,'touch.test')
        self.assertFalse(os.path.exists(filen))
        touch(filen)
        self.assertTrue(os.path.isfile(filen))

class TestFormatFileSize(unittest.TestCase):
    """Unit tests for formatting file sizes

    """

    def test_bytes_to_kb(self):
        """format_file_size converts bytes to Kb
        """
        self.assertEqual("0.9K",format_file_size(900))
        self.assertEqual("0.9K",format_file_size(900,units='K'))
        self.assertEqual("0.9K",format_file_size(900,units='k'))
        self.assertEqual("4.0K",format_file_size(4096))
        self.assertEqual("4.0K",format_file_size(4096,units='K'))
        self.assertEqual("4.0K",format_file_size(4096,units='k'))

    def test_bytes_to_mb(self):
        """format_file_size converts bytes to Mb
        """
        self.assertEqual("186.0M",format_file_size(195035136))
        self.assertEqual("186.0M",format_file_size(195035136,units='M'))
        self.assertEqual("186.0M",format_file_size(195035136,units='m'))
        self.assertEqual("0.0M",format_file_size(900,units='M'))
        self.assertEqual("0.0M",format_file_size(4096,units='M'))

    def test_bytes_to_gb(self):
        """format_file_size converts bytes to Gb
        """
        self.assertEqual("1.6G",format_file_size(1717986919))
        self.assertEqual("1.6G",format_file_size(1717986919,units='G'))
        self.assertEqual("1.6G",format_file_size(1717986919,units='g'))
        self.assertEqual("0.0G",format_file_size(900,units='G'))
        self.assertEqual("0.0G",format_file_size(4096,units='G'))
        self.assertEqual("0.2G",format_file_size(195035136,units='G'))

    def test_bytes_to_tb(self):
        """format_file_size converts bytes to Tb
        """
        self.assertEqual("4.4T",format_file_size(4831838208091))
        self.assertEqual("4.4T",format_file_size(4831838208091,units='T'))
        self.assertEqual("4.4T",format_file_size(4831838208091,units='t'))
        self.assertEqual("0.0T",format_file_size(900,units='T'))
        self.assertEqual("0.0T",format_file_size(4096,units='T'))
        self.assertEqual("0.0T",format_file_size(195035136,units='T'))
        self.assertEqual("0.2T",format_file_size(171798691900,units='T'))

class TestConvertSizeToBytes(unittest.TestCase):
    """
    Unit tests for converting file sizes to bytes
    """
    def test_convert_size_to_bytes(self):
        """
        convert_size_to_bytes: handle different inputs
        """
        self.assertEqual(convert_size_to_bytes('4.0K'),4096)
        self.assertEqual(convert_size_to_bytes('4.0M'),4194304)
        self.assertEqual(convert_size_to_bytes('4.0G'),4294967296)
        self.assertEqual(convert_size_to_bytes('4.0T'),4398046511104)
        self.assertEqual(convert_size_to_bytes('4T'),4398046511104)

class ExampleDirLinks(ExampleDirSpiders):
    """Extended example dir for testing symbolic link handling

    """
    def __init__(self):
        ExampleDirSpiders.__init__(self)
    def create_directory(self):
        ExampleDirSpiders.create_directory(self)
        # Add an absolute link
        self.add_link("absolute.txt",self.path("fly.txt"))
        # Add a broken absolute link
        self.add_link("absolutely_broken.txt",self.path("absolutely_missing.txt"))
        # Add a relative link with '..'
        self.add_link("web/relative.txt","../spider.txt")
        # Add a link to a directory
        self.add_link("web2","web")
        # Add a link to a link
        self.add_link("web/related.txt","relative.txt")
        # Add a file that will appear in the linked directory
        self.add_file("web/parlour.txt","I have a little something here")

class TestSymlink(unittest.TestCase):
    """Tests for the 'Symlink' class

    """
    def setUp(self):
        """Build directory with test data

        """
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        """Remove directory with test data

        """
        self.example_dir.delete_directory()

    def test_not_a_link(self):
        """Symlink raises exception if path is not a link

        """
        self.assertRaises(Exception,Symlink,self.example_dir.path("spider.txt"))

    def test_target(self):
        """Symlink.target returns correct target

        """
        self.assertEqual(Symlink(self.example_dir.path("itsy-bitsy.txt")).target,
                         "spider.txt")
        self.assertEqual(Symlink(self.example_dir.path("broken.txt")).target,
                         "missing.txt")
        self.assertEqual(Symlink(self.example_dir.path("absolute.txt")).target,
                         self.example_dir.path("fly.txt"))
        self.assertEqual(Symlink(self.example_dir.path("absolutely_broken.txt")).target,
                         self.example_dir.path("absolutely_missing.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web/relative.txt")).target,
                         "../spider.txt")
        self.assertEqual(Symlink(self.example_dir.path("web2")).target,"web")

    def test_is_absolute(self):
        """Symlink.is_absolute correctly identifies absolute links

        """
        self.assertTrue(Symlink(self.example_dir.path("absolute.txt")).is_absolute)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_absolute)

    def test_is_broken(self):
        """Symlink.is_broken correctly identifies broken links

        """
        self.assertFalse(Symlink(self.example_dir.path("absolute.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_broken)

    def test_resolve_target(self):
        """Symlink.resolve_target() correctly resolves full link target paths

        """
        self.assertEqual(Symlink(self.example_dir.path("itsy-bitsy.txt")).resolve_target(),
                         self.example_dir.path("spider.txt"))
        self.assertEqual(Symlink(self.example_dir.path("absolute.txt")).resolve_target(),
                         self.example_dir.path("fly.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web/relative.txt")).resolve_target(),
                         self.example_dir.path("spider.txt"))
        self.assertEqual(Symlink(self.example_dir.path("web2")).resolve_target(),
                         self.example_dir.path("web"))

    def test_update_target(self):
        """Symlink.update_target() updates the link target path

        """
        symlink = Symlink(self.example_dir.path("itsy-bitsy.txt"))
        self.assertEqual(symlink.target,"spider.txt")
        symlink.update_target("spider2.txt")
        self.assertEqual(symlink.target,"spider2.txt")

class TestLinksFunction(unittest.TestCase):
    """Tests for the 'links' function

    """
    def setUp(self):
        """Build directory with test data

        """
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()
        self.links = []
        for l in ("itsy-bitsy.txt",
                  "itsy-bitsy2.txt",
                  "broken.txt",
                  "broken2.txt",
                  "absolute.txt",
                  "absolutely_broken.txt",
                  "web/relative.txt",
                  "web/related.txt",
                  "web2"):
            self.links.append(self.example_dir.path(l))

    def tearDown(self):
        """Remove directory with test data

        """
        self.example_dir.delete_directory()

    def test_links(self):
        """links function yields all symlinks

        """
        # Walk the example directory and check all yielded files
        # are in the list of links
        for l in links(self.example_dir.dirn):
            self.assertTrue(l in self.links,"%s not in link list" % l)
            self.links.remove(l)
        self.assertEqual(len(self.links),0,"Some links not found: %s" % ",".join(self.links))

class TestNameFunctions(unittest.TestCase):
    """Unit tests for name handling utility functions

    """

    def test_extract_initials(self):
        self.assertEqual('DR',extract_initials('DR1'))
        self.assertEqual('EP',extract_initials('EP_NCYC2669'))
        self.assertEqual('CW',extract_initials('CW_TI'))

    def test_extract_prefix(self):
        self.assertEqual('LD_C',extract_prefix('LD_C1'))

    def test_extract_index_as_string(self):
        self.assertEqual('1',extract_index_as_string('LD_C1'))
        self.assertEqual('07',extract_index_as_string('DR07'))
        self.assertEqual('',extract_index_as_string('DROHSEVEN'))

    def test_extract_index(self):
        self.assertEqual(1,extract_index('LD_C1'))
        self.assertEqual(7,extract_index('DR07'))
        self.assertEqual(None,extract_index('DROHSEVEN'))
        self.assertEqual(0,extract_index('HUES1A0'))

    def test_pretty_print_names(self):
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

class TestConcatenateFastqFiles(unittest.TestCase):
    """Unit tests for concatenate_fastq_files

    """
    def setUp(self):
        # Create a set of test files
        self.fastq_data1 = u""""@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 1:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 1:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
"""
        self.fastq_data2 = u"""@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

    def tearDown(self):
        os.remove(self.fastq1)
        os.remove(self.fastq2)
        os.remove(self.merged_fastq)

    def make_fastq_file(self,fastq,data):
        # Create a fastq file for the testing
        if os.path.splitext(fastq)[1] != '.gz':
            with io.open(fastq,'wt') as fp:
                fp.write(data)
        else:
            with gzip.open(fastq,'wt') as fp:
                fp.write(data)

    def test_concatenate_fastq_files(self):
        self.fastq1 = "concat.unittest.1.fastq"
        self.fastq2 = "concat.unittest.2.fastq"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        with io.open(self.merged_fastq,'rt') as fp:
            merged_fastq_data = fp.read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

    def test_concatenate_fastq_files_gzipped(self):
        self.fastq1 = "concat.unittest.1.fastq.gz"
        self.fastq2 = "concat.unittest.2.fastq.gz"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq.gz"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        merged_fastq_data = gzip.open(self.merged_fastq,'rt').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

class TestFindProgram(unittest.TestCase):
    """Unit tests for find_program function

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
        self.assertEqual(find_program('ls'),self.ls)

    def test_find_program_with_full_path(self):
        self.assertEqual(find_program(self.ls),self.ls)

    def test_dont_find_program_that_does_exist(self):
        self.assertEqual(find_program('/this/doesnt/exist/ls'),None)

class TestSplitIntoLinesFunction(unittest.TestCase):
    """Unit tests for the split_into_lines function

    """
    def test_split_into_lines(self):
        self.assertEqual(split_into_lines('This is some text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is\nsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is\tsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is \tsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is some text',17),
                         ['This is some text'])
        self.assertEqual(split_into_lines('This is some text',100),
                         ['This is some text'])
    def test_split_into_lines_delimiter_after_line_limit(self):
        self.assertEqual(split_into_lines('This is some text',12),
                         ['This is some','text'])
    def test_split_into_lines_sympathetically(self):
        self.assertEqual(split_into_lines("This is supercalifragilicous text",10),
                         ['This is','supercalif','ragilicous','text'])
        self.assertEqual(split_into_lines("This is supercalifragilicous text",10,
                                          sympathetic=True),
                         ['This is','supercali-','fragilico-','us text'])
    def test_split_into_lines_alternative_delimiters(self):
        self.assertEqual(split_into_lines('This is some text',10,':'),
                         ['This is so','me text'])
        self.assertEqual(split_into_lines('This: is some text',10,':'),
                         ['This',' is some t','ext'])

class TestParseNamedLanesFunction(unittest.TestCase):
    """
    Unit tests for breaking up '[<lanes>:]<name>' expression
    """
    def test_name_no_lanes(self):
        """parse_named_lanes: name with no lanes
        """
        self.assertEqual(parse_named_lanes("PJB"),(None,"PJB"))
    def test_name_with_single_lane(self):
        """parse_named_lanes: name with a single lane
        """
        self.assertEqual(parse_named_lanes("1:PJB"),([1,],"PJB"))
    def test_name_with_range_of_lanes(self):
        """parse_named_lanes: name with a range of lanes
        """
        self.assertEqual(parse_named_lanes("2-4:PJB"),([2,3,4],"PJB"))
    def test_name_with_list_of_lanes(self):
        """parse_named_lanes: name with a list of lanes
        """
        self.assertEqual(parse_named_lanes("1,3,5:PJB"),([1,3,5],"PJB"))
    def test_name_with_mixture(self):
        """parse_named_lanes: name with both range and list of lanes
        """
        self.assertEqual(parse_named_lanes("1,3,5-8:PJB"),
                         ([1,3,5,6,7,8],"PJB"))

class TestParseLanesFunction(unittest.TestCase):
    """
    Unit tests for breaking up range-of-lanes expression
    """
    def test_single_integer(self):
        """parse_lanes: single lane e.g. '1'
        """
        self.assertEqual(parse_lanes("1"),[1,])
    def test_range(self):
        """parse_lanes: range of lanes e.g. '2-4'
        """
        self.assertEqual(parse_lanes("2-4"),[2,3,4,])
    def test_list(self):
        """parse_lanes: list of lanes e.g. '1,2,5'
        """
        self.assertEqual(parse_lanes("1,3,5"),[1,3,5,])
    def test_mixture(self):
        """parse_lanes: mixture of range and list of lanes
        """
        self.assertEqual(parse_lanes("1,3,5-8"),
                         [1,3,5,6,7,8])

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
