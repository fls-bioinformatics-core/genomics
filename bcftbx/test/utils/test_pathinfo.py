#######################################################################
# Tests for utils/pathinfo.py module
#######################################################################


import unittest
import os
import pwd
import grp

from bcftbx.test.mock_data import ExampleDirSpiders
from bcftbx.utils.users import get_user_from_uid
from bcftbx.utils.users import get_group_from_gid
from bcftbx.utils.pathinfo import PathInfo
from bcftbx.utils.pathinfo import Symlink

class ExampleDirLinks(ExampleDirSpiders):
    """
    Extended example dir for testing symbolic link handling
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


class TestPathInfo(unittest.TestCase):
    """
    Unit tests for the PathInfo utility class
    """
    def setUp(self):
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
        os.chmod(self.example_dir.path("unreadable.txt"),0o644)
        os.chmod(self.example_dir.path("group_unreadable.txt"),0o644)
        os.chmod(self.example_dir.path("group_unwritable.txt"),0o644)
        os.chmod(self.example_dir.path("program.exe"),0o644)
        self.example_dir.delete_directory()

    def test_path(self):
        """
        utils.pathinfo.PathInfo: 'path' returns correct path
        """
        self.assertEqual(PathInfo("file1.txt").path,"file1.txt")
        self.assertEqual(PathInfo("/path/to/file1.txt").path,"/path/to/file1.txt")
        self.assertEqual(PathInfo("file1.txt",basedir="/path/to").path,"/path/to/file1.txt")

    def test_is_readable(self):
        """
        utils.pathinfo.PathInfo: 'is_readable' checks if file, directory and link is readable
        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_readable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_readable)
        self.assertFalse(PathInfo(self.example_dir.path("unreadable.txt")).is_readable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unreadable.txt")).is_readable)

    def test_deepest_accessible_parent(self):
        """
        utils.pathinfo.PathInfo: 'deepest_accessible_parent' returns correct parent dir
        """
        d = self.example_dir
        self.assertEqual(PathInfo(d.path("spider.txt")).deepest_accessible_parent,d.dirn)
        self.assertEqual(PathInfo(d.path("web")).deepest_accessible_parent,d.dirn)

    def test_resolve_link_via_parent_dir(self):
        """
        utils.pathinfo.PathInfo: 'resolve_link_via_parent' resolves paths when parent directory is a symlink
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
        """
        utils.pathinfo.PathInfo: 'is_group_readable' checks if file, directory and link is group readable
        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("group_unreadable.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unwritable.txt")).is_group_readable)

    def test_is_group_writable(self):
        """
        utils.pathinfo.PathInfo: 'is_group_writeable' checks if file, directory and link is group writable
        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_group_writable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_group_writable)
        self.assertTrue(PathInfo(self.example_dir.path("group_unreadable.txt")).is_group_writable)
        self.assertFalse(PathInfo(self.example_dir.path("group_unwritable.txt")).is_group_writable)

    def test_uid(self):
        """
        utils.pathinfo.PathInfo: 'uid' returns correct UID (trivial test)
        """
        current_uid = os.getuid()
        self.assertNotEqual(None,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).uid,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).uid,current_uid)
        self.assertEqual(PathInfo(self.example_dir.path("web")).uid,current_uid)

    def test_user(self):
        """
        utils.pathinfo.PathInfo: 'user' returns correct user name (trivial test)
        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        self.assertNotEqual(None,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("web")).user,current_user)

    def test_gid(self):
        """
        utils.pathinfo.PathInfo: 'gid' returns correct GID (trivial test)
        """
        current_uid = os.getuid()
        current_gid = pwd.getpwnam(pwd.getpwuid(current_uid).pw_name).pw_gid
        self.assertNotEqual(None,current_uid)
        self.assertNotEqual(None,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).gid,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).gid,current_gid)
        self.assertEqual(PathInfo(self.example_dir.path("web")).gid,current_gid)

    def test_group(self):
        """
        utils.pathinfo.PathInfo: 'group' returns correct group name (trivial test)
        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        current_group = grp.getgrgid(pwd.getpwnam(current_user).pw_gid).gr_name
        self.assertNotEqual(None,current_user)
        self.assertNotEqual(None,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("web")).group,current_group)

    def test_exists(self):
        """
        utils.pathinfo.PathInfo: 'exists' correctly reports path existence
        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("web")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("web2")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).exists)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).exists)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).exists)

    def test_is_link(self):
        """
        utils.pathinfo.PathInfo: 'is_link' correctly identifies symbolic links
        """
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_link)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("web2")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_link)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_link)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_link)

    def test_is_file(self):
        """
        utils.pathinfo.PathInfo: 'is_file' correctly identifies files
        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("web2")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("broken.txt")).is_file)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_file)

    def test_is_dir(self):
        """
        utils.pathinfo.PathInfo: 'is_dir' correctly identifies directories
        """
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_dir)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("web2")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("broken.txt")).is_dir)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_dir)

    def test_is_executable(self):
        """
        utils.pathinfo.PathInfo: 'is_executable' correctly identifies executable files
        """
        self.assertTrue(PathInfo(self.example_dir.path("program.exe")).is_executable)
        self.assertTrue(PathInfo(self.example_dir.path("program")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("spider.txt")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_executable)
        self.assertFalse(PathInfo(self.example_dir.path("web")).is_executable)

    def test_relpath(self):
        """
        utils.pathinfo.PathInfo: 'relpath' returns expected relative paths
        """
        self.assertEqual(PathInfo("/a/test/path").relpath("/a/test/path"),".")
        self.assertEqual(PathInfo("/a/test/path").relpath("/a/test"),"path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/a"),"test/path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/"),"a/test/path")
        self.assertEqual(PathInfo("/a/test/path").relpath("/b"),"../a/test/path")

    def test_chown_user(self):
        """
        utils.pathinfo.PathInfo: 'chown' can change user
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
        """
        utils.pathinfo.PathInfo: 'chown' can change group
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


class TestSymlink(unittest.TestCase):
    """Tests for the 'Symlink' class

    """
    def setUp(self):
        self.example_dir = ExampleDirLinks()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        self.example_dir.delete_directory()

    def test_not_a_link(self):
        """
        utils.pathinfo.Symlink: raises exception if path is not a link
        """
        self.assertRaises(Exception,Symlink,self.example_dir.path("spider.txt"))

    def test_target(self):
        """
        utils.pathinfo.Symlink: 'target' returns correct target
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
        """
        utils.pathinfo.Symlink: 'is_absolute' correctly identifies absolute links
        """
        self.assertTrue(Symlink(self.example_dir.path("absolute.txt")).is_absolute)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("broken.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_absolute)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_absolute)

    def test_is_broken(self):
        """
        utils.pathinfo.Symlink: 'is_broken' correctly identifies broken links
        """
        self.assertFalse(Symlink(self.example_dir.path("absolute.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("absolutely_broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("itsy-bitsy.txt")).is_broken)
        self.assertTrue(Symlink(self.example_dir.path("broken.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web/relative.txt")).is_broken)
        self.assertFalse(Symlink(self.example_dir.path("web2")).is_broken)

    def test_resolve_target(self):
        """
        utils.pathinfo.Symlink: 'resolve_target' correctly resolves full link target paths
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
        """
        utils.pathinfo.Symlink: 'update_target' updates the link target path
        """
        symlink = Symlink(self.example_dir.path("itsy-bitsy.txt"))
        self.assertEqual(symlink.target,"spider.txt")
        symlink.update_target("spider2.txt")
        self.assertEqual(symlink.target,"spider2.txt")
