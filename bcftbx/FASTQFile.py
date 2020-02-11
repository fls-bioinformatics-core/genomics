#     FASTQFile.py: read and manipulate FASTQ files and data
#     Copyright (C) University of Manchester 2012-19 Peter Briggs
#
########################################################################
#
# FASTQFile.py
#
#########################################################################

"""
A set of classes for reading through FASTQ files and manipulating
the data within them:

* FastqIterator: enables looping through all read records in FASTQ file
* FastqRead: provides access to a single FASTQ read record
* SequenceIdentifier: provides access to sequence identifier info in a read
* FastqAttributes: provides access to gross attributes of FASTQ file

Additionally there are a few utility functions:

* get_fastq_file_handle: return a file handled opened for reading a FASTQ file
* nreads: return the number of reads in a FASTQ file
* fastqs_are_pair: check whether two FASTQs form an R1/R2 pair

Information on the FASTQ file format: http://en.wikipedia.org/wiki/FASTQ_format

"""

__version__ = "1.0.5"

CHUNKSIZE = 102400

#######################################################################
# Import modules that this module depends on
#######################################################################
from builtins import str
try:
    from collections.abc import Iterator
except ImportError:
    from collections import Iterator
import os
import io
import re
import logging
import gzip
from future.moves import itertools

#######################################################################
# Precompiled regular expressions
#######################################################################

# Match Illumina 1.8+ format, e.g.:
# @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
RE_ILLUMINA18 = re.compile(r"^@([^:]+):([0-9]+):([^:]+):([0-9]+):([0-9]+):([0-9]+):([0-9]+) (1|2):(Y|N):([0-9]+):(.*)$")
#
# Match  earlier Illumina format (1.3/1.5), e.g.:
# @HWUSI-EAS100R:6:73:941:1973#0/1
RE_ILLUMINA = re.compile(r"^@([^:]+):([0-9]+):([0-9]+):([0-9]+):([0-9]+)#([0-9]+)/(1|2)$")

#######################################################################
# Class definitions
#######################################################################

class FastqIterator(Iterator):
    """FastqIterator

    Class to loop over all records in a FASTQ file, returning a FastqRead
    object for each record.

    Example looping over all reads:

    >>> for read in FastqIterator(fastq_file):
    >>>    print(read)

    Input FASTQ can be in gzipped format; FASTQ data can also be supplied
    as a file-like object opened for reading, for example:

    >>> fp = io.open(fastq_file,'rt')
    >>> for read in FastqIterator(fp=fp):
    >>>    print(read)
    >>> fp.close()

    """

    def __init__(self,fastq_file=None,fp=None,bufsize=CHUNKSIZE):
        """Create a new FastqIterator

        The input FASTQ can be either a text file or a compressed (gzipped)
        FASTQ, specified via a file name (using the 'fastq' argument), or a
        file-like object opened for line reading (using the 'fp' argument).

        Args:
           fastq_file: name of the FASTQ file to iterate through
           fp: file-like object opened for reading
           bufsize: optional; integer specifying number of bytes to
             read as a single 'chunk' from disk

        """
        self.__fastq_file = fastq_file
        self.__bufsize = bufsize
        if fp is None:
            self.__fp = get_fastq_file_handle(self.__fastq_file)
        else:
            self.__fp = fp
        self._buf = ''
        self._lines = []
        self._ip = 0

    def __next__(self):
        """Return next record from FASTQ file as a FastqRead object
        """
        # Convenience variables
        lines = self._lines
        buf = self._buf
        ip = self._ip
        bufsize = self.__bufsize
        # Do we already have a read to return?
        while len(lines) < 4:
            # Fetch more data
            data = self.__fp.read(bufsize)
            if not data:
                # Reached EOF
                if self.__fastq_file is None:
                    self.__fp.close()
                raise StopIteration
            # Add to buffer and split into lines
            buf = buf + data
            if buf[-1] != '\n':
                i = buf.rfind('\n')
                if i == -1:
                    continue
                else:
                    lines.extend(buf[:i].split('\n'))
                    buf = buf[i+1:]
            else:
                lines.extend(buf[:-1].split('\n'))
                buf = ''
        # Return a read
        read = lines[ip:ip + 4]
        ip = ip + 4
        if (len(lines) - ip) < 4:
            # Not enough lines for another read so
            # reset the buffer
            lines = lines[ip:]
            ip = 0
        # Update internals
        self._lines = lines
        self._buf = buf
        self._ip = ip
        return FastqRead(*read)

    def next(self):
        """
        Implemented for Python2 compatibility
        """
        return self.__next__()

class FastqRead(object):
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
        self.sequence = str(seq_line).rstrip()
        self.optid = str(optid_line).rstrip()
        self.quality = str(quality_line).rstrip()

    @property
    def seqid(self):
        try:
            return self._seqid
        except AttributeError:
            self._seqid = SequenceIdentifier(self.raw_seqid)
            return self._seqid

    @property
    def seqlen(self):
        try:
            return self._seqlen
        except AttributeError:
            if self.is_colorspace:
                self._seqlen = len(self.sequence) - 1
            else:
                self._seqlen = len(self.sequence)
            return self._seqlen

    @property
    def maxquality(self):
        try:
            # Cached value
            return self._maxqual
        except AttributeError:
            # Compute, store and return
            if self.quality:
                self._maxqual = max(self.quality)
            else:
                self._maxqual = ''
        return self._maxqual

    @property
    def minquality(self):
        try:
            # Cached value
            return self._minqual
        except AttributeError:
            # Compute, store and return
            if self.quality:
                self._minqual = min(self.quality)
            else:
                self._minqual = ''
        return self._minqual

    @property
    def is_colorspace(self):
        try:
            return self._is_colorspace
        except AttributeError:
            pass
        if self.seqid.format is None:
            # Check if it looks like colorspace
            # Sequence starts with 'T' and only contains characters
            # 0-3 or '.'
            sequence = self.sequence
            if sequence.startswith('T'):
                for c in sequence[1:]:
                    if c not in '.0123':
                        self._is_colorspace = False
                        return self._is_colorspace
                # Passed colorspace tests
                self._is_colorspace = True
                return self._is_colorspace
        # Not colorspace
        self._is_colorspace = False
        return self._is_colorspace

    def __repr__(self):
        return '\n'.join((str(self.seqid),
                          self.sequence,
                          self.optid,
                          self.quality))

    def __eq__(self,other):
        return (str(self) == str(other))

class SequenceIdentifier(object):
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
        # Initialise
        self.__seqid = str(seqid).rstrip()
        self.instrument_name = None
        self.run_id = None
        self.flowcell_id = None
        self.flowcell_lane = None
        self.tile_no = None
        self.x_coord = None
        self.y_coord = None
        self.multiplex_index_no = None
        self.pair_id =  None
        self.bad_read = None
        self.control_bit_flag = None
        self.index_sequence = None
        self._format = None
        # Identify sequence id line elements
        m = RE_ILLUMINA18.match(self.__seqid)
        if m:
            # example of Illumina 1.8+ format:
            # @EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG
            self._format = 'illumina18'
            self.instrument_name = m.group(1)
            self.run_id = m.group(2)
            self.flowcell_id = m.group(3)
            self.flowcell_lane = m.group(4)
            self.tile_no = m.group(5)
            self.x_coord = m.group(6)
            self.y_coord = m.group(7)
            self.pair_id = m.group(8)
            self.bad_read = m.group(9)
            self.control_bit_flag = m.group(10)
            self.index_sequence = m.group(11)
        else:
            # Example of earlier Illumina format (1.3/1.5):
            # @HWUSI-EAS100R:6:73:941:1973#0/1
            m = RE_ILLUMINA.match(self.__seqid)
            if m:
                self._format = 'illumina'
                self.instrument_name = m.group(1)
                self.flowcell_lane = m.group(2)
                self.tile_no = m.group(3)
                self.x_coord = m.group(4)
                self.y_coord = m.group(5)
                self.multiplex_index_no = m.group(6)
                self.pair_id = m.group(7)

    @property
    def format(self):
        """
        Identify the format of the sequence identifier

        Returns:
          String: 'illumina18', 'illumina' or None

        """
        try:
            return self._format
        except AttributeError:
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

class FastqAttributes(object):
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

def get_fastq_file_handle(fastq,mode='rb'):
    """Return a file handle opened for reading for a FASTQ file

    Deals with both compressed (gzipped) and uncompressed FASTQ
    files.

    Arguments:
      fastq: name (including path, if required) of FASTQ file.
        The file can be gzipped (must have '.gz' extension)
      mode: optional mode for file opening (defaults to 'rb')

    Returns:
      File handle that can be used for read operations.

    """
    if os.path.splitext(fastq)[1] == '.gz':
        return gzip.open(fastq,mode)
    else:
        return io.open(fastq,mode)

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
        fp = get_fastq_file_handle(fastq)
    buf_size = 1024 * 1024
    read_fp = fp.read # optimise the loop
    buf = read_fp(buf_size)
    while buf:
        nlines += buf.count('\n')
        buf = read_fp(buf_size)
    if fastq is not None:
        fp.close()
    if (nlines%4) != 0:
        raise Exception("Bad read count (not fastq file, or corrupted?)")
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
    # Use izip_longest, which will return None if either of
    # the fastqs is exhausted before the other
    i = 0
    for r1,r2 in itertools.zip_longest(
            FastqIterator(fastq_file=fastq1,fp=fp1),
            FastqIterator(fastq_file=fastq2,fp=fp2)):
        i += 1
        if verbose:
            if i%100000 == 0:
                print("Examining pair #%d" % i)
        if not r1.seqid.is_pair_of(r2.seqid):
            if verbose:
                print("Unpaired headers for read position #%d:" % i)
                print("%s\n%s" % (r1.seqid,r2.seqid))
            return False
    return True
