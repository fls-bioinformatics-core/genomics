#!/usr/bin/env python3
#
#     path.py: pathname manipulations
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Pathname manipulations:

* commonprefix: longest common prefix for two paths
* rootname: path with extensions stripped off
* strip_ext: strip extension from path
* is_gzipped_file: check if path has '.gz' extension
"""


import os


def commonprefix(path1, path2):
    """
    Determine common prefix path for path1 and path2

    Use this in preference to os.path.commonprefix as the version
    in os.path compares the two paths in a character-wise fashion
    and so can give counter-intuitive matches; this version compares
    path components which seems more sensible.

    For example: for two paths /mnt/dir1/file and /mnt/dir2/file,
    os.path.commonprefix will return /mnt/dir, whereas this function
    will return /mnt.

    Arguments:
      path1 (str): first path in comparison
      path2 (str): second path in comparison

    Returns:
      String: leading part of path which is common to both input paths.
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


def rootname(name):
    """
    Remove all extensions from name

    Arguments:
      name (str): name of a file

    Returns:
      String: Leading part of name up to first dot, i.e. name without any
        trailing extensions.

    """
    try:
        i = name.index('.')
        return name[0:i]
    except ValueError:
        # No dot
        return name


def strip_ext(name, ext=None):
    """
    Strip extension from file name

    Given a file name or path, remove the extension (including the
    dot) and return just the leading part of the name.

    If an extension is explicitly specified then only remove the
    extension if it matches.

    Extension can be multipart e.g. 'fastq.gz' and can include a
    leading dot e.g. '.gz' or 'gz'.

    Arguments:
      name (str): name of a file

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


def is_gzipped_file(filename):
    """
    Check if a file has a .gz extension

    Arguments:
      filename (str): name of the file to be tested (can include leading path)

    Returns:
      Boolean: True if filename has trailing .gz extension, False if not.
    """
    return os.path.splitext(filename)[1] == '.gz'