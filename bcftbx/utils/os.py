#!/usr/bin/env python3
#
#     os.py: miscellaneous operating system interfaces
#     Copyright (C) University of Manchester 2026 Peter Briggs

"""
Miscellaneous operating system interfaces:

* mkdir: create directory
* mkdirs: create multiple level directory
* mklink: make a symbolic link
* chmod: change file or directory permissions
* touch: create empty file and/or update modification time
"""


import os
import logging
from .path import commonprefix


# Module specific logger
logger = logging.getLogger(__name__)


def mkdir(path, mode=None, recursive=False):
    """
    Make a directory

    Arguments:
      path (str): the path of the directory to be created
      mode (str): (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664
      recursive (bool): (optional) if True then also create any
        intermediate parent directories if they don't already
        exist
    """
    if os.path.exists(path):
        return
    if recursive:
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            mkdir(parent,recursive=True)
    os.mkdir(path)
    if mode is not None:
        chmod(path, mode)


def mkdirs(path, mode=None):
    """
    Make a directory recursively

    Arguments:
      path (str): the path of the directory to be created
      mode (str): (optional) a mode specifier to be applied to the
        new directory once it has been created e.g. 0775 or 0664
    """
    return mkdir(path, mode=mode, recursive=True)


def mklink(target, link_name, relative=False):
    """
    Make a symbolic link

    Arguments:
      target (str): path of the file or directory to link to
      link_name (str): path for the link
      relative (bool): if True then make a relative link (if possible);
        otherwise link to the target as given (default)
    """
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


def chmod(path, mode):
    """
    Change mode of file or directory

    This a wrapper for the os.chmod function, with the
    addition that it doesn't follow symbolic links.

    For symbolic links it attempts to use the os.lchmod
    function instead, as this operates on the link
    itself and not the link target. If os.lchmod is not
    available then links are ignored.

    Arguments:
      path (str): file or directory to apply new mode to
      mode (str): a valid mode specifier e.g. 0775 or 0664

    """
    try:
        if os.path.islink(path):
            # Try to use lchmod to operate on the link
            try:
                os.lchmod(path, mode)
            except AttributeError as ex:
                # lchmod is not available on all systems
                # If not then just ignore
                logger.debug(f"os.lchmod not available? Exception: ex")
        else:
            # Use os.chmod for everything else
            os.chmod(path, mode)
    except OSError as ex:
        logger.warning(f"Failed to change permissions on '{path}' to '{mode}': {ex}")


def touch(path):
    """
    Create new empty file, or update modification time if already exists

    Arguments:
      path (str): path to the file to create or update

    """
    if not os.path.exists(path):
        with open(path, "wb+") as f:
            pass
    os.utime(path,None)