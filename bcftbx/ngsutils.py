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

Extracting reads from Fastq, cfasta and qual files:

- getreads: fetch reads one-by-one from Fastq, cfasta or qual file
- getreads_subset: fetch subset of reads specified by index
- getreads_regexp: fetch subset of reads matching regular expression

"""

#######################################################################
# Imports
#######################################################################

import os
import re
from .utils import getlines

#######################################################################
# Functions
#######################################################################

def getreads(filen):
    """
    Return Fastq, csfasta or qual file reads one-by-one

    This generator function iterates through a
    sequence file (Fastq, csfasta or qual), and yields
    read records one at a time. The read records are
    returned as lists of lines.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Lines starting with '#' at the start of the file will
    be treated as comments and ignored. Lines starting
    with '#' which occur in the body of the file (i.e.
    after one or more lines of data) will be treated as
    data.

    Example usage:

    >>> for r in getreads('illumina_R1.fq'):
    >>> ... print r

    Arguments:
      filen (str): path of the file to fetch reads from

    Yields:
      List: next read record from the file, as a list
        of lines.
    """
    fields = os.path.basename(filen).split('.')
    if fields[-1] == 'gz':
        fields = fields[:-1]
    ext = fields[-1]
    if ext in ('fastq','fq'):
        read_size = 4
    elif ext in ('csfasta','qual'):
        read_size = 2
    header = True
    read = []
    for i,line in enumerate(getlines(filen),start=1):
        if header:
            if line.startswith('#'):
                continue
            else:
                header = False
        read.append(line)
        if i%read_size == 0:
            yield read
            read = []
    if read:
        raise Exception("Incomplete read found at file end: %s"
                        % read)

def getreads_subset(filen,indices):
    """
    Fetch subset of reads from Fastq, csfasta or qual file

    This generator function iterates through a
    sequence file (Fastq, csfasta or qual), and yields a
    subset of the read records which are referenced by the
    supplied iterable indices.

    The subset compromises of reads at the index positions
    specified by the list of indices, with index 0 being the
    first read in the file. Each read is returned as a list
    of lines.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Example usage (returns 1st, 3rd and 5th reads only):

    >>> for r in getreads_subset('illumina_R1.fq',(0,2,4)):
    >>> ... print r

    Arguments:
      filen (str): path of the file to fetch reads from
      indices (list): list of read indices to return

    Yields:
      List: next read record from the file, as a list
        of lines.
    """
    indices_ = [int(i) for i in indices]
    indices_.sort()
    if indices_[0] < 0:
        raise Exception("One or more requested read indices out of range")
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
    Fetch matching reads from  Fastq, csfasta or qual file

    This generator function iterates through a
    sequence file (Fastq, csfasta or qual), and yields a
    subset of read records. Each read is returned as a list
    of lines.

    The subset compromises of reads which match the
    supplied regular expression.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Example usage:

    >>> for r in getreads_regexp('illumina_R1.fq',"2102:3130"):
    >>> ... print r

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
