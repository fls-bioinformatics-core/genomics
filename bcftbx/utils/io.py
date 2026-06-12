#!/usr/bin/env python3
#
#     io.py: file input/output utility functions
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
File input/output utility functions:

* getlines: return lines from a file one-by-one
* concatenate_fastq_files: merge multiple FASTQ files
"""


import os
import gzip
import shutil
from .path import is_gzipped_file


# getlines: default size of data to read from file
CHUNKSIZE = 102400


def getlines(filen):
    """
    Fetch lines from a file and return them one by one

    This generator function tries to implement an efficient
    method of reading lines sequentially from a text file, by
    minimising the number of reads from the file and
    performing the line splitting in memory. It attempts
    to replicate the idiom:

    >>> for line in open(filen):
    >>> ...

    using:

    >>> for line in getlines(filen):
    >>> ...

    The file can be gzipped; this function should handle
    this invisibly provided that the file extension is
    '.gz'.

    Arguments:
      filen (str): path of the file to read lines from

    Yields:
      String: next line of text from the file, with any
        newline character removed.
    """
    if filen.split('.')[-1] == 'gz':
        open_ = gzip.open
    else:
        open_ = open
    # Read in data in chunks
    buf = ''
    lines = []
    with open_(filen,'rb') as fp:
        while True:
            # Grab a chunk of data
            data = fp.read(CHUNKSIZE).decode("UTF-8")
            # Check for EOF
            if not data:
                break
            # Add to buffer and split into lines
            buf = buf + data
            if buf[0] == '\n':
                buf = buf[1:]
            if buf[-1] != '\n':
                i = buf.rfind('\n')
                if i == -1:
                    continue
                else:
                    lines = buf[:i].split('\n')
                    buf = buf[i+1:]
            else:
                lines = buf[:-1].split('\n')
                buf = ''
            # Return the lines one at a time
            for line in lines:
                yield line


def concatenate_fastq_files(merged_fastq,fastq_files,bufsize=10240,
                            overwrite=False,verbose=True):
    """
    Create a single FASTQ file by concatenating one or more FASTQs

    Given a list or tuple of FASTQ files (which can be compressed or
    uncompressed or a combination), creates a single output FASTQ by
    concatenating the contents.

    Arguments:
      merged_fastq (str): name of output FASTQ file (mustn't exist beforehand)
      fastq_files (list): list of FASTQ files to concatenate
      bufsize (int): (optional) size of buffer to use for copying data
      overwrite (bool): (optional) if True then overwrite the output file if it
        already exists (otherwise raise OSError); default is False
      verbose (bool): (optional) if True then report operations to stdout,
        otherwise operate quietly
    """
    if verbose:
        print("Creating merged fastq file '%s'" % merged_fastq)
    # Check that initial file doesn't exist
    if os.path.exists(merged_fastq) and not overwrite:
        raise OSError("Target file '%s' already exists, stopping" %
                      merged_fastq)
    # Create temporary name
    merged_fastq_part = merged_fastq+'.part'
    # Open for writing
    if is_gzipped_file(merged_fastq):
        if is_gzipped_file(fastq_files[0]):
            # Copy first file in list directly and open for append
            if verbose:
                print("Copying %s" % fastq_files[0])
            shutil.copy(fastq_files[0],merged_fastq_part)
            first_file = 1
            fq_merged = gzip.GzipFile(merged_fastq_part,'ab')
        else:
            # Open for write
            first_file = 0
            fq_merged = gzip.GzipFile(merged_fastq_part,'wb')
    else:
        if not is_gzipped_file(fastq_files[0]):
            if verbose: print("Copying %s" % fastq_files[0])
            # Copy first file in list directly and open for append
            shutil.copy(fastq_files[0],merged_fastq_part)
            first_file = 1
            fq_merged = open(merged_fastq_part,'ab')
        else:
            # Assume regular file
            first_file = 1
            fq_merged = open(merged_fastq_part,'wb')
    # For each fastq, read data and append to output - simples!
    for fastq in fastq_files[first_file:]:
        if verbose: print("Adding records from %s" % fastq)
        # Check it exists
        if not os.path.exists(fastq):
            raise OSError("'%s' not found, stopping" % fastq)
        # Open file for reading
        if not is_gzipped_file(fastq):
            fq = open(fastq,'rb')
        else:
            fq = gzip.GzipFile(fastq,'rb')
        # Read and append data
        while True:
            data = fq.read(10240)
            if not data: break
            fq_merged.write(data)
        fq.close()
    # Finished, clean up
    fq_merged.close()
    os.rename(merged_fastq_part,merged_fastq)