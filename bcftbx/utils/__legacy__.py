#!/usr/bin/env python
#
#     utils.py: utility classes and functions shared between BCF codes
#     Copyright (C) University of Manchester 2013-2023 Peter Briggs
#
########################################################################
#
# utils.py
#
#########################################################################

"""utils

Utility classes and functions shared between BCF codes.

General utility classes:

  AttributeDictionary
  OrderedDictionary

File reading utilities:

  getlines

File system wrappers and utilities:

  PathInfo
  mkdir
  mkdirs
  mklink
  chmod
  touch
  format_file_size
  convert_size_to_bytes
  commonprefix
  is_gzipped_file
  rootname
  find_program
  get_current_user
  get_user_from_uid
  get_uid_from_user
  get_group_from_gid
  get_gid_from_group
  get_hostname
  walk
  list_dirs
  strip_ext

Symbolic link handling:

  Symlink
  links

Sample name utilities:

  extract_initials
  extract_prefix
  extract_index_as_string
  extract_index
  pretty_print_names
  name_matches

File manipulations:

  concatenate_fastq_files

Text manipulations:

  split_into_lines

Command line parsing utilities:

  parse_named_lanes
  parse_lanes

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import io
import gzip
import shutil
import stat
import datetime


#######################################################################
# Module constants
#######################################################################


# Default size of data to read from file
CHUNKSIZE = 102400


#######################################################################
# General utility classes
#######################################################################


from .collections import AttributeDictionary
from .collections import OrderedDictionary


#######################################################################
# File reading utilities
#######################################################################

def getlines(filen):
    """
    Fetch lines from a file and return them one by one

    This generator function tries to implement an efficient
    method of reading lines sequentially from a text file, by
    minimising the number of reads from the file and
    performing the line splitting in memory. It attempts
    to replicate the idiom:

    >>> for line in io.open(filen):
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
        open_ = io.open
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

#######################################################################
# File system wrappers and utilities
#######################################################################


from .os import mkdir
from .os import mkdirs
from .os import mklink
from .os import chmod
from .os import touch
from .os import find_program
from .os import walk
from .os import links
from .os import list_dirs
from .os import get_hostname
from .path import commonprefix
from .path import rootname
from .path import strip_ext
from .path import is_gzipped_file
from .users import get_current_user
from .users import get_gid_from_group
from .users import get_uid_from_user
from .users import get_group_from_gid
from .users import get_user_from_uid
from .format import format_file_size
from .format import convert_size_to_bytes
from .pathinfo import PathInfo
from .pathinfo import Symlink


#######################################################################
# Sample/library name utilities
#######################################################################


from .names import extract_initials
from .names import extract_prefix
from .names import extract_index_as_string
from .names import extract_index
from .names import pretty_print_names
from .names import name_matches


#######################################################################
# File manipulations
#######################################################################

def concatenate_fastq_files(merged_fastq,fastq_files,bufsize=10240,
                            overwrite=False,verbose=True):
    """Create a single FASTQ file by concatenating one or more FASTQs

    Given a list or tuple of FASTQ files (which can be compressed or
    uncompressed or a combination), creates a single output FASTQ by
    concatenating the contents.

    Arguments:
      merged_fastq: name of output FASTQ file (mustn't exist beforehand)
      fastq_files:  list of FASTQ files to concatenate
      bufsize: (optional) size of buffer to use for copying data
      overwrite: (optional) if True then overwrite the output file if it
        already exists (otherwise raise OSError); default is False
      verbose: (optional) if True then report operations to stdout,
        otherwise operate quietly

    """
    if verbose: print("Creating merged fastq file '%s'" % merged_fastq)
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
            if verbose: print("Copying %s" % fastq_files[0])
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
            fq_merged = io.open(merged_fastq_part,'ab')
        else:
            # Assume regular file
            first_file = 1
            fq_merged = io.open(merged_fastq_part,'wb')
    # For each fastq, read data and append to output - simples!
    for fastq in fastq_files[first_file:]:
        if verbose: print("Adding records from %s" % fastq)
        # Check it exists
        if not os.path.exists(fastq):
            raise OSError("'%s' not found, stopping" % fastq)
        # Open file for reading
        if not is_gzipped_file(fastq):
            fq = io.open(fastq,'rb')
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

#######################################################################
# Text manipulations
#######################################################################

def split_into_lines(text,char_limit,delimiters=' \t\n',
                     sympathetic=False):
    """Split a string into multiple lines with maximum length

    Splits a string into multiple lines on one or more delimiters
    (defaults to the whitespace characters i.e. ' ',tab and newline),
    such that each line is no longer than a specified length.

    For example:

    >>> split_into_lines("This is some text to split",10)
    ['This is','some text','to split']

    If it's not possible to split part of the text to a suitable
    length then the line is split "unsympathetically" at the
    line length, e.g.

    >>> split_into_lines("This is supercalifragilicous text",10)
    ['This is','supercalif','ragilicous','text']

    Set the 'sympathetic' flag to True to include a hyphen to
    indicate that a word has been broken, e.g.

    >>> split_into_lines("This is supercalifragilicous text",10,
    ...                  sympathetic=True)
    ['This is','supercali-','fragilico-','us text']

    To use an alternative set of delimiter characters, set the
    'delimiters' argument, e.g.

    >>> split_into_lines("This: is some text",10,delimiters=':')
    ['This',' is some t','ext']

    Arguments:
      text: string of text to be split into lines
      char_limit: maximum length for any given line
      delimiters: optional, specify a set of non-default
        delimiter characters (defaults to whitespace)
      sympathetic: optional, if True then add hyphen to
        indicate when a word has been broken

    Returns:
      List of lines (i.e. strings).

    """
    lines = []
    hyphen = '-'
    while len(text) > char_limit:
        # Locate nearest delimiter before the character limit
        i = None
        splitting_word = False
        try:
            # Check if delimiter occurs at the line boundary
            if text[char_limit] in delimiters:
                i = char_limit
        except IndexError:
            pass
        if i is None:
            # Look for delimiter within the line
            for delim in delimiters:
                try:
                    j = text[:char_limit].rindex(delim)
                    i = max([x for x in [i,j] if x is not None])
                except ValueError:
                    pass
        if i is None:
            # Unable to locate delimiter within character
            # limit so set to the limit
            i = char_limit
        # Are we splitting a word?
        try:
            if text[i] not in delimiters and sympathetic:
                splitting_word = True
                i = i - 1
        except IndexError:
            pass
        lines.append("%s%s" % (text[:i].rstrip(delimiters),
                               hyphen if splitting_word else ''))
        text = text[i:].lstrip(delimiters)
    # Append remainder
    lines.append(text)
    return lines

#######################################################################
# Command line parsing utilities
#######################################################################

from .parser import parse_named_lanes
from .parser import parse_lanes