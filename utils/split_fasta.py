#!/bin/env python
#
#
import os
import optparse

__version__ = "0.0.1"

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Process the command line
    p = optparse.OptionParser(usage="%prog OPTIONS fasta_file",
                              version="%prog "+__version__,
                              description="Split input FASTA file with multiple sequences "
                              "into multiple files each containing sequences for a single "
                              "chromosome.")
    options,arguments = p.parse_args()
    if len(arguments) != 1:
        p.error("Expects exactly one fasta file as input")
    fasta = arguments[0]

    # Open input file and loop through sequences
    fp = open(fasta,'rU')
    chrom = None
    fp_chrom = None
    for line in fp:
        if line.startswith(">"):
            # New chromosome
            chrom_name = line.strip()[1:]
            if chrom != chrom_name:
                # Close current output file, if one is open
                if fp_chrom is not None:
                    fp_chrom.close()
                    fp_chrom = None
                # Open new output file
                print "Opening output file for chromosome %s" % chrom_name
                chrom_fasta = "%s.fa" % chrom_name
                fp_chrom = open(chrom_fasta,'w')
        if fp_chrom is not None:
            fp_chrom.write(line)
    # Finished, tidy up loose ends
    if fp_chrom is not None:
        fp_chrom.close()

