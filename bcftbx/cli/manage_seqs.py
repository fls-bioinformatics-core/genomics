#!/usr/bin/env python
#
#     manage_seqs.py: Utility for handling sets of named sequences
#     Copyright (C) University of Manchester 2014-2021 Peter Briggs
#

"""
manage_seqs

Utility for handling sets of named sequences.

Written to deal with extending and validating FastQC contaminant files.

Usage:

manage_seqs.py [-o OUTFILE|-a OUTFILE] [-d DESCRIPTION] INFILE [INFILE...]
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import io
import copy
import sys
import argparse
from .. import get_version

#######################################################################
# Classes
#######################################################################

class SeqDb:
    """Class for storing set of sequences with associated names

    SeqDb stores arbitrary sequence strings associated with
    arbitrary names. The SeqDb instance can be populated from
    one or more files as well as programmatically, e.g.

    >>> s = SeqDb()
    >>> s.load('sequences.txt')
    >>> s.load_from_fasta('sequences.fa')
    >>> s.add('Sequence fragment #1','AGCCGT')

    It is possible for names to be duplicated and refer to
    different sequences (considered to be 'contradictory' entries)
    and for a sequence to be duplicated and be referred to by
    multiple names (considered to be 'redundant' entries).

    Use the 'sequences' and 'names' methods to return lists of
    sequences and names, either for the whole SeqDb instance or
    just for specific names or sequences, respectively.

    To get the number of sequences stored:

    >>> len(s)

    To iterate over the SeqDb use:

    >>> for name,seq in s:
    >>> ... do something
    
    """
    def __init__(self):
        """Create a new SeqDb instance

        """
        self._sequences = dict()

    def add(self,name,seq):
        """Add a sequence to the SeqDb instance

        Arguments
          name: name to associate with the sequence
          seq:  sequence

        """
        name = name.strip()
        seq  = seq.strip()
        if seq not in self._sequences:
            self._sequences[seq] = list()
        if name not in self._sequences[seq]:
            self._sequences[seq].append(name)
        else:
            print("%s:%s already exists, ignored" % (name,seq))

    def sequences(self,name=None):
        """Return a list of sequences

        Arguments
          name: name to return associated sequences for.
            If name is None then all sequences are
            returned.

        Returns:
          List of sequences (strings).
        
        """
        if name is None:
            seqs = copy.copy(list(self._sequences.keys()))
        else:
            seqs = []
            for seq in self._sequences:
                if name in self._sequences[seq]:
                    seqs.append(seq)
        seqs.sort()
        return seqs

    def names(self,seq=None):
        """Return a list of names

        Arguments
          seq: sequence to return associated names for. If
            seq is None then all sequences are returned.

        Returns:
          List of names (strings).
        
        """
        # Return a list of names matching sequence
        # or all names if no sequence specified
        if seq is None:
            names = []
            for seq in self._sequences:
                for name in self._sequences[seq]:
                    if name not in names:
                        names.append(name)
        else:
            try:
                names = copy.copy(self._sequences[seq])
            except KeyError:
                names = []
        names.sort()
        return names

    def load(self,filen):
        """Load name/sequence pairs from a file

        The file should consist of one entry per line, as
        'name' <tab> 'sequence'. Blank lines and lines
        starting with '#' are ignored.

        (This is the format for FastQC's contaminants file.)

        Arguments:
          filen: name of file to load data from

        """
        fp = io.open(filen,'rt')
        for line in fp:
            line = line.strip('\n')
            if line.startswith('#') or line.strip() == '':
                continue
            try:
                name,seq = split_line(line)
                self.add(name,seq)
            except ValueError as ex:
                print("Error for line: '%s'" % line.rstrip('\n'))
                print("%s" % ex)
        fp.close()

    def load_from_fasta(self,fasta,prepend=False):
        """Load name/sequence pairs from a FASTA file

        Arguments:
          fasta: name of FASTA file to load data from
          prepend: optional, if True then prepend the name
            with the FASTA file name.

        """
        fp = io.open(fasta,'rt')
        name = None
        seq = []
        for line in fp:
            if line.startswith('>'):
                if name is not None:
                    self.add(name,''.join(seq))
                name = line[1:].strip()
                if prepend:
                    name = "%s %s" % (os.path.splitext(os.path.basename(fasta))[0],
                                      name)
                seq = []
            else:
                seq.append(line.strip())
        if name is not None:
            self.add(name,''.join(seq))
        fp.close()

    def save(self,filen,header=None,append=False):
        """Write name/sequence pairs out to file

        Arguments:
          filen: name of output file
          header: optional, arbitrary text to write to the
            head of the output as comments
          append: optional, if True then append to
            output file (default is to overwrite)

        """
        if append:
            mode = 'at'
        else:
            mode = 'wt'
        fp = io.open(filen,mode)
        if header is not None:
            for line in split_text(header,68,slack=True):
                fp.write("# %s\n" % line)
        for name,seq in self:
            fp.write(u"%s\t%s\n" % (name,seq))
        fp.close()

    def redundant_entries(self):
        """Return list of sequences with redundant entries

        Returns a list of those sequences for which there
        are multiple associated names.

        Returns:
          List of sequences.

        """
        redundant = []
        for seq in self._sequences:
            if len(self._sequences[seq]) > 1:
                redundant.append(seq)
        return redundant

    def contradictory_entries(self):
        """Return list of names associated with multiple sequences

        Returns a list of those names for which there are
        multiple associated sequences.

        Returns:
          List of names.

        """
        contradict = []
        for name in self.names():
            if len(self.sequences(name)) > 1:
                contradict.append(name)
        return contradict

    def __iter__(self):
        """Implement iteration over the SeqDb

        """
        name_seq = []
        for seq in self._sequences:
            for name in self._sequences[seq]:
                name_seq.append((name,seq))
        return iter(name_seq)

    def __len__(self):
        """Implement len(...) functionality

        """
        return len(self._sequences)

#######################################################################
# Functions
#######################################################################

def split_line(line):
    """Split a line read from file into a name/sequence tuple

    Arguments:
      line: line of text with name and sequence separated by tab.

    Returns:
      (name,sequence) tuple.

    """
    name = line.strip('\n').split('\t')[0]
    seq = line.strip('\n').split('\t')[-1]
    return (name,seq)

def split_text(text,char_limit,delims=' \t\n',strip=True,slack=False):
    """Break text into multiple lines

    Breaks supplied text into multiple lines where no line
    exceeds char_limit in length. Attempts to break text at
    positions marked by delimiters, so that (if using white
    space delimiters) words are not split.

    Arguments:
      text: text to be broken up
      char_limit: maximum length of lines to produce
      delims: optional, set of delimiter characters to
        break text on (defaults to whitespace characters)
      strip: optional, if True then trailing or leading
        delimiters are removed from lines (default)
      slack: optional, if True then allow lines to be
        longer than char_limit if not delimiter is found
        (default is to be strict)

    Returns:
      List of lines.

    """
    lines = []
    while len(text) > char_limit:
        # Locate nearest delimiter to the character limit
        line = text[:char_limit]
        while len(line) > 0:
            if line[-1] in delims:
                # Found delimiter at end of current line
                # fragment
                break
            else:
                line = line[:-1]
        # Unable to locate delimiter
        if len(line) == 0:
            if not slack:
                # Split on the character limit
                line = text[:char_limit]
            else:
                # Extend the line past the limit
                # to look for delimiter
                extent = char_limit
                while extent <= len(text):
                    line = text[:extent]
                    if line[-1] in delims:
                        break
                    else:
                        extent += 1
        # Append current line to list of lines and
        # prepare for next iteration
        text = text[len(line):]
        if strip:
            line = line.rstrip(delims)
            text = text.lstrip(delims)
        lines.append(line)
    # Append remaining text (which is less than character
    # limit)
    if strip:
        text = text.rstrip(delims)
    if text:
        lines.append(text)
    return lines

#######################################################################
# Main program
#######################################################################

def main():
    # Command line processing
    p = argparse.ArgumentParser(
        description="Read sequences and names from one or more "
        "INFILEs (which can be a mixture of FastQC 'contaminants' "
        "format and or Fasta format), check for redundancy "
        "(i.e. sequences with multiple associated names) and "
        "contradictions (i.e. names with multiple associated "
        "sequences).")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument('-o',action='store',dest='out_file',default=None,
                   help="write all sequences to OUT_FILE in FastQC "
                   "'contaminants' format")
    p.add_argument('-a',action='store',dest='append_file',default=None,
                   help="append sequences to existing APPEND_FILE (not "
                   "compatible with -o)")
    p.add_argument('-d',action='store',dest='description',default=None,
                   help="supply arbitrary text to write to the header "
                   "of the output file")
    p.add_argument('infile',metavar="INFILE",nargs='+',
                   help="input sequences")
    args = p.parse_args()
    if args.out_file and args.append_file:
        p.error("Cannot specify -o and -a options together")

    # Read in data
    s = SeqDb()
    for fn in args:
        print("Loading %s" % fn)
        if fn.endswith('.fasta') or fn.endswith('.fa'):
            s.load_from_fasta(fn,prepend=True)
        else:
            s.load(fn)
        print("Done - now have %d sequences stored" % len(s))

    # Do checks
    print("Checking for redundancy")
    redundant = s.redundant_entries()
    if len(redundant) > 0:
        print("Found %s sequence(s) with redundancy" % len(redundant))
        for seq in redundant:
            print("Multiple names for %s:" % seq)
            for name in s.names(seq):
                print("\t'%s'" % name)
    else:
        print("Ok - no redundancy found")

    print("Checking for contradictions")
    contradict = s.contradictory_entries()
    if len(contradict) > 0:
        print("Found %s contradiction(s)" % len(contradict))
        for name in contradict:
            print("Multiple seqs for %s:" % name)
            for seq in s.sequences(name):
                print("\t'%s'" % seq)
        sys.stderr.write("ERROR contradictory entries found, stopping")
        sys.exit(1)
    else:
        print("Ok - no contradictions found")

    # Output
    outfile = None
    if args.out_file is not None:
        print("Writing to %s" % args.out_file)
        s.save(args.out_file,header=args.description,append=False)
    elif args.append_file is not None:
        print("Appending to %s" % args.append_file)
        s.save(args.append_file,header=args.description,append=True)

