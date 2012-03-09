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

__version__ = "0.0.3"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse
import tempfile
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
    """
    if output_file:
        fp = open(output_file,'w')
    else:
        fp = sys.stdout
    for d in os.walk(dirn):
        # Calculate md5sum for each file
        for f in d[2]:
            try:
                filen = os.path.join(d[0],f)
                chksum = Md5sum.md5sum(filen)
                fp.write("%s  %s\n" % (chksum,filen))
            except IOError, ex:
                # Error accessing file, report and skip
                sys.stderr.write("%s: error while generating MD5 sum: '%s'" % (filen,ex))
                sys.stderr.write("%s: skipped" % filen)
    if output_file:
        fp.close()

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
        files checked; otherwise only report summary
    """
    failures = []
    for line in open(chksum_file,'rU'):
        items = line.strip().split()
        if len(items) != 2:
            sys.stderr.write("Badly formatted MD5 checksum line, skipped\n")
            continue
        chksum = items[0]
        chkfile = items[1]
        try:
            new_chksum = Md5sum.md5sum(chkfile)
            if chksum == new_chksum:
                report("%s: OK" % chkfile,verbose)
            else:
                report("%s: FAILED" % chkfile,verbose)
                failures.append(chkfile)
        except IOError, ex:
            if not os.path.exists(chkfile):
                report("%s: FAILED (missing file)" % chkfile,verbose)
            else:
                report("%s: FAILED (%s)" % ex,verbose)
            failures.append(chkfile)
    if failures:
        sys.stderr.write("Check failed for %d file(s):\n" % len(failures))
        for f in failures:
            sys.stderr.write("\t%s\n" % f)

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
    """
    # Move to first dir and generate temporary Md5sum file
    os.chdir(dirn1)
    fp,tmpfile = tempfile.mkstemp()
    os.close(fp)
    compute_md5sums('.',output_file=tmpfile)
    # Run this against the second directory
    os.chdir(dirn2)
    verify_md5sums(tmpfile,verbose=verbose)
    # Delete temporary file
    os.remove(tmpfile)

def report(msg,verbose=False):
    """Write text to stdout

    Convenience function for dealing with verbose/silent modes of
    operation: rhe supplied text in 'msg' is only written if the verbose
    argument is set to True.
    """
    if verbose: print "%s" % (msg)

#######################################################################
# Main program
#######################################################################    

if __name__ == "__main__":
    p = optparse.OptionParser(usage="%prog [OPTIONS] DIR|FILE",
                              version="%prog "+__version__,
                              description=
                              "Compute and verify MD5 checksums for files and directories.")

    # General options
    p.add_option('-c','--check',action="store_true",dest="check",default=False,
                 help="read MD5 sums from the specified file and check them")
    p.add_option('-o','--output',action="store",dest="output_file",default=None,
                 help="write computed MD5 sums to OUTPUT_FILE")
    p.add_option('-d','--diff',action="store_true",dest="diff",default=False,
                 help="check that contents of DIR1 and DIR2 have the same MD5 sums")
    p.add_option('-v','--verbose',action="store_true",dest="verbose",default=False,
                 help="verbose output mode")

    # Process the command line
    options,arguments = p.parse_args()

    # Figure out mode of operation
    if options.check:
        # Running in "check" mode
        if len(arguments) != 1:
            p.error("-c: needs single argument (file containing MD5 sums)")
        chksum_file = arguments[0]
        if not os.path.isfile(chksum_file):
            p.error("Checksum '%s' file not found (or is not a file)" % chksum_file)
        # Do the verification
        verify_md5sums(chksum_file,verbose=options.verbose)
    elif options.diff:
        # Running in "diff" mode
        if len(arguments) != 2:
            p.error("-d: needs two arguments (names of directories to compare)")
        # Get directories as absolute paths
        dirn1 = os.path.abspath(arguments[0])
        dirn2 = os.path.abspath(arguments[1])
        if not (os.path.isdir(dirn1) and os.path.isdir(dirn2)):
            p.error("Supplied arguments must be directories")
        diff_directories(dirn1,dirn2,verbose=options.verbose)
    else:
        # Running in "compute" mode
        if len(arguments) != 1:
            p.error("Needs a single argument (name of directory to generate MD5 sums for)")
        start_dir = arguments[0]
        if not os.path.isdir(start_dir):
            p.error("Supplied argument must be a directory")
        # Check if output file was specified
        output_file = None
        if options.output_file:
            output_file = options.output_file
        # Generate the checksums
        compute_md5sums(start_dir,output_file)
