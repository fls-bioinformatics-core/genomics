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

from .text import split_into_lines

#######################################################################
# Command line parsing utilities
#######################################################################

from .parser import parse_named_lanes
from .parser import parse_lanes