#     bcf_utils.py: utility classes and functions shared between BCF codes
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################
#
# bcf_utils.py
#
#########################################################################

"""bcf_utils

Utility classes and functions shared between BCF codes.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging

#######################################################################
# Class definitions
#######################################################################

# None defined

#######################################################################
# Module Functions
#######################################################################

# File system wrappers and utilities

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

    Arguments:
      target: file or directory to apply new mode to
      mode: a valid mode specifier e.g. 0775 or 0664
    """
    logging.debug("Changing mode of %s to %s" % (target,mode))
    if not os.path.islink(target):
        try:
            os.chmod(target,mode)
        except OSError, ex:
            logging.warning("Failed to change permissions on %s to %s: %s" % (target,mode,ex))
    else:
        logging.warning("Skipped chmod for symbolic link")

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
