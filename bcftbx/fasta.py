#!/usr/bin/env python
#
#     fasta.py: classes and functions for handling FASTA files
#     Copyright (C) University of Manchester 2022 Peter Briggs
#

#######################################################################
# Import modules
#######################################################################

import io
from collections.abc import Iterator

#######################################################################
# Classes
#######################################################################

class FastaChromIterator(Iterator):
    """
    Class to loop over all chromosomes in a FASTA file, returning a
    tuple of the form

    (name,seq)

    for each chromosome (where 'name' is the chromosome name given
    in the '>' record, and 'seq' is the associated sequence).

    Example looping over all chromosomes and echoing to stdout:

    >>> for chrom in FastaChromIterator(fasta_file):
    >>>    print(">%s\n%s" % (chrom[0],chrom[1]))

    The input source can be specified either as a file name or
    as a file-like object opened for line reading.

    Note that newlines within sequence records are preserved,
    however trailing newlines are removed.

    Arguments:
      fasta: name of the Fasta file to iterate through
      fp: file-like object to read Fasta data from
    """

    def __init__(self,fasta=None,fp=None):
        """
        Create a new FastaChromIterator
        """
        if fp is None:
            # Open input fasta file
            self._fasta = fasta
            self._fp = io.open(self._fasta,'rt')
        else:
            # File object already supplied
            self._fasta = None
            self._fp = fp
        # Internal: store last line read from file
        self._line = None

    def _sanitise_sequence(self,seqs):
        """
        Internal: join list of sequences for output
        """
        return ''.join(seqs).rstrip('\n')

    def __next__(self):
        """
        Return next chromosome from Fasta file as a (name,sequence) tuple
        """
        # Initialise line storage
        if self._line is None:
            line = self._fp.readline()
        else:
            line = self._line
        chrom = None
        seq = []
        # Loop over lines in file looking for start of chromosome
        while line != '':
            if line.startswith(">"):
                if chrom is None:
                    # Start of current chromosome, get name
                    chrom = line.strip()[1:]
                else:
                    # Start of next chromosome, finish
                    # Store line for next iteration
                    self._line = line
                    # Return data
                    return (chrom,self._sanitise_sequence(seq))
            elif chrom is not None:
                # Store sequence line
                seq.append(line)
            # Get next line
            line = self._fp.readline()
        # Reached end of file
        if chrom is not None:
            # Close input file?
            if self._fasta is not None:
                self._fp.close()
            # Flush remaining data
            self._line = ''
            return (chrom,self._sanitise_sequence(seq))
        else:
            # Finished iteration
            raise StopIteration
