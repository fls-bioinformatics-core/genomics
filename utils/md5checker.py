#!/bin/env python
#
#     md5checker.py: check files and directories using md5 checksums
#     Copyright (C) University of Manchester 2012-2014 Peter Briggs
#
########################################################################
#
# md5checker.py
#
#########################################################################

"""md5checker

Utility for checking files and directories using md5 checksums.

Uses the 'Md5Checker' and 'Md5Reporter' classes from the Md5sum module
to perform the underlying operations.

"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.3.1"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse
import logging
# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.Md5sum as Md5sum

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
    for filen,chksum in Md5sum.Md5Checker.compute_md5sums(dirn):
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
    reporter = Md5sum.Md5CheckReporter(Md5sum.Md5Checker.verify_md5sums(chksum_file),
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
    reporter = Md5sum.Md5CheckReporter(Md5sum.Md5Checker.md5cmp_dirs(dirn1,dirn2),
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
    reporter = Md5sum.Md5CheckReporter()
    # Compare files
    reporter.add_result(filen1,Md5sum.Md5Checker.md5cmp_files(filen1,filen2))
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
from mock_data import TestUtils,ExampleDirScooby

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
