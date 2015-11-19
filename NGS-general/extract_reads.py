#!/usr/bin/env python
#
#     extract_reads.py: write random subsets of read records from input files
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# extract_reads.py
#
#########################################################################
#
"""extract_reads.py

Pull random sets of read records from various files

Usage: extract_reads.py -m PATTERN | -n NREADS infile [infile ...]

If multiple infiles are specified then the same set of records from
each file.

Recognises FASTQ, CSFASTA and QUAL files.

"""

#######################################################################
# Imports
#######################################################################

import sys
import os
import gzip
import optparse
import random
import re

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.2.0"

CHUNKSIZE = 102400

__description__ = """Extract subsets of reads from each of the
supplied files according to specified criteria (e.g. random,
matching a pattern etc). Input files can be any mixture of FASTQ
(.fastq, .fq), CSFASTA (.csfasta) and QUAL (.qual)."""

#######################################################################
# Functions
#######################################################################

def getlines(filen):
    """
    Fetch lines from a file and return them one by one

    This generator function tries to implement an efficient
    method of reading lines sequentially from a file, by
    minimising the number of reads from the file and
    performing the line splitting in memory. It attempts
    to replicate the idiom:

    >>> for line in open(filen):
    >>> ...

    using:

    >>> for line in getlines(filen):
    >>> ...

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Arguments:
      filen (str): path of the file to read lines from

    Yields:
      String: next line of text from the file, with any
        newline character removed.
    
    """
    if filen.split('.')[-1] == 'gz':
        fp = gzip.open(filen,'rb')
    else:
        fp = open(filen,'rb')
    # Read in data in chunks
    buf = ''
    lines = []
    while True:
        # Grab a chunk of data
        data = fp.read(CHUNKSIZE)
        # Check for EOF
        if not data:
            break
        # Add to buffer and split into lines
        buf = buf + data
        if buf[0] == '\n':
            buf = buf[1:]
        if buf[-1] != '\n':
            i = buf.rfind('\n')
            if i == -1:
                continue
            else:
                lines = buf[:i].split('\n')
                buf = buf[i+1:]
        else:
            lines = buf[:-1].split('\n')
            buf = ''
        # Return the lines one at a time
        for line in lines:
            yield line

def getreads(filen):
    """
    Fetch reads from a file and return them one by one

    This generator function iterates through a
    sequence file (for example fastq), and yields read
    records as a list of lines.

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Arguments:
      filen (str): path of the file to fetch reads from

    Yields:
      List: next read record from the file, as a list
        of lines.

    """
    size = read_size(filen)
    read = []
    for i,line in enumerate(getlines(filen),start=1):
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

#######################################################################
# Main
#######################################################################

def main(args=None):
    # Command line processing
    if args is None:
        args = sys.argv[1:]
    p = optparse.OptionParser(usage="%prog -m PATTERN |-n NREADS infile "
                              "[ infile ... ]",
                              version="%prog "+__version__,
                              description=__description__)
    p.add_option('-m','--match',action='store',dest='pattern',default=None,
                 help="extract records that match Python regular "
                 "expression PATTERN")
    p.add_option('-n',action='store',dest='n',default=None,
                 help="extract N random reads from the input file(s). "
                 "If multiple files are supplied (e.g. R1/R2 pair) then "
                 "the same subsets will be extracted for each. "
                 "(Optionally a percentage can be supplied instead e.g. "
                 "'50%' to extract a subset of half the reads.)")
    p.add_option('-s','--seed',action='store',dest='seed',default=None,
                 help="specify seed for random number generator (used "
                 "for -n option; using the same seed should produce the "
                 "same 'random' sample of reads)")
    opts,args = p.parse_args(args)
    if len(args) < 1:
        p.error("Need to supply at least one input file")
    # Pattern matching option
    if opts.pattern is not None:
        if opts.n is not None:
            p.error("Need to supply only one of -n or -m options")
        print "Extracting reads matching '%s'" % opts.pattern
        for f in args:
            if f.endswith('.gz'):
                outfile = os.path.basename(os.path.splitext(f[:-3])[0])
            else:
                outfile = os.path.basename(os.path.splitext(f)[0])
            outfile += '.subset_regex.fq'
            print "Extracting to %s" % outfile
            with open(outfile,'w') as fp:
                for read in getreads_regex(f,opts.pattern):
                    fp.write('\n'.join(read) + '\n')
    else:
        # Seed random number generator
        if opts.seed is not None:
            random.seed(opts.seed)
        # Count the reads
        nreads = sum(1 for i in getreads(args[0]))
        print "Number of reads: %s" % nreads
        if len(args) > 1:
            print "Verifying read numbers match between files"
        for f in args[1:]:
            if sum(1 for i in getreads(f)) != nreads:
                print "Inconsistent numbers of reads between files"
                sys.exit(1)
        # Generate a subset of read indices to extract
        try:
            nsubset = int(opts.n)
        except ValueError:
            if str(opts.n).endswith('%'):
                nsubset = int(float(opts.n[:-1])*nreads/100.0)
        if nsubset > nreads:
            print "Requested subset (%s) is larger than file (%s)" % (nsubset,
                                                                      nreads)
            sys.exit(1)
        print "Generating set of %s random indices" % nsubset
        subset_indices = random.sample(xrange(nreads),nsubset)
        # Extract the reads to separate files
        for f in args:
            if f.endswith('.gz'):
                outfile = os.path.basename(os.path.splitext(f[:-3])[0])
            else:
                outfile = os.path.basename(os.path.splitext(f)[0])
            outfile += '.subset_%s.fq' % nsubset
            print "Extracting to %s" % outfile
            with open(outfile,'w') as fp:
                for read in getreads_subset(f,subset_indices):
                    fp.write('\n'.join(read) + '\n')

if __name__ == "__main__":
    main()
