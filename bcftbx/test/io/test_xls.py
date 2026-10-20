#######################################################################
# Tests for io.xls.py module
#######################################################################


import unittest
import os
import tempfile
from bcftbx.io.xls import XLSWorkBook, XLSException
from bcftbx.io.xls import XLSWorkSheet
from bcftbx.io.xls import XLSStyle
from bcftbx.io.xls import NumberFormats
from bcftbx.io.xls import CellIndex
from bcftbx.io.xls import ColumnRange
from bcftbx.io.xls import column_integer_to_index
from bcftbx.io.xls import column_index_to_integer
from bcftbx.io.xls import incr_col
from bcftbx.io.xls import cmp_column_indices
from bcftbx.io.xls import eval_formula
from bcftbx.io.xls import format_value
from bcftbx.io.xls import BAD_REF


class TestXLSWorkBook(unittest.TestCase):
    """
    Tests for the XLSWorkBook class.
    """
    def setUp(self):
        # Store temp area, if needed
        self.wd = None

    def tearDown(self):
        # Remove working area, if defined
        if self.wd is not None and os.path.isdir(self.wd):
            try:
                os.rmdir(self.wd)
            except Exception:
                pass

    def _add_test_worksheet(self,ws):
        # Add content to example worksheet
        ws['A1'] = "Arbitrary text"
        # Formula
        ws['A3'] = "Formula example:"
        ws['A5'] = 2
        ws['B5'] = 5
        ws['A6'] = "Sum"
        ws['B6'] = "=A5+B5"
        # Set styles on formula
        ws.set_style(XLSStyle(bold=True),'A6')
        ws.set_style(XLSStyle(bold=True),'B6')
        # More style examples
        ws['A9'] = "Bold"
        ws.set_style(XLSStyle(bold=True),'A9')
        ws['A10'] = "Red"
        ws.set_style(XLSStyle(color='red'),'A10')
        ws['A11'] = "White on green"
        ws.set_style(XLSStyle(bold=True,color='white',bgcolor='green'),'A11')

    def test_work_book_add_worksheet(self):
        """
        XLSWorkBook: add a worksheet
        """
        wb = XLSWorkBook("Test")
        ws1 = wb.add_work_sheet('wsheet1','Test #1')
        self.assertEqual(ws1,wb.worksheet['wsheet1'])
        self.assertEqual(ws1.title,'Test #1')

    def test_work_book_add_worksheet(self):
        """
        XLSWorkBook: add a worksheet with a long title
        """
        wb = XLSWorkBook("Test")
        ws1 = wb.add_work_sheet('wsheet1','This title is excessively long for wsheet1')
        self.assertEqual(ws1,wb.worksheet['wsheet1'])
        self.assertEqual(ws1.title,'This title is excessively long ')

    def test_work_book_save(self):
        """
        XLSWorkBook: save as an xlsx file
        """
        wb = XLSWorkBook("Test")
        self.wd = tempfile.mkdtemp()
        # Add content
        ws = wb.add_work_sheet('test','Test')
        self._add_test_worksheet(ws)
        # Save out to XLS(X) files
        xlsx_out = os.path.join(self.wd,'test.xlsx')
        wb.save(xlsx_out)
        # Check file exists
        self.assertTrue(os.path.isfile(xlsx_out))

class TestXLSWorkSheet(unittest.TestCase):
    """
    Tests for the XLSWorkSheet class.
    """
    def setUp(self):
        self.ws = XLSWorkSheet('Test Worksheet')

    def test_work_sheet(self):
        """
        XLSWorkSheet: check work sheet properties
        """
        ws = self.ws
        self.assertEqual(ws.title,'Test Worksheet')
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,1)

    def test_work_sheet_truncate_long_title(self):
        """
        XLSWorkSheet: truncate long title
        """
        short_title = "Short"
        ws = XLSWorkSheet(short_title)
        self.assertEqual(ws.title,short_title)
        long_title = "This is a very very very very very very long title"
        self.assertRaises(XLSException,
                          XLSWorkSheet,
                          long_title)

    def test_insert_single_items(self):
        """
        XLSWorkSheet: insert single items
        """
        ws = self.ws
        self.assertEqual(ws['A1'],None)
        self.assertEqual(ws['AB2'],None)
        ws['A1'] = 'Some data'
        self.assertEqual(ws['A1'],'Some data')
        self.assertEqual(ws['A']['1'],'Some data')
        ws['A1'] = 'Updated data'
        self.assertEqual(ws['A1'],'Updated data')
        ws['A']['1'] = 'Updated again'
        self.assertEqual(ws['A']['1'],'Updated again')

    def test_del_single_item(self):
        """
        XLSWorkSheet: delete single item
        """
        ws = self.ws
        self.assertEqual(ws['B4'],None)
        ws['B4'] = 'Some data'
        self.assertEqual(ws['B4'],'Some data')
        del(ws['B4'])
        self.assertEqual(ws['B4'],None)

    def test_last_column_and_row(self):
        """
        XLSWorkSheet: check last column & row
        """
        ws = self.ws
        ws['A1'] = 'Some data'
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,1)
        ws['A4'] = 'More data'
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,4)
        ws['D2'] = 'Even more data'
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)
        ws['E11'] = 'More data again'
        self.assertEqual(ws.last_column,'E')
        self.assertEqual(ws.last_row,11)
        del(ws['E11'])
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)

    def test_column_is_empty(self):
        """
        XLSWorkSheet: identify when column is empty
        """
        ws = self.ws
        self.assertTrue(ws.column_is_empty('A'))
        self.assertTrue(ws.column_is_empty('D'))
        ws['A1'] = 'Some data'
        self.assertFalse(ws.column_is_empty('A'))
        self.assertTrue(ws.column_is_empty('D'))
        ws['D3'] = 'More data'
        self.assertFalse(ws.column_is_empty('A'))
        self.assertFalse(ws.column_is_empty('D'))

    def test_row_is_empty(self):
        """
        XLSWorkSheet: identify when row is empty
        """
        ws = self.ws
        self.assertTrue(ws.row_is_empty(1))
        self.assertTrue(ws.row_is_empty(3))
        ws['A1'] = 'Some data'
        self.assertFalse(ws.row_is_empty(1))
        self.assertTrue(ws.row_is_empty(3))
        ws['D3'] = 'More data'
        self.assertFalse(ws.row_is_empty(1))
        self.assertFalse(ws.row_is_empty(3))

    def test_columnof(self):
        """
        XLSWorkSheet: fetch column index for title
        """
        ws = self.ws
        ws.write_row(1,('hello','goodbye','whatev'))
        self.assertEqual(ws.columnof('hello'),'A')
        self.assertEqual(ws.columnof('goodbye'),'B')
        self.assertEqual(ws.columnof('whatev'),'C')
        self.assertRaises(LookupError,ws.columnof,'nowhere')

    def test_insert_column(self):
        """
        XLSWorkSheet: insert column
        """
        ws = self.ws
        ws.write_row(1,('hello','goodbye','whatev'))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['B1'],'goodbye')
        self.assertEqual(ws['C1'],'whatev')
        self.assertEqual(ws.last_column,'C')
        ws.insert_column('A',text='bonjour')
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['B1'],'hello')
        self.assertEqual(ws['C1'],'goodbye')
        self.assertEqual(ws['D1'],'whatev')
        ws.insert_column('C',data=('au revoir',))
        self.assertEqual(ws.last_column,'E')
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['B1'],'hello')
        self.assertEqual(ws['C1'],'au revoir')
        self.assertEqual(ws['D1'],'goodbye')
        self.assertEqual(ws['E1'],'whatev')
        ws.insert_column('H',data=('hola',))
        self.assertEqual(ws.last_column,'H')
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['B1'],'hello')
        self.assertEqual(ws['C1'],'au revoir')
        self.assertEqual(ws['D1'],'goodbye')
        self.assertEqual(ws['E1'],'whatev')
        self.assertEqual(ws['F1'],None)
        self.assertEqual(ws['G1'],None)
        self.assertEqual(ws['H1'],'hola')
        ws.insert_column('G',data=('adios',))
        self.assertEqual(ws.last_column,'I')
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['B1'],'hello')
        self.assertEqual(ws['C1'],'au revoir')
        self.assertEqual(ws['D1'],'goodbye')
        self.assertEqual(ws['E1'],'whatev')
        self.assertEqual(ws['F1'],None)
        self.assertEqual(ws['G1'],'adios')
        self.assertEqual(ws['H1'],None)
        self.assertEqual(ws['I1'],'hola')

    def test_append_column(self):
        """
        XLSWorkSheet: append column
        """
        ws = self.ws
        ws.write_row(1,('hello','goodbye','whatev'))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['B1'],'goodbye')
        self.assertEqual(ws['C1'],'whatev')
        ws.append_column(data=('au revoir',))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['B1'],'goodbye')
        self.assertEqual(ws['C1'],'whatev')
        self.assertEqual(ws['D1'],'au revoir')

    def test_populate_column_from_list(self):
        """
        XLSWorkSheet: populate column from a list
        """
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['B1','B2','B3']
        ws.write_column('B',data=col_data)
        self.assertEqual(ws.last_column,'B')
        self.assertEqual(ws.last_row,3)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['C3','C4','C5']
        ws.write_column('C',data=col_data,from_row=3)
        self.assertEqual(ws.last_column,'C')
        self.assertEqual(ws.last_row,5)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])

    def test_populate_column_from_tab_delimited_text(self):
        """
        XLSWorkSheet: populate column from tab delimited text
        """
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['A1','A2','A3']
        ws.write_column('A',text="hello\ngoodbye\nwhatev")
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,3)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['M7','M8','M9']
        ws.write_column('M',text="hello\ngoodbye\nwhatev",
                        from_row=7)
        self.assertEqual(ws.last_column,'M')
        self.assertEqual(ws.last_row,9)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])

    def test_write_fill_column_with_value(self):
        """
        XLSWorkSheet: fill column with a value
        """
        ws = self.ws
        # Add some data first, then fill
        ws.write_column('A',data=['some','random','items'])
        ws.write_column('L',fill="50")
        self.assertEqual(ws.last_column,'L')
        self.assertEqual(ws.last_row,3)
        for idx in ('L1','L2','L3'):
            self.assertEqual(ws[idx],"50")
        ws.write_column('M',fill="50",from_row=2)
        self.assertEqual(ws.last_column,'M')
        self.assertEqual(ws.last_row,3)
        self.assertEqual(ws['M1'],None)
        for idx in ('M2','M3'):
            self.assertEqual(ws[idx],"50")

    def test_fill_column_empty_worksheet(self):
        """
        XLSWorkSheet: fill a column with values in an empty worksheet
        """
        ws = self.ws
        # Empty spreadsheet, no fill
        ws.write_column('L',fill="50")
        self.assertEqual(ws['L1'],None)
        ws.write_column('L',fill="50",from_row=1)
        self.assertEqual(ws['L1'],None)
        ##ws.write_column('L',fill="50",end=3)
        ##self.assertEqual(ws['L1'],None)
        ### Can fill if both limits are given
        ##ws.write_column('L',fill="50",from_row=1,end=3)
        ##for idx in ('L1','L2','L3'):
        ##    self.assertEqual(ws[idx],"50")

    def test_insert_data_into_column(self):
        """
        XLSWorkSheet: insert data into a column
        """
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['B1','B2','B3']
        ws.write_column('B',col_data)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['C3','C4','C5']
        ws.write_column('C',col_data,from_row=3)
        for i in range(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])

    def test_insert_row(self):
        """
        XLSWorkSheet: insert row
        """
        ws = self.ws
        ws.write_column('A',('hello','goodbye','whatev'))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['A2'],'goodbye')
        self.assertEqual(ws['A3'],'whatev')
        self.assertEqual(ws.last_row,3)
        ws.insert_row(1,text='bonjour')
        self.assertEqual(ws.last_row,4)
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['A2'],'hello')
        self.assertEqual(ws['A3'],'goodbye')
        self.assertEqual(ws['A4'],'whatev')
        ws.insert_row(3,data=('au revoir',))
        self.assertEqual(ws.last_row,5)
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['A2'],'hello')
        self.assertEqual(ws['A3'],'au revoir')
        self.assertEqual(ws['A4'],'goodbye')
        self.assertEqual(ws['A5'],'whatev')
        ws.insert_row(8,data=('hola',))
        self.assertEqual(ws.last_row,8)
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['A2'],'hello')
        self.assertEqual(ws['A3'],'au revoir')
        self.assertEqual(ws['A4'],'goodbye')
        self.assertEqual(ws['A5'],'whatev')
        self.assertEqual(ws['A6'],None)
        self.assertEqual(ws['A7'],None)
        self.assertEqual(ws['A8'],'hola')
        ws.insert_row(7,data=('adios',))
        self.assertEqual(ws.last_row,9)
        self.assertEqual(ws['A1'],'bonjour')
        self.assertEqual(ws['A2'],'hello')
        self.assertEqual(ws['A3'],'au revoir')
        self.assertEqual(ws['A4'],'goodbye')
        self.assertEqual(ws['A5'],'whatev')
        self.assertEqual(ws['A6'],None)
        self.assertEqual(ws['A7'],'adios')
        self.assertEqual(ws['A8'],None)
        self.assertEqual(ws['A9'],'hola')

    def test_populate_row_with_list(self):
        """
        XLSWorkSheet: populate row with list
        """
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        exp_cell = ['A4','B4','C4','D4']
        ws.write_row(4,data=row_data)
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.write_row(5,data=row_data,from_column='E')
        self.assertEqual(ws.last_column,'H')
        self.assertEqual(ws.last_row,5)
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])

    def test_populate_row_with_tab_delimited_text(self):
        """
        XLSWorkSheet: populate row with tab delimited text
        """
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        row_text = "Dozy\tBeaky\tMick\tTitch"
        exp_cell = ['A4','B4','C4','D4']
        ws.write_row(4,text=row_text)
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.write_row(5,text=row_text,from_column='E')
        self.assertEqual(ws.last_column,'H')
        self.assertEqual(ws.last_row,5)
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])

    def test_insert_data_into_row(self):
        """
        XLSWorkSheet: insert data into row
        """
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        exp_cell = ['A4','B4','C4','D4']
        ws.write_row(4,row_data)
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.write_row(5,row_data,from_column='E')
        for i in range(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])

    def test_insert_block_data(self):
        """
        XLSWorkSheet: insert a block of data
        """
        ws = self.ws
        expected = { 'A1':'This','B1':'is','C1':None,'D1':'some',
                     'A2':None,'B2':'random','C2':None,'D2':None,
                     'A3':None,'B3':'data','C3':None,'D3':None }
        ws.insert_block_data("This\tis\t\tsome\n\trandom\n\tdata")
        for idx in expected:
            self.assertEqual(ws[idx],expected[idx])
        expected = { 'M7':'This','N7':'is','O7':None,'P7':'some',
                     'M8':None,'N8':'MORE','O8':'random','P8':None,
                     'M9':None,'N9':'data','O9':None,'P9':None }
        ws.insert_block_data("This\tis\t\tsome\n\tMORE\trandom\n\tdata",
                             col='M',row=7)

    def test_interrogating_columns_and_rows(self):
        """
        XLSWorkSheet: test interrogating columns and rows
        """
        ws = self.ws
        self.assertEqual(ws.columns,[])
        self.assertEqual(ws.rows,[])
        self.assertEqual(ws.next_column,'A')
        self.assertEqual(ws.next_row,1)
        ws['B12'] = "A value"
        self.assertEqual(ws.columns,['B'])
        self.assertEqual(ws.rows,[12])
        self.assertEqual(ws.rows,[12])
        self.assertEqual(ws.next_column,'C')
        self.assertEqual(ws.next_row,13)
        ws['F5'] = "Another value"
        self.assertEqual(ws.columns,['B','F'])
        self.assertEqual(ws.rows,[5,12])
        self.assertEqual(ws.next_column,'G')
        self.assertEqual(ws.next_row,13)
        ws['AZ93'] = "Yet another value"
        self.assertEqual(ws.columns,['B','F','AZ'])
        self.assertEqual(ws.rows,[5,12,93])
        self.assertEqual(ws.next_column,'BA')
        self.assertEqual(ws.next_row,94)

    def test_render_cell_with_static_value(self):
        """
        XLSWorkSheet: test rendering cell with a static value
        """
        self.ws.write_column(self.ws.next_column,['4.5'])
        self.assertEqual(self.ws.render_cell('A1'),'4.5')

    def test_render_cell_formula(self):
        """
        XLSWorkSheet: test rendering cell with a formula
        """
        self.ws.write_column(self.ws.next_column,['4.5','6.7','=A1+A2'])
        self.assertEqual(self.ws.render_cell('A3'),'=A1+A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'11.2')

    def test_render_cell_formula_with_column_substitution(self):
        """
        XLSWorkSheet: test rendering cell with a column substitution
        """
        self.ws.write_column(self.ws.next_column,['4.5','6.7','=#1+#2'])
        self.assertEqual(self.ws.render_cell('A3'),'=A1+A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'11.2')

    def test_render_cell_formula_with_row_substitution(self):
        """
        XLSWorkSheet: test rendering cell with a row substitution
        """
        self.ws.write_column(self.ws.next_column,['4.5'])
        self.ws.write_column(self.ws.next_column,['6.7'])
        self.ws.write_column(self.ws.next_column,['=A?+B?'])
        self.assertEqual(self.ws.render_cell('C1'),'=A1+B1')
        self.assertEqual(self.ws.render_cell('C1',eval_formulae=True),'11.2')

    def test_render_cell_formula_with_formatting(self):
        """
        XLSWorkSheet: test rendering cell with formatting
        """
        self.ws.write_column(self.ws.next_column,['1.0','2.0','=A1/A2'])
        self.ws.set_style(XLSStyle(number_format=NumberFormats.PERCENTAGE),'A3')
        self.assertEqual(self.ws.render_cell('A3'),'=A1/A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'0.5')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True,apply_format=True),
                         '50.0%')


class TestCellIndex(unittest.TestCase):
    """
    XLSWorkSheet: tests for CellIndex class
    """
    def test_cell_index(self):
        """
        XLSWorkSheet: test cell index properties
        """
        self.assertEqual(CellIndex('A1').column,'A')
        self.assertEqual(CellIndex('A1').row,1)
        self.assertEqual(CellIndex('ZB567').column,'ZB')
        self.assertEqual(CellIndex('ZB567').row,567)

    def test_cell_index_is_full(self):
        """
        XLSWorkSheet: check if cell index is fully defined
        """
        self.assertTrue(CellIndex('A1').is_full)
        self.assertTrue(CellIndex('AZ123').is_full)
        self.assertFalse(CellIndex('A').is_full)
        self.assertFalse(CellIndex('1').is_full)
        self.assertFalse(CellIndex('123').is_full)
        self.assertFalse(CellIndex('!1#2').is_full)

    def test_cell_index_repr(self):
        """
        XLSWorkSheet: test cell index repr
        """
        self.assertTrue(str(CellIndex('A1')),'A1')
        self.assertTrue(str(CellIndex('ZB567')),'ZB567')
        self.assertTrue(str(CellIndex('A')),'A')
        self.assertTrue(str(CellIndex('1')),'1')


class TestColumnIndexToInteger(unittest.TestCase):
    """
    Tests for 'column_index_to_integer' function
    """
    def test_column_index_to_integer(self):
        """
        column_index_to_integer: correct integer index returned for column
        """
        self.assertEqual(column_index_to_integer('A'),0)
        self.assertEqual(column_index_to_integer('B'),1)
        self.assertEqual(column_index_to_integer('Z'),25)
        self.assertEqual(column_index_to_integer('AA'),26)
        self.assertEqual(column_index_to_integer('AB'),27)
        self.assertEqual(column_index_to_integer('AZ'),51)


class TestColumnIntegerToIndex(unittest.TestCase):
    """
    Tests for 'column_integer_to_index' function
    """
    def test_column_integer_to_index(self):
        """
        column_integer_to_index: correct column returned for integer index
        """
        self.assertEqual(column_integer_to_index(0),'A')
        self.assertEqual(column_integer_to_index(1),'B')
        self.assertEqual(column_integer_to_index(25),'Z')
        self.assertEqual(column_integer_to_index(26),'AA')
        self.assertEqual(column_integer_to_index(27),'AB')
        self.assertEqual(column_integer_to_index(51),'AZ')


class TestIncrCol(unittest.TestCase):
    """
    Tests for 'incr_incr' function
    """
    def test_incr_col(self):
        """
        incr_incr: returns correct column name
        """
        self.assertEqual(incr_col('A'),'B')
        self.assertEqual(incr_col('C',2),'E')
        self.assertEqual(incr_col('C',-1),'B')
        self.assertEqual(incr_col('C',-2),'A')
        self.assertEqual(incr_col('Z'),'AA')
        self.assertEqual(incr_col('AA',-1),'Z')


class TestColumnRange(unittest.TestCase):
    """
    Tests for ColumnRange class
    """
    def test_column_range(self):
        """
        ColumnRange: returns correct range of columns
        """
        for expected,actual in zip(['A','B','C'],
                                   ColumnRange('A','C')):
            self.assertEqual(expected,actual)

    def test_column_range_implicit_start(self):
        """
        ColumnRange: implicit start column
        """
        for expected,actual in zip(['A','B','C'],
                                   ColumnRange('C')):
            self.assertEqual(expected,actual)

    def test_column_range_dont_include_end(self):
        """
        ColumnRange: dont include end column in range
        """
        for expected,actual in zip(['A','B','C'],
                                   ColumnRange('A','D',include_end=False)):
            self.assertEqual(expected,actual)

    def test_column_range_reverse(self):
        """
        ColumnRange: range of columns reversed
        """
        for expected,actual in zip(['C','B','A'],
                                   ColumnRange('A','C',reverse=True)):
            self.assertEqual(expected,actual)


class TestXLSStyle(unittest.TestCase):
    """
    Tests for XLSStyle class
    """
    def setUp(self):
        self.text = "Some test text"

    def test_cell_style_no_style(self):
        """
        XLSStyle: no style set
        """
        self.assertEqual(XLSStyle().style(self.text),self.text)

    def test_cell_style_bold(self):
        """
        XLSStyle: bold style
        """
        self.assertEqual(XLSStyle(bold=True).style(self.text),
                         "<style font=bold>%s</style>" % self.text)

    def test_cell_style_number_format(self):
        """
        XLSStyle: number format
        """
        self.assertEqual(XLSStyle(number_format=None).style(self.text),
                         "%s" % self.text)
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.THOUSAND_SEPARATOR).style(self.text),
                         "<style number_format=#,###>%s</style>" % self.text)
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.PERCENTAGE).style(self.text),
                         "<style number_format=0.0%%>%s</style>" % self.text)

    def test_excel_number_format(self):
        """
        XLSStyle: number format for Excel
        """
        self.assertEqual(XLSStyle(
            number_format=None).excel_number_format,
                         None)
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.THOUSAND_SEPARATOR).excel_number_format,
                         "#,###")
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.PERCENTAGE).excel_number_format,
                         "0.0%")

    def test_nonzero(self):
        """
        XLSStyle: check __nonzero__ built in
        """
        self.assertFalse(XLSStyle())
        self.assertTrue(XLSStyle(bold=True))
        self.assertTrue(XLSStyle(wrap=True))
        self.assertTrue(XLSStyle(color='red'))
        self.assertTrue(XLSStyle(bgcolor='blue'))
        self.assertTrue(XLSStyle(number_format=NumberFormats.PERCENTAGE))
        self.assertTrue(XLSStyle(border='thick'))
        self.assertTrue(XLSStyle(font_size=14))
        self.assertTrue(XLSStyle(centre=True))
        self.assertTrue(XLSStyle(shrink_to_fit=True))
        self.assertTrue(XLSStyle(bold=True,bgcolor='green'))

    def test_name(self):
        """
        XLSStyle: check 'name' property
        """
        self.assertEqual(XLSStyle().name,'')
        self.assertEqual(XLSStyle(bold=True).name,'__bold__')
        self.assertEqual(XLSStyle(color='red').name,'__color=red__')
        self.assertEqual(XLSStyle(bgcolor='blue').name,'__bgcolor=blue__')
        self.assertEqual(XLSStyle(number_format=NumberFormats.PERCENTAGE).name,
                         '__number_format=1__')
        self.assertEqual(XLSStyle(border='thick').name,'__border=thick__')
        self.assertEqual(XLSStyle(font_size=14).name,'__font_size=14__')
        self.assertEqual(XLSStyle(centre=True).name,'__centre__')
        self.assertEqual(XLSStyle(shrink_to_fit=True).name,'__shrink_to_fit__')
        self.assertEqual(XLSStyle(bold=True,bgcolor='green').name,
                         '__bold__bgcolor=green__')
        self.assertEqual(XLSStyle(bold=True,font_size=14,centre=True).name,
                         '__bold__font_size=14__centre__')


class TestCmpColumnIndices(unittest.TestCase):
    """
    Tests for the 'cmp_column_indices' function
    """
    def test_cmp_column_indices(self):
        self.assertEqual(-1,cmp_column_indices('A','B'))
        self.assertEqual(1,cmp_column_indices('B','A'))
        self.assertEqual(0,cmp_column_indices('A','A'))
        self.assertEqual(-1,cmp_column_indices('A','AZ'))
        self.assertEqual(1,cmp_column_indices('AZ','A'))
        self.assertEqual(0,cmp_column_indices('AZ','AZ'))
        self.assertEqual(-1,cmp_column_indices('ABZ','AABZ'))
        self.assertEqual(1,cmp_column_indices('AABZ','ABZ'))
        self.assertEqual(0,cmp_column_indices('AABZ','AABZ'))


class TestEvalFormula(unittest.TestCase):
    """
    Tests for the 'eval_formula' function
    """
    def setUp(self):
        ws = XLSWorkSheet('Test Worksheet')
        ws.write_column('A',['1.0','2.0','3.0'])
        ws.write_column('B',['4.0','5.0','6.0'])
        ws.write_column('C',['7.0','8.0','9.0'])
        self.ws = ws

    def test_simple_substitutions(self):
        """
        eval_formula: eveluate substitutions
        """
        self.assertEqual(eval_formula("123",self.ws),"123")
        self.assertEqual(eval_formula("123.0",self.ws),"123.0")
        self.assertEqual(eval_formula("",self.ws),"")
        self.assertEqual(eval_formula("not a number",self.ws),"not a number")
        self.assertEqual(eval_formula("=A1",self.ws),1.0)

    def test_operations(self):
        """
        eval_formula: eveluate operations
        """
        self.assertEqual(eval_formula("=A1+A2",self.ws),3.0)
        self.assertEqual(eval_formula("=A1-A2",self.ws),-1.0)
        self.assertEqual(eval_formula("=A1*A2",self.ws),2.0)
        self.assertEqual(eval_formula("=A1/A2",self.ws),0.5)

    def test_recursive_evaluation(self):
        """
        eval_formula: recursive evaluation
        """
        self.ws.write_column('D',['=C1','=C1+C2','=D1+D2'])
        self.assertEqual(eval_formula("=D1",self.ws),7.0)
        self.assertEqual(eval_formula("=D2",self.ws),15.0)
        self.assertEqual(eval_formula("=D3",self.ws),22.0)

    def test_bad_values(self):
        """
        eval_formula: handle invalid values
        """
        self.ws.write_column('D',['one','two','=D1+D2'])
        self.assertEqual(eval_formula("=D1",self.ws),'one')
        self.assertEqual(eval_formula("=D3",self.ws),BAD_REF)

    def test_simple_substitutions_with_integers(self):
        """
        eval_formula: eveluate substitutions with integers
        """
        self.ws.write_column('D',['1','2','3'])
        self.assertEqual(eval_formula("=D1",self.ws),1)
        self.assertEqual(eval_formula("=D2",self.ws),2)
        self.assertEqual(eval_formula("=D3",self.ws),3)

    def test_operations_with_integers(self):
        """
        eval_formula: eveluate operations with integers
        """
        self.ws.write_column('D',['1','2','3'])
        self.assertEqual(eval_formula("=D1+D2",self.ws),3)
        self.assertEqual(eval_formula("=D1-D2",self.ws),-1)
        self.assertEqual(eval_formula("=D1*D2",self.ws),2)
        self.assertEqual(eval_formula("=D1/D2",self.ws),0.5)

    def test_operations_mixing_integers_and_floats(self):
        """
        eval_formula: eveluate operations with integers and floats
        """
        self.ws.write_column('D',['1','2','3'])
        self.assertEqual(eval_formula("=A1+D2",self.ws),3.0)
        self.assertEqual(eval_formula("=A1-D2",self.ws),-1.0)
        self.assertEqual(eval_formula("=A1*D2",self.ws),2.0)
        self.assertEqual(eval_formula("=A1/D2",self.ws),0.5)


class TestFormatValue(unittest.TestCase):
    """
    Tests for the 'format_value' function
    """
    def test_no_format(self):
        """
        format_value: no format specified
        """
        self.assertEqual(format_value("value"),"value")

    def test_thousands_separator(self):
        """
        format_value: format with 'thousands' separator
        """
        self.assertEqual(format_value(1,NumberFormats.THOUSAND_SEPARATOR),"1")
        self.assertEqual(format_value(10,NumberFormats.THOUSAND_SEPARATOR),"10")
        self.assertEqual(format_value(100,NumberFormats.THOUSAND_SEPARATOR),"100")
        self.assertEqual(format_value(1000,NumberFormats.THOUSAND_SEPARATOR),"1,000")
        self.assertEqual(format_value(10000,NumberFormats.THOUSAND_SEPARATOR),"10,000")
        self.assertEqual(format_value(100000,NumberFormats.THOUSAND_SEPARATOR),"100,000")
        self.assertEqual(format_value(1000000,NumberFormats.THOUSAND_SEPARATOR),"1,000,000")
        self.assertEqual(format_value(12726554,NumberFormats.THOUSAND_SEPARATOR),"12,726,554")

    def test_percentage(self):
        """
        format_value: format as percentage
        """
        self.assertEqual(format_value(0.5,NumberFormats.PERCENTAGE),"50.0%")
        self.assertEqual(format_value(0.872667,NumberFormats.PERCENTAGE),"87.3%")
