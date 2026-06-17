#     FASTQFile.py: read and manipulate FASTQ files and data
#     Copyright (C) University of Manchester 2012-2026 Peter Briggs
#
########################################################################
#
# FASTQFile.py
#
#########################################################################

"""
Legacy module providing a set of classes for reading through FASTQ files
and manipulating the data within them.

The core functionality has been reimplemented in the ``io.fastq`` module;
the classes and functions in this module are now deprecated and only
maintained for backwards compatibility; they will be removed in a future
release.

The legacy classes and functions are:

* FastqIterator: enables looping through all read records in FASTQ file
* FastqRead: provides access to a single FASTQ read record
* SequenceIdentifier: provides access to sequence identifier info in a read
* FastqAttributes: provides access to gross attributes of FASTQ file
* get_fastq_file_handle: return a file handled opened for reading a FASTQ file
* nreads: return the number of reads in a FASTQ file
* fastqs_are_pair: check whether two FASTQs form an R1/R2 pair

.. note::

   The ``FastqAttributes`` class has not been reimplemented in
   ``io.fastq``; it should no longer be used.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################


import os
from .io.fastq import FastqIterator as _FastqIterator
from .io.fastq import FastqRead as _FastqRead
from .io.fastq import SequenceIdentifier as _SequenceIdentifier
from .io.fastq import get_fastq_file_handle
from .io.fastq import count_reads as nreads
from .io.fastq import fastqs_are_pair


#######################################################################
# Class definitions
#######################################################################


class FastqIterator(_FastqIterator):
    """
    Iterator for looping over all records in a FASTQ file.

    Deprecated legacy class: use ``FastqIterator`` from ``io.fastq``
    instead.

    Arguments:
        fastq_file (str): name of the FASTQ file to iterate through
        fp (any): file-like object opened for reading
        bufsize (int): optional integer specifying number of bytes to
            read as a single 'chunk' from disk
    """
    def __init__(self, fastq_file=None, fp=None, bufsize=None):
        _FastqIterator.__init__(self, fastq_file=fastq_file, fp=fp, bufsize=bufsize)

    def _fastq_read(self, read):
        return FastqRead(*read)


class FastqRead(_FastqRead):
    """
    Class to store a FASTQ record with information about a read

    Deprecated legacy class: use ``FastqRead`` from ``io.fastq``
    instead.

    Provides the following properties for accessing the read data:

    - seqid: the "sequence identifier" information (first line of the
      read record) as a SequenceIdentifier object
    - sequence: the raw sequence (second line of the record)
    - optid: the optional sequence identifier line (third line of the
      record)
    - quality: the quality values (fourth line of the record)

    Additional properties:

    - raw_seqid: the original sequence identifier string supplied
      when the object was created
    - seqlen: length of the sequence
    - maxquality: maximum quality value (in character representation)
    - minquality: minimum quality value (in character representation)
    - is_colorspace: returns True if the read looks like a colorspace
      read, False otherwise
    """
    def __init__(self,seqid_line=None,seq_line=None,optid_line=None,quality_line=None):
        _FastqRead.__init__(self, header=seqid_line, sequence=seq_line, optid=optid_line,
                            quality=quality_line)

    @property
    def seqid(self):
        return self.header

    @property
    def raw_seqid(self):
        return self.raw_header

    @property
    def seqlen(self):
        return len(self)

    @property
    def maxquality(self):
        return self.max_quality

    @property
    def minquality(self):
        return self.min_quality

    def _sequencer_identifier(self, fastq_header):
        # Internal, use this to an instance of the appropriate class
        # Subclasses should override this if they're using a
        # different class
        return SequenceIdentifier(fastq_header)


class SequenceIdentifier(_SequenceIdentifier):
    """
    Class to store/manipulate sequence identifier information from a FASTQ record

    Deprecated legacy class: use ``SequenceIdentifier`` from ``io.fastq``
    instead.

    Provides access to the data items in the sequence identifier line of a FASTQ
    record.
    """

    def __init__(self,seqid):
        _SequenceIdentifier.__init__(self, fastq_header=seqid)


class FastqAttributes:
    """
    Class to provide access to gross attributes of a FASTQ file

    Deprecated legacy class; do not use as it will be removed in
    a future release.

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
