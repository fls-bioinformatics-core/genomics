#######################################################################
# Tests for io.html.py module
#######################################################################


import unittest
import io
import tempfile
from base64 import b64encode
from bcftbx.io.html import HTMLWriter
from bcftbx.io.html import PNGBase64Encoder


class TestHTMLWriter(unittest.TestCase):
    """
    Tests for the HTMLWriter class
    """
    def test_empty_content(self):
        """
        HTMLWriter: should return an 'empty' document
        """
        expected = """<!DOCTYPE html>
<html>
<head>
<title></title>
</head>
<body>
</body>
</html>
"""
        html = HTMLWriter()
        fp = io.StringIO()
        self.assertEqual(html.write(fp=fp), expected)
        self.assertEqual(fp.getvalue(), expected)

    def test_simple_content(self):
        """
        HTMLWriter: should return a 'simple' document
        """
        expected = """<!DOCTYPE html>
<html>
<head>
<title>Test</title>
</head>
<body>
This is a test
</body>
</html>
"""
        html = HTMLWriter("Test")
        html.add("This is a test")
        fp = io.StringIO()
        self.assertEqual(html.write(fp=fp), expected)
        self.assertEqual(fp.getvalue(), expected)

    def test_multiple_content_additions(self):
        """
        HTMLWriter: should return a document with multiple paragraphs
        """
        expected = """<!DOCTYPE html>
<html>
<head>
<title>Test</title>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p>
</body>
</html>
"""
        html = HTMLWriter("Test")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        self.assertEqual(html.write(fp=fp), expected)
        self.assertEqual(fp.getvalue(), expected)

    def test_add_css_rules(self):
        """
        HTMLWriter: should include CSS rules
        """
        expected = """<!DOCTYPE html>
<html>
<head>
<title>Test</title>
<style type='text/css'>
body { color: blue; }
</style>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p>
</body>
</html>
"""
        html = HTMLWriter("Test")
        html.add_css_rule("body { color: blue; }")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        self.assertEqual(html.write(fp=fp), expected)
        self.assertEqual(fp.getvalue(), expected)

    def test_add_javascript(self):
        """
        HTMLWriter: should include JavaScript code
        """
        expected = """<!DOCTYPE html>
<html>
<head>
<title>Test</title>
<script language='javascript' type='text/javascript'><!--
// Comment
--></script>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p>
</body>
</html>
"""
        html = HTMLWriter("Test")
        html.add_javascript("// Comment")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        self.assertEqual(html.write(fp=fp), expected)
        self.assertEqual(fp.getvalue(), expected)


class TestPNGBase64Encoder(unittest.TestCase):
    """
    Tests for the PNGBase64Encoder class.
    """
    def setUp(self):
        # Make a psuedo-PNG test file
        data = b"PNG data"
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            self.filen = fp.name
            fp.write(data)
        self.encoded_data = b64encode(data).decode()

    def test_encodePNG(self):
        """
        PNGBase64Encoder: should return a base64 encoded PNG image
        """
        self.assertEqual(self.encoded_data,
                         PNGBase64Encoder().encodePNG(self.filen))

    def test_encodePNG_insert_into_text(self):
        """
        PNGBase64Encoder: encoded PNG image can be inserted into text
        """
        self.assertEqual(f"the encoded text is: '{self.encoded_data}'",
                         f"the encoded text is: '{PNGBase64Encoder().encodePNG(self.filen)}'")
