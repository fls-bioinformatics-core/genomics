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

__version__ = "0.0.1"

"""fastq_edit.py

Usage: fastq_edit.py [options] <fastq_file>

Read in FASTQ file, perform edit operations and write new version to stdout.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  --instrument-name=INSTRUMENT_NAME
                        Update the 'instrument name' in the sequence
                        identifier part of each read record
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

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Process command line using optparse
    p = optparse.OptionParser(usage="%prog [options] <fastq_file>",
                              version="%prog "+__version__,
                              description=
                              "Read in FASTQ file, perform edit operations and write new "
                              "version to stdout.")
    p.add_option('--instrument-name',action='store',dest='instrument_name',default=None,
                 help="Update the 'instrument name' in the sequence identifier part of each read "
                 "record")

    # Process the command line
    options,arguments = p.parse_args()
    new_instrument_name = options.instrument_name

    # Deal with arguments
    if len(arguments) != 1:
        p.error("input FASTQ file required")
    else:
        fastq = arguments[0]
        if not os.path.exists(fastq):
            p.error("Input file '%s' not found" % fasta)

    # Run the edit instrument name program
    edit_instrument_name(fastq,new_instrument_name)
