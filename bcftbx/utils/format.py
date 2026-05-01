#!/usr/bin/env python3
#
#     format.py: text formatting helpers
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Text formatting helpers:

* format_file_size: convert bytes to human-readable format
* convert_size_to_bytes: convert human-readable size to bytes
"""


import math


def format_file_size(fsize, units=None):
    """
    Format a file size from bytes to human-readable form

    Takes a file size in bytes and returns a human-readable
    string, e.g. 4.0K, 186M, 1.5G.

    Alternatively specify the required units via the 'units'
    arguments.

    Arguments:
      fsize (int): size in bytes
      units (str): (optional) specify output in kb ('K'), Mb ('M'),
        Gb ('G'), Tb ('T') or Pb ('P')

    Returns:
      String: human-readable version of file size.
    """
    # Return size in human readable form
    if units is not None:
        units = units.upper()
    fsize = float(fsize)/1024
    unit_list = 'KMGTP'
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
    return "%.1f%s" % (fsize, unit)


def convert_size_to_bytes(size):
    """
    Converts a human-readable size specification to bytes

    Given an arbitrary human-readable file size (e.g.
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