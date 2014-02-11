#######################################################################
# Tests for Md5sum.py module
#######################################################################
from Md5sum import *
import unittest
import os
import tempfile

test_text = """Md5sum is a Python module with functions for generating
MD5 checksums for files."""

class TestHexify(unittest.TestCase):

    def test_hexify(self):
        """Test hexify function
        """
        self.assertEqual(hexify("hello!"),'68656c6c6f21')
        self.assertEqual(hexify("goodbye"),'676f6f64627965')

class TestMd5sum(unittest.TestCase):

    def setUp(self):
        # mkstemp returns a tuple
        tmpfile = tempfile.mkstemp()
        self.filen = tmpfile[1]
        fp = open(self.filen,'w')
        fp.write(test_text)
        fp.close()

    def tearDown(self):
        os.remove(self.filen)

    def test_md5sum(self):
        """Test generation of md5sum
        """
        self.assertEqual(md5sum(self.filen),
                         '08a6facee51e5435b9ef3744bd4dd5dc')

    def test_no_file_name(self):
        """Test handling of file name 'None'
        """
        self.assertRaises(Exception,md5sum,None)
        
########################################################################
# Main: test runner
#########################################################################
if __name__ == "__main__":
    # Run tests
    unittest.main()
