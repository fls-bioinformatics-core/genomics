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

Utility for checking files and directories using md5 checksums.
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.2.1"

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
# Functions
#######################################################################

def compute_md5sums(dirn,output_file=None):
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

    Returns:
      Zero on success, 1 if errors were encountered
    """
    retval = 0
    if output_file:
        fp = open(output_file,'w')
    else:
        fp = sys.stdout
    for d in os.walk(dirn):
        # Calculate md5sum for each file
        for f in d[2]:
            try:
                filen = os.path.normpath(os.path.join(d[0],f))
                chksum = Md5sum.md5sum(filen)
                fp.write("%s  %s\n" % (chksum,filen))
            except IOError, ex:
                # Error accessing file, report and skip
                logging.error("%s: error while generating MD5 sum: '%s'" % (filen,ex))
                logging.error("%s: skipped" % filen)
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
    retval = 0
    nsuccess = 0
    failures = []
    missing = []
    badlines = []
    # Perform the verification
    for line in open(chksum_file,'rU'):
        items = line.strip().split()
        if len(items) < 2:
            logging.error("Unable to read MD5 sum from line (skipped):")
            logging.error("%s" % line)
            badlines.append(line)
            retval = 1
            continue
        chksum = items[0]
        chkfile = line[len(chksum):].strip()
        try:
            new_chksum = Md5sum.md5sum(chkfile)
            if chksum == new_chksum:
                report("%s: OK" % chkfile,verbose)
                nsuccess += 1
            else:
                logging.error("%s: FAILED" % chkfile)
                failures.append(chkfile)
                retval = 1
        except IOError, ex:
            if not os.path.exists(chkfile):
                logging.error("%s: FAILED (file not found)" % chkfile)
                missing.append(chkfile)
            else:
                logging.error("%s: FAILED (%s)" % (chkfile,ex))
                failures.append(chkfile)
            retval = 1
    # Summarise
    nfailed = len(failures)
    nmissing = len(missing)
    nbad = len(badlines)
    report("Summary:",verbose)
    report("\t%d files checked" % (nsuccess + nfailed + nmissing),verbose)
    report("\t%d okay" % nsuccess,verbose)
    report("\t%d failed" % nfailed,verbose)
    report("\t%d not found" % nmissing,verbose) 
    report("\t%d 'bad' MD5 checksum lines" % nbad,verbose)
    return retval

def diff_directories(dirn1,dirn2,verbose=False):
    """Check one directory against another using MD5 sums

    This compares one directory against another by computing the
    MD5 sums for the contents of the first, and then checking these
    against the second.

    (Essentially this is automatically performing the compute/verify
    steps in a single operation.)

    Note that if there are different files in one directory compared
    with the other then this function will give different results
    depending on the order theh directories are specified. However
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
    retval = 0
    nsuccess = 0
    failures = []
    missing = []
    broken = []
    # Iterate over all files in the source directory
    for d in os.walk(dirn1):
        for f in d[2]:
            # Get full paths for source and target files
            filen1 = os.path.normpath(os.path.join(d[0],f))
            filen2 = filen1.replace(dirn1,dirn2,1)
            # Check that source exists
            if not os.path.isfile(filen1):
                logging.error("%s: FAILED (broken file)" % filen1)
                broken.append(filen1)
                retval = 1
            # Check that target exists
            elif not os.path.isfile(filen2):
                logging.error("%s: FAILED (file not found)" % filen2)
                missing.append(filen2)
                retval = 1
            else:
                try:
                    # Calculate and compare MD5 sums
                    chksum1 = Md5sum.md5sum(filen1)
                    chksum2 = Md5sum.md5sum(filen2)
                    if chksum1 == chksum2:
                        report("%s: OK" % filen2,verbose)
                        nsuccess += 1
                    else:
                        logging.error("%s: FAILED" % filen2)
                        failures.append(filen2)
                        retval = 1
                except IOError, ex:
                    # Error accessing one or both files, report and skip
                    logging.error("%s: FAILED" % filen2)
                    logging.error("Error while generating MD5 sums: '%s'" % ex)
                    failures.append(filen2)
                    retval = 1
    # Summarise
    nfailed = len(failures)
    nmissing = len(missing)
    nbroken = len(broken)
    report("Summary:",verbose)
    report("\t%d files checked" % (nsuccess + nfailed + nmissing),verbose)
    report("\t%d okay" % nsuccess,verbose)
    report("\t%d failed" % nfailed,verbose)
    report("\t%d broken files" % nbroken,verbose)
    report("\t%d not found" % nmissing,verbose)
    # Return status
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
    # Generate Md5sum for each file
    retval = 1
    try:
        chksum1 = Md5sum.md5sum(filen1)
        chksum2 = Md5sum.md5sum(filen2)
        if chksum1 == chksum2:
            report("OK: MD5 sums match",verbose)
            retval = 0
        else:
            report("FAILED: MD5 sums don't match",verbose)
    except IOError, ex:
        report("FAILED (%s)" % ex,verbose)
    return retval

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

class TestUtils:
    """Utilities to help with setting up/running tests etc

    """
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

    def make_dir(self,dirname):
        """Create test directory
        
        """
        if dirname is None:
            dirname = tempfile.mkdtemp()
        else:
            os.mkdir(dirname)
        return dirname

    def make_sub_dir(self,basedir,dirname):
        """Create a subdirectory in an existing directory
        
        """
        subdir = os.path.join(basedir,dirname)
        os.mkdir(subdir)
        return subdir

    def make_test_directory(self):
        """Create a template test directory structure

        """
        test_dir = TestUtils().make_dir(None)
        fred = TestUtils().make_sub_dir(test_dir,"fred")
        daphne = TestUtils().make_sub_dir(fred,"daphne")
        thelma = TestUtils().make_sub_dir(test_dir,"thelma")
        shaggy = TestUtils().make_sub_dir(test_dir,"shaggy")
        scooby = TestUtils().make_sub_dir(shaggy,"scooby")
        TestUtils().make_file("test.txt","This is a test file",basedir=test_dir)
        for sub_dir in (fred,daphne,thelma,shaggy,scooby):
            TestUtils().make_file("test.txt","This is another test file",basedir=sub_dir)
        return test_dir

class TestMd5sums(unittest.TestCase):
    """Test computing and verifying MD5 sums via files

    """
    def setUp(self):
        # Create and populate test directory
        self.dir = TestUtils().make_test_directory()
        # Make temporary area for input/ouput checksum files
        self.md5sum_dir = tempfile.mkdtemp()
        self.checksum_file = os.path.join(self.md5sum_dir,"checksums")
        # Reference checksums for test directory
        self.checksums = """0b26e313ed4a7ca6904b0e9369e5b957  test.txt
d0914057907f9d04dd9e68b1c1e180f0  shaggy/test.txt
d0914057907f9d04dd9e68b1c1e180f0  shaggy/scooby/test.txt
d0914057907f9d04dd9e68b1c1e180f0  fred/test.txt
d0914057907f9d04dd9e68b1c1e180f0  fred/daphne/test.txt
d0914057907f9d04dd9e68b1c1e180f0  thelma/test.txt
"""
        # Store current dir and move to top level of test directory
        self.pwd = os.getcwd()
        os.chdir(self.dir)

    def tearDown(self):
        # Move back to original directory
        os.chdir(self.pwd)
        # Clean up test directory and checksum file
        shutil.rmtree(self.dir)
        shutil.rmtree(self.md5sum_dir)

    def test_compute_md5sums(self):
        # Compute md5sums for test directory
        compute_md5sums('.',output_file=self.checksum_file)
        checksums = open(self.checksum_file,'r').read()
        self.assertEqual(self.checksums,checksums)

    def test_verify_md5sums(self):
        # Verify md5sums for test directory
        fp = open(self.checksum_file,'w')
        fp.write(self.checksums)
        fp.close()
        self.assertEqual(verify_md5sums(self.checksum_file),0)

    def test_compute_md5sum_for_file(self):
        # Compute md5sum for a single file
        compute_md5sum_for_file('test.txt',output_file=self.checksum_file)
        checksum = open(self.checksum_file,'r').read()
        self.assertEqual("0b26e313ed4a7ca6904b0e9369e5b957  test.txt\n",checksum)

class TestDiffFiles(unittest.TestCase):
    """Test checking pairs of files

    """
    def setUp(self):
        # Create a set of files to compare
        self.file1 = TestUtils().make_file(None,"This is a test file")
        self.file2 = TestUtils().make_file(None,"This is a test file")
        self.file3 = TestUtils().make_file(None,"This is another test file")

    def tearDown(self):
        # Delete the test files
        os.remove(self.file1)
        os.remove(self.file2)
        os.remove(self.file3)

    def test_same_file(self):
        # Check that identical files checksum to the same value
        self.assertEqual(diff_files(self.file1,self.file2),0)

    def test_different_files(self):
        # Check that different files checksum to different values
        self.assertNotEqual(diff_files(self.file1,self.file3),0)

class TestDiffDirectories(unittest.TestCase):
    """Test checking pairs of directories

    """

    def setUp(self):
        # Make test directories
        self.dir1 = TestUtils().make_test_directory()
        self.dir2 = TestUtils().make_test_directory()
        # Empty dirctories
        self.empty_dir1 = TestUtils().make_test_directory()
        self.empty_dir2 = TestUtils().make_test_directory()
        # Directory with extra file
        self.extra_file_dir = TestUtils().make_test_directory()
        TestUtils().make_file("extra.txt","This is an extra test file",
                              basedir=self.extra_file_dir)
        # Directories with altered file
        self.diff_file_dir1 = TestUtils().make_test_directory()
        TestUtils().make_file("diff.txt","This is one version of the file",
                              basedir=self.diff_file_dir1)
        self.diff_file_dir2 = TestUtils().make_test_directory()
        TestUtils().make_file("diff.txt","This is another version of the file",
                              basedir=self.diff_file_dir2)
        # Directory with a broken link
        self.broken_link_dir = TestUtils().make_test_directory()
        TestUtils().make_file("missing.txt","This is another test file",
                              basedir=self.broken_link_dir)
        os.symlink(os.path.join(self.broken_link_dir,"missing.txt"),
                   os.path.join(self.broken_link_dir,"broken"))
        os.remove(os.path.join(self.broken_link_dir,"missing.txt"))

    def tearDown(self):
        # Remove test directories
        shutil.rmtree(self.dir1)
        shutil.rmtree(self.dir2)
        shutil.rmtree(self.empty_dir1)
        shutil.rmtree(self.empty_dir2)
        shutil.rmtree(self.extra_file_dir)
        shutil.rmtree(self.diff_file_dir1)
        shutil.rmtree(self.diff_file_dir2)
        shutil.rmtree(self.broken_link_dir)

    def test_same_dirs(self):
        # Check that identical directories are identified as the same
        self.assertEqual(diff_directories(self.empty_dir1,self.empty_dir2),0)
        self.assertEqual(diff_directories(self.dir1,self.dir2),0)

    def test_extra_file(self):
        # Check when one directory contains an extra file
        self.assertEqual(diff_directories(self.dir1,self.extra_file_dir),0)
        self.assertNotEqual(diff_directories(self.extra_file_dir,self.dir1),0)

    def test_different_file(self):
        # Check when directories have a file that differs
        self.assertNotEqual(diff_directories(self.diff_file_dir1,
                                             self.diff_file_dir2),0)
        self.assertNotEqual(diff_directories(self.diff_file_dir2,
                                             self.diff_file_dir1),0)

    def test_broken_links(self):
        # Check when directories contain broken links
        self.assertNotEqual(diff_directories(self.broken_link_dir,
                                             self.dir1),0)
        self.assertEqual(diff_directories(self.dir1,
                                          self.broken_link_dir),0)

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
