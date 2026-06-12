#!/usr/bin/env python3
#
#     names.py: sample name manipulations
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Sample name manipulations:

* extract_initials: return leading initials from a sample name
* extract_prefix: return the sample name prefix
* extract_index_as_string: return the sample name index as a string
* extract_index: return the sample name index as an integer
* pretty_print_names: format a list of sample names for pretty printing
* name_matches: simple wildcard matching of project and sample names
"""


import string


def extract_initials(name):
    """
    Return leading initials from the sample name

    Conventionally the experimenter's initials are the leading characters
    of the name e.g. 'DR' for 'DR1', 'EP' for 'EP_NCYC2669', 'CW' for
    'CW_TI' etc

    Arguments:
      name (str): the name of a sample

    Returns:
      String: the leading initials from the name.
    """
    initials = []
    for c in str(name):
        if c.isalpha():
            initials.append(c)
        else:
            break
    return ''.join(initials)


def extract_prefix(name):
    """
    Return the sample name prefix

    Arguments:
      name (str): the name of a sample

    Returns:
      String: the prefix consisting of the name with trailing numbers
        removed, e.g. 'LD_C' for 'LD_C1'
    """
    return str(name).rstrip(string.digits)


def extract_index_as_string(name):
    """
    Return the sample name index as a string

    Arguments:
      name (str): the name of a sample or library

    Returns:
      String: the extracted index, consisting of the trailing numbers from the
        name, returned as a string to preserve leading zeroes (e.g. '1' for
       'LD_C1', '07' for 'DR07' etc)
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
    """
    Return the sample name index as an integer

    Arguments:
      name (str): the name of a sample or library

    Returns:
      Integer: the index as an integer, or None if the index cannot be
        converted to integer format.
    """
    indx = extract_index_as_string(name)
    if indx == '':
        return None
    else:
        return int(indx)


def pretty_print_names(name_list):
    """
    Format a list of sample names for pretty printing.

    Arguments:
      name_list (list): a list or tuple of sample names

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
            if prefix == last_prefix and index_ == last_index + 1:
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
            out.append(group[0] + "-" + extract_index_as_string(group[-1]))
    # Concatenate and return
    return ', '.join(out)


def name_matches(name, pattern):
    """
    Simple wildcard matching of project and sample names

    Matching options are:

    - exact match of a single name e.g. pattern 'PJB' matches 'PJB'
    - match start of a name using trailing '*' e.g. pattern 'PJ*' matches
      'PJB','PJBriggs' etc
    - match using multiple patterns by separating with comma e.g. pattern
      'PJB,IJD' matches 'PJB' or 'IJD'. Subpatterns can include trailing
      '*' character to match more names.

    Arguments
      name (str): text to match against pattern
      pattern (str): simple 'glob'-like pattern to match against

    Returns
      Boolean: True if name matches pattern; False otherwise.
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