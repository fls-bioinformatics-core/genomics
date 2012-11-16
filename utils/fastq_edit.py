#!/bin/env python
#
#     fastq_edit.py: edit FASTQ files and data
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# fastq_edit.py
#
########################################################################

__version__ = "0.0.2"

"""fastq_edit.py

Usage: fastq_edit.py [options] <fastq_file>

Perform various operations on FASTQ file.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  --stats               Generate basic stats for input FASTQ
  --instrument-name=INSTRUMENT_NAME
                        Update the 'instrument name' in the sequence
                        identifier part of each read record and write updated
                        FASTQ file to stdout

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys,os
import optparse

# Set up for local modules in "share"
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import FASTQFile

#######################################################################
# Functions
#######################################################################

def edit_instrument_name(fastq_file,new_instrument_name):
    """Edit the instrument name for all records in FASTQ file

    Loop over all records in a supplied FASTQ file, update the sequence identifier
    (i.e. first line in the each record) by changing the instrument name, and write
    the updated records to stdout.
    """
    # Loop over all reads in the FASTQ
    # Update the instrument name in the sequence identifier and echo to stdout
    for read in FASTQFile.FastqIterator(fastq_file):
        if new_instrument_name:
            # Modify the instrument name
            read.seqid.instrument_name = new_instrument_name
        # Echo updated read to stdout
        print read

def stats(fastq_file):
    """Generate basic stats from FASTQ file
    """
    # Loop over all reads in the FASTQ
    n_reads = 0
    read_lengths = {}
    index_sequences = {}
    for read in FASTQFile.FastqIterator(fastq_file):
        # Count of reads
        n_reads += 1
        # Read length distribution
        read_len = len(read.sequence)
        if read_len in read_lengths:
            read_lengths[read_len] += 1
        else:
            read_lengths[read_len] = 1
        # Tag name distribution
        index_seq = read.seqid.index_sequence
        if index_seq is not None:
            if index_seq in index_sequences:
                index_sequences[index_seq] += 1
            else:
                index_sequences[index_seq] = 1
    # Finished
    print "Total reads: %d" % n_reads
    print "Read lengths"
    for len_ in read_lengths:
        print "\t%d: %d" % (len_,read_lengths[len_])
    print "Index sequences"
    for seq in index_sequences:
        print "\t%s: %d" % (seq,index_sequences[seq])

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Process command line using optparse
    p = optparse.OptionParser(usage="%prog [options] <fastq_file>",
                              version="%prog "+__version__,
                              description=
                              "Perform various operations on FASTQ file.")
    p.add_option('--stats',action='store_true',dest='do_stats',default=False,
                 help="Generate basic stats for input FASTQ")
    p.add_option('--instrument-name',action='store',dest='instrument_name',default=None,
                 help="Update the 'instrument name' in the sequence identifier part of each read "
                 "record and write updated FASTQ file to stdout")

    # Process the command line
    options,arguments = p.parse_args()
    new_instrument_name = options.instrument_name
    do_stats = options.do_stats

    # Deal with arguments
    if len(arguments) != 1:
        p.error("input FASTQ file required")
    else:
        fastq = arguments[0]
        if not os.path.exists(fastq):
            p.error("Input file '%s' not found" % fasta)

    # Run the edit instrument name program
    if new_instrument_name is not None:
        edit_instrument_name(fastq,new_instrument_name)

    # Generate the stats
    if do_stats:
        stats(fastq)
