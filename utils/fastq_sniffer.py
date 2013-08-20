#!/bin/env python
#
#     fastq_sniffer.py: "sniff" FASTQ file to determine quality encoding
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# fastq_sniffer.py
#
########################################################################

__version__ = "0.0.2"

"""fastq_sniffer.py

Usage: fastq_sniffer.py [ --subset N ] <fastq_file>

"Sniff" FASTQ file to try and determine likely format and quality encoding.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import optparse

# Set up for local modules in "share"
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import FASTQFile

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Process command line using optparse
    p = optparse.OptionParser(usage="%prog [options] <fastq_file>",
                              version="%prog "+__version__,
                              description=
                              "'Sniff' FASTQ file to determine likely quality encoding.")
    p.add_option('--subset',action="store",dest="n_subset",default=None,
                 help="try to determine encoding from a subset of consisting of the first "
                 "N_SUBSET reads. (Quicker than using all reads but may not be accurate "
                 "if subset is not representative of the file as a whole.)")

    # Process the command line
    options,arguments = p.parse_args()
    if len(arguments) != 1:
        p.error("input FASTQ file required")
    else:
        fastq_file = arguments[0]
        if not os.path.exists(fastq_file):
            p.error("Input file '%s' not found" % fastq_file)

    # Get broad format type
    print "Sniffing %s" % fastq_file
    print "\nData from first read:"
    for read in FASTQFile.FastqIterator(fastq_file):
        fastq_format = read.seqid.format
        if fastq_format is None and read.is_colorspace:
            fastq_format = 'colorspace'
        print "\tHeader format:\t%s" % str(fastq_format)
        print "\tSeq length:\t%d" % read.seqlen
        break

    # Determine the quality score range (and count reads)
    try:
        n_subset = int(options.n_subset)
    except TypeError:
        n_subset = None
    n_reads = 0
    min_max_qual = (None,None)
    for read in FASTQFile.FastqIterator(fastq_file):
        n_reads += 1
        if min_max_qual == (None,None):
            min_max_qual = (ord(read.minquality),ord(read.maxquality))
        else:
            min_max_qual = (min(min_max_qual[0],ord(read.minquality)),
                            max(min_max_qual[1],ord(read.maxquality)))
        if n_subset is not None and n_reads == n_subset:
            break

    # Number of reads
    print "\nProcessed %d reads" % n_reads
    # Print min,max quality values
    min_qual = min_max_qual[0]
    max_qual = min_max_qual[1]
    print "Min,max quality scores:\t%d,%d\t(%s,%s)" % \
        (min_qual,max_qual,chr(min_qual),chr(max_qual))
    # Match to possible formats and quality encodings
    print "\nIdentifying possible formats/quality encodings..."
    encodings = []
    galaxy_types = []
    if min_qual >= ord('!') and max_qual <= ord('I'):
        print "\tPossible Sanger/Phred+33"
        encodings.append('Phred+33')
    if fastq_format != 'colorspace':
        if min_qual >= ord(';') and max_qual <= ord('h'):
            print "\tPossible Solexa/Solexa+64"
            encodings.append('Solexa+64')
            galaxy_types.append('fastqsolexa')
        if min_qual >= ord('@') and max_qual <= ord('h'):
            print "\tPossible Illumina 1.3+/Phred+64"
            encodings.append('Phred+64')
            galaxy_types.append('fastqillumina')
        if min_qual >= ord('C') and max_qual <= ord('h'):
            print "\tPossible Illumina 1.5+/Phred+64"
            encodings.append('Phred+64')
            galaxy_types.append('fastqillumina')
        if min_qual >= ord('!') and max_qual <= ord('I'):
            print "\tPossible Illumina 1.8+/Phred+33"
            encodings.append('Phred+33')
            galaxy_types.append('fastqsanger')
    else:
        galaxy_types.append('fastqcssanger')
    print "\nLikely encodings:"
    if encodings:
        # Make sure list only has unique values
        encodings = list(set(encodings))
        for encoding in encodings:
            print "\t%s" % encoding
    else:
        print "\tNone identified"
    print "\nLikely galaxy types:"
    if galaxy_types:
        # Make sure list only has unique values
        galaxy_types = list(set(galaxy_types))
        for galaxy_type in galaxy_types:
            print "\t%s" % galaxy_type
    else:
        print "\tNone identified"
    
