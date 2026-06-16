#######################################################################
# Tests for io.tabular.py module
#######################################################################


import unittest
import os
import shutil
import tempfile
from io import StringIO
from bcftbx.io.tabular import TabFile
from bcftbx.io.tabular import TabLine
from bcftbx.io.tabular import TabFileIterator


class TestTabFile(unittest.TestCase):

    def setUp(self):
        # Header
        self.header = u"#chr\tstart\tend\tdata\n"
        # Tab-delimited data
        self.data = \
u"""chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
"""
        # Make file-like object to read data in
        self.fp = StringIO(self.header + self.data)

        # Make temporary directory
        self.working_dir = tempfile.mkdtemp(suffix='TestTabFile')

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()
        # Remove the temporary directory
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_load_data(self):
        """
        TabFile: create and load new TabFile instance
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), [], "Header should be empty")
        self.assertEqual(str(tabfile[0]), u"chr1\t1\t234\t4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2][0], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.filename(), 'test')

    def test_write_data(self):
        """
        TabFile: write data to file-like object
        """
        tabfile = TabFile(fp=self.fp)
        fp = StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(), self.data)
        fp.close()

    def test_write_data_include_header(self):
        """
        TabFile: write data to file-like object including header
        """
        tabfile = TabFile(fp=self.fp, first_line_is_header=True)
        fp = StringIO()
        tabfile.write(fp=fp, include_header=True)
        self.assertEqual(fp.getvalue(), self.header + self.data)
        fp.close()

    def test_write_data_to_file(self):
        """
        TabFile: write data to file
        """
        tabfile = TabFile(fp=self.fp)
        out_file = os.path.join(self.working_dir, "test.tsv")
        tabfile.write(filen=out_file)
        with open(out_file, 'rt') as fp:
            self.assertEqual(fp.read(), self.data)

    def test_write_data_to_file_include_header(self):
        """
        TabFile: write data to file including header
        """
        tabfile = TabFile(fp=self.fp, first_line_is_header=True)
        out_file = os.path.join(self.working_dir, "test.tsv")
        tabfile.write(filen=out_file, include_header=True)
        with open(out_file, 'rt') as fp:
            self.assertEqual(fp.read(), self.header + self.data)

    def test_load_data_with_header(self):
        """
        TabFile: create and load Tabfile using first line as header
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'], "Wrong header")
        self.assertEqual(str(tabfile[0]), "chr1\t1\t234\t4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)

    def test_load_data_setting_explicit_header(self):
        """
        TabFile: create and load TabFile setting the header explicitly
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True,
                          column_names=('CHROM', 'START', 'STOP', 'VALUES'))
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), ['CHROM', 'START', 'STOP', 'VALUES'], "Wrong header")
        self.assertEqual(str(tabfile[0]), "chr1\t1\t234\t4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2]['CHROM'], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)

    def test_lookup(self):
        """
        TabFile: look up data
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Look for lines with 'chr1' in the chr column
        matching = tabfile.lookup('chr', 'chr1')
        self.assertEqual(len(matching), 2)
        for m in matching:
            self.assertEqual(m['chr'], 'chr1', "Lookup returned bad match: '%s'" % m)
        self.assertNotEqual(matching[0], matching[1])
        # Look for lines with 'chr2' in the chr column
        matching = tabfile.lookup('chr', 'chr2')
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]['chr'], 'chr2', "Lookup returned bad match: '%s'" % m)
        # Look for lines with 'bananas' in the chr column
        self.assertEqual(len(tabfile.lookup('chr', 'bananas')), 0)

    def test_get_index_by_line_number(self):
        """
        TabFile: look up line numbers from a TabFile
        """
        tabfile = TabFile('test', self.fp)
        # Look for an existing line
        self.assertEqual(tabfile.index_by_line_number(2), 0)
        self.assertEqual(tabfile[tabfile.index_by_line_number(2)].line_number(), 2)
        # Look for the first line in the file (the commented header)
        self.assertRaises(IndexError, tabfile.index_by_line_number, 1)
        # Look for a generally non-existant line number
        self.assertRaises(IndexError, tabfile.index_by_line_number, -12)
        # Look for a negative line number
        self.assertRaises(IndexError, tabfile.index_by_line_number, 99)

    def test_append_empty_line(self):
        """
        TabFile: append a blank line
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.append()
        self.assertEqual(len(tabfile), 4)
        # Check new line is empty
        for i in range(len(line)):
            self.assertTrue(str(line[i]) == '')

    def test_append_line_with_data(self):
        """
        TabFile: append line populated with data
        """
        data = ['chr1', 678, 901, 6.1]
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.append(data)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        for i in range(len(data)):
            self.assertTrue(line[i] == data[i])

    def test_append_line_with_raw_line(self):
        """
        TabFile: append line populated with 'raw' tabbed data
        """
        data = "chr1\t10000\t20000\t+"
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.append(data)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        self.assertTrue(str(line) == data)

    def test_append_line(self):
        """
        TabFile: append a TabLine to a TabFile
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        tabline = TabLine('chr1\t10000\t20000\t+')
        line = tabfile.append(tabline)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        self.assertTrue(len(line) == len(tabline))
        for x,y in zip(line, tabline):
            self.assertTrue(str(x) == str(y))

    def test_insert_empty_line(self):
        """
        TabFile: insert a blank line into a TabFile
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.insert(2)
        self.assertEqual(len(tabfile), 4)
        # Check new line is empty
        for i in range(len(line)):
            self.assertTrue(str(line[i]) == '')

    def test_insert_line_with_data(self):
        """
        TabFile: insert line into a TabFile populated with data
        """
        data = ['chr1', 678, 901, 6.1]
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.insert(2, data)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        for i in range(len(data)):
            self.assertTrue(line[i] == data[i])

    def test_insert_line_with_tabbed_data(self):
        """
        TabFile: insert line of 'raw' tabbed data
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        line = tabfile.insert(2, data)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        self.assertTrue(str(line) == data)

    def test_insert_line(self):
        """
        TabFile: insert a populated TabLine
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 3)
        tabline = TabLine('chr1\t10000\t20000\t+')
        line = tabfile.insert(2, tabline)
        self.assertEqual(len(tabfile), 4)
        # Check new line is correct
        self.assertTrue(len(line) == len(tabline))
        for x,y in zip(line, tabline):
            self.assertTrue(str(x) == str(y))

    def test_append_column(self):
        """
        TabFile: append a new column
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        self.assertEqual(len(tabfile.header()), 4)
        tabfile.append_column('new')
        self.assertEqual(len(tabfile.header()), 5)
        self.assertEqual(tabfile.header()[4], 'new')
        self.assertEqual(tabfile[0]['new'], '')

    def test_append_column_with_value(self):
        """
        TabFile: append new column with a fill value
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        self.assertEqual(len(tabfile.header()), 4)
        tabfile.append_column('new', fill_value='new_value')
        self.assertEqual(len(tabfile.header()), 5)
        self.assertEqual(tabfile.header()[4], 'new')
        self.assertEqual(tabfile[0]['new'], 'new_value')


class TestWhiteSpaceHandlingTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""chr1\t1\t234\t4.6\tA comment
chr1\t567\t890\t5.7\tComment with a trailing space 
chr2\t1234\t5678\t6.8\t.
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_preserve_trailing_spaces_on_lines(self):
        """
        TabFile: check that trailing spaces aren't lost
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(tabfile[0][4], "A comment")
        self.assertEqual(tabfile[1][4], "Comment with a trailing space ")
        self.assertEqual(tabfile[2][4], ".")


class TestUncommentedHeaderTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_expected_uncommented_header(self):
        """
        TabFile: read in a tab file with an expected uncommented header
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'], "Wrong header")
        self.assertEqual(str(tabfile[0]), "chr1\t1\t234\t4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)

    def test_unexpected_uncommented_header(self):
        """
        TabFile: read in a tab file with an unexpected uncommented header
        """
        tabfile = TabFile('test', self.fp)
        self.assertEqual(len(tabfile), 4, "Input has 4 lines of data")
        self.assertEqual(tabfile.header(), [], "Wrong header")
        self.assertEqual(str(tabfile[0]), "chr\tstart\tend\tdata", "Incorrect string representation")
        self.assertRaises(KeyError, tabfile[3].__getitem__, 'chr')
        self.assertEqual(tabfile.ncols(), 4)


class TestEmptyTabFile(unittest.TestCase):

    def test_make_empty_tabfile(self):
        """
        TabFile: create an empty TabFile (no associated file)
        """
        tabfile = TabFile()
        self.assertEqual(len(tabfile), 0, "new TabFile should have zero length")

    def test_add_data_to_new_tabfile(self):
        """
        TabFile: add data as a list of items to a new empty TabFile
        """
        data = ['chr1', 10000, 20000, '+']
        tabfile = TabFile()
        tabfile.append(data)
        self.assertEqual(len(tabfile), 1, "TabFile should now have one line")
        for i in range(len(data)):
            self.assertEqual(tabfile[0][i], data[i])

    def test_add_tab_data_to_new_tabfile(self):
        """
        TabFile: add 'raw' tabbed data to a new empty TabFile
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile()
        tabfile.append(data)
        self.assertEqual(len(tabfile), 1, "TabFile should now have one line")
        self.assertEqual(str(tabfile[0]), data)


class TestTabFileCSV(unittest.TestCase):
    """
    Test behaviour of different field delimiters
    """

    def setUp(self):
        # Header
        self.header = u"#chr\tstart\tend\tdata\n"
        # Tab-delimited data
        self.data = \
u"""chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
"""
        # Make file-like object to read data in
        self.fp = StringIO(self.header.replace('\t', ',') +
                           self.data.replace('\t', ','))

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_load_data_csv(self):
        """
        TabFile: create and load new TabFile instance with CSV data
        """
        tabfile = TabFile('test', self.fp, delimiter=',')
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), [], "Header should be empty")
        self.assertEqual(str(tabfile[0]), "chr1,1,234,4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2][0], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.filename(), 'test')

    def test_write_data_csv(self):
        """
        TabFile: write CSV data to file-like object
        """
        tabfile = TabFile('test', self.fp)
        fp = StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(), self.data.replace('\t', ','))
        fp.close()

    def test_load_data_with_header_csv(self):
        """
        TabFile: create and load CSV data using first line as header
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True, delimiter=',')
        self.assertEqual(len(tabfile), 3, "Input has 3 lines of data")
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'], "Wrong header")
        self.assertEqual(str(tabfile[0]), "chr1,1,234,4.6", "Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'], 'chr2', "Incorrect data")
        self.assertEqual(tabfile.ncols(), 4)

    def test_write_data_with_header_csv(self):
        """
        TabFile: write CSV data to file-like object including a header line
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True, delimiter=',')
        fp = StringIO()
        tabfile.write(fp=fp, include_header=True)
        self.assertEqual(fp.getvalue(), self.header.replace('\t', ',') + self.data.replace('\t', ','))
        fp.close()

    def test_append_line_csv(self):
        """
        TabFile: append a CSV line to a file
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True, delimiter=',')
        line = 'chr3,10,9,8'
        tabfile.append(line)
        self.assertEqual(str(tabfile[-1]), line)

    def test_append_line_as_data_csv(self):
        """
        TabFile: append a line to a CSV file with data supplied as a list
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True, delimiter=',')
        data = ['chr3', '10', '9', '8']
        tabfile.append(data)
        self.assertEqual(str(tabfile[-1]), ','.join([str(x) for x in data]))

    def test_change_delimiter_for_write(self):
        """
        TabFile: write data out with different delimiter to input
        """
        tabfile = TabFile('test', self.fp, delimiter=',')
        # Modified delimiter (tab)
        fp = StringIO()
        tabfile.write(fp=fp, delimiter='\t')
        self.assertEqual(fp.getvalue(), self.data)
        fp.close()
        # Default (should revert to comma)
        fp = StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(), self.data.replace('\t', ','))
        fp.close()


class TestTabFileValueConversions(unittest.TestCase):
    """
    Test that appropriate conversions are performed on input values
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""chr\tstart\tend\tdata
chr1\t1\t4.6
chr1\t567\t5.7
chr2\t1234\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_convert_values_to_type_read_from_file(self):
        """
        TabFile: convert input values to appropriate types when reading from file
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        for line in tabfile:
            self.assertTrue(isinstance(line[0], str))
            self.assertTrue(isinstance(line[1], int))
            self.assertTrue(isinstance(line[2], float))

    def test_convert_values_to_str_read_from_file(self):
        """
        TabFile: convert all input values to strings when reading from file
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True,
                          convert_values=False)
        for line in tabfile:
            for value in line:
                self.assertEqual(value, str(value))

    def test_convert_values_to_type_append_tabdata(self):
        """
        TabFile: convert input values to appropriate types when appending 'raw' tabbded data
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        tabfile.append("chr3\t5678\t7.9")
        for line in tabfile:
            self.assertEqual(line[0], str(line[0]))
            self.assertTrue(isinstance(line[1], int))
            self.assertTrue(isinstance(line[2], float))

    def test_convert_values_to_str_append_tabdata(self):
        """
        TabFile: convert all input values to strings when appending 'raw' tabbed data
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True,
                          convert_values=False)
        tabfile.append("chr3\t5678\t7.9")
        for line in tabfile:
            for value in line:
                self.assertEqual(value, str(value))

    def test_convert_values_to_type_append_list(self):
        """
        TabFile: convert input values to appropriate types when appending a list
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        tabfile.append(["chr3", "5678", "7.9"])
        tabfile.append(["chr3", 5678, 7.9])
        for line in tabfile:
            self.assertEqual(line[0], str(line[0]))
            self.assertTrue(isinstance(line[1], int))
            self.assertTrue(isinstance(line[2], float))

    def test_convert_values_to_str_append_list(self):
        """
        TabFile: convert all input values to strings when appending a list
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True,
                          convert_values=False)
        tabfile.append(["chr3", "5678", "7.9"])
        tabfile.append(["chr3", 5678, 7.9])
        for line in tabfile:
            for value in line:
                self.assertEqual(value, str(value))

    def test_convert_values_to_type_handle_underscores_in_numbers(self):
        """
        TabFile: handle conversion of numeric values with underscores
        """
        fp = StringIO(
            u"""chr\tstart\tend
chr1\t1_012\t4_292.6
""")
        tabfile = TabFile('test', fp, first_line_is_header=True,
                          convert_values=True,
                          allow_underscores_in_numeric_literals=True)
        self.assertEqual(tabfile[0]['start'], 1012)
        self.assertEqual(tabfile[0]['end'], 4292.6)
        fp = StringIO(
            u"""chr\tstart\tend
chr1\t1_012\t4_292.6
""")
        tabfile = TabFile('test', fp, first_line_is_header=True,
                          convert_values=True,
                          allow_underscores_in_numeric_literals=False)
        self.assertEqual(tabfile[0]['start'], "1_012")
        self.assertEqual(tabfile[0]['end'], "4_292.6")


class TestHandleCommentsInTabFile(unittest.TestCase):
    """
    Test handling commented lines
    """

    def test_remove_commented_lines_by_default(self):
        """
        TabFile: check commented lines are removed by default
        """
        content = \
u"""#chr\tstart\tend\tdata
chr1\t1\t234\t1.2
#chr1\t567\t890\t5.7
#chr2\t1234\t5678\t6.8
chr2\t2345\t6789\t12.1
"""
        final = \
u"""chr1\t1\t234\t1.2
chr2\t2345\t6789\t12.1"""
        fp = StringIO(content)
        tabfile = TabFile(fp=fp, first_line_is_header=True)
        self.assertEqual(len(tabfile), 2)
        self.assertEqual(tabfile[0]['chr'], "chr1")
        self.assertEqual(tabfile[0]['start'], 1)
        self.assertEqual(tabfile[0]['end'], 234)
        self.assertEqual(tabfile[0]['data'], 1.2)
        self.assertEqual(tabfile[1]['chr'], "chr2")
        self.assertEqual(tabfile[1]['start'], 2345)
        self.assertEqual(tabfile[1]['end'], 6789)
        self.assertEqual(tabfile[1]['data'], 12.1)
        self.assertEqual(str(tabfile), final)

    def test_keep_commented_lines(self):
        """
        TabFile: keep commented lines
        """
        content = \
u"""#chr\tstart\tend\tdata
chr1\t1\t234\t1.2
#chr1\t567\t890\t5.7
#chr2\t1234\t5678\t6.8
chr2\t2345\t6789\t12.1
"""
        final = \
u"""chr1\t1\t234\t1.2
#chr1\t567\t890\t5.7
#chr2\t1234\t5678\t6.8
chr2\t2345\t6789\t12.1"""
        fp = StringIO(content)
        tabfile = TabFile(fp=fp,
                          first_line_is_header=True,
                          keep_commented_lines=True)
        self.assertEqual(len(tabfile), 4)
        self.assertEqual(tabfile[0]['chr'], "chr1")
        self.assertEqual(tabfile[0]['start'], 1)
        self.assertEqual(tabfile[0]['end'], 234)
        self.assertEqual(tabfile[0]['data'], 1.2)
        self.assertEqual(tabfile[1]['chr'], "#chr1")
        self.assertEqual(tabfile[1]['start'], 567)
        self.assertEqual(tabfile[1]['end'], 890)
        self.assertEqual(tabfile[1]['data'], 5.7)
        self.assertEqual(tabfile[2]['chr'], "#chr2")
        self.assertEqual(tabfile[2]['start'], 1234)
        self.assertEqual(tabfile[2]['end'], 5678)
        self.assertEqual(tabfile[2]['data'], 6.8)
        self.assertEqual(tabfile[3]['chr'], "chr2")
        self.assertEqual(tabfile[3]['start'], 2345)
        self.assertEqual(tabfile[3]['end'], 6789)
        self.assertEqual(tabfile[3]['data'], 12.1)
        self.assertEqual(str(tabfile), final)


class TestBadTabFile(unittest.TestCase):
    """
    Test with 'bad' input files
    """

    def setUp(self):
        # Make file-like object with "bad" data
        self.fp = StringIO(
u"""#chr\tstart\tend\tdata
chr1\t1\t234
chr1\t567\t890\t5.7\t4.6
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_ragged_input_file(self):
        """
        TabFile: 'ragged' input (different numbers of items on each line)
        """
        self.assertRaises(IndexError, TabFile, 'test', self.fp, first_line_is_header=True)

    def test_ragged_input_file_no_header(self):
        """
        TabFile: 'ragged' input (different numbers of items on each line, no header)
        """
        self.assertRaises(IndexError, TabFile, 'test', self.fp)


class TestReorderTabFile(unittest.TestCase):
    """
    Test reordering of columns in TabFiles
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_reorder_columns(self):
        """
        TabFile: reorder columns
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Reorder
        new_columns = ['chr', 'data', 'start', 'end']
        tabfile = tabfile.reorder(new_columns)
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), new_columns)
        self.assertEqual(str(tabfile[0]), "chr1\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]), "chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]), "chr2\t6.8\t1234\t5678")

    def test_reorder_columns_empty_cells(self):
        """
        TabFile: reorder columns where some lines have empty cells at the start
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Reset some cells to empty
        tabfile[0]['chr'] = ''
        tabfile[2]['chr'] = ''
        # Reorder
        new_columns = ['chr', 'data', 'start', 'end']
        tabfile = tabfile.reorder(new_columns)
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), new_columns)
        self.assertEqual(str(tabfile[0]), "\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]), "chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]), "\t6.8\t1234\t5678")


class TestTransposeTabFile(unittest.TestCase):
    """
    Test transposing the contents of a TabFile
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_transpose_tab_file(self):
        """
        TabFile: transpose data (i.e. rows -> columns)
        """
        tabfile1 = TabFile('test', self.fp, first_line_is_header=False)
        tabfile2 = tabfile1.transpose()
        self.assertEqual(len(tabfile1), tabfile2.ncols())
        self.assertEqual(len(tabfile2), tabfile1.ncols())


class TestWholeColumnOperations(unittest.TestCase):
    """
    Test the 'transform' and 'compute' methods
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_set_column_to_constant_value(self):
        """
        TabFile: transform (set a column to a constant value)
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Add a strand column
        tabfile.append_column('strand')
        self.assertEqual(tabfile.ncols(), 5)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data', 'strand'])
        # Set all values to '+'
        tabfile.transform('strand', lambda x: '+')
        for line in tabfile:
            self.assertEqual(line['strand'], '+')

    def test_apply_operation_to_column(self):
        """
        TabFile: transform (divide values in a column by 10)
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Divide data column by 10
        tabfile.transform('data', lambda x: x / 10.0)
        results = [0.46, 0.57, 0.68]
        for i in range(len(tabfile)):
            # When checking the transformed column, coerce
            # the values to two decimal places to avoid tests
            # failing because of rounding errors (e.g.
            # 0.45999999999999996 != 0.46)
            self.assertEqual(float("%.2f" % tabfile[i]['data']),
                             results[i])

    def test_compute_midpoint(self):
        """
        TabFile: compute (midpoint of start and end columns)
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Compute midpoint of start and end
        tabfile.compute('midpoint', lambda line: (line['end'] + line['start']) / 2.0)
        self.assertEqual(tabfile.ncols(), 5)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data', 'midpoint'])
        results = [117.5, 728.5, 3456]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['midpoint'], results[i])

    def test_compute_and_overwrite_existing_column(self):
        """
        TabFile: compute (overwrite values in an existing column)
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Compute new values for data column
        tabfile.compute('data', lambda line: line['end'] - line['start'])
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        results = [233, 323, 4444]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'], results[i])

    def test_compute_and_overwrite_existing_column_integer_index(self):
        """
        TabFile: compute (overwrite existing column referenced using integer index)
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        # Compute new values for data column
        tabfile.compute(3, lambda line: line['end'] - line['start'])
        self.assertEqual(tabfile.ncols(), 4)
        self.assertEqual(tabfile.header(), ['chr', 'start', 'end', 'data'])
        results = [233, 323, 4444]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'], results[i])


class TestSortTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = StringIO(
u"""#chr\tstart\tend\tdata
chr1\t567\t890\t5.7
chr1\t1\t234\t6.8
chr2\t1234\t5678\t3.4
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_sort_on_column(self):
        """
        TabFile: sort data on a numerical column into (default) ascending order
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        tabfile.sort(lambda line: line['data'])
        sorted_data = [3.4, 5.7, 6.8]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'], sorted_data[i])

    def test_reverse_sort_on_column(self):
        """
        TabFile: sort data on a numerical column into (reverse) descending order
        """
        tabfile = TabFile('test', self.fp, first_line_is_header=True)
        tabfile.sort(lambda line: line['data'], reverse=True)
        sorted_data = [6.8, 5.7, 3.4]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'], sorted_data[i])


class TestTabLine(unittest.TestCase):

    def test_new_line_no_data(self):
        """
        TabLine: new data line with no data
        """
        line = TabLine()
        self.assertEqual(len(line), 0, "Line should have zero length")
        self.assertEqual(str(line), "", "String representation should be empty string")
        self.assertEqual(line.line_number(), None, "Line number should not be set")

    def test_new_line_header_no_data(self):
        """
        TabLine: new data line with header but no data
        """
        line = TabLine(column_names=('one', 'two', 'three', 'four'))
        self.assertEqual(len(line), 4, "Line should have 4 items")
        self.assertEqual(str(line), "\t\t\t", "String representation should be 3 tabs")
        self.assertEqual(line.line_number(), None, "Line number should not be set")

    def test_new_line_data_no_header(self):
        """
        TabLine: new data line with data but no header
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data)
        self.assertEqual(len(line), 4, "Line should have 4 items")
        self.assertEqual(str(line), input_data)

    def test_new_line_no_header_empty_items(self):
        """
        TabLine: new data line with no header and a line with empty items
        """
        input_data = "\t\t\t"
        line = TabLine(line=input_data)
        self.assertEqual(len(line), 4, "Line should have 4 items")
        self.assertEqual(str(line), input_data, "String representation should match input")

    def test_new_line_no_header_leading_empty_item(self):
        """
        TabLine: new data line with no header and a line with a leading empty item
        """
        input_data = "\t1.2\t3.4\t5.6"
        line = TabLine(line=input_data)
        self.assertEqual(len(line), 4, "Line should have 4 items")
        self.assertEqual(str(line), input_data, "String representation should match input")

    def test_get_and_set_data(self):
        """
        TabLine: 'get' and 'set' operations
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data, column_names=('one', 'two', 'three', 'four'))
        self.assertEqual(len(line), 4, "Line should have 4 items")
        self.assertEqual(str(line), input_data, "String representation should be same as input")
        # Test getting
        self.assertEqual(line[1], 2.2, "Column 2 data is incorrect")
        self.assertEqual(line["two"], 2.2, "Column 2 data is incorrect")
        # Test setting
        line["two"] = 4.4
        self.assertEqual(line[1], 4.4, "Column 2 data is incorrect after set operation")
        self.assertEqual(line["two"], 4.4, "Column 2 data is incorrect after set operation")

    def test_subsetting(self):
        """
        TabLine: retrieve subset from new data line
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data, column_names=('one', 'two', 'three', 'four'))
        # Subset with integer indices
        subset = line.subset(2, 3)
        self.assertEqual(len(subset), 2, "Subset should have 2 items")
        self.assertEqual(str(subset), "3.3\t4.4", "String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three", "four")
        self.assertEqual(len(subset), 2, "Subset should have 2 items")
        self.assertEqual(str(subset), "3.3\t4.4", "String representation should be last two columns")
        # Check key lookup still works
        self.assertEqual(subset["three"], 3.3)

    def test_subsetting_no_header(self):
        """
        TabLine: retrieve subset from new data line (no header)
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data)
        # Subset with integer indices
        subset = line.subset(2, 3)
        self.assertEqual(len(subset), 2, "Subset should have 2 items")
        self.assertEqual(str(subset), "3.3\t4.4", "String representation should be last two columns")
        # Check key lookup
        self.assertEqual(subset[2], 3.3)

    def test_subsetting_leading_empty_items(self):
        """
        TabLine: retrieve subset from new data line with leading empty item
        """
        input_data = "\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data, column_names=('one', 'two', 'three', 'four'))
        # Subset with integer indices
        subset = line.subset(2, 3)
        self.assertEqual(len(subset), 2, "Subset should have 2 items")
        self.assertEqual(str(subset), "3.3\t4.4", "String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three", "four")
        self.assertEqual(len(subset), 2, "Subset should have 2 items")
        self.assertEqual(str(subset), "3.3\t4.4", "String representation should be last two columns")

    def test_line_number(self):
        """
        TabLine: new data line with line number
        """
        line = TabLine(line="test", line_number=3)
        self.assertEqual(line.line_number(), 3, "Line number should be three")

    def test_invalid_line_numbers(self):
        """
        TabLine: can't create new data lines with invalid line numbers
        """
        self.assertRaises(ValueError, TabLine, line_number=-3)
        self.assertRaises(ValueError, TabLine, line_number="three")

    def test_iteration_over_items(self):
        """
        TabLine: iterate over data items in a line
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabLine(line=input_data)
        try:
            # This should work
            for item in line:
                pass
        except Exception as ex:
            # It hasn't worked
            self.fail("Iteration test exception: '%s'" % ex)

    def test_preserve_trailing_spaces_in_data_items(self):
        """
        TabLine: trailing spaces aren't lost from data items
        """
        input_data = "1.1\t2.2\tThis has trailing space "
        line = TabLine(line=input_data)
        self.assertEqual(line[2], "This has trailing space ")


class TestTabLineTypeConversion(unittest.TestCase):

    def test_convert_integers(self):
        """
        TabLine: string data should be converted to integers
        """
        test_values = [12, 34, 56]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i], test_values[i])

    def test_convert_floats(self):
        """
        TabLine: string data should be converted to floats
        """
        test_values = [1.2, 3.4, 5.6]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i], test_values[i])

    def test_convert_append_items(self):
        """
        TabLine: append items as strings and check type conversions
        """
        test_values = ['chr1', 2, 3.4]
        line = TabLine()
        for value in test_values:
            line.append(str(value))
        for i in range(len(test_values)):
            self.assertEqual(line[i], test_values[i])

    def test_convert_set_items(self):
        """
        TabLine: check type conversions for new values
        """
        test_values = ['chr1', 2, 3.4]
        line = TabLine(line="x\ty\tz")
        for i in range(len(test_values)):
            line[i] = str(test_values[i])
        for i in range(len(test_values)):
            self.assertEqual(line[i], test_values[i])

    def test_convert_preserve_objects(self):
        """
        TabLine: set item to object and check its type is preserved
        """
        test_values = ['chr1', {'this': 'is a dictionary'}]
        line = TabLine()
        for value in test_values:
            line.append(value)
        for i in range(len(test_values)):
            self.assertEqual(line[i], test_values[i])


class TestTabLineNoTypeConversion(unittest.TestCase):

    def test_no_type_conversion(self):
        """
        TabLine: disable type conversion
        """
        test_values = ['hello', 12, 34.56]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabLine(line=input_data, convert_values=False)
        for i in range(len(test_values)):
            self.assertEqual(line[i], str(test_values[i]))


class TestTabLineDelimiters(unittest.TestCase):

    def test_default_delimiters(self):
        """
        TabLine: check default delimiter (tab)
        """
        input_data = [1.1, 2.2, 3.3, 4.4]
        line = TabLine(line='\t'.join([str(x) for x in input_data]))
        for i in range(len(input_data)):
            self.assertEqual(input_data[i], line[i])

    def test_non_default_delimiters(self):
        """
        TabLine: check non-default delimiter (comma)
        """
        input_data = [1.1, 2.2, 3.3, 4.4]
        line = TabLine(line=','.join([str(x) for x in input_data]),
                           delimiter=',')
        for i in range(len(input_data)):
            self.assertEqual(input_data[i], line[i])


class TestTabFileIterator(unittest.TestCase):

    def setUp(self):
        # Tab-delimited data
        self.data = \
u"""chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
"""
        # Make file-like object to read data in
        self.fp = StringIO(self.data)

        # Make temporary directory
        self.working_dir = tempfile.mkdtemp(suffix='TestTabFileIterator')

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()
        # Remove the temporary directory
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_tabfileiterator_iterate_through_file(self):
        """
        TabFileIterator: iterates through TSV file
        """
        # Make test file
        tabfile = os.path.join(self.working_dir, 'test.tsv')
        with open(tabfile, 'wt') as fp:
            fp.write(self.data)
        # Iterate though file
        tsv = TabFileIterator(tabfile)
        for tabline, data in zip(tsv, self.data.split('\n')):
            self.assertTrue(isinstance(tabline, TabLine))
            self.assertEqual(str(tabline), data)

    def test_tabfileiterator_iterate_through_file_object(self):
        """
        TabFileIterator: iterates through TSV file-like object
        """
        # Make file-like object to read data from
        self.fp = StringIO(self.data)
        # Iterate though data
        tsv = TabFileIterator(fp=self.fp)
        for tabline, data in zip(tsv, self.data.split('\n')):
            self.assertTrue(isinstance(tabline, TabLine))
            self.assertEqual(str(tabline), data)

    def test_tabfileiterator_set_column_names(self):
        """
        TabFileIterator: specify column names
        """
        # Make file-like object to read data from
        self.fp = StringIO(self.data)
        # Column names for data
        columns = ['chrom', 'start', 'end', 'p_value']
        # Iterate though data
        tsv = TabFileIterator(fp=self.fp, column_names=columns)
        for tabline, data in zip(tsv, self.data.split('\n')):
            self.assertTrue(isinstance(tabline, TabLine))
            self.assertEqual(str(tabline), data)
            # Check columns
            for col, value in zip(columns, data.split('\t')):
                self.assertEqual(str(tabline[col]), value)