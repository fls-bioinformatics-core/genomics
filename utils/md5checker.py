#!/bin/env python
#
#     md5checker.py: check files and directories using md5 checksums
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# md5checker.py
#
#########################################################################

"""md5checker

Utilities for checking files and directories using md5 checksums.
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.3.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse
import logging
# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import Md5sum

#######################################################################
# Classes
#######################################################################

class Md5Checker:
    """Provides static methods for performing checks using MD5 sums

    The Md5Checker class is a collection of static methods that can
    be used for performing checks using MD5 sums.

    It also provides a set of constants to

    """
    # Class constants representing check results
    MD5_OK=0
    MD5_FAILED=1
    MD5_ERROR=2
    MISSING_SOURCE=3
    MISSING_TARGET=4
    LINKS_SAME=5
    LINKS_DIFFER=6
    TYPES_DIFFER=7
    # Class constants representing link handling
    FOLLOW_LINKS=0
    IGNORE_LINKS=1

    @classmethod
    def walk(self,dirn,links=FOLLOW_LINKS):
        """Traverse all files found in a directory structure

        Given a directory, traverses the structure underneath (including
        subdirectories) and yields the path for each file that is
        found.

        How symbolic links are handled depends on the setting of the
        'links' option:

        FOLLOW_LINKS: symbolic links to files are treated as files; links
                      to directories are followed.
        IGNORE_LINKS: symbolic links to files are ignored; links to
                      directories are not followed.

        Arguments:
          dirn: name of the top-level directory
          links: (optional) specify how symbolic links are handled

        Returns:
          Yields the name and full path for each file under 'dirn'.
          
        """
        for d in os.walk(dirn):
            if os.path.islink(d[0]) and links != self.FOLLOW_LINKS:
                continue
            for f in d[2]:
                path = os.path.join(d[0],f)
                if os.path.islink(path) and links != self.FOLLOW_LINKS:
                    continue
                else:
                    yield os.path.normpath(path)

    @classmethod
    def md5_walk(self,dirn,links=FOLLOW_LINKS):
        """Calculate MD5 sums for all files in directory

        Given a directory, traverses the structure underneath (including
        subdirectories) and yields the path and MD5 sum for each file that
        is found.

        The 'links' option determines how symbolic links are handled, see
        the 'walk' function for details.

        Arguments:
          dirn: name of the top-level directory
          links: (optional) specify how symbolic links are handled

        Returns:
          Yields a tuple (f,md5) where f is the path of a file relative to
          the top-level directory, and md5 is the calculated MD5 sum.

        """
        for f in self.walk(dirn,links=links):
            yield (os.path.relpath(f,dirn),Md5sum.md5sum(f))

    @classmethod
    def md5cmp_files(self,f1,f2):
        """Compares the MD5 sums of two files 

        Given two file names, attempts to compute and compare their
        MD5 sums.

        If the MD5s match then returns MD5_OK, if they don't match
        then returns MD5_FAILED.

        If one or both MD5 sums cannot be computed then returns
        MD5_ERROR.

        Note that if either file is a link then MD5 sums will be
        computed for the link target(s), if they exist and can be
        accessed.
        
        Arguments:
          f1: name and path for reference file
          f2: name and path for file to be checked

        Returns:
          Md5Checker constant representing the outcome of the
          comparison.

        """
        # Compute and compare MD5 sums
        try:
            if Md5sum.md5sum(f1) == Md5sum.md5sum(f2):
                status = self.MD5_OK
            else:
                status = self.MD5_FAILED
        except IOError, ex:
            # Error accessing one or both files
            logging.error("%s: error while generating MD5 sums: '%s'" % (f1,ex))
            status = self.MD5_ERROR
        return status

    @classmethod
    def md5cmp_dirs(self,d1,d2,links=FOLLOW_LINKS):
        """Compares the contents of one directory with another using MD5 sums

        Given two directory names 'd1' and 'd2', compares the MD5 sum of
        each file found in 'd1' against that of the equivalent file in 'd2',
        and yields the result as an Md5checker constant for each file pair,
        i.e.:
        
        MD5_OK:     if MD5 sums match;
        MD5_FAILED: if MD5 sums differ.

        If the equivalent file doesn't exist then yields MISSING_TARGET.

        If one or both MD5 sums cannot be computed then yields MD5_ERROR.

        How symbolic links are handled depends on the setting of the 'links'
        option:

        FOLLOW_LINKS: (default) MD5 sums are computed and compared for
                      the targets of symbolic links. Broken links are
                      treated as if the file was missing.
        IGNORE_LINKS: MD5 sums are not computed or compared if either file
                      is a symbolic link, and links to directories are
                      not followed.

        Arguments:
          d1: 'reference' directory
          d2: 'target' directory to be compared with the reference
          links: (optional) specify how symbolic links are handled.

        Returns:
          Yields a tuple (f,status) where f is the relative path of the
          file pair being compared, and status is the Md5Checker constant
          representing the outcome of the comparison.

        """
        for f1 in self.walk(d1,links=links):
            f2 = os.path.join(d2,os.path.relpath(f1,d1))
            if not os.path.exists(f2):
                result = self.MISSING_TARGET
            else:
                try:
                    result = self.md5cmp_files(f1,f2)
                except Exception,ex:
                    logging.debug("Failed to compute one or both checksums:")
                    logging.debug("Reference file: %s" % f1)
                    logging.debug("Target file   : %s" % f2)
                    logging.debug("Exception     : %s" % ex)
                    result = self.MD5_ERROR
            yield (os.path.relpath(f1,d1),result)

    @classmethod
    def compute_md5sums(self,d,links=FOLLOW_LINKS):
        """Calculate MD5 sums for all files in directory

        Given a directory, traverses the structure underneath (including
        subdirectories) and yields the path and MD5 sum for each file that
        is found.

        The 'links' option determines how symbolic links are handled, see
        the 'walk' function for details.

        Arguments:
          dirn: name of the top-level directory
          links: (optional) specify how symbolic links are handled

        Returns:
          Yields a tuple (f,md5) where f is the path of a file relative to
          the top-level directory, and md5 is the calculated MD5 sum.

        """
        for f in self.walk(d,links=links):
            yield (os.path.relpath(f,d),Md5sum.md5sum(f))

    @classmethod
    def verify_md5sums(self,filen=None,fp=None):
        """Verify md5sums from a file

        Given a file (or a file-like object opened for reading), reads
        each line and attemps to interpret as an md5sum line i.e. of
        the form

        <md5 sum>  <path/to/file>

        e.g.

        66b201ae074c36ae9bffec7fb74ff03a  md5checker.py

        It then attempts to verify the MD5 sum against the file located
        on the file system, and yields the result as an Md5checker constant
        for each file line i.e.:
        
        MD5_OK:     if MD5 sums match;
        MD5_FAILED: if MD5 sums differ.

        If the file cannot be found then it yields MISSING_TARGET; if
        there is a problem computing the MD5 sum then it yields
        MD5_ERROR.

        Arguments:
          filen: name of the file containing md5sum output
          fp   : file-like object opened for reading, with md5sum output

        Returns:
          Yields a tuple (f,status) where f is the path of the file being
          verified (as it appears in the file), and status is the Md5Checker
          constant representing the outcome.

        """
        if fp is not None:
            filen=None
        else:
            fp = open(filen,'rU')
        for line in fp:
            items = line.strip().split()
            if len(items) < 2:
                raise IndexError,"Bad MD5 sum line: %s" % line.rstrip('\n')
            chksum = items[0]
            f = line[len(chksum):].strip()
            try:
                if not os.path.exists(f):
                    status = self.MISSING_TARGET
                elif Md5sum.md5sum(f) == chksum:
                    status = self.MD5_OK
                else:
                    status = self.MD5_FAILED
            except IOError, ex:
                # Error accessing file
                logging.error("%s: error while generating MD5 sum: '%s'" % (f,ex))
                status = self.MD5_ERROR
            yield (f,status)

class Md5CheckReporter:
    """Provides a generic reporting class for Md5Checker methods

    Typical usage modes are either:

    >>> r = Md5CheckReporter()
    >>> for f,s in Md5Checker.md5cmp_dirs(d1,d2):
    ...    r.add_result(f,s)

    or more concisely:

    >>> r = Md5CheckReporter(Md5Checker.md5cmp_dirs(d1,d2))

    Use the 'summary' method to generate a summary of all the checks.

    Use the 'status' method to get a single indicator of success or
    failure which is consistent with UNIX-style return codes.

    To find out how many results were processed in total, how many
    failed etc use the following properties:

    n_files  : total number of results examined
    n_ok     : number that passed MD5 checks (MD5_OK)
    n_failed : number that failed due to different MD5 sums (MD5_FAILED)
    n_missing: number that failed due to a missing target file
               (MISSING_TARGET)
    n_errors : number that had errors calculating their MD5 sums
               (MD5 ERROR)

    """
    def __init__(self,results=None,verbose=False,fp=sys.stdout):
        """Create a new Md5CheckReporter instance

        Arguments:
          results: a list or iterable of tuples (f,s) where f is a
            file name and s is an Md5Checker status code
          verbose: if True then report the results of all checks;
            otherwise only report failures (default)
          fp: specify a file-like object to write messages to. Must
            already be opened for writing (defaults to sys.stdout)

        """
        self._verbose = verbose
        self._fp = fp
        self._n_files = 0
        self._md5_failed = []
        self._md5_error = []
        self._missing_target = []
        if results is not None:
            for result in results:
                self.add_result(result[0],result[1])

    @property
    def n_files(self):
        """Total number of files checked
        """
        return self._n_files

    @property
    def n_ok(self):
        """Number of passed MD5 sum checks
        """
        return self.n_files - self.n_failed - self.n_errors - self.n_missing

    @property
    def n_failed(self):
        """Number of failed MD5 sum checks
        """
        return len(self._md5_failed)

    @property
    def n_errors(self):
        """Number of files with errors checking MD5 sums
        """
        return len(self._md5_error)

    @property
    def n_missing(self):
        """Number of missing files
        """
        return len(self._missing_target)

    def add_result(self,f,status):
        """Add a result to the reporter

        Takes a file and an Md5Checker status code and adds
        it to the results.

        If the status code indicates a failed check then the
        file name is added to a list corresponding to the
        nature of the failure (e.g. MD5 sums didn't match,
        target was missing etc).

        """
        self._n_files += 1
        if status == Md5Checker.MD5_OK:
            status_msg = "OK"
            if self._verbose:
                self._fp.write("%s: %s\n" % (f,status_msg))
        else:
            if status == Md5Checker.MD5_FAILED:
                status_msg = "FAILED"
                self._md5_failed.append(f)
            elif status == Md5Checker.MISSING_TARGET:
                status_msg = "MISSING"
                self._missing_target.append(f)
            elif status == Md5Checker.MD5_ERROR:
                status_msg = "ERROR"
                self._md5_error.append(f)
            else:
                # Unrecognised code
                raise Exception, "Unrecognised status: '%s'" % status
            self._fp.write("%s: %s\n" % (f,status_msg))

    def summary(self):
        """Print a summary of the results

        Prints a summary of the number of files checked, how many passed
        or failed MD5 checks and so on.

        """
        self._fp.write("Summary:\n")
        self._fp.write("\t%d files checked\n" % self.n_files)
        self._fp.write("\t%d okay\n" % self.n_ok)
        self._fp.write("\t%d failed\n" % self.n_failed)
        self._fp.write("\t%d not found\n" % self.n_missing)
        self._fp.write("\t%d 'bad' files (MD5 computation errors)\n" % self.n_errors)

    @property
    def status(self):
        """Return status code

        Returns 0 if all files that were checked passed the MD5 check, or
        1 if at least one file failed the check for whatever reason.

        """
        if self.n_files == self.n_ok:
            return 0
        else:
            return 1

#######################################################################
# Functions
#######################################################################

def compute_md5sums(dirn,output_file=None,relative=False):
    """Compute and write MD5 sums for all files in a directory

    Walks the directory tree under the specified directory and
    computes the MD5 for each file it finds. The sums are written
    along with the names of the files either to stdout or to the
    specified file name.

    Note that the output format is compatible with the Linux
    'md5sum' program's '-c' option.

    Arguments:
      dirn: directory to run the MD5 sum computation on
      output_file: (optional) name of file to write MD5 sums to
      relative: if True then output file paths relative to
        the supplied directory (otherwise write absolute paths)

    Returns:
      Zero on success, 1 if errors were encountered
    """
    retval = 0
    if output_file:
        fp = open(output_file,'w')
    else:
        fp = sys.stdout
    for filen,chksum in Md5Checker.compute_md5sums(dirn):
        if not relative:
            filen = os.path.join(dirn,filen)
        fp.write("%s  %s\n" % (chksum,filen))
    if output_file:
        fp.close()
    return retval

def compute_md5sum_for_file(filen,output_file=None):
    """Compute and write MD5 sum for specifed file

    Computes the MD5 sum for a file, and writes the sum and the file
    name either to stdout or to the specified file name.

    Note that the output format is compatible with the Linux
    'md5sum' program's '-c' option.

    Arguments:
      filen: file to compute the MD5 sum for
      output_file: (optional) name of file to write MD5 sum to

    Returns:
      Zero on success, 1 if errors were encountered

    """
    retval = 1
    if output_file:
        fp = open(output_file,'w')
    else:
        fp = sys.stdout
    try:
        chksum = Md5sum.md5sum(filen)
        fp.write("%s  %s\n" % (chksum,filen))
    except IOError, ex:
        # Error accessing file, report and skip
        logging.error("%s: error while generating MD5 sum: '%s'" % (filen,ex))
        retval = 1
    if output_file:
        fp.close()
    return retval

def verify_md5sums(chksum_file,verbose=False):
    """Check the MD5 sums for all entries specified in a file

    For all entries in the supplied file, check the MD5 sum is
    the same as that calculated by the function, and report
    whether they match or are different.

    The input file can either be output from this program or
    from the Linux 'md5sum' program.

    Arguments:
      chksum_file: name of the file containing the MD5 sums
      verbose: (optional) if True then report status for all
        files checked, plus a summary; otherwise only report
        failures

    Returns:
      Zero on success, 1 if errors were encountered

    """
    # Set up reporter object
    reporter = Md5CheckReporter(Md5Checker.verify_md5sums(chksum_file),
                                verbose=verbose)
    # Summarise
    if verbose: reporter.summary()
    return reporter.status

def diff_directories(dirn1,dirn2,verbose=False):
    """Check one directory against another using MD5 sums

    This compares one directory against another by computing the
    MD5 sums for the contents of the first, and then checking these
    against the second.

    (Essentially this is automatically performing the compute/verify
    steps in a single operation.)

    Note that if there are different files in one directory compared
    with the other then this function will give different results
    depending on the order the directories are specified. However
    for common files the actual MD5 sums will be the same regardless
    of order.

    Arguments:
      dirn1: "source" directory
      dirn2: "target" directory to be compared to dirn1
      verbose: (optional) if True then report status for all
        files checked; otherwise only report summary

    Returns:
      Zero on success, 1 if errors were encountered

    """
    # Set up reporter object
    reporter = Md5CheckReporter(Md5Checker.md5cmp_dirs(dirn1,dirn2),
                                verbose=verbose)
    # Summarise
    if verbose: reporter.summary()
    return reporter.status

def diff_files(filen1,filen2,verbose=False):
    """Check that the MD5 sums of two files match

    This compares two files by computing the MD5 sums for each.

    Arguments:
      filen1: "source" file
      filen2: "target" file to be compared with filen1
      verbose: (optional) if True then report status for all
        files checked; otherwise only report summary

    Returns:
      Zero on success, 1 if errors were encountered

    """
    # Set up reporter object
    reporter = Md5CheckReporter()
    # Compare files
    reporter.add_result(filen1,Md5Checker.md5cmp_files(filen1,filen2))
    if verbose:
        if reporter.n_ok:
            print "OK: MD5 sums match"
        elif reporer.n_failed:
            print "FAILED: MD5 sums don't match"
        else:
            print "ERROR: unable to compute one or both MD5 sums"
    return reporter.status

def report(msg,verbose=False):
    """Write text to stdout

    Convenience function for dealing with verbose/silent modes of
    operation: rhe supplied text in 'msg' is only written if the verbose
    argument is set to True.
    """
    if verbose: print "%s" % (msg)

#######################################################################
# Tests
#######################################################################
import unittest
import tempfile
import shutil
import copy
import cStringIO
import bcf_utils

class TestUtils:
    """Utilities to help with setting up/running tests etc

    """
    @classmethod
    def make_file(self,filename,text,basedir=None):
        """Create test file
        
        """
        if filename is None:
            # mkstemp returns a tuple
            tmpfile = tempfile.mkstemp(dir=basedir,text=True)
            filename = tmpfile[1]
        elif basedir is not None:
            filename = os.path.join(basedir,filename)
        fp = open(filename,'w')
        fp.write(text)
        fp.close()
        return filename

    @classmethod
    def make_dir(self,dirname=None):
        """Create test directory
        
        """
        if dirname is None:
            dirname = tempfile.mkdtemp()
        else:
            os.mkdir(dirname)
        return dirname

    @classmethod
    def make_sub_dir(self,basedir,dirname):
        """Create a subdirectory in an existing directory
        
        """
        subdir = os.path.join(basedir,dirname)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        return subdir

    @classmethod
    def make_sym_link(self,target,link_name=None,basedir=None):
        """Create a symbolic link

        """
        if link_name is None:
            link_name = os.path.basename(target)
        if basedir is not None:
            link_name = os.path.join(basedir,link_name)
        os.symlink(target,link_name)
        return link_name

# Base class for making test data directories
class BaseExampleDir:
    """Base class for making test data directories

    Create, populate and destroy directory with test data.

    Typically you should subclass the BaseExampleDir and then
    use method calls to add files, links and directories. For
    example:

    >>> class MyExampleDir(BaseExampleDir):
    >>>    def __init__(self):
    >>>       BaseExampleDir.__init__(self)
    >>>       self.add_file("Test","This is a test file")
    >>>

    Then to use in a program:

    >>> d = MyExampleDir()
    >>> d.create_directory()
    >>> # do stuff
    >>> d.delete_directory()

    """

    def __init__(self):
        self.dirn = None
        self.files = []
        self.content = {}
        self.links = []
        self.targets = {}
        self.dirs = []

    def add_dir(self,path):
        if path not in self.dirs:
            self.dirs.append(path)
            if self.dirn is not None:
                TestUtils.make_sub_dir(self.dirn,path)

    def add_file(self,path,content=''):
        self.files.append(path)
        self.content[path] = content
        self.add_dir(os.path.dirname(path))
        if self.dirn is not None:
            TestUtils.make_file(path,self.content[path],basedir=self.dirn)

    def add_link(self,path,target=None):
        self.links.append(path)
        self.targets[path] = target
        self.add_dir(os.path.dirname(path))
        if self.dirn is not None:
            TestUtils.make_sym_link(self.targets[path],path,basedir=self.dirn)

    def path(self,filen):
        if self.dirn is not None:
            return os.path.join(self.dirn,filen)
        else:
            return filen

    def filelist(self,include_links=True,full_path=True):
        filelist = copy.copy(self.files)
        if include_links:
            for link in self.links:
                resolved_link = os.path.join(os.path.dirname(self.path(link)),
                                             os.readlink(self.path(link)))
                if not os.path.isdir(resolved_link):
                    filelist.append(link)
        filelist.sort()
        if full_path:
            filelist = [self.path(x) for x in filelist]
        return filelist

    def create_directory(self):
        self.dirn = TestUtils.make_dir()
        for d in self.dirs:
            TestUtils.make_sub_dir(self.dirn,d)
        for f in self.files:
            TestUtils.make_file(f,self.content[f],basedir=self.dirn)
        for l in self.links:
            TestUtils.make_sym_link(self.targets[l],l,basedir=self.dirn)
        return self.dirn

    def delete_directory(self):
        if self.dirn is not None:
            shutil.rmtree(self.dirn)
            self.dirn = None

    def checksum_for_file(self,path):
        """
        """
        return Md5sum.md5sum(self.path(path))

class ExampleDir0(BaseExampleDir):
    """Small test data directory with files and subdirectories

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        self.add_file("test.txt","This is a test file")
        self.add_file("fred/test.txt","This is another test file")
        self.add_file("daphne/test.txt","This is another test file")
        self.add_file("thelma/test.txt","This is another test file")
        self.add_file("shaggy/test.txt","This is another test file")
        self.add_file("scooby/test.txt","This is another test file")

class ExampleDir1(BaseExampleDir):
    """Small test data directory with files and links

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        # Files
        self.add_file("spider.txt","The itsy-bitsy spider\nClimbed up the chimney spout")
        self.add_file("spider2.txt","The itsy-bitsy spider\nClimbed up the chimney spout")
        self.add_file("fly.txt","'Come into my parlour'\nSaid the spider to the fly")
        # Symbolic links
        self.add_link("itsy-bitsy.txt","spider.txt")
        self.add_link("itsy-bitsy2.txt","spider2.txt")
        # Broken links
        self.add_link("broken.txt","missing.txt")
        self.add_link("broken2.txt","missing.txt")

class ExampleDir2(BaseExampleDir):
    """Test data directory with more complicated structure and linking

    """
    def __init__(self):
        BaseExampleDir.__init__(self)
        # Files
        self.add_file("hello","Hello!")
        self.add_file("goodbye","Goodbye!")
        self.add_file("spanish/hola","Hello!")
        self.add_file("spanish/adios","Goodbye!")
        self.add_file("welsh/north_wales/maen_ddrwg_gen_i","Sorry!")
        self.add_file("welsh/south_wales/maen_flin_da_fi","Sorry!")
        self.add_file("icelandic/takk_fyrir","Thank you!")
        # Symbolic links
        self.add_link("hi","hello")
        self.add_link("bye","goodbye")
        self.add_dir("countries")
        self.add_link("countries/spain","../spanish")
        self.add_link("countries/north_wales","../welsh/north_wales")
        self.add_link("countries/south_wales","../welsh/south_wales")
        self.add_link("countries/iceland","../icelandic")

class TestMd5CheckerMd5cmpFiles(unittest.TestCase):
    """Tests for the 'md5cmp_files' method of the Md5Checker class

    """
    def setUp(self):
        """Build directory with test data
        """
        self.example_dir = ExampleDir1()
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
        self.example_dir = ExampleDir2()
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
        print str(file_list)
        for f in Md5Checker.walk(self.dirn):
            print "Check for %s" % f
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
        self.dir1 = ExampleDir2()
        self.dir1.create_directory()
        self.dir2 = ExampleDir2()
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
            print "%s: %d" % (f,status)
            if os.path.basename(f) == "portuguese":
                self.assertEqual(Md5Checker.MD5_ERROR,status)
            else:
                self.assertEqual(Md5Checker.MD5_OK,status)

class TestMd5CheckerComputeMd5sms(unittest.TestCase):
    """Tests for the 'compute_md5sums' method of the Md5Checker class

    """
    def setUp(self):
        self.example_dir = ExampleDir2()
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

    def test_compute_md5dums_ignore_links(self):
        """Md5Checker.compute_md5sums ignores links

        """
        files = self.example_dir.filelist(include_links=False,full_path=False)
        for f,md5 in Md5Checker.compute_md5sums(self.example_dir.dirn,
                                                links=Md5Checker.IGNORE_LINKS):
            self.assertTrue(f in files)
            self.assertEqual(md5,self.example_dir.checksum_for_file(f))

class TestMd5CheckerVerifyMd5sms(unittest.TestCase):
    """Tests for the 'verify_md5sums' method of the Md5Checker class

    """
    def setUp(self):
        self.example_dir = ExampleDir2()
        self.example_dir.create_directory()

    def tearDown(self):
        self.example_dir.delete_directory()

    def test_verify_md5sums(self):
        """Md5Checker.verify_md5sums checks 'md5sum'-format file

        """
        # Create MD5sum 'file'
        md5sums = []
        for f in self.example_dir.filelist(full_path=True):
            md5sums.append("%s  %s" % (Md5sum.md5sum(f),f))
        md5sums = '\n'.join(md5sums)
        fp = cStringIO.StringIO(md5sums)
        # Run verification
        files = self.example_dir.filelist(full_path=True)
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
        fp = cStringIO.StringIO()
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
        fp = cStringIO.StringIO()
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
        fp = cStringIO.StringIO()
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

class TestMd5sums(unittest.TestCase):
    """Test computing and verifying MD5 sums via files

    """
    def setUp(self):
        # Create and populate test directory
        self.dir = ExampleDir0()
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
        self.dir1 = ExampleDir0()
        self.dir2 = ExampleDir0()
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

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    usage = """
  %prog -d SOURCE_DIR DEST_DIR
  %prog -d FILE1 FILE2
  %prog [ -o CHKSUM_FILE ] DIR
  %prog [ -o CHKSUM_FILE ] FILE
  %prog -c CHKSUM_FILE"""
    p = optparse.OptionParser(usage=usage,
                              version="%prog "+__version__,
                              description=
                              "Compute and verify MD5 checksums for files and directories.")

    # Define options
    p.add_option('-d','--diff',action="store_true",dest="diff",default=False,
                 help="for two directories: check that contents of directory DIR1 are present "
                 "in DIR2 and have the same MD5 sums; for two files: check that FILE1 and FILE2 "
                 "have the same MD5 sums")
    p.add_option('-c','--check',action="store_true",dest="check",default=False,
                 help="read MD5 sums from the specified file and check them")
    p.add_option('-q','--quiet',action="store_false",dest="verbose",default=True,
                 help="suppress output messages and only report failures")

    # Directory differencing
    group = optparse.OptionGroup(p,"Directory comparison (-d, --diff)",
                                 "Check that the contents of SOURCE_DIR are present in "
                                 "TARGET_DIR and have matching MD5 sums. Note that files that "
                                 "are only present in TARGET_DIR are not reported.")
    p.add_option_group(group)

    # File differencing
    group = optparse.OptionGroup(p,"File comparison (-d, --diff)",
                                 "Check that FILE1 and FILE2 have matching MD5 sums.")
    p.add_option_group(group)

    # Checksum generation
    group = optparse.OptionGroup(p,"Checksum generation",
                                 "MD5 checksums are calcuated for all files in the specified "
                                 "directory, or for a single specified file.")
    group.add_option('-o','--output',action="store",dest="chksum_file",default=None,
                     help="optionally write computed MD5 sums to CHKSUM_FILE (otherwise the "
                     "sums are written to stdout). The output format is the same as that used "
                     "by the Linux 'md5sum' tool.")
    p.add_option_group(group)

    # Checksum verification
    group = optparse.OptionGroup(p,"Checksum verification (-c, --check)",
                                 "Check MD5 sums for each of the files listed in the "
                                 "specified CHKSUM_FILE relative to the current directory. "
                                 "This option behaves the same as the Linux 'md5sum' tool.")
    p.add_option_group(group)

    # Testing
    group = optparse.OptionGroup(p,"Testing")
    group.add_option('--test',action="store_true",dest="run_tests",default=False,
                     help="run unit tests")
    p.add_option_group(group)

    # Process the command line
    options,arguments = p.parse_args()

    # Set up logging output
    logging.basicConfig(format='%(message)s')

    # Unit tests
    if options.run_tests:
        print "Running unit tests"
        logging.getLogger().setLevel(logging.CRITICAL)
        suite = unittest.TestSuite(unittest.TestLoader().\
                                       discover(os.path.dirname(sys.argv[0]), \
                                                    pattern=os.path.basename(sys.argv[0])))
        unittest.TextTestRunner(verbosity=2).run(suite)
        print "Tests finished"
        sys.exit()

    # Figure out mode of operation
    if options.check:
        # Running in "check" mode
        if len(arguments) != 1:
            p.error("-c: needs single argument (file containing MD5 sums)")
        chksum_file = arguments[0]
        if not os.path.isfile(chksum_file):
            p.error("Checksum '%s' file not found (or is not a file)" % chksum_file)
        # Do the verification
        status = verify_md5sums(chksum_file,verbose=options.verbose)
    elif options.diff:
        # Running in "diff" mode
        if len(arguments) != 2:
            p.error("-d: takes two arguments but got %s: %s"
                    % (len(arguments),arguments))
        # Get directories/files as absolute paths
        source = os.path.abspath(arguments[0])
        target = os.path.abspath(arguments[1])
        for arg in (source,target):
            if not os.path.exists(arg):
                p.error("%s: not found" % arg)
        if os.path.isdir(source) and os.path.isdir(target):
            # Compare two directories
            report("Recursively check copies of files in %s against originals in %s" %
                   (target,source),
                   options.verbose)
            status = diff_directories(source,target,verbose=options.verbose)
        elif os.path.isfile(source) and os.path.isfile(target):
            # Compare two files
            report("Checking MD5 sums for %s and %s" % (source,target),options.verbose)
            status = diff_files(source,target,verbose=options.verbose)
        else:
            p.error("Supplied arguments must be a pair of directories or a pair of files")
    else:
        # Running in "compute" mode
        if len(arguments) != 1:
            p.error("Needs a single argument (name of directory to generate MD5 sums for)")
        # Check if output file was specified
        output_file = None
        if options.chksum_file:
            output_file = options.chksum_file
        # Generate the checksums
        if os.path.isdir(arguments[0]):
            status = compute_md5sums(arguments[0],output_file)
        elif os.path.isfile(arguments[0]):
            status = compute_md5sum_for_file(arguments[0],output_file)
        else:
            p.error("Cannot generate checksums for '%s': not a directory or file" % arguments[0])
    # Finish
    sys.exit(status)
