#!/usr/bin/env python
#
#     md5checker.py: check files and directories using md5 checksums
#     Copyright (C) University of Manchester 2012-2022 Peter Briggs
#

"""
Utility for checking files and directories using md5 checksums.

Uses the 'Md5Checker' and 'Md5CheckReporter' classes from the Md5sum
module to perform the underlying operations.
"""

#######################################################################
# Imports
#######################################################################

import sys
import os
import io
import argparse
import logging
from ..Md5sum import md5sum
from ..Md5sum import Md5CheckReporter
from ..Md5sum import Md5Checker
from .. import get_version

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
        fp = io.open(output_file,'wt')
    else:
        fp = sys.stdout
    for filen,chksum in Md5Checker.compute_md5sums(dirn):
        if not relative:
            filen = os.path.join(dirn,filen)
        fp.write(u"%s  %s\n" % (chksum,filen))
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
    retval = 0
    if output_file:
        fp = io.open(output_file,'wt')
    else:
        fp = sys.stdout
    try:
        chksum = md5sum(filen)
        fp.write(u"%s  %s\n" % (chksum,filen))
    except IOError as ex:
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
            print("OK: MD5 sums match")
        elif reporter.n_failed:
            print("FAILED: MD5 sums don't match")
        else:
            print("ERROR: unable to compute one or both MD5 sums")
    return reporter.status

def report(msg,verbose=False):
    """Write text to stdout

    Convenience function for dealing with verbose/silent modes of
    operation: rhe supplied text in 'msg' is only written if the verbose
    argument is set to True.
    """
    if verbose:
        print("%s" % msg)

#######################################################################
# Main program
#######################################################################

def main():
    """
    Driver for md5checker
    """
    usage = """
  %(prog)s -d SOURCE_DIR DEST_DIR
  %(prog)s -d FILE1 FILE2
  %(prog)s [ -o CHKSUM_FILE ] DIR
  %(prog)s [ -o CHKSUM_FILE ] FILE
  %(prog)s -c CHKSUM_FILE"""
    p = argparse.ArgumentParser(
        usage=usage,
        description=
        "Compute and verify MD5 checksums for files and directories.")

    # Define options
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument('-d','--diff',action="store_true",dest="diff",
                   default=False,
                   help="for two directories: check that contents of "
                   "directory DIR1 are present in DIR2 and have the "
                   "same MD5 sums; for two files: check that FILE1 and "
                   "FILE2 have the same MD5 sums")
    p.add_argument('-c','--check',action="store_true",dest="check",
                   default=False,
                   help="read MD5 sums from the specified file and "
                   "check them")
    p.add_argument('-q','--quiet',action="store_false",dest="verbose",
                   default=True,
                   help="suppress output messages and only report "
                   "failures")

    # Directory differencing
    group = p.add_argument_group("Directory comparison (-d, --diff)",
                                 "Check that the contents of SOURCE_DIR "
                                 "are present in TARGET_DIR and have "
                                 "matching MD5 sums. Note that files that "
                                 "are only present in TARGET_DIR are not "
                                 "reported.")

    # File differencing
    group = p.add_argument_group("File comparison (-d, --diff)",
                                 "Check that FILE1 and FILE2 have matching "
                                 "MD5 sums.")

    # Checksum generation
    group = p.add_argument_group("Checksum generation",
                                 "MD5 checksums are calcuated for all "
                                 "files in the specified directory, or for "
                                 "a single specified file.")
    group.add_argument('-o','--output',action="store",dest="chksum_file",
                       default=None,
                       help="optionally write computed MD5 sums to "
                       "CHKSUM_FILE (otherwise the sums are written to "
                       "stdout). The output format is the same as that used "
                       "by the Linux 'md5sum' tool.")

    # Checksum verification
    group = p.add_argument_group("Checksum verification (-c, --check)",
                                 "Check MD5 sums for each of the files "
                                 "listed in the specified CHKSUM_FILE "
                                 "relative to the current directory. "
                                 "This option behaves the same as the Linux "
                                 "'md5sum' tool.")

    # Process the command line
    arguments,args = p.parse_known_args()

    # Set up logging output
    logging.basicConfig(format='%(message)s')

    # Figure out mode of operation
    if arguments.check:
        # Running in "check" mode
        if len(args) != 1:
            p.error("-c: needs single argument (file containing MD5 sums)")
        chksum_file = args[0]
        if not os.path.isfile(chksum_file):
            p.error("Checksum '%s' file not found (or is not a file)" % 
                    chksum_file)
        # Do the verification
        status = verify_md5sums(chksum_file,
                                verbose=arguments.verbose)
    elif arguments.diff:
        # Running in "diff" mode
        if len(args) != 2:
            p.error("-d: takes two arguments but got %s: %s"
                    % (len(args),args))
        # Get directories/files as absolute paths
        source = os.path.abspath(args[0])
        target = os.path.abspath(args[1])
        for arg in (source,target):
            if not os.path.exists(arg):
                p.error("%s: not found" % arg)
        if os.path.isdir(source) and os.path.isdir(target):
            # Compare two directories
            report("Recursively check copies of files in %s against "
                   "originals in %s" % (target,source),arguments.verbose)
            status = diff_directories(source,
                                      target,
                                      verbose=arguments.verbose)
        elif os.path.isfile(source) and os.path.isfile(target):
            # Compare two files
            report("Checking MD5 sums for %s and %s" % (source,target),
                   arguments.verbose)
            status = diff_files(source,
                                target,
                                verbose=arguments.verbose)
        else:
            p.error("Supplied arguments must be a pair of directories "
                    "or a pair of files")
    else:
        # Running in "compute" mode
        if len(args) != 1:
            p.error("Needs a single argument (name of directory to "
                    "generate MD5 sums for)")
        # Check if output file was specified
        output_file = None
        if arguments.chksum_file:
            output_file = arguments.chksum_file
        # Generate the checksums
        if os.path.isdir(args[0]):
            status = compute_md5sums(args[0],output_file)
        elif os.path.isfile(args[0]):
            status = compute_md5sum_for_file(args[0],output_file)
        else:
            p.error("Cannot generate checksums for '%s': not a "
                    "directory or file" % args[0])
    # Finish
    sys.exit(status)
