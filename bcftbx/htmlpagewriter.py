#!/usr/bin/env python
#
#     htmlpagewriter: programmatic generation of HTML files
#     Copyright (C) University of Manchester 2012-2026 Peter Briggs
#
########################################################################
#
# htmlpagewriter.py
#
#########################################################################

"""
Legacy module providing utility classes for programmatic HTML document
generation.

The core functionality has been moved to the ``io.html`` module, which
implements the ``HTMLWriter`` (refactored version of ``HTMLPageWriter``)
and ``PNGBase64Encoder`` classes, and which are used within this module as
the basis for the backwards-compatible versions.

The classes in this module are now deprecated and should not be used in new
code; they are likely to be removed in a future release.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from builtins import str
import io
import base64
from .io import html

#######################################################################
# Classes
#######################################################################

class HTMLPageWriter(html.HTMLWriter):
    """Generic HTML generation class

    HTMLPageWriter provides basic operations for writing HTML
    files.

    Example usage:

    >>> p = HTMLPageWriter("Example page")
    >>> p.add("This is some text")
    >>> p.write("example.html")
    """

    def __init__(self,title=''):
        """Create a new HTMLPageWriter instance

        Arguments:
          title: optional title for the HTML document
        """
        super().__init__(title)

    def addCSSRule(self,css_rule):
        """Add CSS rule

        Defines a CSS rule that will be inlined into a
        "style" tag in the HTML head when the document is
        written out.

        The rule text is added as-is, e.g.:

        >>> p = HTMLPageWriter("Example page")
        >>> p.addCSSRule("body { color: blue; }")

        No checking or validation is performed.

        Arguments:
          css_rule: text defining CSS rule
        """
        self.add_css_rule(css_rule)

    def addJavaScript(self,javascript):
        """Add JavaScript

        Defines a line of Javascript code that will be
        inlined into a "script" tag in the HTML head when
        the document is written out.

        The code is added as-is, no checking or validation
        is performed.

        Arguments:
          javascript: Javascript code
        """
        self.add_javascript(javascript)

# Utility class to encode PNGs for embedding in HTML
class PNGBase64Encoder(html.PNGBase64Encoder):
    """Utility class to encode PNG file into a base64 string

    Base64 encoded PNGs can be embedded in HTML <img> tags.

    To use:

    >>> p = PNGBase64Encoder.encodePNG("image.png")
    """