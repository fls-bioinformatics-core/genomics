#!/usr/bin/env python3
#
#     fasta.py: classes and utilities for handling FASTA files
#     Copyright (C) University of Manchester 2026 Peter Briggs
#


"""
Classes for reading FASTQ files and manipulating the data within them:

* FastaChromIterator: enables looping through chromosomes in FASTA file
"""


from collections.abc import Iterator


class FastaChromIterator(Iterator):
    """
    Class to loop over chromosomes in a FASTA file

    Implements an iterator which can be used to loop through the
    chromosome records in a FASTA-format file.

    For each record it returns a tuple of the form:

    (name, seq)

    for each chromosome, where 'name' is the chromosome name
    (given in the '>' record), and 'seq' is the associated sequence.

    Note that newlines within multiline sequence records are
    preserved, however trailing newlines are removed.

    Example looping over all chromosomes and echoing to stdout:

    >>> for chrom, sequence in FastaChromIterator(fasta_file):
    ...     print(f">{chrom}\n{sequence}")

    The input source can be specified either as a file name or
    as a file-like object opened for line reading.

    Arguments:
      fasta (str): name of the Fasta file to iterate through
      fp (any): file-like object to read Fasta data from
    """
    def __init__(self, fasta=None, fp=None):
        """
        Create a new FastaChromIterator
        """
        if fp is None:
            # Open input fasta file
            self._fasta = fasta
            self._fp = open(self._fasta, "rt")
        else:
            # File object already supplied
            self._fasta = None
            self._fp = fp
        # Internal: store last line read from file
        self._line = None

    @staticmethod
    def _sanitise_sequence(seqs):
        """
        Internal: join list of sequences for output
        """
        return "".join(seqs).rstrip("\n")

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
        while line != "":
            if line.startswith(">"):
                if chrom is None:
                    # Start of current chromosome, get name
                    chrom = line.strip()[1:]
                else:
                    # Start of next chromosome, finish
                    # Store line for next iteration
                    self._line = line
                    # Return data
                    return chrom, self._sanitise_sequence(seq)
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
            self._line = ""
            return chrom, self._sanitise_sequence(seq)
        else:
            # Finished iteration
            raise StopIteration
