#!/usr/bin/env python3
#
#     text.py: text manipulations
#     Copyright (C) University of Manchester 2026 Peter Briggs


"""
Text manipulations:

* split_into_lines: split text into multiple lines with length limit
"""


def split_into_lines(text, char_limit, delimiters=' \t\n',
                     sympathetic=False):
    """
    Split a string into multiple lines with maximum length

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
      text (str): string of text to be split into lines
      char_limit (int): maximum length for any given line
      delimiters (str): optional, specify a set of non-default
        delimiter characters (defaults to whitespace)
      sympathetic (bool): optional, if True then add hyphen to
        indicate when a word has been broken

    Returns:
      List: lines of split text as strings.
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