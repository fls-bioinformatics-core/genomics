#!/usr/bin/env python3
#
#     pathinfo.py: file and symlink manipulations
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
File and symlink manipulations:

* PathInfo: class for querying and manipulating files and directories
* SymLink: class for querying and manipulating symbolic links
"""


import os
import stat
import datetime
from .users import get_group_from_gid
from .users import get_user_from_uid


class PathInfo:
    """
    Collect and report information on a file

    The PathInfo class provides an interface to getting general
    information on a path, which may point to a file, directory, link
    or non-existent location.

    The properties provide information on whether the path is
    readable (i.e. accessible) by the current user, whether it is
    readable by members of the same group, who is the owner and
    what group does it belong to, when was it last modified etc.

    Arguments:
      path (str): a filesystem path, which can be relative or
        absolute, or point to a non-existent location
      basedir (str): (optional) if supplied then is prepended to
        the supplied path
    """
    def __init__(self, path, basedir=None):
        self.__basedir = basedir
        if self.__basedir is not None:
            self.__path = os.path.join(self.__basedir, path)
        else:
            self.__path = path
        try:
            self.__st = os.lstat(self.__path)
        except OSError:
            self.__st = None

    @property
    def path(self):
        """
        Return the filesystem path
        """
        return self.__path

    @property
    def is_readable(self):
        """
        Return True if the path exists and is readable by the owner

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
        """
        Return True if the path exists and is group-readable

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
        """
        Return True if the path exists and is group-writable

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
        """
        Return longest accessible directory that leads to path

        Tries to find the longest parent directory above path
        which is accessible by the current user.

        If it's not possible to find a parent that is accessible
        then raise an exception.
        """
        path = os.path.dirname(os.path.abspath(self.__path))
        while path != os.sep:
            if os.access(path, os.R_OK):
                return path
            path = os.path.dirname(path)
        raise OSError("Unable to find readable parent for %s" %
                      self.__path)

    @property
    def resolve_link_via_parent(self):
        """
        If path or parent directory is a link then return actual path

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
        """
        Return associated UID (user ID)

        Attempts to return the UID (user ID) number associated with
        the path.

        If the UID can't be found then returns None.
        """
        if self.__st is None:
            return None
        return self.__st.st_uid

    @property
    def user(self):
        """
        Return associated user name

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
        """
        Return associated GID (group ID)

        Attempts to return the GID (group ID) number associated with
        the path.

        If the GID can't be found then returns None.
        """
        if self.__st is None:
            return None
        return self.__st.st_gid

    @property
    def group(self):
        """
        Return associated group name

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
        """
        Return True if the path refers to an existing location

        Note that this is a wrapper to os.path.lexists so it reports
        the existence of symbolic links rather than their targets.
        """
        return os.path.lexists(self.__path)

    @property
    def is_link(self):
        """
        Return True if path refers to a symbolic link
        """
        return os.path.islink(self.__path)

    @property
    def is_file(self):
        """
        Return True if path refers to a file
        """
        if not self.is_link:
            return os.path.isfile(self.__path)
        else:
            return False

    @property
    def is_dir(self):
        """
        Return True if path refers to a directory
        """
        if not self.is_link:
            return os.path.isdir(self.__path)
        else:
            return False

    @property
    def is_executable(self):
        """
        Return True if path refers to an executable file
        """
        if self.__st is None:
            return False
        if self.is_link:
            print(f"{self.__path} is a link")
            return PathInfo(Symlink(self.__path).resolve_target()).is_executable
        print(f"{self.__path} is NOT a link")
        return bool(self.__st.st_mode & stat.S_IXUSR) and self.is_file

    @property
    def mtime(self):
        """
        Return last modification timestamp for path
        """
        if self.__st is None:
            return None
        return self.__st.st_mtime

    @property
    def datetime(self):
        """
        Return last modification time as datetime object
        """
        if self.mtime is None:
            return None
        return datetime.datetime.fromtimestamp(self.mtime)

    def relpath(self, dirn):
        """
        Return part of path relative to a directory

        Wrapper for os.path.relpath(...).

        Arguments:
          dirn (str): directory to relpath to

        Returns:
          String: relative path
        """
        return os.path.relpath(self.__path, dirn)

    def chown(self, user=None, group=None):
        """
        Change associated owner and group

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
        os.lchown(self.__path, user, group)
        # Update the stat information
        try:
            self.__st = os.lstat(self.__path)
        except OSError:
            self.__st = None

    def __repr__(self):
        return str(self.__path)


class Symlink:
    """
    Class for interrogating and modifying symbolic links

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

    Arguments:
      path (str): path to the link
    """
    def __init__(self,path):
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
        """
        Return True if the link target is an absolute link
        """
        return os.path.isabs(self.target)

    @property
    def is_broken(self):
        """
        Return True if the link target doesn't exist i.e. link is broken
        """
        return not os.path.exists(self.resolve_target())

    def resolve_target(self):
        """
        Return the normalised absolute path to the link target
        """
        if self.is_absolute:
            path = self.target
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(self._abspath),
                                                self.target))
        return os.path.normpath(path)

    def update_target(self,new_target):
        """
        Replace the current link target with new_target

        Arguments:
          new_target: path to replace the existing target with
        """
        os.unlink(self._abspath)
        os.symlink(new_target,self._abspath)

    def __repr__(self):
        return self._path