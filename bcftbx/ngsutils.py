#!/usr/bin/env python
#
#     utils.py: utility classes & functions specific to NGS applications
#     Copyright (C) University of Manchester 2017 Peter Briggs
#
########################################################################
#
# ngsutils.py
#
#########################################################################

"""
ngsutils

Utility classes and functions specific to NGS applications.

- getreads
- getreads_subset
- getreads_regexp
- read_size

"""

#######################################################################
# Imports
#######################################################################

import re
from .utils import getlines

#######################################################################
# Functions
#######################################################################

def getreads(filen):
    """
    Fetch reads from a file and return them one by one

    This generator function iterates through a
    sequence file (for example fastq), and yields read
    records as a list of lines.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Lines starting with '#' at the start of the file will
    be treated as comments and ignored. Lines starting
    with '#' which occur in the body of the file (i.e.
    after one or more lines of data) will be treated as
    data.

    Arguments:
      filen (str): path of the file to fetch reads from

    Yields:
      List: next read record from the file, as a list
        of lines.
    """
    header = True
    size = read_size(filen)
    read = []
    for i,line in enumerate(getlines(filen),start=1):
        if header:
            if line.startswith('#'):
                continue
            else:
                header = False
        read.append(line)
        if i%size == 0:
            yield read
            read = []
    if read:
        raise Exception("Incomplete read found at file end: %s"
                        % read)

def getreads_subset(filen,indices):
    """
    Fetch subset of reads from a file

    This generator function iterates through a
    sequence file (for example fastq), and yields a subset
    of read records. Each read is returned as a list of
    lines.

    The subset compromises of reads at the index positions
    specified by the list of indices, with index 0 being the
    first read in the file.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Arguments:
      filen (str): path of the file to fetch reads from
      indices (list): list of read indices to return

    Yields:
      List: next read record from the file, as a list
        of lines.
    """
    indices_ = [int(i) for i in indices]
    indices_.sort()
    i = 0
    next_idx = indices_[i]
    for idx,read in enumerate(getreads(filen)):
        if idx == next_idx:
            #print "Extracting read %s" % idx
            #print read
            yield read
            try:
                i += 1
                next_idx = indices_[i]
            except IndexError:
                # No more reads to extract
                return
    raise Exception("One or more requested read indices out of range")

def getreads_regex(filen,pattern):
    """
    Fetch subset of reads from a file

    This generator function iterates through a
    sequence file (for example fastq), and yields a subset
    of read records. Each read is returned as a list of
    lines.

    The subset compromises of reads which match the
    supplied regular expression.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Arguments:
      filen (str): path of the file to fetch reads from
      pattern (list): Python regular expression pattern

    Yields:
      List: next read record from the file, as a list
        of lines.
    """
    regex = re.compile(pattern)
    for read in getreads(filen):
        if regex.search(''.join(read)):
            yield read

def read_size(filen):
    """
    Return size of read based on file type

    Arguments:
      filen (str): name of file

    Returns:
      int: number of lines that each read
        record occupies in this type of file
    """
    # Strip trailing .gz
    if filen.endswith('.gz'):
        filen = filen[:-3]
    # Identify file type from extension
    ext = filen.split('.')[-1]
    if ext in ('fastq','fq'):
        return 4
    elif ext in ('csfasta','qual'):
        return 2
