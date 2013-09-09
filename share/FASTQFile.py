#     FASTQFile.py: read and manipulate FASTQ files and data
#     Copyright (C) University of Manchester 2012-13 Peter Briggs
#
########################################################################
#
# FASTQFile.py
#
#########################################################################

__version__ = "0.3.0"

"""FASTQFile

Implements a set of classes for reading through FASTQ files and manipulating
the data within them:

* FastqIterator: enables looping through all read records in FASTQ file
* FastqRead: provides access to a single FASTQ read record
* SequenceIdentifier: provides access to sequence identifier info in a read
* FastqAttributes: provides access to gross attributes of FASTQ file

Information on the FASTQ file format: http://en.wikipedia.org/wiki/FASTQ_format
"""

#######################################################################
# Import modules that this module depends on
#######################################################################
from collections import Iterator
import os
import re
import logging
import gzip
import itertools

#######################################################################
# Class definitions
#######################################################################

class FastqIterator(Iterator):
    """FastqIterator

    Class to loop over all records in a FASTQ file, returning a FastqRead
    object for each record.

    Example looping over all reads
    >>> for read in FastqIterator(fastq_file):
    >>>    print read

    Input FASTQ can be in gzipped format; FASTQ data can also be supplied
    as a file-like object opened for reading, for example
    >>> fp = open(fastq_file,'rU')
    >>> for read in FastqIterator(fp=fp):
    >>>    print read
    >>> fp.close()

    """

    def __init__(self,fastq_file=None,fp=None):
        """Create a new FastqIterator

        The input FASTQ can be either a text file or a compressed (gzipped)
        FASTQ, specified via a file name (using the 'fastq' argument), or a
        file-like object opened for line reading (using the 'fp' argument).

        Arguments:
           fastq_file: name of the FASTQ file to iterate through
           fp: file-like object opened for reading

        """
        self.__fastq_file = fastq_file
        if fp is None:
            self.__fp = get_fastq_file_handle(self.__fastq_file)
        else:
            self.__fp = fp

    def next(self):
        """Return next record from FASTQ file as a FastqRead object
        """
        seqid_line = self.__fp.readline()
        seq_line = self.__fp.readline()
        optid_line = self.__fp.readline()
        quality_line = self.__fp.readline()
        if quality_line != '':
            return FastqRead(seqid_line,seq_line,optid_line,quality_line)
        else:
            # Reached EOF
            if self.__fastq_file is None:
                self.__fp.close()
            raise StopIteration

class FastqRead:
    """Class to store a FASTQ record with information about a read

    Provides the following properties for accessing the read data:

    seqid: the "sequence identifier" information (first line of the read record)
      as a SequenceIdentifier object
    sequence: the raw sequence (second line of the record)
    optid: the optional sequence identifier line (third line of the record)
    quality: the quality values (fourth line of the record)

    Additional properties:

    raw_seqid: the original sequence identifier string supplied when the
               object was created
    seqlen: length of the sequence
    maxquality: maximum quality value (in character representation)
    minquality: minimum quality value (in character representation)

    (Note that quality scores can only be obtained from character representations
    once the encoding scheme is known)

    is_colorspace: returns True if the read looks like a colorspace read, False
      otherwise

    """

    def __init__(self,seqid_line=None,seq_line=None,optid_line=None,quality_line=None):
        """Create a new FastqRead object

        Arguments:
          seqid_line: first line of the read record
          sequence: second line of the record
          optid: third line of the record
          quality: fourth line of the record
        """
        self.raw_seqid = seqid_line
        self.sequence = str(seq_line).strip()
        self.optid = str(optid_line.strip())
        self.quality = str(quality_line.strip())

    @property
    def seqid(self):
        try:
            return self._seqid
        except AttributeError:
            self._seqid = SequenceIdentifier(self.raw_seqid)
            return self._seqid

    @property
    def seqlen(self):
        if self.is_colorspace:
            return len(self.sequence) - 1
        else:
            return len(self.sequence)

    @property
    def maxquality(self):
        maxqual = None
        for q in self.quality:
            if maxqual is None:
                maxqual = ord(q)
            else:
                maxqual = max(maxqual,ord(q))
        return chr(maxqual)

    @property
    def minquality(self):
        minqual = None
        for q in self.quality:
            if minqual is None:
                minqual = ord(q)
            else:
                minqual = min(minqual,ord(q))
        return chr(minqual)

    @property
    def is_colorspace(self):
        if self.seqid.format is None:
            # Check if it looks like colorspace
            # Sequence starts with 'T' and only contains characters
            # 0-3 or '.'
            sequence = self.sequence
            if sequence.startswith('T'):
                for c in sequence[1:]:
                    if c not in '.0123':
                        return False
                # Passed colorspace tests
                return True
        # Not colorspace
        return False

    def __repr__(self):
        return '\n'.join((str(self.seqid),
                          self.sequence,
                          self.optid,
                          self.quality))

class SequenceIdentifier:
    """Class to store/manipulate sequence identifier information from a FASTQ record

    Provides access to the data items in the sequence identifier line of a FASTQ
    record.
    """

    def __init__(self,seqid):
        """Create a new SequenceIdentifier object

        Arguments:
          seqid: the sequence identifier line (i.e. first line) from the
            FASTQ read record
        """
        self.__seqid = str(seqid).strip()
        self.format = None
        # Identify sequence id line elements
        if seqid.startswith('@'):
            # example of Illumina 1.8+ format:
            # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
            try:
                fields = self.__seqid[1:].split(':')
                self.instrument_name = fields[0]
                self.run_id = fields[1]
                self.flowcell_id = fields[2]
                self.flowcell_lane = fields[3]
                self.tile_no = fields[4]
                self.x_coord = fields[5]
                self.y_coord = fields[6].split(' ')[0]
                self.multiplex_index_no = None
                self.pair_id = fields[6].split(' ')[1]
                self.bad_read = fields[7]
                self.control_bit_flag = fields[8]
                self.index_sequence = fields[9]
                self.format = 'illumina18'
                return
            except IndexError:
                pass
            # Example of earlier Illumina format (1.3/1.5):
            # @HWUSI-EAS100R:6:73:941:1973#0/1
            try:
                fields = self.__seqid[1:].split(':')
                self.instrument_name = fields[0]
                self.run_id = None
                self.flowcell_id = None
                self.flowcell_lane = fields[1]
                self.tile_no = fields[2]
                self.x_coord = fields[3]
                self.y_coord = fields[4].split('#')[0]
                self.multiplex_index_no = fields[4].split('#')[1].split('/')[0]
                self.pair_id = fields[4].split('#')[1].split('/')[1]
                self.bad_read = None
                self.control_bit_flag = None
                self.index_sequence = None
                self.format = 'illumina'
                return
            except IndexError:
                pass

    def is_pair_of(self,seqid):
        """Check if this forms a pair with another SequenceIdentifier

        """
        # Check we have r1/r2
        read_indices = [int(self.pair_id),int(seqid.pair_id)]
        read_indices.sort()
        if read_indices != [1,2]:
            return False
        # Check all other attributes match
        try:
            return (self.instrument_name  == seqid.instrument_name and
                    self.run_id           == seqid.run_id and
                    self.flowcell_id      == seqid.flowcell_id and
                    self.flowcell_lane    == seqid.flowcell_lane and
                    self.tile_no          == seqid.tile_no and
                    self.x_coord          == seqid.x_coord and
                    self.y_coord          == seqid.y_coord and
                    self.multiplex_index_no == seqid.multiplex_index_no and
                    self.bad_read         == seqid.bad_read and
                    self.control_bit_flag == seqid.control_bit_flag and
                    self.index_sequence   == seqid.index_sequence)
        except Exception:
            return False
        
    def __repr__(self):
        if self.format == 'illumina18':
            return "@%s:%s:%s:%s:%s:%s:%s %s:%s:%s:%s" % (self.instrument_name, 
                                                          self.run_id,
                                                          self.flowcell_id,
                                                          self.flowcell_lane,
                                                          self.tile_no,
                                                          self.x_coord,
                                                          self.y_coord,
                                                          self.pair_id,
                                                          self.bad_read,
                                                          self.control_bit_flag,
                                                          self.index_sequence)
        elif self.format == 'illumina':
            return "@%s:%s:%s:%s:%s#%s/%s" % (self.instrument_name,
                                              self.flowcell_lane,
                                              self.tile_no,
                                              self.x_coord,
                                              self.y_coord,
                                              self.multiplex_index_no,
                                              self.pair_id)
        else:
            # Return what was put in
            return self.__seqid

class FastqAttributes:
    """Class to provide access to gross attributes of a FASTQ file

    Given a FASTQ file (can be uncompressed or gzipped), enables
    various attributes to be queried via the following properties:

    nreads: number of reads in the FASTQ file
    fsize:  size of the file (in bytes)
    

    """
    def __init__(self,fastq_file=None,fp=None):
        """Create a new FastqAttributes object

        Arguments:
           fastq_file: name of the FASTQ file to iterate through
           fp: file-like object opened for reading
          
        """
        self.__fastq_file = fastq_file
        if fp is None:
            self.__fp = get_fastq_file_handle(self.__fastq_file)
        else:
            self.__fp = fp
        self.__nreads = None

    @property
    def nreads(self):
        """Return number of reads in the FASTQ file

        """
        if self.__nreads is None:
            self.__nreads = nreads(fastq=self.__fastq_file,fp=self.__fp)
        return self.__nreads

    @property
    def fsize(self):
        """Return size of the FASTQ file (bytes)
        
        """
        return os.path.getsize(self.__fastq_file)

#######################################################################
# Functions
#######################################################################

def get_fastq_file_handle(fastq):
    """Return a file handle opened for reading for a FASTQ file

    Deals with both compressed (gzipped) and uncompressed FASTQ
    files.

    Arguments:
      fastq: name (including path, if required) of FASTQ file.
        The file can be gzipped (must have '.gz' extension)

    Returns:
      File handle that can be used for read operations.
    """
    if os.path.splitext(fastq)[1] == '.gz':
        return gzip.open(fastq,'r')
    else:
        return open(fastq,'rU')

def nreads(fastq=None,fp=None):
    """Return number of reads in a FASTQ file

    Performs a simple-minded read count, by counting the number of lines
    in the file and dividing by 4.

    The FASTQ file can be specified either as a file name (using the 'fastq'
    argument) or as a file-like object opened for line reading (using the
    'fp' argument).

    This function can handle gzipped FASTQ files supplied via the 'fastq'
    argument.

    Line counting uses a variant of the "buf count" method outlined here:
    http://stackoverflow.com/a/850962/579925

    Arguments:
      fastq: fastq(.gz) file
      fp: open file descriptor for fastq file

    Returns:
      Number of reads

    """
    nlines = 0
    if fp is None:
        if os.path.splitext(fastq)[1] == '.gz':
            fp = gzip.open(fastq)
        else:
            fp = open(fastq)
    buf_size = 1024 * 1024
    read_fp = fp.read # optimise the loop
    buf = read_fp(buf_size)
    while buf:
        nlines += buf.count('\n')
        buf = read_fp(buf_size)
    if fastq is not None:
        fp.close()
    if (nlines%4) != 0:
        raise Exception,"Bad read count (not fastq file, or corrupted?)"
    return nlines/4

def fastqs_are_pair(fastq1=None,fastq2=None,verbose=True,fp1=None,fp2=None):
    """Check that two FASTQs form an R1/R2 pair

    Arguments:
      fastq1: first FASTQ
      fastq2: second FASTQ

    Returns:
      True if each read in fastq1 forms an R1/R2 pair with the equivalent
      read (i.e. in the same position) in fastq2, otherwise False if
      any do not form an R1/R2 (or if there are more reads in one than
      than the other).

    """
    # Use itertools.izip_longest, which will return None if either of
    # the fastqs is exhausted before the other
    i = 0
    for r1,r2 in itertools.izip_longest(FastqIterator(fastq_file=fastq1,fp=fp1),
                                        FastqIterator(fastq_file=fastq2,fp=fp2)):
        i += 1
        if verbose:
            if i%100000 == 0:
                print "Examining pair #%d" % i
        if not r1.seqid.is_pair_of(r2.seqid):
            if verbose:
                print "Unpaired headers for read position #%d:" % i
                print "%s\n%s" % (r1.seqid,r2.seqid)
            return False
    return True

#######################################################################
# Tests
#######################################################################

import unittest
import cStringIO

fastq_data = """@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 1:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 1:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

fastq_data2 = """@73D9FA:3:FC:1:1:7507:1000 2:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 2:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 2:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
@73D9FA:3:FC:1:1:7488:1000 2:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 2:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

class TestFastqIterator(unittest.TestCase):
    """Tests of the FastqIterator class
    """

    def test_fastq_iterator(self):
        """Check iteration over small FASTQ file
        """
        fp = cStringIO.StringIO(fastq_data)
        fastq = FastqIterator(fp=fp)
        nreads = 0
        fastq_source = cStringIO.StringIO(fastq_data)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

class TestFastqRead(unittest.TestCase):
    """Tests of the FastqRead class
    """

    def test_fastqread(self):
        """Check FastqRead stores input correctly
        """
        seqid = "@HWI-ST1250:47:c0tr3acxx:4:1101:1283:2323 1:N:0:ACAGTGATTCTTTCCC\n"
        seq = "GGTGTCTTCAAAAAGGCCAACCAGATAGGCCTCACTTGCCTCCTGCAAAGCACCGATAGCTGCGCTCTGGAAGCGCAGATCTGTTTTAAAGTCCTGAGCAA\n"
        optid = "+\n"
        quality = "=@@D;DDFFHDHHIJIIIIIIGIGIGDIHGGEIGICFGIGHIIGII@?FGIGIEI@EHEFFEEBAACD;@ACCDDBDBDDACCC3>CD>:ADCCDDD?C@\n"
        read = FastqRead(seqid,seq,optid,quality)
        self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
        self.assertEqual(str(read.seqid),seqid.rstrip('\n'))
        self.assertEqual(read.raw_seqid,seqid)
        self.assertEqual(read.sequence,seq.rstrip('\n'))
        self.assertEqual(read.optid,optid.rstrip('\n'))
        self.assertEqual(read.quality,quality.rstrip('\n'))
        self.assertEqual(read.seqlen,len(seq.rstrip('\n')))
        self.assertEqual(read.maxquality,'J')
        self.assertEqual(read.minquality,'3')
        self.assertFalse(read.is_colorspace)

    def test_is_colorspace(self):
        """Check FastqRead detects colorspace correctly
        """
        read = FastqRead("@1_14_622",
                         "T221.0033033232320030021103233332300123110201010031",
                         "+",
                         "BBA!>AA,B>;;=A%39%B8====>0?-?%9A2<)3?(4*36%A%4&+9%")
        self.assertTrue(read.is_colorspace)

class TestSequenceIdentifier(unittest.TestCase):
    """Tests of the SequenceIdentifier class
    """

    def test_read_illumina18_id(self):
        """Process an 'illumina18'-style sequence identifier
        """
        seqid_string = "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('EAS139',seqid.instrument_name)
        self.assertEqual('136',seqid.run_id)
        self.assertEqual('FC706VJ',seqid.flowcell_id)
        self.assertEqual('2',seqid.flowcell_lane)
        self.assertEqual('2104',seqid.tile_no)
        self.assertEqual('15343',seqid.x_coord)
        self.assertEqual('197393',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('Y',seqid.bad_read)
        self.assertEqual('18',seqid.control_bit_flag)
        self.assertEqual('ATCACG',seqid.index_sequence)

    def test_read_illumina18_id_no_index_sequence(self):
        """Process an 'illumina18'-style sequence id with no index sequence (barcode)
        """
        seqid_string = "@73D9FA:3:FC:1:1:7507:1000 1:N:0:"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('73D9FA',seqid.instrument_name)
        self.assertEqual('3',seqid.run_id)
        self.assertEqual('FC',seqid.flowcell_id)
        self.assertEqual('1',seqid.flowcell_lane)
        self.assertEqual('1',seqid.tile_no)
        self.assertEqual('7507',seqid.x_coord)
        self.assertEqual('1000',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('N',seqid.bad_read)
        self.assertEqual('0',seqid.control_bit_flag)
        self.assertEqual('',seqid.index_sequence)        

    def test_read_illumina_id(self):
        """Process an 'illumina'-style sequence identifier
        """
        seqid_string = "@HWUSI-EAS100R:6:73:941:1973#0/1"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('HWUSI-EAS100R',seqid.instrument_name)
        self.assertEqual('6',seqid.flowcell_lane)
        self.assertEqual('73',seqid.tile_no)
        self.assertEqual('941',seqid.x_coord)
        self.assertEqual('1973',seqid.y_coord)
        self.assertEqual('0',seqid.multiplex_index_no)
        self.assertEqual('1',seqid.pair_id)

    def test_unrecognised_id_format(self):
        """Process an unrecognised sequence identifier
        """
        seqid_string = "@SEQID"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual(None,seqid.format)

    def test_is_pair_of(self):
        """Check that paired sequence identifiers are recognised as such
        """
        seqid1 = "@HWI-700511R:183:D2C8UACXX:1:1101:1115:2123 1:N:0:GCCAAT"
        seqid2 = "@HWI-700511R:183:D2C8UACXX:1:1101:1115:2123 2:N:0:GCCAAT"
        seqid3 = "@HWI-700511R:183:D2C8UACXX:5:1101:1496:2199 2:N:0:GCCAAT"
        self.assertTrue(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid2)))
        self.assertTrue(SequenceIdentifier(seqid2).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid2).is_pair_of(SequenceIdentifier(seqid2)))
        self.assertFalse(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid3).is_pair_of(SequenceIdentifier(seqid1)))

class TestFastqAttributes(unittest.TestCase):
    """Tests of the FastqAttributes class
    """

    def test_fastq_attributes_nreads(self):
        """Check number of reads
        """
        fp = cStringIO.StringIO(fastq_data)
        attrs = FastqAttributes(fp=fp)
        self.assertEqual(attrs.nreads,5)

class TestNReads(unittest.TestCase):
    """Tests of the nreads function
    """

    def test_nreads(self):
        """Check that nreads returns correct read count
        """
        fp = cStringIO.StringIO(fastq_data)
        self.assertEqual(nreads(fp=fp),5)

class TestFastqsArePair(unittest.TestCase):
    """Tests of the fastqs_are_pair function
    """
    
    def test_fastqs_are_pair(self):
        """Check that fastq pair is recognised as such
        """
        fp1 = cStringIO.StringIO(fastq_data)
        fp2 = cStringIO.StringIO(fastq_data2)
        self.assertTrue(fastqs_are_pair(fp1=fp1,fp2=fp2,verbose=False))

def run_tests():
    """Run the tests
    """
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Run the tests
    run_tests()
