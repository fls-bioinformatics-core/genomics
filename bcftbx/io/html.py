#!/usr/bin/env python3
#
#     html.py: classes for generating HTML
#     Copyright (C) University of Manchester 2026 Peter Briggs
#


"""
Utility classes for generating HTML documents programmatically:

* ``HTMLWriter``: construct and output HTML documents, including
  embedding CSS rules and JavaScript code
* ``PNGBase64Encoder``: encode PNG images as base64 strings

The ``HTMLWriter`` class provides an interface for constructing the
boilerplate scaffolding for HTML documents.

Note that content added to the body of the document is reproduced
verbatim, so it's the job of the calling subprogram to include the
appropriate tags to enclose the content and ensure that it will
render correctly (for example by including opening and closing
tag pairs).

The ``PNGBase64Encoder`` class provides a single method that converts
a PNG image into a string that can be embedded in ``<img>`` tags in
HTML documents.
"""


from base64 import b64encode


class HTMLWriter:
    """
    Generic HTML generation class

    HTMLWriter provides basic operations for writing HTML files.

    Example usage:

    >>> p = HTMLWriter("Example page")
    >>> p.add("This is some text")
    >>> p.write("example.html")
    """

    def __init__(self,title=''):
        """
        Class for generating HTML documents programmatically

        Arguments:
          title (str): optional title for the HTML document
        """
        self._page_title = str(title)
        self._content = []
        self._css_rules = []
        self._javascript = []

    def add(self, content):
        """
        Add content to the HTML document

        Note that the supplied content is added to the HTML
        document as-is; no escaping is performed so the content
        can include arbitrary HTML tags. Note also that no
        validation is performed.

        Arguments:
          content (str): text to add to the HTML document
            body
        """
        self._content.append(str(content))

    def add_css_rule(self, rule):
        """
        Add CSS rule to the HTML document

        Defines a CSS rule that will be inlined into a
        "style" tag in the HTML head when the document is
        written out.

        The rule text is added as-is, e.g.:

        >>> p = HTMLWriter("Example page")
        >>> p.add_css_rule("body { color: blue; }")

        No checking or validation is performed.

        Arguments:
          rule: text defining CSS rule
        """
        self._css_rules.append(str(rule))

    def add_javascript(self, script):
        """Add JavaScript

        Defines a line of JavaScript code that will be
        inlined into a "script" tag in the HTML head when
        the document is written out.

        The code is added as-is, no checking or validation
        is performed.

        Arguments:
          script (str): JavaScript code
        """
        self._javascript.append(str(script))

    def write(self, filen=None, fp=None):
        """
        Write the HTML document to file

        Generates an HTML document based on the content, styles
        etc that have been defined by calls to the object's
        methods.

        Can supply either a filename or a file-like object
        opened for writing.

        Arguments:
          filen (str or None): name of the file to write the
            document to
          fp (object): file-like object opened for writing; if
            this is supplied then filen argument will be
            ignored even if it is not None

        Returns:
          String: the generated HTML document.
        """
        # Construct the HTML document line by line
        html = ["<!DOCTYPE html>",
                "<html>"]
        # Header
        html.extend(["<head>",
                     f"<title>{self._page_title}</title>",])
        # CSS rules
        if self._css_rules:
            html.append("<style type='text/css'>")
            html.extend(self._css_rules)
            html.append("</style>")
        # JavaScript
        if self._javascript:
            html.append("<script language='javascript' type='text/javascript'><!--")
            html.extend(self._javascript)
            html.append("--></script>")
        html.append("</head>")
        # Body
        html.append("<body>")
        html.extend(self._content)
        html.extend(["</body>",
                     "</html>"])
        # Write to file
        html = "\n".join(html) + "\n"
        if fp is None:
            with open(filen, "wt") as fp:
                fp.write(html)
        else:
            fp.write(html)
        return html


class PNGBase64Encoder:
    """
    Utility class to encode PNG file into a base64 string

    Base64 encoded PNGs can be embedded in HTML <img> tags.

    Provides a single method ``encodePNG``:

    >>> p = PNGBase64Encoder.encodePNG("image.png")
    """

    def encodePNG(self, png):
        """
        Encode a PNG image into a base64 string

        Arguments:
          png (str): PNG image to encode

        Returns:
          String: the base64 encoded PNG image.
        """
        with open(png, "rb") as fp:
            return b64encode(fp.read()).decode()
