#!/usr/bin/env python
#
#     extract_reads.py: write random subsets of read records from input files
#     Copyright (C) University of Manchester 2012-2021 Peter Briggs
#

"""
Pull random sets of read records from various files

Usage: extract_reads.py -m PATTERN | -n NREADS infile [infile ...]

If multiple infiles are specified then the same set of records from
each file.

Recognises FASTQ, CSFASTA and QUAL files.
"""

#######################################################################
# Imports
#######################################################################

from builtins import str
from builtins import range
import sys
import os
import io
import gzip
import argparse
import random
import re
from ..ngsutils import getreads
from ..ngsutils import getreads_subset
from ..ngsutils import getreads_regex
from .. import get_version

#######################################################################
# Module metadata
#######################################################################

__description__ = """Extract subsets of reads from each of the
supplied files according to specified criteria (e.g. random,
matching a pattern etc). Input files can be any mixture of FASTQ
(.fastq, .fq), CSFASTA (.csfasta) and QUAL (.qual)."""

#######################################################################
# Main
#######################################################################

def main(args=None):
    # Command line processing
    if args is None:
        args = sys.argv[1:]
    p = argparse.ArgumentParser(description=__description__)
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument('-m','--match',action='store',dest='pattern',
                   default=None,
                   help="extract records that match Python regular "
                   "expression PATTERN")
    p.add_argument('-n',action='store',dest='n',default=None,
                   help="extract N random reads from the input file(s). "
                   "If multiple files are supplied (e.g. R1/R2 pair) then "
                   "the same subsets will be extracted for each. "
                   "(Optionally a percentage can be supplied instead e.g. "
                   "'50%%' to extract a subset of half the reads.)")
    p.add_argument('-s','--seed',action='store',dest='seed',default=None,
                   help="specify seed for random number generator (used "
                   "for -n option; using the same seed should produce the "
                   "same 'random' sample of reads)")
    p.add_argument('infiles',metavar='infile',nargs='+',
                   help="input FASTQ, CSFASTA, or QUAL file")
    args = p.parse_args(args)
    # Pattern matching option
    if args.pattern is not None:
        if args.n is not None:
            p.error("Need to supply only one of -n or -m options")
        print("Extracting reads matching '%s'" % args.pattern)
        for f in args.infiles:
            if f.endswith('.gz'):
                outfile = os.path.basename(os.path.splitext(f[:-3])[0])
            else:
                outfile = os.path.basename(os.path.splitext(f)[0])
            outfile += '.subset_regex.fq'
            print("Extracting to %s" % outfile)
            with io.open(outfile,'wt') as fp:
                for read in getreads_regex(f,args.pattern):
                    fp.write('\n'.join(read) + '\n')
    else:
        # Seed random number generator
        if args.seed is not None:
            random.seed(args.seed)
        # Count the reads
        nreads = sum(1 for i in getreads(args.infiles[0]))
        print("Number of reads: %s" % nreads)
        if len(args.infiles) > 1:
            print("Verifying read numbers match between files")
        for f in args.infiles[1:]:
            if sum(1 for i in getreads(f)) != nreads:
                print("Inconsistent numbers of reads between files")
                sys.exit(1)
        # Generate a subset of read indices to extract
        try:
            nsubset = int(args.n)
        except ValueError:
            if str(args.n).endswith('%'):
                nsubset = int(float(args.n[:-1])*nreads/100.0)
        if nsubset > nreads:
            print("Requested subset (%s) is larger than file (%s)" % (nsubset,
                                                                      nreads))
            sys.exit(1)
        print("Generating set of %s random indices" % nsubset)
        subset_indices = random.sample(range(nreads),nsubset)
        # Extract the reads to separate files
        for f in args.infiles:
            if f.endswith('.gz'):
                outfile = os.path.basename(os.path.splitext(f[:-3])[0])
            else:
                outfile = os.path.basename(os.path.splitext(f)[0])
            outfile += '.subset_%s.fq' % nsubset
            print("Extracting to %s" % outfile)
            with io.open(outfile,'wt') as fp:
                for read in getreads_subset(f,subset_indices):
                    fp.write('\n'.join(read) + '\n')
