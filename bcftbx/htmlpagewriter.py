#!/usr/bin/env python
#
#     htmlpagewriter: programmatic generation of HTML files
#     Copyright (C) University of Manchester 2012-2020 Peter Briggs
#
########################################################################
#
# htmlpagewriter.py
#
#########################################################################

__version__ = "1.0.3"

"""htmlpagewriter

Provides HTMLPageWriter class which provides a simple programmatic
interface for generating HTML files.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

from builtins import str
import os
import io
import logging
import xml.dom.minidom
import shutil
import base64
from . import platforms
from . import TabFile

#######################################################################
# Classes
#######################################################################

class HTMLPageWriter(object):
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
        self.__page_title = str(title)
        self.__content = []
        self.__css_rules = []
        self.__javascript = []

    def add(self,content):
        """Add content to page body

        Note that the supplied content is added to the HTML
        document as-is; no escaping is performed so the content
        can include arbitrary HTML tags. Note also that no
        validation is performed.

        Arguments:
          content: text to add to the HTML document body
        """
        self.__content.append(str(content))

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
        self.__css_rules.append(str(css_rule))

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
        self.__javascript.append(str(javascript))

    def write(self,filen=None,fp=None):
        """Write the HTML document to file

        Generates a HTML document based on the content, styles
        etc that have been defined by calls to the object's
        methods.

        Can supply either a filename or a file-like object
        opened for writing.

        Arguments:
          filen: name of the file to write the document to.
          fp   : file-like object opened for writing; if this
                 is supplied then filen argument will be
                 ignored even if it is not None.

        """
        if fp is None and filen is not None:
            fp = io.open(filen,'wt')
        fp.write(u"<html>\n")
        # Header
        fp.write(u"<head>\n")
        fp.write(u"<title>%s</title>\n" % self.__page_title)
        # CSS rules
        if self.__css_rules:
            fp.write(u"<style type=\"text/css\">\n")
            fp.write(u'\n'.join(self.__css_rules))
            fp.write(u"</style>\n")
        # JavaScript
        if self.__javascript:
            fp.write(u"<script language='javascript' type='text/javascript'><!--\n")
            fp.write(u'\n'.join(self.__javascript))
            fp.write(u"\n--></script>\n")
        fp.write(u"</head>\n")
        # Body and content
        fp.write(u"<body>\n")
        fp.write(u'\n'.join(self.__content))
        fp.write(u"</body>\n")
        # Finish
        fp.write(u"</html>\n")
        if filen is not None:
            fp.close()

# Utility class to encode PNGs for embedding in HTML
class PNGBase64Encoder(object):
    """Utility class to encode PNG file into a base64 string

    Base64 encoded PNGs can be embedded in HTML <img> tags.

    To use:

    >>> p = PNGBase64Encoder.encodePNG("image.png")
    """

    def encodePNG(self,pngfile):
        """Return base64 string encoding a PNG file.
        """
        return base64.b64encode(io.open(pngfile,'rb').read()).decode()
