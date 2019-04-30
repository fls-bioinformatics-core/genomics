#!/usr/bin/env python
#
#     manage_seqs.py: Utility for handling sets of named sequences
#     Copyright (C) University of Manchester 2014-2019 Peter Briggs
#
########################################################################
#
# manage_seqs.py
#
#########################################################################

"""manage_seqs

Utility for handling sets of named sequences.

Written to deal with extending and validating FastQC contaminant files.

Usage:

manage_seqs.py [-o OUTFILE|-a OUTFILE] [-d DESCRIPTION] INFILE [INFILE...]

"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.0.3"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import copy
import sys
import optparse

#######################################################################
# Classes
#######################################################################

class SeqDb(object):
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
            print "%s:%s already exists, ignored" % (name,seq)

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
            seqs = copy.copy(self._sequences.keys())
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
        fp = open(filen,'rU')
        for line in fp:
            line = line.strip('\n')
            if line.startswith('#') or line.strip() == '':
                continue
            try:
                name,seq = split_line(line)
                self.add(name,seq)
            except ValueError,ex:
                print "Error for line: '%s'" % line.rstrip('\n')
                print "%s" % ex
        fp.close()

    def load_from_fasta(self,fasta,prepend=False):
        """Load name/sequence pairs from a FASTA file

        Arguments:
          fasta: name of FASTA file to load data from
          prepend: optional, if True then prepend the name
            with the FASTA file name.

        """
        fp = open(fasta,'rU')
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
            mode = 'a'
        else:
            mode = 'w'
        fp = open(filen,mode)
        if header is not None:
            for line in split_text(header,68,slack=True):
                fp.write("# %s\n" % line)
        for name,seq in self:
            fp.write("%s\t%s\n" % (name,seq))
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
# Unit tests
#######################################################################

import unittest
import tempfile

class TestSeqDb(unittest.TestCase):
    """Tests for the SeqDb class

    """
    def setUp(self):
        # Placeholder for temporary file used in some tests
        self.tmp_file = None
    def tearDown(self):
        # Remove temporary file after test completes, if it exists
        if self.tmp_file and os.path.exists(self.tmp_file):
            os.remove(self.tmp_file)
    def test_empty_seqdb(self):
        """Check 'empty' SeqDb instance
        """
        s = SeqDb()
        self.assertEqual(len(s),0)
        self.assertEqual(s.sequences(),[])
        self.assertEqual(s.names(),[])
    def test_seqdb_add(self):
        """Add sequence fragments to SeqDb programmatically
        """
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        self.assertEqual(len(s),1)
        self.assertEqual(s.sequences(),['ATAGAC'])
        self.assertEqual(s.names(),['Sequence #1'])
        s.add('Sequence #2','ATAGGC')
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_add_multiples(self):
        """Add repeated sequences to SeqDb
        """
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.add('Sequence #2','ATAGGC')
        s.add('Sequence #3','ATAGGC')
        s.add('Sequence #4','ATAGCC')
        s.add('Sequence #4','ATAGCA')
        self.assertEqual(len(s),4)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGCA','ATAGCC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2','Sequence #3','Sequence #4'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #4'),['ATAGCA','ATAGCC'])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2','Sequence #3'])
        self.assertEqual(s.names('ATAGCC'),['Sequence #4'])
        self.assertEqual(s.names('ATAGCA'),['Sequence #4'])
        self.assertEqual(s.redundant_entries(),['ATAGGC'])
        self.assertEqual(s.contradictory_entries(),['Sequence #4'])
    def test_seqdb_load(self):
        """Load sequences into SeqDb from FastQC-style input file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'w')
        fp.write("Sequence #1\tATAGAC\nSequence #2\t\tATAGGC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.load(self.tmp_file)
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_load_from_fasta(self):
        """Load sequences into SeqDb from FASTA input file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'w')
        fp.write(">Sequence #1\nATAGAC\n>Sequence #2\nATA\nGGC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.load_from_fasta(self.tmp_file)
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_save(self):
        """Write sequences from SeqDb to new output file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        # Run test
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.save(self.tmp_file)
        content = open(self.tmp_file,'r').read()
        self.assertEqual(content,"Sequence #1\tATAGAC\nSequence #2\tATAGGC\n")
    def test_seqdb_save_append(self):
        """Append sequences from SeqDb to an existing file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'w')
        fp.write("# Initial sequence\nSequence #3\tATAGCC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.save(self.tmp_file,append=True)
        content = open(self.tmp_file,'r').read()
        self.assertEqual(content,"# Initial sequence\nSequence #3\tATAGCC\nSequence #1\tATAGAC\nSequence #2\tATAGGC\n")

class TestSplitLineFunction(unittest.TestCase):
    """Unit tests for the 'split_line' function
    """
    def test_split_line_defaults(self):
        """'split_line' works with default settings
        """
        self.assertEqual(split_text("Some text",10),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10),
                         ['This is','some text'])
        self.assertEqual(split_text("This is some even longer text",10),
                         ['This is','some even','longer','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10),
                         ['This is','some text','Over','multiple','lines'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_no_strip(self):
        """'split_line' works when delimiter stripping is turned off
        """
        self.assertEqual(split_text("Some text",10,strip=False),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,strip=False),
                         ['This is ','some text'])
        self.assertEqual(split_text("This is some even longer text",10,strip=False),
                         ['This is ','some even ','longer ','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10,strip=False),
                         ['This is ','some text\n','Over ','multiple ','lines\n'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_non_default_delimiter(self):
        """'split_line' works with non-default delimiter
        """
        self.assertEqual(split_text("Some text",10,delims=':'),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,delims=':'),
                         ['This is so','me text'])
        self.assertEqual(split_text("This:is:some:even:longer:text",10,delims=':'),
                         ['This:is','some:even','longer','text'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10,delims=':'),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_slack(self):
        """'split_line' works when 'slack' splitting is used
        """
        self.assertEqual(split_text("Some text",10,slack=True),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,slack=True),
                         ['This is','some text'])
        self.assertEqual(split_text("This is some even longer text",10,slack=True),
                         ['This is','some even','longer','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10,slack=True),
                         ['This is','some text','Over','multiple','lines'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10,slack=True),
                         ['Supercalifragilisticexpialidocious'])

#######################################################################
# Main program
#######################################################################

if __name__ == '__main__':

    # Command line processing
    p = optparse.OptionParser(usage="%prog OPTIONS INFILE [INFILE...]",
                              version="%prog "+__version__,
                              description="Read sequences and names from one or more "
                              "INFILEs (which can be a mixture of FastQC 'contaminants' "
                              "format and or Fasta format), check for redundancy "
                              "(i.e. sequences with multiple associated names) and "
                              "contradictions (i.e. names with multiple associated "
                              "sequences).")
    p.add_option('-o',action='store',dest='out_file',default=None,
                 help="write all sequences to OUT_FILE in FastQC 'contaminants' "
                 "format")
    p.add_option('-a',action='store',dest='append_file',default=None,
                 help="append sequences to existing APPEND_FILE (not compatible with -o)")
    p.add_option('-d',action='store',dest='description',default=None,
                 help="supply arbitrary text to write to the header of the output "
                 "file")
    options,args = p.parse_args()
    if not len(args):
        p.error("Need at least one input file")
    if options.out_file and options.append_file:
        p.error("Cannot specify -o and -a options together")

    # Read in data
    s = SeqDb()
    for fn in args:
        print "Loading %s" % fn
        if fn.endswith('.fasta') or fn.endswith('.fa'):
            s.load_from_fasta(fn,prepend=True)
        else:
            s.load(fn)
        print "Done - now have %d sequences stored" % len(s)

    # Do checks
    print "Checking for redundancy"
    redundant = s.redundant_entries()
    if len(redundant) > 0:
        print "Found %s sequence(s) with redundancy" % len(redundant)
        for seq in redundant:
            print "Multiple names for %s:" % seq
            for name in s.names(seq):
                print "\t'%s'" % name
    else:
        print "Ok - no redundancy found"

    print "Checking for contradictions"
    contradict = s.contradictory_entries()
    if len(contradict) > 0:
        print "Found %s contradiction(s)" % len(contradict)
        for name in contradict:
            print "Multiple seqs for %s:" % name
            for seq in s.sequences(name):
                print "\t'%s'" % seq
        sys.stderr.write("ERROR contradictory entries found, stopping")
        sys.exit(1)
    else:
        print "Ok - no contradictions found"

    # Output
    outfile = None
    if options.out_file is not None:
        print "Writing to %s" % options.append_file
        s.save(options.out_file,header=options.description,append=False)
    elif options.append_file is not None:
        print "Appending to %s" % options.append_file
        s.save(options.append_file,header=options.description,append=True)
