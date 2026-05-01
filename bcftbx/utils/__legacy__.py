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
import math


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


class PathInfo:
    """Collect and report information on a file

    The PathInfo class provides an interface to getting general
    information on a path, which may point to a file, directory, link
    or non-existent location.

    The properties provide information on whether the path is
    readable (i.e. accessible) by the current user, whether it is
    readable by members of the same group, who is the owner and
    what group does it belong to, when was it last modified etc.

    """
    def __init__(self,path,basedir=None):
        """Create a new PathInfo object

        Arguments:
          path: a filesystem path, which can be relative or
            absolute, or point to a non-existent location
          basedir: (optional) if supplied then prepended to
            the supplied path

        """
        self.__basedir = basedir
        if self.__basedir is not None:
            self.__path = os.path.join(self.__basedir,path)
        else:
            self.__path = path
        try:
            self.__st = os.lstat(self.__path)
        except OSError:
            self.__st = None

    @property
    def path(self):
        """Return the filesystem path

        """
        return self.__path

    @property
    def is_readable(self):
        """Return True if the path exists and is readable by the owner

        Paths may be reported as unreadable for various reasons,
        e.g. the target doesn't exist, or doesn't have permission
        for this user to read it, or if part of the path doesn't
        allow the user to read the file.

        """
        if self.__st is None:
            return False
        return bool(self.__st.st_mode & stat.S_IRUSR)

    @property
    def is_group_readable(self):
        """Return True if the path exists and is group-readable

        Paths may be reported as unreadable for various reasons,
        e.g. the target doesn't exist, or doesn't have permission
        for this user to read it, or if part of the path doesn't
        allow the user to read the file.

        """
        if self.__st is None:
            return False
        return bool(self.__st.st_mode & stat.S_IRGRP)

    @property
    def is_group_writable(self):
        """Return True if the path exists and is group-writable

        Paths may be reported as unwritable for various reasons,
        e.g. the target doesn't exist, or doesn't have permission
        for this user to write to it, or if part of the path
        doesn't allow the user to read the file.

        """
        if self.__st is None:
            return False
        return bool(self.__st.st_mode & stat.S_IWGRP)

    @property
    def deepest_accessible_parent(self):
        """Return longest accessible directory that leads to path

        Tries to find the longest parent directory above path
        which is accessible by the current user.

        If it's not possible to find a parent that is accessible
        then raise an exception.

        """
        path = os.path.dirname(os.path.abspath(self.__path))
        while path != os.sep:
            if os.access(path,os.R_OK):
                return path
            path = os.path.dirname(path)
        raise OSError("Unable to find readable parent for %s" %
                      self.__path)

    @property
    def resolve_link_via_parent(self):
        """If path or parent directory is a link then return actual path

        Resolves and returns the 'real' path for a path where either
        it or one of its parent directories is a symbolic link.

        It will resolve multiple levels of symlinks to generate a path
        that is free of links (nb it is possible that the resolved path
        will not be an existing file or directory).

        If there are no links in the directory tree then returns the
        full path of the input.

        """
        path = os.path.abspath(self.__path)
        realpath = []
        while path != os.sep:
            if os.path.islink(path):
                # Construct actual path
                link_path = os.readlink(path)
                if os.path.isabs(link_path):
                    path = link_path
                else:
                    path = os.path.normpath(os.path.join(os.path.dirname(path),
                                                         link_path))
                continue
            # Descend to next level
            realpath.append(os.path.basename(path))
            path = os.path.dirname(path)
        # Descended to root, rebuild path
        realpath = os.sep + os.sep.join(realpath[::-1])
        return realpath

    @property
    def uid(self):
        """Return associated UID (user ID)

        Attempts to return the UID (user ID) number associated with
        the path.

        If the UID can't be found then returns None.

        """
        if self.__st is None:
            return None
        return self.__st.st_uid

    @property
    def user(self):
        """Return associated user name

        Attempts to return the user name associated with the path.
        If the name can't be found then tries to return the UID
        instead.

        If neither pieces of information can be found then returns
        None.

        """
        if self.__st is None:
            return None
        user = get_user_from_uid(self.uid)
        if user is not None:
            return user
        else:
            return self.uid

    @property
    def gid(self):
        """Return associated GID (group ID)

        Attempts to return the GID (group ID) number associated with
        the path.

        If the GID can't be found then returns None.

        """
        if self.__st is None:
            return None
        return self.__st.st_gid

    @property
    def group(self):
        """Return associated group name

        Attempts to return the group name associated with the path.
        If the name can't be found then tries to return the GID
        instead.

        If neither pieces of information can be found then returns
        None.

        """
        if self.__st is None:
            return None
        group = get_group_from_gid(self.gid)
        if group is not None:
            return group
        else:
            return self.gid

    @property
    def exists(self):
        """Return True if the path refers to an existing location

        Note that this is a wrapper to os.path.lexists so it reports
        the existence of symbolic links rather than their targets.

        """
        return os.path.lexists(self.__path)

    @property
    def is_link(self):
        """Return True if path refers to a symbolic link

        """
        return os.path.islink(self.__path)

    @property
    def is_file(self):
        """Return True if path refers to a file

        """
        if not self.is_link:
            return os.path.isfile(self.__path)
        else:
            return False

    @property
    def is_dir(self):
        """Return True if path refers to a directory

        """
        if not self.is_link:
            return os.path.isdir(self.__path)
        else:
            return False

    @property
    def is_executable(self):
        """Return True if path refers to an executable file

        """
        if self.__st is None:
            return False
        if self.is_link:
            return PathInfo(Symlink(self.__path).resolve_target()).is_executable
        return bool(self.__st.st_mode & stat.S_IXUSR) and self.is_file

    @property
    def mtime(self):
        """Return last modification timestamp for path

        """
        if self.__st is None:
            return None
        return self.__st.st_mtime

    @property
    def datetime(self):
        """Return last modification time as datetime object

        """
        if self.mtime is None:
            return None
        return datetime.datetime.fromtimestamp(self.mtime)

    def relpath(self,dirn):
        """Return part of path relative to a directory

        Wrapper for os.path.relpath(...).
        
        """
        return os.path.relpath(self.__path,dirn)

    def chown(self,user=None,group=None):
        """Change associated owner and group

        'user' and 'group' must be supplied as UID/GID
        numbers (or None to leave the current values
        unchanged).

        *** Note that chown will fail attempting to
        change the owner if the current process is not
        owned by root ***

        This is actually a wrapper to the os.lchmod
        function, so it doesn't follow symbolic links.

        """
        if user is None and group is None:
            # Nothing to do
            return
        if user is None:
            user = -1
        if group is None:
            group = -1
        # Convert to ints
        user = int(user)
        group = int(group)
        # Do chown - note this will fail if the user
        # performing the operation is not root
        os.lchown(self.__path,user,group)
        # Update the stat information
        try:
            self.__st = os.lstat(self.__path)
        except OSError:
            self.__st = None

    def __repr__(self):
        """Implements the built-in __repr__ function
        """
        return str(self.__path)

def format_file_size(fsize,units=None):
    """Format a file size from bytes to human-readable form

    Takes a file size in bytes and returns a human-readable
    string, e.g. 4.0K, 186M, 1.5G.

    Alternatively specify the required units via the 'units'
    arguments.

    Arguments:
      fsize: size in bytes
      units: (optional) specify output in kb ('K'), Mb ('M'),
             Gb ('G') or Tb ('T')

    Returns:
      Human-readable version of file size.

    """
    # Return size in human readable form
    if units is not None:
        units = units.upper()
    fsize = float(fsize)/1024
    unit_list = 'KMGT'
    for unit in unit_list:
        if units is None:
            if fsize > 1024:
                fsize = fsize/1024
            else:
                break
        else:
            if units != unit:
                fsize = fsize/1024
            else:
                break
    return "%.1f%s" % (fsize,unit)

def convert_size_to_bytes(size):
    """
    Converts a human-readable size specification to bytes

    Given an arbitary human-readable file size (e.g.
    '4.0K', '186M', '1.5G'), returns the equivalent size
    in bytes.

    Arguments:
      size (str): size specification string

    Returns:
      Integer: size expressed as number of bytes.
    """
    try:
        return int(str(size))
    except ValueError:
        units = str(size)[-1].upper()
        p = "KMGTP".index(units) + 1
        return int(float(str(size)[:-1])) * int(math.pow(1024,p))

#######################################################################
# Symbolic link handling
#######################################################################

class Symlink:
    """Class for interrogating and modifying symbolic links

    The Symlink class provides an interface for getting information
    about a symbolic link.

    To create a new Symlink instance do e.g.:

    >>> l = Symlink('my_link.lnk')

    Information about the link can be obtained via the various
    properties:

    - target = returns the link target
    - is_absolute = reports if the target represents an absolute link
    - is_broken = reports if the target doesn't exist

    There are also methods:

    - resolve_target() = returns the normalise absolute path to the 
      target
    - update_target() = updates the target to a new location

    """
    def __init__(self,path):
        """Create a new Symlink instance

        Raises an exception if the supplied path doesn't point to
        a link instance.

        Arguments:
          path: path to the link

        """
        if not os.path.islink(path):
            raise Exception("%s is not a link" % path)
        self._path = path
        self._abspath = os.path.abspath(self._path)

    @property
    def target(self):
        """Return the target of the symlink

        """
        return os.readlink(self._abspath)

    @property
    def is_absolute(self):
        """Return True if the link target is an absolute link

        """
        return os.path.isabs(self.target)

    @property
    def is_broken(self):
        """Return True if the link target doesn't exist i.e. link is broken

        """
        return not os.path.exists(self.resolve_target())

    def resolve_target(self):
        """Return the normalised absolute path to the link target

        """
        if self.is_absolute:
            path = self.target
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(self._abspath),
                                                self.target))
        return os.path.normpath(path)

    def update_target(self,new_target):
        """Replace the current link target with new_target

        Arguments:
          new_target: path to replace the existing target with

        """
        os.unlink(self._abspath)
        os.symlink(new_target,self._abspath)

    def __repr__(self):
        """Implement the __repr__ built-in

        """
        return self._path

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