#######################################################################
# Tests for Md5sum.py module
#######################################################################
from builtins import str
from bcftbx.Md5sum import *
from bcftbx.test.mock_data import ExampleDirSpiders,ExampleDirLanguages
import unittest
import os
import tempfile
import io

TEST_TEXT = u"""Md5sum is a Python module with functions for generating
MD5 checksums for files."""

class TestMd5sum(unittest.TestCase):

    def setUp(self):
        # mkstemp returns a tuple
        tmpfile = tempfile.mkstemp()
        self.filen = tmpfile[1]
        with io.open(self.filen,'wt') as fp:
            fp.write(TEST_TEXT)

    def tearDown(self):
        os.remove(self.filen)

    def test_md5sum_for_file(self):
        """md5sum function generates correct MD5 hash for file
        """
        self.assertEqual(md5sum(self.filen),
                         '08a6facee51e5435b9ef3744bd4dd5dc')

    def test_md5sum_for_stream(self):
        """md5sum function generates correct MD5 hash for stream
        """
        with io.open(self.filen,'rb') as fp:
            self.assertEqual(md5sum(fp),
                             '08a6facee51e5435b9ef3744bd4dd5dc')

    def test_no_file_name(self):
        """md5sum function handles 'None' as input file name
        """
        self.assertRaises(Exception,md5sum,None)

class TestMd5CheckerMd5cmpFiles(unittest.TestCase):
    """Tests for the 'md5cmp_files' method of the Md5Checker class

    """
    def setUp(self):
        """Build directory with test data
        """
        self.example_dir = ExampleDirSpiders()
        self.wd = self.example_dir.create_directory()

    def tearDown(self):
        """Remove directory with test data
        """
        self.example_dir.delete_directory()

    def test_cmp_identical_files(self):
        """Md5Checker.md5cmp_files compare identical files
        """
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.path('spider2.txt')))
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider2.txt'),
                                                 self.example_dir.path('spider.txt')))

    def test_cmp_different_files(self):
        """Md5Checker.md5cmp_files compare different files
        """
        self.assertEqual(Md5Checker.MD5_FAILED,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.path('fly.txt')))
        self.assertEqual(Md5Checker.MD5_FAILED,
                         Md5Checker.md5cmp_files(self.example_dir.path('fly.txt'),
                                                 self.example_dir.path('spider.txt')))

    def test_cmp_missing_reference(self):
        """Md5Checker.md5cmp_files with missing reference file
        """
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('missing.txt'),
                                                 self.example_dir.path('spider.txt')))

    def test_cmp_missing_target(self):
        """Md5Checker.md5cmp_files with missing target file
        """
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.path('missing.txt')))

    def test_cmp_file_and_link(self):
        """Md5Checker.md5cmp_files with a file against a symlink
        """
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.path('itsy-bitsy.txt')))
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('itsy-bitsy.txt'),
                                                 self.example_dir.path('spider.txt')))
        self.assertEqual(Md5Checker.MD5_FAILED,
                         Md5Checker.md5cmp_files(self.example_dir.path('fly.txt'),
                                                 self.example_dir.path('itsy-bitsy.txt')))
        self.assertEqual(Md5Checker.MD5_FAILED,
                         Md5Checker.md5cmp_files(self.example_dir.path('itsy-bitsy.txt'),
                                                 self.example_dir.path('fly.txt')))

    def test_cmp_identical_links(self):
        """Md5Checker.md5cmp_files with symlinks pointing to identical files
        """
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('itsy-bitsy.txt'),
                                                 self.example_dir.path('itsy-bitsy2.txt')))
        self.assertEqual(Md5Checker.MD5_OK,
                         Md5Checker.md5cmp_files(self.example_dir.path('itsy-bitsy2.txt'),
                                                 self.example_dir.path('itsy-bitsy.txt')))

    def test_cmp_broken_link(self):
        """Md5Checker.md5cmp_files with a broken symlink
        """
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.path('broken.txt')))
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('broken.txt'),
                                                 self.example_dir.path('spider.txt')))        

    def test_cmp_identical_broken_links(self):
        """Md5Checker.md5cmp_files with identical broken links
        """
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('broken.txt'),
                                                 self.example_dir.path('broken2.txt')))
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('broken2.txt'),
                                                 self.example_dir.path('broken.txt')))        

    def test_cmp_file_and_directory(self):
        """Md5Checker.md5cmp_files when one 'file' is a directory
        """
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.path('spider.txt'),
                                                 self.example_dir.dirn))
        self.assertEqual(Md5Checker.MD5_ERROR,
                         Md5Checker.md5cmp_files(self.example_dir.dirn,
                                                 self.example_dir.path('spider.txt')))

class TestMd5CheckerWalk(unittest.TestCase):
    """Tests for the 'walk' method of the Md5Checker class

    """
    def setUp(self):
        """Build directory with test data
        """
        self.example_dir = ExampleDirLanguages()
        self.dirn = self.example_dir.create_directory()

    def tearDown(self):
        """Remove directory with test data
        """
        self.example_dir.delete_directory()

    def test_walk(self):
        """Md5Checker.walk yields all files
        """
        # Walk the example directory and check all yielded files
        # are in the list of created files
        file_list = self.example_dir.filelist(include_links=True)
        print(str(file_list))
        for f in Md5Checker.walk(self.dirn):
            print("Check for %s" % f)
            self.assertTrue(f in file_list,"%s not in files or links?" % f)
            file_list.remove(f)
        # Check that no files were missed
        self.assertTrue(len(file_list) == 0,
                        "Some files not yielded: %s" % file_list)

    def test_walk_ignore_links(self):
        """Md5Checker.walk ignores links
        """
        # Walk the example directory and check all yielded files
        # are in the list of created files
        file_list = self.example_dir.filelist(include_links=False)
        for f in Md5Checker.walk(self.dirn,links=Md5Checker.IGNORE_LINKS):
            self.assertTrue(f in file_list,"%s not in files?" % f)
            file_list.remove(f)
        # Check that no files were missed
        self.assertTrue(len(file_list) == 0,
                        "Some files not yielded: %s" % file_list)

    def test_walk_yields_broken_links(self):
        """Md5Checker.walk yields broken links
        """
        # Add broken link
        self.example_dir.add_link("broken.txt","missing.txt")
        # Walk the example directory and check all yielded files
        # are in the list of created files
        file_list = self.example_dir.filelist(include_links=False)
        for f in Md5Checker.walk(self.dirn,links=Md5Checker.IGNORE_LINKS):
            self.assertTrue(f in file_list,"%s not in files?" % f)
            file_list.remove(f)
        # Check that no files were missed
        self.assertTrue(len(file_list) == 0,
                        "Some files not yielded: %s" % file_list)

class TestMd5CheckerMd5cmpDirs(unittest.TestCase):
    """Tests for the 'md5cmp_dirs' method of the Md5Checker class

    """
    def setUp(self):
        """Build directory with test data
        """
        self.dir1 = ExampleDirLanguages()
        self.dir1.create_directory()
        self.dir2 = ExampleDirLanguages()
        self.dir2.create_directory()

    def tearDown(self):
        """Remove directory with test data
        """
        self.dir1.delete_directory()
        self.dir2.delete_directory()

    def test_cmp_identical_dirs(self):
        """Md5Checker.md5cmp_dirs with identical directories
        """
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn):
            self.assertEqual(Md5Checker.MD5_OK,status,
                             "Failed for %s (status %d)" % (f,status))

    def test_cmp_identical_dirs_ignore_links(self):
        """Md5Checker.md5cmp_dirs with identical directories ignoring links
        """
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn,
                                               links=Md5Checker.IGNORE_LINKS):
            self.assertFalse(os.path.islink(os.path.join(self.dir1.dirn,f)))
            self.assertEqual(Md5Checker.MD5_OK,status)

    def test_cmp_different_dirs_missing_file(self):
        """Md5Checker.md5cmp_dirs with different directories (missing file)
        """
        # Add an additional file in reference
        self.dir1.add_file("portuguese/ola","Hello!")
        found_missing = False
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn):
            if f == "portuguese/ola":
                self.assertEqual(Md5Checker.MISSING_TARGET,status)
                found_missing = True
            else:
                self.assertEqual(Md5Checker.MD5_OK,status)
        self.assertTrue(found_missing,"Didn't pick up extra file in reference?")

    def test_cmp_different_dirs_extra_file(self):
        """Md5Checker.md5cmp_dirs with different directories (extra file)
        """
        # Add an additional file in target
        self.dir2.add_file("portuguese/ola","Hello!")
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn):
            if os.path.basename(f) == "portuguese/ola":
                self.assertFaile("Target file 'portuguese/ola' should not be found")
            else:
                self.assertEqual(Md5Checker.MD5_OK,status)

    def test_cmp_different_dirs_different_file(self):
        """Md5Checker.md5cmp_dirs with different directories (different file)
        """
        # Replace file in target with different content
        self.dir2.add_file("goodbye","Goooooodbyeeee!")
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn,
                                               links=Md5Checker.IGNORE_LINKS):
            if os.path.basename(f) == "goodbye":
                self.assertEqual(Md5Checker.MD5_FAILED,status)
            else:
                self.assertEqual(Md5Checker.MD5_OK,status)

    def test_cmp_different_dirs_file_is_dir(self):
        """Md5Checker.md5cmp_dirs with different directories ('file' is dir)
        """
        # Make a file in reference which is same as dir in target
        self.dir1.add_file("portuguese","This is gonna be trouble")
        self.dir2.add_dir("portuguese")
        for f,status in Md5Checker.md5cmp_dirs(self.dir1.dirn,
                                               self.dir2.dirn):
            print("%s: %d" % (f,status))
            if os.path.basename(f) == "portuguese":
                self.assertEqual(Md5Checker.MD5_ERROR,status)
            else:
                self.assertEqual(Md5Checker.MD5_OK,status)

class TestMd5CheckerComputeMd5sms(unittest.TestCase):
    """Tests for the 'compute_md5sums' method of the Md5Checker class

    """
    def setUp(self):
        self.example_dir = ExampleDirLanguages()
        self.example_dir.create_directory()

    def tearDown(self):
        self.example_dir.delete_directory()

    def test_compute_md5dums(self):
        """Md5Checker.compute_md5sums returns correct md5sums

        """
        files = self.example_dir.filelist(include_links=True,full_path=False)
        for f,md5 in Md5Checker.compute_md5sums(self.example_dir.dirn,
                                                links=Md5Checker.FOLLOW_LINKS):
            self.assertTrue(f in files)
            self.assertEqual(md5,self.example_dir.checksum_for_file(f))

    def test_compute_md5sums_ignore_links(self):
        """Md5Checker.compute_md5sums ignores links

        """
        files = self.example_dir.filelist(include_links=False,full_path=False)
        for f,md5 in Md5Checker.compute_md5sums(self.example_dir.dirn,
                                                links=Md5Checker.IGNORE_LINKS):
            self.assertTrue(f in files)
            self.assertEqual(md5,self.example_dir.checksum_for_file(f))

    def test_compute_md5sums_handle_broken_links(self):
        """Md5Checker.compute_md5sums handles broken links

        """
        # Add a broken link
        self.example_dir.add_link("broken","missing.txt")
        # Get file list including links
        files = self.example_dir.filelist(include_links=True,full_path=False)
        # Check checksums
        for f,md5 in Md5Checker.compute_md5sums(self.example_dir.dirn):
            self.assertTrue(f in files,"%s doesn't appear in file list?" % f)
            self.assertEqual(md5,self.example_dir.checksum_for_file(f))

class TestMd5CheckerVerifyMd5sms(unittest.TestCase):
    """Tests for the 'verify_md5sums' method of the Md5Checker class

    """
    def setUp(self):
        self.example_dir = ExampleDirLanguages()
        self.example_dir.create_directory()

    def tearDown(self):
        self.example_dir.delete_directory()

    def test_verify_md5sums(self):
        """Md5Checker.verify_md5sums checks 'md5sum'-format file

        """
        # Create MD5sum 'file'
        md5sums = []
        for f in self.example_dir.filelist(full_path=True):
            md5sums.append(u"%s  %s" % (md5sum(f),f))
        md5sums = '\n'.join(md5sums)
        fp = io.StringIO(md5sums)
        # Run verification
        files = self.example_dir.filelist(full_path=True)
        self.assertNotEqual(len(files),0)
        for f,status in Md5Checker.verify_md5sums(fp=fp):
            self.assertTrue(f in files,"%s not in %s" % (f,files))
            self.assertEqual(status,Md5Checker.MD5_OK)
            files.remove(f)
        # Check no files were missed
        self.assertEqual(len(files),0)

class TestMd5CheckReporter(unittest.TestCase):
    """Test the Md5CheckReporter class

    """
    def test_empty_md5checkreporter(self):
        """Md5CheckReporter with no input has correct counts

        """
        reporter = Md5CheckReporter()
        self.assertEqual(reporter.n_files,0)
        self.assertEqual(reporter.n_ok,0)
        self.assertEqual(reporter.n_failed,0)
        self.assertEqual(reporter.n_errors,0)
        self.assertEqual(reporter.n_missing,0)
        self.assertEqual(reporter.status,0)

    def test_md5checkreporter_add_result(self):
        """Md5CheckReporter.add_result has correct counts

        """
        reporter = Md5CheckReporter()
        reporter.add_result('hello.txt',Md5Checker.MD5_OK)
        reporter.add_result('goodbye.txt',Md5Checker.MD5_OK)
        self.assertEqual(reporter.n_files,2)
        self.assertEqual(reporter.n_ok,2)
        self.assertEqual(reporter.n_failed,0)
        self.assertEqual(reporter.n_errors,0)
        self.assertEqual(reporter.n_missing,0)
        self.assertEqual(reporter.status,0)
        reporter.add_result('different.txt',Md5Checker.MD5_FAILED)
        self.assertEqual(reporter.n_files,3)
        self.assertEqual(reporter.n_ok,2)
        self.assertEqual(reporter.n_failed,1)
        self.assertEqual(reporter.n_errors,0)
        self.assertEqual(reporter.n_missing,0)
        self.assertEqual(reporter.status,1)
        reporter.add_result('missing.txt',Md5Checker.MISSING_TARGET)
        reporter.add_result('another_missing.txt',Md5Checker.MISSING_TARGET)
        self.assertEqual(reporter.n_files,5)
        self.assertEqual(reporter.n_ok,2)
        self.assertEqual(reporter.n_failed,1)
        self.assertEqual(reporter.n_errors,0)
        self.assertEqual(reporter.n_missing,2)
        self.assertEqual(reporter.status,1)
        reporter.add_result('bad.txt',Md5Checker.MD5_ERROR)
        self.assertEqual(reporter.n_files,6)
        self.assertEqual(reporter.n_ok,2)
        self.assertEqual(reporter.n_failed,1)
        self.assertEqual(reporter.n_errors,1)
        self.assertEqual(reporter.n_missing,2)
        self.assertEqual(reporter.status,1)

    def test_md5reporter_load_results_on_init(self):
        """Md5CheckReporter processes results supplied via init

        """
        reporter = Md5CheckReporter(
            (('hello.txt',Md5Checker.MD5_OK),
             ('goodbye.txt',Md5Checker.MD5_OK),
             ('different.txt',Md5Checker.MD5_FAILED),
             ('missing.txt',Md5Checker.MISSING_TARGET),
             ('another_missing.txt',Md5Checker.MISSING_TARGET),
             ('bad.txt',Md5Checker.MD5_ERROR),
            ))
        self.assertEqual(reporter.n_files,6)
        self.assertEqual(reporter.n_ok,2)
        self.assertEqual(reporter.n_failed,1)
        self.assertEqual(reporter.n_errors,1)
        self.assertEqual(reporter.n_missing,2)
        self.assertEqual(reporter.status,1)

    def test_md5reporter_bad_code_raises_exception(self):
        """Md5CheckReporter raises an exception for unrecognised result code

        """
        reporter = Md5CheckReporter()
        self.assertRaises(Exception,reporter.add_result,'hello.txt',1.01)

    def test_md5reporter_file_output(self):
        """Md5CheckReporter output to file is correct

        """
        fp = io.StringIO()
        reporter = Md5CheckReporter(
            (('hello.txt',Md5Checker.MD5_OK),
             ('goodbye.txt',Md5Checker.MD5_OK),
             ('different.txt',Md5Checker.MD5_FAILED),
             ('missing.txt',Md5Checker.MISSING_TARGET),
             ('another_missing.txt',Md5Checker.MISSING_TARGET),
             ('bad.txt',Md5Checker.MD5_ERROR),
            ),fp=fp,verbose=False)  
        self.assertEqual(fp.getvalue(),"""different.txt: FAILED
missing.txt: MISSING
another_missing.txt: MISSING
bad.txt: ERROR
""")

    def test_md5reporter_verbose_file_output(self):
        """Md5CheckReporter verbose output to file is correct

        """
        fp = io.StringIO()
        reporter = Md5CheckReporter(
            (('hello.txt',Md5Checker.MD5_OK),
             ('goodbye.txt',Md5Checker.MD5_OK),
             ('different.txt',Md5Checker.MD5_FAILED),
             ('missing.txt',Md5Checker.MISSING_TARGET),
             ('another_missing.txt',Md5Checker.MISSING_TARGET),
             ('bad.txt',Md5Checker.MD5_ERROR),
            ),fp=fp,verbose=True)
        self.assertEqual(fp.getvalue(),"""hello.txt: OK
goodbye.txt: OK
different.txt: FAILED
missing.txt: MISSING
another_missing.txt: MISSING
bad.txt: ERROR
""")

    def test_md5reporter_summary_output(self):
        """Md5CheckReporter summary output is correct

        """
        fp = io.StringIO()
        reporter = Md5CheckReporter(
            (('hello.txt',Md5Checker.MD5_OK),
             ('goodbye.txt',Md5Checker.MD5_OK),
             ('different.txt',Md5Checker.MD5_FAILED),
             ('missing.txt',Md5Checker.MISSING_TARGET),
             ('another_missing.txt',Md5Checker.MISSING_TARGET),
             ('bad.txt',Md5Checker.MD5_ERROR),
            ),fp=fp,verbose=False)
        reporter.summary()
        self.assertEqual(fp.getvalue(),"""different.txt: FAILED
missing.txt: MISSING
another_missing.txt: MISSING
bad.txt: ERROR
Summary:
\t6 files checked
\t2 okay
\t1 failed
\t2 not found
\t1 'bad' files (MD5 computation errors)
""")
        
########################################################################
# Main: test runner
#########################################################################
if __name__ == "__main__":
    # Run tests
    unittest.main()
