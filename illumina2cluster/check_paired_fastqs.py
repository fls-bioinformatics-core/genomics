#!/bin/env python
#
import os
import sys
import optparse
import IlluminaData
import FASTQFile
import logging
import itertools
#
def get_nreads(fastq_file):
    nreads = 0
    fp = open(fastq_file,'rU')
    for line in fp:
        nreads += 1
    fp.close()
    return nreads
#
if __name__ == "__main__":
    
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS R1.fastq R2.fastq",
                              description="Check that read headers for R1 and R2 fastq files "
                              "are in agreement for all reads")
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
