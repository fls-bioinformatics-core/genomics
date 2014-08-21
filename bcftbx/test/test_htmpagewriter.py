#######################################################################
# Tests for htmlpagewriter.py module
#######################################################################
from bcftbx.htmlpagewriter import HTMLPageWriter,PNGBase64Encoder
import unittest
import cStringIO

class TestHTMLPageWriter(unittest.TestCase):
    """
    """
    def test_empty_content(self):
        html = HTMLPageWriter()
        fp = cStringIO.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title></title>
<head>
<body>
</body>
</html>
""")
        
    def test_simple_content(self):
        html = HTMLPageWriter("Test")
        html.add("This is a test")
        fp = cStringIO.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<head>
<body>
This is a test</body>
</html>
""")
        
    def test_multiple_content_additions(self):
        html = HTMLPageWriter("Test")
        html.add("<p>This is a test</p>")
        html.add("<p>We can see how well it works...</p>")
        fp = cStringIO.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<head>
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
        fp = cStringIO.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<style type=\"text/css\">
body { color: blue; }</style>
<head>
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
        fp = cStringIO.StringIO()
        html.write(fp=fp)
        self.assertEqual(fp.getvalue(),
                         """<html>
<head>
<title>Test</title>
<script language='javascript' type='text/javascript'><!--
// Comment
--></script>
<head>
<body>
<p>This is a test</p>
<p>We can see how well it works...</p></body>
</html>
""")
        
