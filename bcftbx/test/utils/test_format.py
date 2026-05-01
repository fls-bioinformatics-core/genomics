#######################################################################
# Tests for utils/format.py module
#######################################################################

import unittest


from bcftbx.utils.format import format_file_size
from bcftbx.utils.format import convert_size_to_bytes


class TestFormatFileSize(unittest.TestCase):
    """
    Unit tests for formatting file sizes
    """
    def test_bytes_to_kb(self):
        """
        utils.format.format_file_size: converts bytes to Kb
        """
        self.assertEqual("0.9K",format_file_size(900))
        self.assertEqual("0.9K",format_file_size(900,units='K'))
        self.assertEqual("0.9K",format_file_size(900,units='k'))
        self.assertEqual("4.0K",format_file_size(4096))
        self.assertEqual("4.0K",format_file_size(4096,units='K'))
        self.assertEqual("4.0K",format_file_size(4096,units='k'))

    def test_bytes_to_mb(self):
        """
        utils.format.format_file_size: converts bytes to Mb
        """
        self.assertEqual("186.0M",format_file_size(195035136))
        self.assertEqual("186.0M",format_file_size(195035136,units='M'))
        self.assertEqual("186.0M",format_file_size(195035136,units='m'))
        self.assertEqual("0.0M",format_file_size(900,units='M'))
        self.assertEqual("0.0M",format_file_size(4096,units='M'))

    def test_bytes_to_gb(self):
        """
        utils.format.format_file_size: converts bytes to Gb
        """
        self.assertEqual("1.6G",format_file_size(1717986919))
        self.assertEqual("1.6G",format_file_size(1717986919,units='G'))
        self.assertEqual("1.6G",format_file_size(1717986919,units='g'))
        self.assertEqual("0.0G",format_file_size(900,units='G'))
        self.assertEqual("0.0G",format_file_size(4096,units='G'))
        self.assertEqual("0.2G",format_file_size(195035136,units='G'))

    def test_bytes_to_tb(self):
        """
        utils.format.format_file_size converts bytes to Tb
        """
        self.assertEqual("4.4T",format_file_size(4831838208091))
        self.assertEqual("4.4T",format_file_size(4831838208091,units='T'))
        self.assertEqual("4.4T",format_file_size(4831838208091,units='t'))
        self.assertEqual("0.0T",format_file_size(900,units='T'))
        self.assertEqual("0.0T",format_file_size(4096,units='T'))
        self.assertEqual("0.0T",format_file_size(195035136,units='T'))
        self.assertEqual("0.2T",format_file_size(171798691900,units='T'))


class TestConvertSizeToBytes(unittest.TestCase):
    """
    Unit tests for converting file sizes to bytes
    """
    def test_convert_size_to_bytes(self):
        """
        utils.format.convert_size_to_bytes: handle different inputs
        """
        self.assertEqual(convert_size_to_bytes('4.0K'),4096)
        self.assertEqual(convert_size_to_bytes('4.0M'),4194304)
        self.assertEqual(convert_size_to_bytes('4.0G'),4294967296)
        self.assertEqual(convert_size_to_bytes('4.0T'),4398046511104)
        self.assertEqual(convert_size_to_bytes('4T'),4398046511104)