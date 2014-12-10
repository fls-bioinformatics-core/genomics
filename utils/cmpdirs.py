#!/bin/env python
#
#     cmpdirs.py: compare contents of two directories
#     Copyright (C) University of Manchester 2014 Peter Briggs
#
########################################################################
#
# cmpdirs.py
#
#########################################################################

"""cmpdirs.py

Compare the contents of two directories.

"""

#######################################################################
# Module metadata
#######################################################################

__version__ = '0.0.2'

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse
import logging
import itertools
from multiprocessing import Pool

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.Md5sum as Md5sum

#######################################################################
# Classes
#######################################################################

class CmpResult:
    """Class to hold results of a file comparison
    """
    # Human-readable text corresponding to comparison outcomes
    _status_messages = {
        Md5sum.Md5Checker.MD5_OK: 'OK',
        Md5sum.Md5Checker.MD5_FAILED: 'FAILED: MD5s don\'t match',
        Md5sum.Md5Checker.MD5_ERROR: 'FAILED: error generating MD5',
        Md5sum.Md5Checker.MISSING_SOURCE: 'FAILED: source missing',
        Md5sum.Md5Checker.MISSING_TARGET: 'FAILED: target missing',
        Md5sum.Md5Checker.LINKS_SAME: 'OK',
        Md5sum.Md5Checker.LINKS_DIFFER: 'FAILED: symlink targets don\'t match',
        Md5sum.Md5Checker.TYPES_DIFFER: 'FAILED: different types'
    }
    def __init__(self,path,path2,status):
        """Create a new CmpResult

        Arguments:
          path  : first path being compared
          path2 : second path being compared
          status: result code from Md5sum.Md5Checker 

        """
        self.path = path
        self.path2 = path2
        self.status = status
    def relpath(self,dir_path):
        """Return 'path' relative to 'dir_path'

        """
        return os.path.relpath(self.path,dir_path)
    @property
    def status_message(self):
        """Return message corresponding to result code

        """
        return self._status_messages[self.status]

#######################################################################
# Functions
#######################################################################

def yield_filepairs(dir1,dir2,include_dirs=False):
    """Return pairs of equivalent files under two directories
 
    Walk directory structure under dir1 and iteratively yield
    file pair tuples (f1,f2), where f1 is a file under dir1 and
    f2 is its counterpart under dir2.

    Note that the first file in the pair is guaranteed to exist
    but the second may not. Also additional files may exist
    under dir2 but these will not be returned.

    """
    dir1 = os.path.abspath(dir1)
    dir2 = os.path.abspath(dir2)
    for d in os.walk(dir1):
        d1 = os.path.normpath(d[0])
        if include_dirs:
            yield (d1,os.path.normpath(
                os.path.join(dir2,os.path.relpath(d1,dir1))))
        for f in d[2]:
            # File in dir1
            f1 = os.path.join(d1,f)
            f2 = os.path.join(dir2,os.path.relpath(f1,dir1))
            yield (f1,f2)

def cmp_filepair(file_pair):
    """Compare a pair of files

    'file_pair' is a tuple consisting of a pair of file paths
    (a 'source' file and a corresponding 'target').

    The two paths are compared and a CmpResult object is
    returned.

    """
    f1,f2 = file_pair
    if not os.path.lexists(f1):
        result = Md5sum.Md5Checker.MISSING_SOURCE
    elif not os.path.lexists(f2):
        result = Md5sum.Md5Checker.MISSING_TARGET
    elif os.path.islink(f1):
        # Compare symlinks
        if os.path.islink(f2):
            if os.path.realpath(f1) == os.path.realpath(f2):
                result = Md5sum.Md5Checker.LINKS_SAME
            else:
                result = Md5sum.Md5Checker.LINKS_DIFFER
        else:
            result = Md5sum.Md5Checker.TYPES_DIFFER
    elif os.path.isdir(f1):
        # Compare directories
        if os.path.isdir(f2):
            result = Md5sum.Md5Checker.MD5_OK
        else:
            result = Md5sum.Md5Checker.TYPES_DIFFER
    else:
        # Compare files
        result = Md5sum.Md5Checker.md5cmp_files(f1,f2)
    return CmpResult(f1,f2,result)

def cmp_dirs(dir1,dir2,n=1):
    """Compare the contents of a pair of directories

    

    """
    counts = {}
    if n == 1:
        mapper = itertools.imap
    else:
        pool = Pool(n)
        mapper = pool.imap
    for result in mapper(cmp_filepair,yield_filepairs(dir1,dir2)):
        print "%s: %s" % (result.relpath(dir1),result.status_message)
        try:
            counts[result.status] += 1
        except KeyError:
            counts[result.status] = 1
    if n > 1:
        pool.close()
        pool.join()
    return counts

#######################################################################
# Main
#######################################################################

if __name__ == '__main__':
    p = optparse.OptionParser(usage="%prog [OPTIONS] DIR1 DIR2",
                              version="%prog "+__version__,
                              description="Compare contents of DIR1 against "
                              "corresponding files and directories in DIR2. "
                              "Files are compared using MD5 sums, symlinks "
                              "using their targets.")
    p.add_option('-n',action='store',dest='n_processors',
                 default=1,type='int',
                 help="specify number of cores to use")
    options,args = p.parse_args()
    if len(args) != 2:
        p.error("supply two directories to compare")
    counts = cmp_dirs(args[0],args[1],n=options.n_processors)
    if counts:
        total = sum([counts[x] for x in counts])
    else:
        total = 0
    verified = 0
    for status in (Md5sum.Md5Checker.MD5_OK,Md5sum.Md5Checker.LINKS_SAME):
        try:
            verified += counts[status]
        except KeyError:
            pass
    print "Verified %d Total %d" % (verified,total)
    sys.exit(0 if total == verified else 1)

