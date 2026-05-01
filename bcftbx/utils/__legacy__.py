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
# General utility classes
#######################################################################


from .collections import AttributeDictionary
from .collections import OrderedDictionary


#######################################################################
# File reading utilities
#######################################################################


from .io import getlines


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

from .io import concatenate_fastq_files

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