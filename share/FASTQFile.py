#     FASTQFile.py: read and manipulate FASTQ files and data
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# FASTQFile.py
#
#########################################################################

__version__ = "0.1.0"

"""FASTQFile

Implements a set of classes for reading through FASTQ files and manipulating
the data within them:

* FastqIterator: enables looping through all read records in FASTQ file
* FastqRead: provides access to a single FASTQ read record

Information on the FASTQ file format:
http://en.wikipedia.org/wiki/FASTQ_format
"""

#######################################################################
# Import modules that this module depends on
#######################################################################
from collections import Iterator
import os
import re
import logging
import gzip

#######################################################################
# Constants/globals
#######################################################################

# Regular expression to match an "ILLUMINA18" format sequence identifier
# i.e. Illumina 1.8+
# @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
ILLUMINA18_SEQID = re.compile(r"^@([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^ ]+) ([^\:]+):([^\:]+):([^\:]+):([^\:]+)$")

# Regular expression to match a "ILLUMINA" format sequence identifier
# i.e. Illumina 1.3+, 1.5+
# @HWUSI-EAS100R:6:73:941:1973#0/1
ILLUMINA_SEQID = re.compile(r"^@([^\:]+):([^\:]+):([^\:]+):([^\:]+):([^\#]+)#([^/])/(.+)$")

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
    """

    def __init__(self,fastq_file):
        """Create a new FastqIterator

        The input FASTQ can be either a text file or a compressed (gzipped)
        FASTQ.

        Arguments:
           fastq_file: name of the FASTQ file to iterate through
        """
        if os.path.splitext(fastq_file)[1] == '.gz':
            self.__fp = gzip.open(fastq_file,'r')
        else:
            self.__fp = open(fastq_file,'rU')

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
            self.__fp.close()
            raise StopIteration

class FastqRead:
    """Class to store a FASTQ record with information about a read

    Provides the following properties:

    seqid: the "sequence identifier" information (first line of the read record)
      as a SequenceIdentifier object
    sequence: the raw sequence (second line of the record)
    optid: the optional sequence identifier line (third line of the record)
    quality: the quality values (fourth line of the record)
    """

    def __init__(self,seqid_line=None,seq_line=None,optid_line=None,quality_line=None):
        """Create a new FastqRead object

        Arguments:
          seqid_line: first line of the read record
          sequence: second line of the record
          optid: third line of the record
          quality: fourth line of the record
        """
        self.seqid = SequenceIdentifier(seqid_line)
        self.sequence = str(seq_line).strip()
        self.optid = str(optid_line.strip())
        self.quality = str(quality_line.strip())

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
        # There are at least two variants of the sequence id line, this is an
        # example of Illumina 1.8+ format:
        # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
        # The alternative is Illumina:
        # @HWUSI-EAS100R:6:73:941:1973#0/1
        illumina18 = ILLUMINA18_SEQID.match(self.__seqid)
        illumina = ILLUMINA_SEQID.match(self.__seqid)
        if illumina18:
            self.format = 'illumina18'
            self.instrument_name = illumina18.group(1)
            self.run_id = illumina18.group(2)
            self.flowcell_id = illumina18.group(3)
            self.flowcell_lane = illumina18.group(4)
            self.tile_no = illumina18.group(5)
            self.x_coord = illumina18.group(6)
            self.y_coord = illumina18.group(7)
            self.multiplex_index_no = None
            self.pair_id = illumina18.group(8)
            self.bad_read = illumina18.group(9)
            self.control_bit_flag = illumina18.group(10)
            self.index_sequence = illumina18.group(11)
        elif illumina:
            self.format = 'illumina'
            self.instrument_name = illumina.group(1)
            self.run_id = None
            self.flowcell_id = None
            self.flowcell_lane = illumina.group(2)
            self.tile_no = illumina.group(3)
            self.x_coord = illumina.group(4)
            self.y_coord = illumina.group(5)
            self.multiplex_index_no = illumina.group(6)
            self.pair_id = illumina.group(7)
            self.bad_read = None
            self.control_bit_flag = None
            self.index_sequence = None
        
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

#######################################################################
# Functions
#######################################################################

def run_tests():
    """Run the tests
    """
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()

#######################################################################
# Tests
#######################################################################

import unittest

class TestSequenceIdentifier(unittest.TestCase):
    """Tests of the SequenceIdentifier class
    """

    def test_read_illumina18_id(self):
        """Process a 'illumina18'-style sequence identifier
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

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Run the tests
    run_tests()
