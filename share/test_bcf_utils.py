#######################################################################
# Tests for bcf_utils.py module
#######################################################################
import unittest
import os
import tempfile
import shutil
from bcf_utils import *

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
        self.example_dir.add_file("program.exe")
        os.chmod(self.example_dir.path("unreadable.txt"),0044)
        os.chmod(self.example_dir.path("group_unreadable.txt"),0604)
        os.chmod(self.example_dir.path("program.exe"),0755)
        self.example_dir.add_link("program","program.exe")

    def tearDown(self):
        """Remove directory with test data

        """
        os.chmod(self.example_dir.path("unreadable.txt"),0644)
        os.chmod(self.example_dir.path("group_unreadable.txt"),0644)
        os.chmod(self.example_dir.path("program.exe"),0644)
        self.example_dir.delete_directory()

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

    def test_is_group_readable(self):
        """PathInfo.is_group_readable checks if file, directory and link is group readable

        """
        self.assertTrue(PathInfo(self.example_dir.path("spider.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("web")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("itsy-bitsy.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("broken.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("not_there.txt")).is_group_readable)
        self.assertTrue(PathInfo(self.example_dir.path("unreadable.txt")).is_group_readable)
        self.assertFalse(PathInfo(self.example_dir.path("group_unreadable.txt")).is_group_readable)

    def test_user(self):
        """PathInfo.user returns correct user name (trivial test)

        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).user,current_user)
        self.assertEqual(PathInfo(self.example_dir.path("web")).user,current_user)

    def test_group(self):
        """PathInfo.group returns correct group name (trivial test)

        """
        current_user = pwd.getpwuid(os.getuid()).pw_name
        current_group = grp.getgrgid(pwd.getpwnam(current_user).pw_gid).gr_name
        self.assertEqual(PathInfo(self.example_dir.path("spider.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("itsy-bitsy.txt")).group,current_group)
        self.assertEqual(PathInfo(self.example_dir.path("web")).group,current_group)

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

from mock_data import ExampleDirSpiders
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
        self.fastq_data1 = """"@73D9FA:3:FC:1:1:7507:1000 1:N:0:
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
        self.fastq_data2 = """@73D9FA:3:FC:1:1:7488:1000 1:N:0:
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
            open(fastq,'wt').write(data)
        else:
            gzip.GzipFile(fastq,'wt').write(data)

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
        merged_fastq_data = open(self.merged_fastq,'r').read()
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
        merged_fastq_data = gzip.GzipFile(self.merged_fastq,'r').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

class TestFindProgram(unittest.TestCase):
    """Unit tests for find_program function

    """

    def test_find_program_that_exists(self):
        self.assertEqual(find_program('ls'),'/usr/bin/ls')

    def test_find_program_with_full_path(self):
        self.assertEqual(find_program('/usr/bin/ls'),'/usr/bin/ls')

    def test_dont_find_program_that_does_exist(self):
        self.assertEqual(find_program('/this/doesnt/exist/ls'),None)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
