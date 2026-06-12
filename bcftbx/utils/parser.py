#!/usr/bin/env python3
#
#     parser.py: command line parsing helpers
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Command line parsing helper functions:

* parse_named_lanes: process "named lane expression" ('[<lanes>:]<name>')
* parse_lanes: process specifier with lists and/or ranges of lane numbers
"""


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