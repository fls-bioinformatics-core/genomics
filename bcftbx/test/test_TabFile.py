########################################################################
# Tests for TabFile.py module
#########################################################################
from bcftbx.TabFile import *
import unittest
import cStringIO

class TestTabFile(unittest.TestCase):

    def setUp(self):
        # Header
        self.header = "#chr\tstart\tend\tdata\n"
        # Tab-delimited data
        self.data = \
"""chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
"""
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(self.header+self.data)

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_load_data(self):
        """Create and load new TabFile instance
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),[],"Header should be empty")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2][0],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.filename(),'test')

    def test_write_data(self):
        """Write data to file-like object
        """
        tabfile = TabFile('test',self.fp)
        fp = cStringIO.StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.data)
        fp.close()

    def test_load_data_with_header(self):
        """Create and load Tabfile using first line as header
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['chr','start','end','data'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_load_data_setting_explicit_header(self):
        """Create and load TabFile setting the header explicitly
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,
                          column_names=('CHROM','START','STOP','VALUES'))
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['CHROM','START','STOP','VALUES'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['CHROM'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_lookup(self):
        """Look up data from a TabFile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Look for lines with 'chr1' in the chr column
        matching = tabfile.lookup('chr','chr1')
        self.assertEqual(len(matching),2)
        for m in matching:
            self.assertEqual(m['chr'],'chr1',"Lookup returned bad match: '%s'" % m)
        self.assertNotEqual(matching[0],matching[1])
        # Look for lines with 'chr2' in the chr column
        matching = tabfile.lookup('chr','chr2')
        self.assertEqual(len(matching),1)
        self.assertEqual(matching[0]['chr'],'chr2',"Lookup returned bad match: '%s'" % m)
        # Look for lines with 'bananas' in the chr column
        self.assertEqual(len(tabfile.lookup('chr','bananas')),0)

    def test_get_index_for_line_number(self):
        """Look up line numbers from a TabFile
        """
        tabfile = TabFile('test',self.fp)
        # Look for an existing line
        self.assertEqual(tabfile.indexByLineNumber(2),0)
        self.assertEqual(tabfile[tabfile.indexByLineNumber(2)].lineno(),2)
        # Look for the first line in the file (the commented header)
        self.assertRaises(IndexError,tabfile.indexByLineNumber,1)
        # Look for a generally non-existant line number
        self.assertRaises(IndexError,tabfile.indexByLineNumber,-12)
        # Look for a negative line number
        self.assertRaises(IndexError,tabfile.indexByLineNumber,99)

    def test_append_empty_line(self):
        """Append a blank line to a TabFile
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.append()
        self.assertEqual(len(tabfile),4)
        # Check new line is empty
        for i in range(len(line)):
            self.assertTrue(str(line[i]) == '')

    def test_append_line_with_data(self):
        """Append line to a TabFile populated with data
        """
        data = ['chr1',678,901,6.1]
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.append(data=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        for i in range(len(data)):
            self.assertTrue(line[i] == data[i])

    def test_append_line_with_tab_data(self):
        """Append line to a TabFile populated from tabbed data
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.append(tabdata=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        self.assertTrue(str(line) == data)

    def test_append_tab_data_line(self):
        """Append a TabDataLine to a TabFile
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        tabdataline = TabDataLine('chr1\t10000\t20000\t+')
        line = tabfile.append(tabdataline=tabdataline)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        self.assertTrue(line is tabdataline)

    def test_insert_empty_line(self):
        """Insert a blank line into a TabFile
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2)
        self.assertEqual(len(tabfile),4)
        # Check new line is empty
        for i in range(len(line)):
            self.assertTrue(str(line[i]) == '')

    def test_insert_line_with_data(self):
        """Insert line into a TabFile populated with data
        """
        data = ['chr1',678,901,6.1]
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2,data=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        for i in range(len(data)):
            self.assertTrue(line[i] == data[i])

    def test_insert_line_with_tab_data(self):
        """Insert line into a TabFile populated from tabbed data
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        line = tabfile.insert(2,tabdata=data)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        self.assertTrue(str(line) == data)

    def test_insert_tab_data_line(self):
        """Insert a TabDataLine into a TabFile
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),3)
        tabdataline = TabDataLine('chr1\t10000\t20000\t+')
        line = tabfile.insert(2,tabdataline=tabdataline)
        self.assertEqual(len(tabfile),4)
        # Check new line is correct
        self.assertTrue(line is tabdataline)

    def test_append_column(self):
        """Append new column to a Tabfile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile.header()),4)
        tabfile.appendColumn('new')
        self.assertEqual(len(tabfile.header()),5)
        self.assertEqual(tabfile.header()[4],'new')
        self.assertEqual(tabfile[0]['new'],'')

class TestWhiteSpaceHandlingTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""chr1\t1\t234\t4.6\tA comment
chr1\t567\t890\t5.7\tComment with a trailing space 
chr2\t1234\t5678\t6.8\t.
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_preserve_trailing_spaces_on_lines(self):
        """Check that trailing spaces aren't lost
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(tabfile[0][4],"A comment")
        self.assertEqual(tabfile[1][4],"Comment with a trailing space ")
        self.assertEqual(tabfile[2][4],".")

class TestUncommentedHeaderTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_expected_uncommented_header(self):
        """Test reading in a tab file with an expected uncommented header
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['chr','start','end','data'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1\t1\t234\t4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_unexpected_uncommented_header(self):
        """Test reading in a tab file with an unexpected uncommented header
        """
        tabfile = TabFile('test',self.fp)
        self.assertEqual(len(tabfile),4,"Input has 4 lines of data")
        self.assertEqual(tabfile.header(),[],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr\tstart\tend\tdata","Incorrect string representation")
        self.assertRaises(KeyError,tabfile[3].__getitem__,'chr')
        self.assertEqual(tabfile.nColumns(),4)

class TestEmptyTabFile(unittest.TestCase):

    def test_make_empty_tabfile(self):
        """Test creating an empty TabFile with no associated file
        """
        tabfile = TabFile()
        self.assertEqual(len(tabfile),0,"new TabFile should have zero length")

    def test_add_data_to_new_tabfile(self):
        """Test adding data as a list of items to a new empty TabFile
        """
        data = ['chr1',10000,20000,'+']
        tabfile = TabFile()
        tabfile.append(data=data)
        self.assertEqual(len(tabfile),1,"TabFile should now have one line")
        for i in range(len(data)):
            self.assertEqual(tabfile[0][i],data[i])

    def test_add_tab_data_to_new_tabfile(self):
        """Test adding data as a tab-delimited line to a new empty TabFile
        """
        data = 'chr1\t10000\t20000\t+'
        tabfile = TabFile()
        tabfile.append(tabdata=data)
        self.assertEqual(len(tabfile),1,"TabFile should now have one line")
        self.assertEqual(str(tabfile[0]),data)

class TestTabFileDelimiters(unittest.TestCase):
    """Test behaviour of different field delimiters
    """

    def setUp(self):
        # Header
        self.header = "#chr\tstart\tend\tdata\n"
        # Tab-delimited data
        self.data = \
"""chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
"""
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(self.header.replace('\t',',')+
                                     self.data.replace('\t',','))

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_load_data(self):
        """Create and load new TabFile instance
        """
        tabfile = TabFile('test',self.fp,delimiter=',')
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),[],"Header should be empty")
        self.assertEqual(str(tabfile[0]),"chr1,1,234,4.6","Incorrect string representation")
        self.assertEqual(tabfile[2][0],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.filename(),'test')

    def test_write_data(self):
        """Write data to file-like object
        """
        tabfile = TabFile('test',self.fp)
        fp = cStringIO.StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.data.replace('\t',','))
        fp.close()

    def test_load_data_with_header(self):
        """Create and load Tabfile using first line as header
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,delimiter=',')
        self.assertEqual(len(tabfile),3,"Input has 3 lines of data")
        self.assertEqual(tabfile.header(),['chr','start','end','data'],"Wrong header")
        self.assertEqual(str(tabfile[0]),"chr1,1,234,4.6","Incorrect string representation")
        self.assertEqual(tabfile[2]['chr'],'chr2',"Incorrect data")
        self.assertEqual(tabfile.nColumns(),4)

    def test_write_data_with_header(self):
        """Write data to file-like object including a header line
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,delimiter=',')
        fp = cStringIO.StringIO()
        tabfile.write(fp=fp,include_header=True)
        self.assertEqual(fp.getvalue(),self.header.replace('\t',',')+self.data.replace('\t',','))
        fp.close()

    def test_append_line(self):
        """Append a line to a file
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,delimiter=',')
        line = 'chr3,10,9,8'
        tabfile.append(tabdata=line)
        self.assertEqual(str(tabfile[-1]),line)

    def test_append_line_as_data(self):
        """Append a line to a file with data supplied as a list
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,delimiter=',')
        data = ['chr3','10','9','8']
        tabfile.append(data=data)
        self.assertEqual(str(tabfile[-1]),','.join([str(x) for x in data]))

    def test_change_delimiter_for_write(self):
        """Write data out with different delimiter to input
        """
        tabfile = TabFile('test',self.fp,delimiter=',')
        # Modified delimiter (tab)
        fp = cStringIO.StringIO()
        tabfile.write(fp=fp,delimiter='\t')
        self.assertEqual(fp.getvalue(),self.data)
        fp.close()
        # Default (should revert to comma)
        fp = cStringIO.StringIO()
        tabfile.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.data.replace('\t',','))
        fp.close()

class TestTabFileValueConversions(unittest.TestCase):
    """Test that appropriate conversions are performed on input values
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""chr\tstart\tend\tdata
chr1\t1\t4.6
chr1\t567\t5.7
chr2\t1234\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_convert_values_to_type_read_from_file(self):
        """Convert input values to appropriate types (e.g. integer) when reading from file
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        for line in tabfile:
            self.assertTrue(isinstance(line[0],str))
            self.assertTrue(isinstance(line[1],(int,long)))
            self.assertTrue(isinstance(line[2],float))

    def test_convert_values_to_str_read_from_file(self):
        """Convert all input values to strings when reading from file
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,
                          convert=False)
        for line in tabfile:
            for value in line:
                self.assertTrue(isinstance(value,str))

    def test_convert_values_to_type_append_tabdata(self):
        """Convert input values to appropriate types (e.g. integer) when appending tabdata
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.append(tabdata="chr3\t5678\t7.9")
        for line in tabfile:
            self.assertTrue(isinstance(line[0],str))
            self.assertTrue(isinstance(line[1],(int,long)))
            self.assertTrue(isinstance(line[2],float))

    def test_convert_values_to_str_append_tabdata(self):
        """Convert all input values to strings when appending tabdata
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,
                          convert=False)
        tabfile.append(tabdata="chr3\t5678\t7.9")
        for line in tabfile:
            for value in line:
                self.assertTrue(isinstance(value,str))

    def test_convert_values_to_type_append_list(self):
        """Convert input values to appropriate types (e.g. integer) when appending a list
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.append(data=["chr3","5678","7.9"])
        tabfile.append(data=["chr3",5678,7.9])
        for line in tabfile:
            self.assertTrue(isinstance(line[0],str))
            self.assertTrue(isinstance(line[1],(int,long)))
            self.assertTrue(isinstance(line[2],float))

    def test_convert_values_to_str_append_list(self):
        """Convert all input values to strings when appending a list
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True,
                          convert=False)
        tabfile.append(data=["chr3","5678","7.9"])
        tabfile.append(data=["chr3",5678,7.9])
        for line in tabfile:
            for value in line:
                self.assertTrue(isinstance(value,str))

class TestBadTabFile(unittest.TestCase):
    """Test with 'bad' input files
    """

    def setUp(self):
        # Make file-like object with "bad" data 
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234
chr1\t567\t890\t5.7\t4.6
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()
    
    def test_ragged_input_file(self):
        """Deal with mismatched numbers of items on different lines
        """
        self.assertRaises(IndexError,TabFile,'test',self.fp,first_line_is_header=True)
    
    def test_ragged_input_file_no_header(self):
        """Deal with mismatched numbers of items on different lines
        """
        self.assertRaises(IndexError,TabFile,'test',self.fp)

class TestReorderTabFile(unittest.TestCase):
    """Test reordering of columns in TabFiles
    """
    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def test_reorder_columns(self):
        """Reorder columns in a TabFile
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Reorder
        new_columns = ['chr','data','start','end']
        tabfile = tabfile.reorderColumns(new_columns)
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),new_columns)
        self.assertEqual(str(tabfile[0]),"chr1\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]),"chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]),"chr2\t6.8\t1234\t5678")

    def test_reorder_columns_empty_cells(self):
        """Reorder columns where some lines have empty cells at the start
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Reset some cells to empty
        tabfile[0]['chr'] = ''
        tabfile[2]['chr'] = ''
        # Reorder
        new_columns = ['chr','data','start','end']
        tabfile = tabfile.reorderColumns(new_columns)
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),new_columns)
        self.assertEqual(str(tabfile[0]),"\t4.6\t1\t234")
        self.assertEqual(str(tabfile[1]),"chr1\t5.7\t567\t890")
        self.assertEqual(str(tabfile[2]),"\t6.8\t1234\t5678")

class TestTransposeTabFile(unittest.TestCase):
    """Test transposing the contents of a TabFile
    """
    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_transpose_tab_file(self):
        """Test transposing TabFile
        """
        tabfile1 = TabFile('test',self.fp,first_line_is_header=False)
        tabfile2 = tabfile1.transpose()
        self.assertEqual(len(tabfile1),tabfile2.nColumns())
        self.assertEqual(len(tabfile2),tabfile1.nColumns())

class TestWholeColumnOperations(unittest.TestCase):
    """Test the transformColumn and computeColumn methods
    """

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t1\t234\t4.6
chr1\t567\t890\t5.7
chr2\t1234\t5678\t6.8
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_set_column_to_constant_value(self):
        """Set a column to a constant value using transformColumn
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Add a strand column
        tabfile.appendColumn('strand')
        self.assertEqual(tabfile.nColumns(),5)
        self.assertEqual(tabfile.header(),['chr','start','end','data','strand'])
        # Set all values to '+'
        tabfile.transformColumn('strand',lambda x: '+')
        for line in tabfile:
            self.assertEqual(line['strand'],'+')

    def test_apply_operation_to_column(self):
        """Divide values in a column by 10
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Divide data column by 10
        tabfile.transformColumn('data',lambda x: x/10)
        results = [0.46,0.57,0.68]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],results[i])

    def test_compute_midpoint(self):
        """Compute the midpoint of the start and end columns
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Compute midpoint of start and end
        tabfile.computeColumn('midpoint',lambda line: (line['end'] + line['start'])/2.0)
        self.assertEqual(tabfile.nColumns(),5)
        self.assertEqual(tabfile.header(),['chr','start','end','data','midpoint'])
        results = [117.5,728.5,3456]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['midpoint'],results[i])
        
    def test_compute_and_overwrite_existing_column(self):
        """Compute new values for an existing column
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Compute new values for data column
        tabfile.computeColumn('data',lambda line: line['end'] - line['start'])
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        results = [233,323,4444]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],results[i])
        
    def test_compute_and_overwrite_existing_column_integer_index(self):
        """Compute new values for an existing column referenced using integer index
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        # Check number of columns and header items
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        # Compute new values for data column
        tabfile.computeColumn(3,lambda line: line['end'] - line['start'])
        self.assertEqual(tabfile.nColumns(),4)
        self.assertEqual(tabfile.header(),['chr','start','end','data'])
        results = [233,323,4444]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],results[i])

class TestSortTabFile(unittest.TestCase):

    def setUp(self):
        # Make file-like object to read data in
        self.fp = cStringIO.StringIO(
"""#chr\tstart\tend\tdata
chr1\t567\t890\t5.7
chr1\t1\t234\t6.8
chr2\t1234\t5678\t3.4
""")

    def tearDown(self):
        # Close the open file-like input
        self.fp.close()

    def test_sort_on_column(self):
        """Sort data on a numerical column into (default) ascending order
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.sort(lambda line: line['data'])
        sorted_data = [3.4,5.7,6.8]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],sorted_data[i])

    def test_reverse_sort_on_column(self):
        """Sort data on a numerical column into (reverse) descending order
        """
        tabfile = TabFile('test',self.fp,first_line_is_header=True)
        tabfile.sort(lambda line: line['data'],reverse=True)
        sorted_data = [6.8,5.7,3.4]
        for i in range(len(tabfile)):
            self.assertEqual(tabfile[i]['data'],sorted_data[i])
        
class TestTabDataLine(unittest.TestCase):

    def test_new_line_no_data(self):
        """Create new data line with no data
        """
        line = TabDataLine()
        self.assertEqual(len(line),0,"Line should have zero length")
        self.assertEqual(str(line),"","String representation should be empty string")
        self.assertEqual(line.lineno(),None,"Line number should not be set")

    def test_new_line_header_no_data(self):
        """Create new data line with header but no data
        """
        line = TabDataLine(column_names=('one','two','three','four'))
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),"\t\t\t","String representation should be 3 tabs")
        self.assertEqual(line.lineno(),None,"Line number should not be set")

    def test_new_line_data_no_header(self):
        """Create new data line with data but no header
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data)

    def test_new_line_no_header_empty_items(self):
        """Create new data line with no header and a line with empty items
        """
        input_data = "\t\t\t"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should match input")

    def test_new_line_no_header_leading_empty_item(self):
        """Create new data line with no header and a line with a leading empty item
        """
        input_data = "\t1.2\t3.4\t5.6"
        line = TabDataLine(line=input_data)
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should match input")

    def test_get_and_set_data(self):
        """Create new data line and do get and set operations
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        self.assertEqual(len(line),4,"Line should have 4 items")
        self.assertEqual(str(line),input_data,"String representation should be same as input")
        # Test getting
        self.assertEqual(line[1],2.2,"Column 2 data is incorrect")
        self.assertEqual(line["two"],2.2,"Column 2 data is incorrect")
        # Test setting
        line["two"] = 4.4
        self.assertEqual(line[1],4.4,"Column 2 data is incorrect after set operation")
        self.assertEqual(line["two"],4.4,"Column 2 data is incorrect after set operation")
        
    def test_subsetting(self):
        """Create new data line and retrieve subset
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three","four")
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Check key lookup still works
        self.assertEqual(subset["three"],3.3)

    def test_subsetting_no_header(self):
        """Create new data line with no header and retrieve subset
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Check key lookup
        self.assertEqual(subset[2],3.3)

    def test_subsetting_leading_empty_items(self):
        """Create new data line with a leading empty items and retrieve subset
        """
        input_data = "\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data,column_names=('one','two','three','four'))
        # Subset with integer indices
        subset = line.subset(2,3)
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")
        # Subset with keys
        subset = line.subset("three","four")
        self.assertEqual(len(subset),2,"Subset should have 2 items")
        self.assertEqual(str(subset),"3.3\t4.4","String representation should be last two columns")

    def test_line_number(self):
        """Create new data line with line number
        """
        line = TabDataLine(line="test",lineno=3)
        self.assertEqual(line.lineno(),3,"Line number should be three")

    def test_invalid_line_numbers(self):
        """Attempt to create new data lines with invalid line numbers
        """
        self.assertRaises(ValueError,TabDataLine,lineno=-3)
        self.assertRaises(ValueError,TabDataLine,lineno="three")

    def test_iteration_over_items(self):
        """Iterate over the data items in a data line
        """
        input_data = "1.1\t2.2\t3.3\t4.4"
        line = TabDataLine(line=input_data)
        try:
            # This should work
            for item in line:
                pass
        except Exception as ex:
            # It hasn't worked
            self.fail("Iteration test exception: '%s'" % ex)

    def test_preserve_trailing_spaces_in_data_items(self):
        """Check that trailing spaces aren't lost from data items
        """
        input_data = "1.1\t2.2\tThis has trailing space "
        line = TabDataLine(line=input_data)
        self.assertEqual(line[2],"This has trailing space ")

class TestTabDataLineTypeConversion(unittest.TestCase):

    def test_convert_integers(self):
        """Load string data which should be converted to integers
        """
        test_values = [12,34,56]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabDataLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_floats(self):
        """Load string data which should be converted to floats
        """
        test_values = [1.2,3.4,5.6]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabDataLine(line=input_data)
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_append_items(self):
        """Append items as strings and check type conversions
        """
        test_values = ['chr1',2,3.4]
        line = TabDataLine()
        for value in test_values:
            line.append(str(value))
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_set_items(self):
        """Set items as strings and check type conversions
        """
        test_values = ['chr1',2,3.4]
        line = TabDataLine(line="x\ty\tz")
        for i in range(len(test_values)):
            line[i] = str(test_values[i])
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

    def test_convert_preserve_objects(self):
        """Set item to object and check its type is preserved
        """
        test_values = ['chr1',{'this': 'is a dictionary'}]
        line = TabDataLine()
        for value in test_values:
            line.append(value)
        for i in range(len(test_values)):
            self.assertEqual(line[i],test_values[i])

class TestTabDataLineNoTypeConversion(unittest.TestCase):

    def test_no_type_conversion(self):
        """Load data which should not be converted to integers etc
        """
        test_values = ['hello',12,34.56]
        input_data = '\t'.join([str(x) for x in test_values])
        line = TabDataLine(line=input_data,convert=False)
        for i in range(len(test_values)):
            self.assertEqual(line[i],str(test_values[i]))

    

class TestTabDataLineDelimiters(unittest.TestCase):

    def test_default_delimiters(self):
        """Check that default delimiter (tab) works
        """
        input_data = [1.1,2.2,3.3,4.4]
        line = TabDataLine(line='\t'.join([str(x) for x in input_data]))
        for i in range(len(input_data)):
            self.assertEqual(input_data[i],line[i])

    def test_non_default_delimiters(self):
        """Check that non-default delimiter (comma) works
        """
        input_data = [1.1,2.2,3.3,4.4]
        line = TabDataLine(line=','.join([str(x) for x in input_data]),
                           delimiter=',')
        for i in range(len(input_data)):
            self.assertEqual(input_data[i],line[i])
        
########################################################################
# Main: test runner
#########################################################################
if __name__ == "__main__":
    # Run tests
    unittest.main()
