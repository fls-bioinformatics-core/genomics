#!/bin/env python
#
#     verify_paired.py: check R1 and R2 fastq files are consistent
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# verify_paired.py
#
#########################################################################

"""verify_paired.py

Checks that headers for R1 and R2 fastq files are in agreement, and that
the files form an R1/2 pair.

"""

__version__ = "1.0.0"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import sys
import itertools
import optparse
import logging
logging.basicConfig(format="%(levelname)s %(message)s")

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.FASTQFile as FASTQFile

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    
    # Create command line parser
    p = optparse.OptionParser(usage="%prog OPTIONS R1.fastq R2.fastq",
                              version="%prog "+__version__,
                              description="Check that read headers for R1 and R2 fastq files "
                              "are in agreement, and that the files form an R1/2 pair.")
    # Parse command line
    options,args = p.parse_args()
    # Get data directory name
    if len(args) != 2:
        p.error("expected two arguments (R1 and R2 fastq files to compare)")
    fastq_file_r1 = args[0]
    fastq_file_r2 = args[1]
    # Process the data
    if FASTQFile.fastqs_are_pair(fastq_file_r1,fastq_file_r2):
        sys.exit(0)
    else:
        logging.error("Not R1/R2 pair")
        sys.exit(1)
        
        
        
            
        
    
