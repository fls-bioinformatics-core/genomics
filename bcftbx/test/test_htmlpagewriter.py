#######################################################################
# Tests for htmlpagewriter.py module
#######################################################################
from bcftbx.htmlpagewriter import HTMLPageWriter
from bcftbx.htmlpagewriter import PNGBase64Encoder
import unittest
import io
import base64
import tempfile

class TestHTMLPageWriter(unittest.TestCase):
    """
    """
    def test_empty_content(self):
        html = HTMLPageWriter()
        fp = io.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title></title>
</head>
<body>
</body>
</html>
""")
        
    def test_simple_content(self):
        html = HTMLPageWriter("Test")
        html.add("This is a test")
        fp = io.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
</head>
<body>
This is a test</body>
</html>
""")
        
    def test_multiple_content_additions(self):
        html = HTMLPageWriter("Test")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p></body>
</html>
""")
        
    def test_add_css_rules(self):
        html = HTMLPageWriter("Test")
        html.addCSSRule("body { color: blue; }")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<style type=\"text/css\">
body { color: blue; }</style>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p></body>
</html>
""")
        
    def test_add_javascript(self):
        html = HTMLPageWriter("Test")
        html.addJavaScript("// Comment")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = io.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<script language='javascript' type='text/javascript'><!--
// Comment
--></script>
</head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p></body>
</html>
""")

class TestPNGBase64Encoder(unittest.TestCase):
    def setUp(self):
        # Make a psuedo-PNG test file
        data = b"PNG data"
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            self.filen = fp.name
            fp.write(data)
        self.encoded_data = base64.b64encode(data)

    def test_encodePNG(self):
        self.assertEqual(self.encoded_data,
                         PNGBase64Encoder().encodePNG(self.filen))

    def test_encodePNG_insert_into_text(self):
        self.assertEqual("the encoded text is: '%s'" % self.encoded_data,
                         "the encoded text is: '%s'" %
                         PNGBase64Encoder().encodePNG(self.filen))
