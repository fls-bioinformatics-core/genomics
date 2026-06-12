#######################################################################
# Tests for utils/text.py module
#######################################################################


import unittest
from bcftbx.utils.text import split_into_lines


class TestSplitIntoLinesFunction(unittest.TestCase):
    """
    Unit tests for the split_into_lines function
    """
    def test_split_into_lines(self):
        """
        utils.text.split_into_lines: check line splitting
        """
        self.assertEqual(split_into_lines('This is some text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is\nsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is\tsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is \tsome text',10),
                         ['This is','some text'])
        self.assertEqual(split_into_lines('This is some text',17),
                         ['This is some text'])
        self.assertEqual(split_into_lines('This is some text',100),
                         ['This is some text'])

    def test_split_into_lines_delimiter_after_line_limit(self):
        """
        utils.text.split_into_lines: delimiter after line limit
        """
        self.assertEqual(split_into_lines('This is some text',12),
                         ['This is some','text'])

    def test_split_into_lines_sympathetically(self):
        """
        utils.text.split_into_lines: split sympathetically
        """
        self.assertEqual(split_into_lines("This is supercalifragilicous text",10),
                         ['This is','supercalif','ragilicous','text'])
        self.assertEqual(split_into_lines("This is supercalifragilicous text",10,
                                          sympathetic=True),
                         ['This is','supercali-','fragilico-','us text'])

    def test_split_into_lines_alternative_delimiters(self):
        """
        utils.text.split_into_lines: use alternative delimiter
        """
        self.assertEqual(split_into_lines('This is some text',10,':'),
                         ['This is so','me text'])
        self.assertEqual(split_into_lines('This: is some text',10,':'),
                         ['This',' is some t','ext'])