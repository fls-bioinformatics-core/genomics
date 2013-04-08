#!/bin/env python
#
#     check_paired_fastqs.py: verify that R1/R2 fastq pair are consistent
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# check_paired_fastqs.py
#
#########################################################################

"""check_paired_fastqs.py

Verify that an R1/R2 pair of FASTQ files is consistent, specifically:

1. That they both contain the same number of reads, and
2. That the read headers for each read contain the same information
   in the same order.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

__version__ = "0.0.1"

import os
import sys
import optparse
import itertools
import logging

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import IlluminaData
import FASTQFile

#######################################################################
# Module Functions
#######################################################################

def get_nreads(fastq_file):
    """Return number of reads in a FASTQ file

    Simple-minded read count performed by counting the number of lines
    in the file and dividing by 4.

    Arguments:
      fastq_file: file to get read count for

    Returns:
      Number of reads.

    """
    nreads = 0
    fp = open(fastq_file,'rU')
    for line in fp:
        nreads += 1
    fp.close()
    return nreads

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS R1_fastq R2_fastq",
                              version="%prog "+__version__,
                              description="Check that read headers for R1 and R2 fastq files "
                              "are in agreement for all reads. Input files can be either fastq "
                              "or fastq.gz.")
    # Parse command line
    options,args = p.parse_args()
    # Get data directory name
    if len(args) != 2:
        p.error("expected two arguments (R1 and R2 fastq files to compare)")
    fastq_file_r1 = args[0]
    fastq_file_r2 = args[1]
    # Loop through the two files in parallel
    nreads = 0
    for r1,r2 in itertools.izip(FASTQFile.FastqIterator(fastq_file_r1),
                                FASTQFile.FastqIterator(fastq_file_r2)):
        nreads += 1
        if r1.seqid.pair_id != "1" or r2.seqid.pair_id != "2":
            print "Wrong pair id for read:"
            print "R1: %s" % str(r1.seqid)
            print "R2: %s" % str(r2.seqid)
            logging.error("Wrong pair id for read #%d" % nreads)
            sys.exit(1)
        if r1.seqid.instrument_name != r2.seqid.instrument_name or \
                r1.seqid.run_id != r2.seqid.run_id or \
                r1.seqid.flowcell_id != r2.seqid.flowcell_id or \
                r1.seqid.flowcell_lane != r2.seqid.flowcell_lane or \
                r1.seqid.tile_no != r2.seqid.tile_no or \
                r1.seqid.x_coord != r2.seqid.x_coord or \
                r1.seqid.y_coord != r2.seqid.y_coord or \
                r1.seqid.bad_read != r2.seqid.bad_read or \
                r1.seqid.control_bit_flag != r2.seqid.control_bit_flag or \
                r1.seqid.index_sequence != r2.seqid.index_sequence:
            # No match
            print "Mismatched R1/R2 pair:"
            print "R1: %s" % str(r1.seqid)
            print "R2: %s" % str(r2.seqid)
            logging.error("Mismatch in read header for read #%d" % nreads)
            sys.exit(1)
        if nreads%100000 == 0:
            print "\t%d reads" % nreads
    # All done
    print "Finished: read headers match"
    sys.exit(0)
