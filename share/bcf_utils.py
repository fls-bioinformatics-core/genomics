#     bcf_utils.py: utility classes and functions shared between BCF codes
#     Copyright (C) University of Manchester 2013-14 Peter Briggs
#
########################################################################
#
# bcf_utils.py
#
#########################################################################

__version__ = "1.4.5"

"""bcf_utils

Utility classes and functions shared between BCF codes.

General utility classes:

  AttributeDictionary
  OrderedDictionary

File system wrappers and utilities:

  PathInfo
  mkdir
  mklink
  chmod
  touch
  format_file_size
  commonprefix
  is_gzipped_file
  rootname
  find_program
  get_user_from_uid
  get_uid_from_user
  get_group_from_gid
  get_gid_from_group
  walk

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

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
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

#######################################################################
# General utility classes
#######################################################################

class AttributeDictionary:
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
    >>>    print "%s = %s" % (attr,d[attr])

    """
    def __init__(self,**args):
        self.__dict = dict(args)

    def __getattr__(self,attr):
        try:
            return self.__dict[attr]
        except KeyError:
            raise AttributeError, "No attribute '%s'" % attr

    def __getitem__(self,key):
        return self.__dict[key]

    def __setitem__(self,key,value):
        self.__dict[key] = value

    def __iter__(self):
        return iter(self.__dict)

    def __len__(self):
        return len(self.__dict)

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
            raise KeyError, "Key '%s' already exists" % key

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
        raise OSError,"Unable to find readable parent for %s" % self.__path

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

def mkdir(dirn,mode=None):
    """Make a directory

    Arguments:
      dirn: the path of the directory to be created
      mode: (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664

    """
    logging.debug("Making %s" % dirn)
    if not os.path.isdir(dirn):
        os.mkdir(dirn)
        if mode is not None: chmod(dirn,mode)

def mklink(target,link_name,relative=False):
    """Make a symbolic link

    Arguments:
      target: the file or directory to link to
      link_name: name of the link
      relative: if True then make a relative link (if possible);
        otherwise link to the target as given (default)"""
    logging.debug("Linking to %s from %s" % (target,link_name))
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
    logging.debug("Changing mode of %s to %s" % (target,mode))
    try:
        if os.path.islink(target):
            # Try to use lchmod to operate on the link
            try:
                os.lchmod(target,mode)
            except AttributeError,ex:
                # lchmod is not available on all systems
                # If not then just ignore
                logging.debug("os.lchmod not available? Exception: %s" % ex)
        else:
            # Use os.chmod for everything else
            os.chmod(target,mode)
    except OSError, ex:
        logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))

def touch(filename):
    """Create new empty file, or update modification time if already exists

    Arguments:
      filename: name of the file to create (can include leading path)

    """
    if not os.path.exists(filename):
        open(filename,'wb+').close()
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
    except KeyError,ex:
        return None


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
        self.__path = path
        self.__abspath = os.path.abspath(self.__path)

    @property
    def target(self):
        """Return the target of the symlink

        """
        return os.readlink(self.__abspath)

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
            path = os.path.abspath(os.path.join(os.path.dirname(self.__abspath),
                                                self.target))
        return os.path.normpath(path)

    def update_target(self,new_target):
        """Replace the current link target with new_target

        Arguments:
          new_target: path to replace the existing target with

        """
        os.unlink(self.__abspath)
        os.symlink(new_target,self.__abspath)

    def __repr__(self):
        """Implement the __repr__ built-in

        """
        return self.__path

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
                                    key=lambda n: (extract_prefix(n),extract_index(n)))]
    # Go through and group
    groups = []
    group = []
    last_index = None
    for name in names:
        # Check if this is next in sequence
        try:
            if extract_index(name) == last_index+1:
                # Next in sequence
                group.append(name)
                last_index = extract_index(name)
                continue
        except TypeError:
            # One or both of the indexes was None
            pass
        # Current name is not next in previous sequence
        # Tidy up and start new group
        if group:
            groups.append(group)
        group = [name]
        last_index = extract_index(name)
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
    if verbose: print "Creating merged fastq file '%s'" % merged_fastq
    # Check that initial file doesn't exist
    if os.path.exists(merged_fastq) and not overwrite:
        raise OSError, "Target file '%s' already exists, stopping" % merged_fastq
    # Create temporary name
    merged_fastq_part = merged_fastq+'.part'
    # Open for writing
    if is_gzipped_file(merged_fastq):
        if is_gzipped_file(fastq_files[0]):
            # Copy first file in list directly and open for append
            if verbose: print "Copying %s" % fastq_files[0]
            shutil.copy(fastq_files[0],merged_fastq_part)
            first_file = 1
            fq_merged = gzip.GzipFile(merged_fastq_part,'ab')
        else:
            # Open for write
            first_file = 0
            fq_merged = gzip.GzipFile(merged_fastq_part,'wb')
    else:
        if not is_gzipped_file(fastq_files[0]):
            if verbose: print "Copying %s" % fastq_files[0]
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
        if verbose: print "Adding records from %s" % fastq
        # Check it exists
        if not os.path.exists(fastq):
            raise OSError, "'%s' not found, stopping" % fastq
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
