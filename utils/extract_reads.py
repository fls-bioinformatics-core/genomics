#!/bin/env python
#
#     extract_reads.py: write random subsets of read records from input files
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# extract_reads.py
#
#########################################################################
#
"""extract_reads.py

Pull random sets of read records from various files

Usage: extract_reads.py [-n <n_records> ] infile [infile ...]

If multiple infiles are specified then the same set of records from
each file.

Recognises FASTQ, CSFASTA and QUAL files.
"""
#######################################################################
# Module metadata
#######################################################################

__version__ = "0.1.2"

#######################################################################
# Import modules
#######################################################################

import sys,os
import random
import logging
import optparse
import re

#######################################################################
# Classes
#######################################################################

class ReadExtractor:
    """Class to extract subsets of read records from a file
    """
    def __init__(self,file_name,lines_per_record=None):
        """Create and populate a new ReadExtractor instance

        Arguments:
          file_name: file containing reads
          lines_per_record: number of lines making up one record
        """
        # Initialise
        self.__file_name = file_name
        self.__file_type = None
        if lines_per_record is not None:
            self.__lines_per_record = lines_per_record
        else:
            self.__set_lines_per_record()
        self.__n_header_lines = 0
        self.__n_data_lines = 0
        self.__n_records = 0
        # Get number of records etc
        fp = open(self.__file_name,'rU')
        for line in fp:
            if line.startswith('#'):
                self.__n_header_lines += 1
            else:
                self.__n_data_lines += 1
        fp.close()
        self.__n_records = self.__n_data_lines/self.__lines_per_record

    def __set_lines_per_record(self):
        """Internal: set number of lines per record based on file extension
        """
        self.__file_type = os.path.splitext(self.__file_name)[1].strip('.')
        if self.__file_type == "csfasta" or self.__file_type == "qual":
            self.__lines_per_record = 2
        elif self.__file_type == "fastq" or self.__file_type == "fq":
            self.__lines_per_record = 4
        else:
            logging.warning("Unknown file type: '%s'" % self.__file_type)
            self.__lines_per_record = 1

    @property
    def nRecords(self):
        """Number of records found in the file
        """
        return self.__n_records

    @property
    def nLines(self):
        """Total number of lines in the file
        """
        return self.__n_data_lines

    @property
    def nHeaders(self):
        """Number of header lines in the file
        """
        return self.__n_header_lines

    def subset(self,record_indexes=[]):
        """Extract subset of records and write to a new file

        Arguments:
          record_indexes: a list of record numbers which will be written to
            the output file
        """
        fr = open(self.__file_name,'rU')
        fp = open(os.path.basename(self.__file_name)+'.subset','w')
        print "Outputting to %s" % os.path.basename(self.__file_name)+'.subset'
        current_line = 0
        for line in fr:
            i = (current_line - self.__n_header_lines)/self.__lines_per_record
            if i in record_indexes:
                fp.write(line)
            current_line += 1 
        fp.close()

    def regex_subset(self,regex_pattern):
        """Extract and write subset of records matching a regular expression

        Arguments:
          regex_pattern: Python-style regular expression
        """
        fr = open(self.__file_name,'rU')
        fp = open(os.path.basename(self.__file_name)+'.subset','w')
        regex = re.compile(regex_pattern)
        print "Outputting to %s" % os.path.basename(self.__file_name)+'.subset'
        record = []
        for line in fr:
            record.append(line)
            if len(record) == self.__lines_per_record:
                # See if the record matches the pattern
                if regex.search(''.join(record)):
                    for line0 in record:
                        fp.write(line0)
                # Reset for next record
                record = []
        fp.close()

#######################################################################
# Functions
#######################################################################

# No functions defined
    
#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Process the command line
    p = optparse.OptionParser(usage="%prog OPTIONS infile [infile ...]",
                              version="%prog "+__version__,
                              description="Extract subsets of reads from each of the "
                              "supplied files according to specified criteria (e.g. "
                              "random, matching a pattern etc). Input files can be "
                              "any mixture of FASTQ (.fastq, .fq), CSFASTA (.csfasta) "
                              "and QUAL (.qual). Output file names will be the input "
                              "file names with '.subset' appended.")
    p.add_option('-m','--match',action='store',dest='pattern',default=None,
                 help="Extract records that match Python regular expression PATTERN")
    p.add_option('-n',action='store',dest='N',default=500,type="int",
                 help="Extract N random records from the input file(s) (default 500). If "
                 "multiple input files are specified, the same subsets will be extracted "
                 "for each.")
    options,arguments = p.parse_args()
    if len(arguments) < 1:
        p.error("No input files supplied")

    # Report version
    p.print_version()

    # Initialise
    if options.pattern:
        # Do pattern matching
        print "Extracting reads that match '%s'" % options.pattern
        for f in arguments:
            s = ReadExtractor(f)
            s.regex_subset(options.pattern)
        sys.exit()
    else:
        # Extract random reads
        N = options.N
        print "Extracting %d unique random reads from input files" % N
        # Loop over input files and collect data
        nrecords = None
        for f in arguments:
            if nrecords is None:
                nrecords = ReadExtractor(f).nRecords
            else:
                if ReadExtractor(f).nRecords != nrecords:
                    print "Inconsistent numbers of records between files"
                    sys.exit(1)
        # Generate indexes for a random subset
        rand_records = []
        while len(rand_records) < N:
            r = random.randint(0,nrecords-1)
            if r not in rand_records: rand_records.append(r)
        # Loop over files again
        for f in arguments:
            s = ReadExtractor(f)
            s.subset(rand_records)
        
    
