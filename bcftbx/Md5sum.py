#!/usr/bin/env python
#
#     Md5sum.py: classes and functions for md5 checksum operations
#     Copyright (C) University of Manchester 2012-2019 Peter Briggs
#
########################################################################
#
# Md5sum.py
#
#########################################################################

"""Md5sum

Classes and functions for performing various MD5 checksum operations.

The code function is the 'md5sum' function, which computes the MD5 hash for
a file and is based on examples at:

http://www.python.org/getit/releases/2.0.1/md5sum.py

and
    
http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python

Usage:

>>> import Md5sum
>>> Md5Sum.md5sum("myfile.txt")
... eacc9c036025f0e64fb724cacaadd8b4

This module implements two methods for generating the md5 digest of a file:
the first uses a method based on the hashlib module, while the second (used
as a fallback for pre-2.5 Python) uses the now deprecated md5 module. Note
however that the md5sum function determines itself which method to use.

There is also a high-level class 'Md5Checker' which implements various
class methods for running MD5 checks across all files in a directory, and
a wrapper class 'Md5Reporter' which

"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "1.1.2"

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import logging
try:
    # Preferentially use hashlib module
    import hashlib
except ImportError:
    # hashlib not available, use deprecated md5 module
    import md5

#######################################################################
# Modules constants
#######################################################################

BLOCKSIZE = 1024*1024

#######################################################################
# Classes
#######################################################################

class Md5Checker(object):
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
            yield (os.path.relpath(f,dirn),md5sum(f))

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
            if md5sum(f1) == md5sum(f2):
                status = self.MD5_OK
            else:
                status = self.MD5_FAILED
        except IOError as ex:
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
                except Exception as ex:
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
            try:
                md5 = md5sum(f)
                yield (os.path.relpath(f,d),md5)
            except IOError as ex:
                logging.error("md5sum: %s: %s" % (f,ex))

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
                raise IndexError("Bad MD5 sum line: %s" % line.rstrip('\n'))
            chksum = items[0]
            f = line[len(chksum):].strip()
            try:
                if not os.path.exists(f):
                    status = self.MISSING_TARGET
                elif md5sum(f) == chksum:
                    status = self.MD5_OK
                else:
                    status = self.MD5_FAILED
            except IOError as ex:
                # Error accessing file
                logging.error("%s: error while generating MD5 sum: '%s'" % (f,ex))
                status = self.MD5_ERROR
            yield (f,status)

class Md5CheckReporter(object):
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
                raise Exception("Unrecognised status: '%s'" % status)
            self._fp.write("%s: %s\n" % (f,status_msg))

    def summary(self):
        """Write a summary of the results

        Writes a summary of the number of files checked, how many passed
        or failed MD5 checks and so on, to the specified output stream.

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

def hexify(s):
    """Return the hex representation of a string

    """
    return ("%02x"*len(s)) % tuple(map(ord, s))

def md5sum(f):
    """Return md5sum digest for a file or stream
    
    This implements the md5sum checksum generation using both
    the hashlib module (which should be available in Python 2.5) and
    the deprecated md5 module (which will be used if hashlib is
    unavailable, as is the case for Python 2.4 and earlier).

    The choice of hashlib versus md5 is made automatically and there
    is no need for the invoking subprogram to decide: the resulting
    checksums are the same using either library regardless.

    Arguments:
      f: name of the file to generate the checksum from, or
        a file-like object opened for reading in binary mode.
        
    Returns:
      Md5sum digest for the named file.

    """
    # Initialise checksum using whatever is available
    try:
        chksum = hashlib.md5()
    except NameError:
        chksum = md5.new()
    # Generate checksum
    try:
        f = open(f,"rb")
    except TypeError:
        pass
    for block in iter(lambda: f.read(BLOCKSIZE), ''):
        chksum.update(block)
    return hexify(chksum.digest())
