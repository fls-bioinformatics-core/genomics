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
import logging
import string
import gzip
import shutil
import copy
import stat
import pwd
import grp
import datetime
import re
import socket
import math
from builtins import range

#######################################################################
# Module constants
#######################################################################

# Default size of data to read from file
CHUNKSIZE = 102400

#######################################################################
# General utility classes
#######################################################################

class AttributeDictionary(dict):
    """Dictionary-like object with items accessible as attributes

    AttributeDict provides a dictionary-like object where the value
    of items can also be accessed as attributes of the object.

    For example:

    >>> d = AttributeDict()
    >>> d['salutation'] = "hello"
    >>> d.salutation
    ... "hello"

    Attributes can only be assigned by using dictionary item assignment
    notation i.e. d['key'] = value. d.key = value doesn't work.

    If the attribute doesn't match a stored item then an
    AttributeError exception is raised.

    len(d) returns the number of stored items.

    The AttributeDict behaves like a dictionary for iterations, for
    example:

    >>> for attr in d:
    >>>    print("%s = %s" % (attr,d[attr]))

    """
    def __init__(self,**args):
        dict.__init__(self,**args)

    def __getattr__(self,attr):
        try:
            return dict.__getattr__(self,attr)
        except AttributeError:
            pass
        try:
            return self[attr]
        except KeyError:
            raise AttributeError("'AttributeDictionary' has no "
                                 "attribute '%s'" % attr)

class OrderedDictionary:
    """Augumented dictionary which keeps keys in order

    OrderedDictionary provides an augmented Python dictionary
    class which keeps the dictionary keys in the order they are
    added to the object.

    Items are added, modified and removed as with a standard
    dictionary e.g.:

    >>> d[key] = value
    >>> value = d[key]
    >>> del(d[key])

    The 'keys()' method returns the OrderedDictionary's keys in
    the correct order.
    """
    def __init__(self):
        self.__keys = []
        self.__dict = {}

    def __getitem__(self,key):
        if key not in self.__keys:
            raise KeyError
        return self.__dict[key]

    def __setitem__(self,key,value):
        if key not in self.__keys:
            self.__keys.append(key)
        self.__dict[key] = value

    def __delitem__(self,key):
        try:
            i = self.__keys.index(key)
            del(self.__keys[i])
            del(self.__dict[key])
        except ValueError:
            raise KeyError

    def __len__(self):
        return len(self.__keys)

    def __contains__(self,key):
        return key in self.__keys

    def __iter__(self):
        return iter(self.__keys)

    def keys(self):
        return copy.copy(self.__keys)

    def insert(self,i,key,value):
        if key not in self.__keys:
            self.__keys.insert(i,key)
            self.__dict[key] = value
        else:
            raise KeyError("Key '%s' already exists" % key)

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

def mkdir(dirn,mode=None,recursive=False):
    """Make a directory

    Arguments:
      dirn: the path of the directory to be created
      mode: (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664
      recursive: (optional) if True then also create any
        intermediate parent directories if they don't already
        exist
    """
    if os.path.exists(dirn):
        return
    if recursive:
        parent = os.path.dirname(dirn)
        if not os.path.exists(parent):
            mkdir(parent,recursive=True)
    os.mkdir(dirn)
    if mode is not None: chmod(dirn,mode)

def mkdirs(dirn,mode=None):
    """Make a directory recursively

    Arguments:
      dirn: the path of the directory to be created
      mode: (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664
    """
    return mkdir(dirn,mode=mode,recursive=True)

def mklink(target,link_name,relative=False):
    """Make a symbolic link

    Arguments:
      target: the file or directory to link to
      link_name: name of the link
      relative: if True then make a relative link (if possible);
        otherwise link to the target as given (default)"""
    target_path = target
    if relative:
        # Try to construct relative link to target
        target_abs_path = os.path.abspath(target)
        link_abs_path = os.path.abspath(link_name)
        common_prefix = commonprefix(target_abs_path,link_abs_path)
        if common_prefix:
            # Use relpath to generate the relative path from the link
            # to the target
            target_path = os.path.relpath(target_abs_path,os.path.dirname(link_abs_path))
    os.symlink(target_path,link_name)

def chmod(target,mode):
    """Change mode of file or directory

    This a wrapper for the os.chmod function, with the
    addition that it doesn't follow symbolic links.

    For symbolic links it attempts to use the os.lchmod
    function instead, as this operates on the link
    itself and not the link target. If os.lchmod is not
    available then links are ignored.

    Arguments:
      target: file or directory to apply new mode to
      mode: a valid mode specifier e.g. 0775 or 0664

    """
    try:
        if os.path.islink(target):
            # Try to use lchmod to operate on the link
            try:
                os.lchmod(target,mode)
            except AttributeError as ex:
                # lchmod is not available on all systems
                # If not then just ignore
                logging.debug("os.lchmod not available? Exception: %s" % ex)
        else:
            # Use os.chmod for everything else
            os.chmod(target,mode)
    except OSError as ex:
        logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))

def touch(filename):
    """Create new empty file, or update modification time if already exists

    Arguments:
      filename: name of the file to create (can include leading path)

    """
    if not os.path.exists(filename):
        io.open(filename,'wb+').close()
    os.utime(filename,None)

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

def commonprefix(path1,path2):
    """Determine common prefix path for path1 and path2

    Use this in preference to os.path.commonprefix as the version
    in os.path compares the two paths in a character-wise fashion
    and so can give counter-intuitive matches; this version compares
    path components which seems more sensible.

    For example: for two paths /mnt/dir1/file and /mnt/dir2/file,
    os.path.commonprefix will return /mnt/dir, whereas this function
    will return /mnt.

    Arguments:
      path1: first path in comparison
      path2: second path in comparison

    Returns:
      Leading part of path which is common to both input paths.
    """
    path1_components = str(path1).split(os.sep)
    path2_components = str(path2).split(os.sep)
    common_components = []
    ncomponents = min(len(path1_components),len(path2_components))
    for i in range(ncomponents):
        if path1_components[i] == path2_components[i]:
            common_components.append(path1_components[i])
        else:
            break
    commonprefix = "%s" % os.sep.join(common_components)
    return commonprefix

def is_gzipped_file(filename):
    """Check if a file has a .gz extension

    Arguments:
      filename: name of the file to be tested (can include leading path)

    Returns:
      True if filename has trailing .gz extension, False if not.

    """
    return os.path.splitext(filename)[1] == '.gz'

def rootname(name):
    """Remove all extensions from name

    Arguments:
      name: name of a file

    Returns:
      Leading part of name up to first dot, i.e. name without any
      trailing extensions.

    """
    try:
        i = name.index('.')
        return name[0:i]
    except ValueError:
        # No dot
        return name

def find_program(name):
    """Find a program on the PATH

    Search the current PATH for the specified program name and return
    the full path, or None if not found.

    """
    if os.path.isabs(name) and PathInfo(name).is_executable:
        return name
    for path in os.environ['PATH'].split(os.pathsep):
        name_path = os.path.abspath(os.path.join(path,name))
        if PathInfo(name_path).is_executable:
            return name_path
    return None

def get_current_user():
    """Return name of the current user

    Looks up user name for the current user; returns
    None if no matching name can be found.

    """
    try:
        return pwd.getpwuid(os.getuid()).pw_name
    except (KeyError,ValueError,OverflowError):
        return None

def get_user_from_uid(uid):
    """Return user name from UID

    Looks up user name matching the supplied UID;
    returns None if no matching name can be found.

    """
    try:
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError,ValueError,OverflowError):
        return None

def get_uid_from_user(user):
    """Return UID from user name

    Looks up UID matching the supplied user name;
    returns None if no matching name can be found.

    NB returned UID will be an integer.

    """
    try:
        return pwd.getpwnam(str(user)).pw_uid
    except KeyError:
        return None

def get_group_from_gid(gid):
    """Return group name from GID

    Looks up group name matching the supplied GID;
    returns None if no matching name can be found.

    """
    try:
        return grp.getgrgid(int(gid)).gr_name
    except (KeyError,ValueError,OverflowError):
        return None

def get_gid_from_group(group):
    """Return GID from group name

    Looks up GID matching the supplied group name;
    returns None if no matching name can be found.

    NB returned GID will be an integer.

    """
    try:
        return grp.getgrnam(group).gr_gid
    except KeyError as ex:
        return None

def get_hostname():
    """
    Return the hostname for the current system
    """
    return socket.getfqdn()

def walk(dirn,include_dirs=True,pattern=None):
    """Traverse the directory, subdirectories and files

    Essentially this 'walk' function is a convenience wrapper
    for the 'os.walk' function.

    Arguments:
      dirn: top-level directory to start traversal from
      include_dirs: if True then yield directories as well
        as files (default)
      pattern: if not None then specifies a regular expression
        pattern which restricts the set of yielded files and
        directories to a subset of those which match the
        pattern
        
    """
    if pattern is not None:
        matcher = re.compile(pattern)
    if include_dirs:
        if pattern is None or matcher.match(dirn):
            yield dirn
    for dirpath,dirnames,filenames in os.walk(dirn):
        if include_dirs:
            for d in dirnames:
                d1 = os.path.join(dirpath,d)
                if pattern is None or matcher.match(d1):
                    yield d1
        for f in filenames:
            f1 = os.path.join(dirpath,f)
            if pattern is None or matcher.match(f1):
                yield f1

def list_dirs(parent,matches=None,startswith=None):
    """Return list of subdirectories relative to 'parent'

    Arguments:
      parent: directory to list subdirectories of
      matches: if not None then only include subdirectories
        that exactly match the supplied string
      startswith: if not None then then return subset of
        subdirectories that start with the supplied string

    Returns:
      List of subdirectories (relative to the parent dir).

    """
    dirs = []
    for d in os.listdir(parent):
        if os.path.isdir(os.path.join(parent,d)):
            if startswith is None or d.startswith(startswith):
                if matches is None or d == matches:
                    dirs.append(d)
    dirs.sort()
    return dirs

def strip_ext(name,ext=None):
    """Strip extension from file name

    Given a file name or path, remove the extension (including the
    dot) and return just the leading part of the name.

    If an extension is explicitly specified then only remove the
    extension if it matches.

    Extension can be multipart e.g. 'fastq.gz' and can include a
    leading dot e.g. '.gz' or 'gz'.

    Arguments:
      name: name of a file

    Returns:
      Leading part of name excluding specified extension, or first
      extension i.e. to last dot.

    """
    name0 = name
    try:
        for ext in ext.lstrip('.').split('.')[::-1]:
            # Loop over extensions in reverse order
            try:
                i = name0.rindex('.')
                if name0[i+1:] == ext:
                    # Trim off matching extension
                    name0 = name0[:i]
                else:
                    # At least one part of the
                    # extension doesn't match so
                    # return original name
                    return name
            except ValueError:
                # At least one part of the
                # extension doesn't match
                return name
        # All extensions matched, return
        # stripped name
        return name0
    except AttributeError:
        # Unable to split the strip, lose just the
        # last extension
        try:
            i = name.rindex('.')
            return name[:i]
        except ValueError:
            return name

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

def links(dirn):
    """Traverse and return all symbolic links in under a directory

    Given a starting directory, traverses the structure underneath
    and yields the path for each symlink that is found.

    Arguments:
      dirn: name of the top-level directory

    Returns:
      Yields the name and full path for each symbolic link under 'dirn'.

    """
    for d in os.walk(dirn):
        if os.path.islink(d[0]):
            yield d[0]
        for sd in d[1]:
            path = os.path.join(d[0],sd)
            if os.path.islink(path):
                yield path
        for f in d[2]:
            path = os.path.join(d[0],f)
            if os.path.islink(path):
                yield path

#######################################################################
# Sample/library name utilities
#######################################################################

def extract_initials(name):
    """Return leading initials from the library or sample name

    Conventionaly the experimenter's initials are the leading characters
    of the name e.g. 'DR' for 'DR1', 'EP' for 'EP_NCYC2669', 'CW' for
    'CW_TI' etc

    Arguments:
      name: the name of a sample or library

    Returns:
      The leading initials from the name.
    """
    initials = []
    for c in str(name):
        if c.isalpha():
            initials.append(c)
        else:
            break
    return ''.join(initials)
        
def extract_prefix(name):
    """Return the library or sample name prefix

    Arguments:
      name: the name of a sample or library

    Returns:
      The prefix consisting of the name with trailing numbers
      removed, e.g. 'LD_C' for 'LD_C1'
    """
    return str(name).rstrip(string.digits)

def extract_index_as_string(name):
    """Return the library or sample name index as a string

    Arguments:
      name: the name of a sample or library

    Returns:
      The index, consisting of the trailing numbers from the name. It is
      returned as a string to preserve leading zeroes, e.g. '1' for
      'LD_C1', '07' for 'DR07' etc
    """
    index = []
    chars = [c for c in str(name)]
    chars.reverse()
    for c in chars:
        if c.isdigit():
            index.append(c)
        else:
            break
    index.reverse()
    return ''.join(index)

def extract_index(name):
    """Return the library or sample name index as an integer

    Arguments:
      name: the name of a sample or library

    Returns:
      The index as an integer, or None if the index cannot be converted to
      integer format.
    """
    indx = extract_index_as_string(name)
    if indx == '':
        return None
    else:
        return int(indx)

def pretty_print_names(name_list):
    """Given a list of library or sample names, format for pretty printing.

    Arguments:
      name_list: a list or tuple of library or sample names

    Returns:
      String with a condensed description of the library
      names, for example:

      ['DR1', 'DR2', 'DR3', DR4'] -> 'DR1-4'
    """
    # Create a list of string-type names sorted into prefix and index order
    names = [str(x) for x in sorted(name_list,
                                    key=lambda n: (extract_prefix(n),
                                                   extract_index(n)))]
    # Go through and group
    groups = []
    group = []
    last_prefix = None
    last_index = None
    for name in names:
        # Check if this is next in sequence
        prefix = extract_prefix(name)
        index_ = extract_index(name)
        try:
            if prefix == last_prefix and index_ == last_index+1:
                # Next in sequence
                group.append(name)
                last_prefix = prefix
                last_index = index_
                continue
        except TypeError:
            # One or both of the indexes was None
            pass
        # Current name is not next in previous sequence
        # Tidy up and start new group
        if group:
            groups.append(group)
        group = [name]
        last_prefix = prefix
        last_index = index_
    # Capture last group
    if group:
        groups.append(group)
    # Pretty print
    out = []
    for group in groups:
        if len(group) == 1:
            # "group" of one
            out.append(group[0])
        else:
            # Group with at least two members
            out.append(group[0]+"-"+extract_index_as_string(group[-1]))
    # Concatenate and return
    return ', '.join(out)

def name_matches(name,pattern):
    """Simple wildcard matching of project and sample names

    Matching options are:

    - exact match of a single name e.g. pattern 'PJB' matches 'PJB'
    - match start of a name using trailing '*' e.g. pattern 'PJ*' matches
      'PJB','PJBriggs' etc
    - match using multiple patterns by separating with comma e.g. pattern
      'PJB,IJD' matches 'PJB' or 'IJD'. Subpatterns can include trailing
      '*' character to match more names.
    
    Arguments
      name: text to match against pattern
      pattern: simple 'glob'-like pattern to match against

    Returns
      True if name matches pattern; False otherwise.
    """
    for subpattern in pattern.split(','):
        if not subpattern.endswith('*'):
            # Exact match required
            if name == subpattern:
                return True
        else:
            if name.startswith(subpattern.rstrip('*')):
                return True
    else:
        return False

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

def parse_named_lanes(name_expr):
    """Break up 'named lane expression' into lane numbers and name

    A 'named lane expression' takes the form '[<lanes>:]<name>',
    where lanes can be absent or consist of any of:

    - a single integer (e.g. 1), or
    - a list of comma-separated integers (e.g. 1,2,3), or
    - a range (e.g. 1-4), or
    - a combination of lists and ranges (e.g. 1,3,5-8).

    Arguments:
      name_expr (str): a named lane expression

    Returns:
      Tuple: a tuple of the form (lanes,name), where lanes is a
        Python list of integers representing lanes (or None, if no
        lanes were specified), and name is a string with the
        associated name.
    """
    # Name expressions are of the form 'expr:name'
    try:
        # Extract components
        i = str(name_expr).index(':')
        name = str(name_expr)[i+1:]
        # Extract lane numbers from leading expression
        lanes = parse_lanes(str(name_expr)[:i])
    except ValueError:
        # No lanes specified
        name = str(name_expr)
        lanes = None
    # Return tuple
    return (lanes,name)

def parse_lanes(lane_expr):
    """
    Break up a 'lane expression' into a list of lane numbers

    A 'lane expression' is a string consisting of:

    - a single integer (e.g. 1), or
    - a list of comma-separated integers (e.g. 1,2,3), or
    - a range (e.g. 1-4), or
    - a combination of lists and ranges (e.g. 1,3,5-8).

    Arguments:
      lane_expr (str): a lane expression

    Returns:
      List: list of integers representing lane numbers.
    """
    # Extract lane numbers
    fields = lane_expr.split(',')
    lanes = []
    for field in fields:
        # Check for ranges i.e. 1-3
        try:
            i = field.index('-')
            l1 = int(field[:i])
            l2 = int(field[i+1:])
            for i in range(l1,l2+1): lanes.append(i)
        except ValueError:
            # Not a range
            lanes.append(int(field))
    # Sort into order
    lanes.sort()
    return lanes
