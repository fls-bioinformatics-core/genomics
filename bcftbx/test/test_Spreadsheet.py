#######################################################################
# Tests for Spreadsheet.py
#######################################################################
from bcftbx.Spreadsheet import *
import unittest
import tempfile

class TestWorkbook(unittest.TestCase):
    """Tests of the Workbook class
    """

    def test_make_empty_workbook(self):
        """Make a new empty workbook
        """
        wb = Workbook()
        self.assertEqual(len(wb.sheets),0,"New workbook shouldn't have any sheets")
        self.assertRaises(KeyError,wb.getSheet,"Nonexistant sheet")

    def test_make_workbook_add_sheets(self):
        """Make a new empty workbook and add sheets to it
        """
        wb = Workbook()
        ws1 = wb.addSheet("sheet 1")
        self.assertTrue(isinstance(ws1,Worksheet),"addSheet should return a Worksheet instance")
        self.assertEqual(len(wb.sheets),1,"Workbook should have one sheet")
        ws2 = wb.addSheet("sheet 2")
        self.assertTrue(isinstance(ws2,Worksheet),"addSheet should return a Worksheet instance")
        self.assertEqual(len(wb.sheets),2,"Workbook should have two sheets")

    def test_make_workbook_get_sheets(self):
        """Make a new empty workbook and add and retrieve sheets
        """
        wb = Workbook()
        ws1 = wb.addSheet("sheet 1")
        self.assertEqual(ws1,wb.getSheet("sheet 1"),"Didn't fetch expected worksheet #1")
        ws2 = wb.addSheet("sheet 2")
        self.assertEqual(ws2,wb.getSheet("sheet 2"),"Didn't fetch expected worksheet #2")
        self.assertNotEqual(ws1,ws2,"Worksheets should be different")

class TestWorksheet(unittest.TestCase):
    """Tests of the Worksheet class
    """

    def setUp(self):
        """Set up common to all tests in this class
        """
        self.wb = Workbook()

    def test_too_long_title(self):
        """Try to create a worksheet with a title exceeding xlwt length limit
        """
        long_title = "This is a very long title indeed for a worksheet"
        trunc_title = long_title[0:MAX_LEN_WORKSHEET_TITLE]
        ws = self.wb.addSheet(long_title)
        self.assertEqual(ws.title,trunc_title)

    def test_add_tab_data(self):
        """Add data to the sheet as tab delimited rows
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        data = ["1\t2\t3","4\t5\t6"]
        ws.addTabData(data)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        for i in range(2):
            self.assertEqual(data[i],ws.data[i])

    def test_add_text(self):
        """Add data to the sheet as tab delimited text
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        data = ["1\t2\t3","4\t5\t6"]
        text = '\n'.join(data)
        ws.addText(text)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        for i in range(2):
            self.assertEqual(data[i],ws.data[i])

    def test_set_cell_value(self):
        """Set the value of a cell in a populated sheet
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        data = ["1\t2\t3","4\t5\t6"]
        ws.addTabData(data)
        ws.setCellValue(0,1,'7')
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        new_data = ["1\t7\t3","4\t5\t6"]
        for i in range(2):
            self.assertEqual(new_data[i],ws.data[i])

    def test_set_cell_value_in_empty_sheet(self):
        """Set the value of a cell in an empty sheet
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        ws.setCellValue(2,1,'7')
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,2)
        new_data = ["","","\t7"]
        for i in range(1):
            self.assertEqual(new_data[i],ws.data[i])

    def test_get_column_id_from_index(self):
        """Check column id ('A','B',...,'AB' etc) for index
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(ws.column_id_from_index(0),'A')
        self.assertEqual(ws.column_id_from_index(25),'Z')
        self.assertEqual(ws.column_id_from_index(26),'AA')
        self.assertEqual(ws.column_id_from_index(27),'AB')
        self.assertEqual(ws.column_id_from_index(32),'AG')

class TestWorksheetInsertColumn(unittest.TestCase):
    """Tests specifically for inserting columns of data
    """

    def setUp(self):
        """Set up common to all tests in this class
        """
        self.wb = Workbook()

    def test_insert_first_column_into_empty_sheet(self):
        """Insert a column of data as first column in a blank sheet (no title)
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        column = ['1','2','3']
        ws.insertColumn(0,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,1)
        for i in range(len(column)):
            self.assertEqual(str(column[i]),ws.data[i])

    def test_insert_second_column_into_empty_sheet(self):
        """Insert a column of data as second column in a blank sheet
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        column = ['1','2','3']
        ws.insertColumn(1,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,2)
        for i in range(len(column)):
            self.assertEqual("\t"+str(column[i]),ws.data[i])

    def test_insert_column_into_sheet_with_data(self):
        """Insert a column of data into a sheet with data
        """
        ws = self.wb.addSheet("test sheet")
        data = ["1\t2\t3","4\t5\t6"]
        ws.addTabData(data)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        column = ['1','2','3']
        ws.insertColumn(1,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,4)
        new_data = ["1\t1\t2\t3","4\t2\t5\t6","\t3"]
        for i in range(len(new_data)):
            self.assertEqual(new_data[i],ws.data[i])

    def test_insert_column_into_sheet_with_data_single_value(self):
        """Insert a single value as a column into a sheet with data
        """
        ws = self.wb.addSheet("test sheet")
        data = ["1\t2\t3","4\t5\t6"]
        ws.addTabData(data)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        value = '7'
        ws.insertColumn(1,insert_items=value)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,4)
        new_data = ["1\t7\t2\t3","4\t7\t5\t6"]
        for i in range(len(new_data)):
            self.assertEqual(new_data[i],ws.data[i])

    def test_insert_titled_column_into_empty_sheet(self):
        """Insert a column of data with a title into an empty sheet
        """
        ws = self.wb.addSheet("test sheet")
        self.assertEqual(len(ws.data),0)
        self.assertEqual(ws.ncols,0)
        title = 'hello'
        column = ['1','2']
        ws.insertColumn(1,title=title,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,2)
        new_data = ["\thello","\t1","\t2"]
        for i in range(len(new_data)):
            self.assertEqual(new_data[i],ws.data[i])

    def test_insert_titled_column_into_sheet_with_data(self):
        """Insert a column of data with a title into a sheet with data
        """
        ws = self.wb.addSheet("test sheet")
        data = ["1\t2\t3","4\t5\t6","7\t8\t9"]
        ws.addTabData(data)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,3)
        title = 'hello'
        column = ['1','2']
        ws.insertColumn(1,title=title,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,4)
        new_data = ["1\thello\t2\t3","4\t1\t5\t6","7\t2\t8\t9"]
        for i in range(len(new_data)):
            self.assertEqual(new_data[i],ws.data[i])

    def test_insert_long_titled_column_into_sheet_with_data(self):
        """Insert a column of data with a title into a sheet with fewer rows of data
        """
        ws = self.wb.addSheet("test sheet")
        data = ["1\t2\t3","4\t5\t6"]
        ws.addTabData(data)
        self.assertEqual(len(ws.data),2)
        self.assertEqual(ws.ncols,3)
        title = 'hello'
        column = ['1','2']
        ws.insertColumn(1,title=title,insert_items=column)
        self.assertEqual(len(ws.data),3)
        self.assertEqual(ws.ncols,4)
        new_data = ["1\thello\t2\t3","4\t1\t5\t6","\t2"]
        for i in range(len(new_data)):
            self.assertEqual(new_data[i],ws.data[i])

class TestWorkbookSave(unittest.TestCase):
    """Test saving the workbook to disk
    """

    def setUp(self):
        """Set up common to all tests in this class
        """
        self.wb = Workbook()
        # Make a temporary file name
        self.xls = tempfile.mkstemp(suffix=".xls")
        os.close(self.xls[0])
        self.xls = self.xls[1]

    def tearDown(self):
        """Do clean up after tests
        """
        if os.path.exists(self.xls): os.remove(self.xls)

    def test_basic_write(self):
        """Create and write a simple one-sheet spreadsheet
        """
        ws = self.wb.addSheet("test sheet")
        ws.addText("This is a\ttest")
        self.wb.save(self.xls)
        self.assertTrue(os.path.exists(self.xls))
        # Open the file with xlrd and check it contains what we expect
        rb = xlrd.open_workbook(self.xls)
        self.assertEqual(len(rb.sheets()),1)
        s = rb.sheets()[0]
        self.assertEqual(s.name,"test sheet")
        self.assertEqual(s.nrows,1)
        self.assertEqual(s.ncols,2)
        self.assertEqual(s.cell(0,0).value,"This is a")
        self.assertEqual(s.cell(0,1).value,"test")

    def test_basic_write_with_formula(self):
        """Create and write a simple one-sheet spreadsheet including a formula
        """
        ws = self.wb.addSheet("test sheet")
        ws.addText("Test\t1\t2\t=B?+C?")
        self.wb.save(self.xls)
        self.assertTrue(os.path.exists(self.xls))
        # Open the file with xlrd and check it contains what we expect
        rb = xlrd.open_workbook(self.xls)
        self.assertEqual(len(rb.sheets()),1)
        s = rb.sheets()[0]
        self.assertEqual(s.name,"test sheet")
        self.assertEqual(s.nrows,1)
        self.assertEqual(s.ncols,4)

    def test_too_long_cell_value(self):
        """Insert a data item into a worksheet which exceeds the xlwt length limit
        """
        long_value = "This is a very very very very very very very very very very very very very very very very very very long long long long looooooooong loooooooooooooooooooooooong loooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooong string value to put into a cell"
        ws = self.wb.addSheet("test sheet")
        ws.addText(long_value)
        self.wb.save(self.xls)
        self.assertTrue(os.path.exists(self.xls))
        # Open the file with xlrd and check it contains what we expect
        rb = xlrd.open_workbook(self.xls)
        self.assertEqual(len(rb.sheets()),1)
        s = rb.sheets()[0]
        self.assertEqual(s.name,"test sheet")
        self.assertEqual(s.nrows,1)
        self.assertEqual(s.ncols,1)
        self.assertEqual(s.cell(0,0).value,long_value[:MAX_LEN_WORKSHEET_CELL_VALUE])

    def test_too_many_rows(self):
        """Insert one more row into a worksheet than xlwt can handle
        """
        n_rows = MAX_NUMBER_ROWS_PER_WORKSHEET + 1
        data = []
        ws = self.wb.addSheet("test sheet")
        for i in range(n_rows):
            data.append("value")
        ws.addText('\n'.join(data))
        self.wb.save(self.xls)
        self.assertTrue(os.path.exists(self.xls))
        # Open the file with xlrd and check it contains what we expect
        rb = xlrd.open_workbook(self.xls)
        self.assertEqual(len(rb.sheets()),1)
        s = rb.sheets()[0]
        self.assertEqual(s.name,"test sheet")
        self.assertEqual(s.nrows,MAX_NUMBER_ROWS_PER_WORKSHEET)
        self.assertEqual(s.ncols,1)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()
