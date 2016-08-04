#######################################################################
# Tests for simple_xls module
#######################################################################
from bcftbx.simple_xls import *
import unittest
import itertools

class TestXLSWorkSheet(unittest.TestCase):
    """
    """
    def setUp(self):
        self.ws = XLSWorkSheet('Test Worksheet')
    def test_work_sheet(self):
        ws = self.ws
        self.assertEqual(ws.title,'Test Worksheet')
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,1)
    def test_work_sheet_truncate_long_title(self):
        short_title = "Short"
        ws = XLSWorkSheet(short_title)
        self.assertEqual(ws.title,short_title)
        long_title = "This is a very very very very very very long title"
        ws = XLSWorkSheet(long_title)
        self.assertEqual(ws.title,long_title[0:31])
    def test_insert_single_items(self):
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
        ws = self.ws
        self.assertEqual(ws['B4'],None)
        ws['B4'] = 'Some data'
        self.assertEqual(ws['B4'],'Some data')
        del(ws['B4'])
        self.assertEqual(ws['B4'],None)
    def test_last_column_and_row(self):
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
        ws = self.ws
        ws.insert_row_data(1,('hello','goodbye','whatev'))
        self.assertEqual(ws.columnof('hello'),'A')
        self.assertEqual(ws.columnof('goodbye'),'B')
        self.assertEqual(ws.columnof('whatev'),'C')
        self.assertRaises(LookupError,ws.columnof,'nowhere')
    def test_insert_column(self):
        ws = self.ws
        ws.insert_row_data(1,('hello','goodbye','whatev'))
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
        ws = self.ws
        ws.insert_row_data(1,('hello','goodbye','whatev'))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['B1'],'goodbye')
        self.assertEqual(ws['C1'],'whatev')
        ws.append_column(data=('au revoir',))
        self.assertEqual(ws['A1'],'hello')
        self.assertEqual(ws['B1'],'goodbye')
        self.assertEqual(ws['C1'],'whatev')
        self.assertEqual(ws['D1'],'au revoir')
    def test_write_column_with_list(self):
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['B1','B2','B3']
        ws.write_column('B',data=col_data)
        self.assertEqual(ws.last_column,'B')
        self.assertEqual(ws.last_row,3)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['C3','C4','C5']
        ws.write_column('C',data=col_data,from_row=3)
        self.assertEqual(ws.last_column,'C')
        self.assertEqual(ws.last_row,5)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
    def test_write_column_with_text(self):
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['A1','A2','A3']
        ws.write_column('A',text="hello\ngoodbye\nwhatev")
        self.assertEqual(ws.last_column,'A')
        self.assertEqual(ws.last_row,3)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['M7','M8','M9']
        ws.write_column('M',text="hello\ngoodbye\nwhatev",
                        from_row=7)
        self.assertEqual(ws.last_column,'M')
        self.assertEqual(ws.last_row,9)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
    def test_write_column_with_fill(self):
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
    def test_insert_column_data(self):
        ws = self.ws
        col_data = ['hello','goodbye','whatev']
        exp_cell = ['B1','B2','B3']
        ws.insert_column_data('B',col_data)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
        exp_cell = ['C3','C4','C5']
        ws.insert_column_data('C',col_data,start=3)
        for i in xrange(3):
            self.assertEqual(ws[exp_cell[i]],col_data[i])
    def test_insert_row(self):
        ws = self.ws
        ws.insert_column_data('A',('hello','goodbye','whatev'))
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
    def test_write_row_with_list(self):
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        exp_cell = ['A4','B4','C4','D4']
        ws.write_row(4,data=row_data)
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.write_row(5,data=row_data,from_column='E')
        self.assertEqual(ws.last_column,'H')
        self.assertEqual(ws.last_row,5)
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
    def test_write_row_with_text(self):
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        row_text = "Dozy\tBeaky\tMick\tTitch"
        exp_cell = ['A4','B4','C4','D4']
        ws.write_row(4,text=row_text)
        self.assertEqual(ws.last_column,'D')
        self.assertEqual(ws.last_row,4)
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.write_row(5,text=row_text,from_column='E')
        self.assertEqual(ws.last_column,'H')
        self.assertEqual(ws.last_row,5)
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
    def test_insert_row_data(self):
        ws = self.ws
        row_data = ['Dozy','Beaky','Mick','Titch']
        exp_cell = ['A4','B4','C4','D4']
        ws.insert_row_data(4,row_data)
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
        exp_cell = ['E5','F5','G5','H5']
        ws.insert_row_data(5,row_data,start='E')
        for i in xrange(4):
            self.assertEqual(ws[exp_cell[i]],row_data[i])
    def test_insert_block_data(self):
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
    def test_fill_column(self):
        ws = self.ws
        # Add some data first, then fill
        ws.insert_column_data('A',['some','random','items'])
        ws.fill_column('L',"50")
        for idx in ('L1','L2','L3'):
            self.assertEqual(ws[idx],"50")
    def test_fill_column_empty_worksheet(self):
        ws = self.ws
        # Empty spreadsheet, no fill
        ws.fill_column('L',"50")
        self.assertEqual(ws['L1'],None)
        ws.fill_column('L',"50",start=1)
        self.assertEqual(ws['L1'],None)
        ws.fill_column('L',"50",end=3)
        self.assertEqual(ws['L1'],None)
        # Can fill if both limits are given
        ws.fill_column('L',"50",start=1,end=3)
        for idx in ('L1','L2','L3'):
            self.assertEqual(ws[idx],"50")
    def test_columns_and_rows(self):
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
    def test_render_cell(self):
        self.ws.insert_column_data(self.ws.next_column,['4.5'])
        self.assertEqual(self.ws.render_cell('A1'),'4.5')
    def test_render_cell_formula(self):
        self.ws.insert_column_data(self.ws.next_column,['4.5','6.7','=A1+A2'])
        self.assertEqual(self.ws.render_cell('A3'),'=A1+A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'11.2')
    def test_render_cell_formula_with_column_substitution(self):
        self.ws.insert_column_data(self.ws.next_column,['4.5','6.7','=#1+#2'])
        self.assertEqual(self.ws.render_cell('A3'),'=A1+A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'11.2')
    def test_render_cell_formula_with_row_substitution(self):
        self.ws.insert_column_data(self.ws.next_column,['4.5'])
        self.ws.insert_column_data(self.ws.next_column,['6.7'])
        self.ws.insert_column_data(self.ws.next_column,['=A?+B?'])
        self.assertEqual(self.ws.render_cell('C1'),'=A1+B1')
        self.assertEqual(self.ws.render_cell('C1',eval_formulae=True),'11.2')
    def test_render_cell_formula_with_formatting(self):
        self.ws.insert_column_data(self.ws.next_column,['1.0','2.0','=A1/A2'])
        self.ws.set_style(XLSStyle(number_format=NumberFormats.PERCENTAGE),'A3')
        self.assertEqual(self.ws.render_cell('A3'),'=A1/A2')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True),'0.5')
        self.assertEqual(self.ws.render_cell('A3',eval_formulae=True,apply_format=True),
                         '50.0%')

class TestCellIndex(unittest.TestCase):
    """
    """
    def test_cell_index(self):
        self.assertEqual(CellIndex('A1').column,'A')
        self.assertEqual(CellIndex('A1').row,1)
        self.assertEqual(CellIndex('ZB567').column,'ZB')
        self.assertEqual(CellIndex('ZB567').row,567)
    def test_cell_index_is_full(self):
        self.assertTrue(CellIndex('A1').is_full)
        self.assertTrue(CellIndex('AZ123').is_full)
        self.assertFalse(CellIndex('A').is_full)
        self.assertFalse(CellIndex('1').is_full)
        self.assertFalse(CellIndex('123').is_full)
        self.assertFalse(CellIndex('!1#2').is_full)
    def test_cell_index_repr(self):
        self.assertTrue(str(CellIndex('A1')),'A1')
        self.assertTrue(str(CellIndex('ZB567')),'ZB567')
        self.assertTrue(str(CellIndex('A')),'A')
        self.assertTrue(str(CellIndex('1')),'1')

class TestColumnIndexToInteger(unittest.TestCase):
    """
    """
    def test_column_index_to_integer(self):
        self.assertEqual(column_index_to_integer('A'),0)
        self.assertEqual(column_index_to_integer('B'),1)
        self.assertEqual(column_index_to_integer('Z'),25)
        self.assertEqual(column_index_to_integer('AA'),26)
        self.assertEqual(column_index_to_integer('AB'),27)
        self.assertEqual(column_index_to_integer('AZ'),51)

class TestColumnIntegerToIndex(unittest.TestCase):
    """
    """
    def test_column_integer_to_index(self):
        self.assertEqual(column_integer_to_index(0),'A')
        self.assertEqual(column_integer_to_index(1),'B')
        self.assertEqual(column_integer_to_index(25),'Z')
        self.assertEqual(column_integer_to_index(26),'AA')
        self.assertEqual(column_integer_to_index(27),'AB')
        self.assertEqual(column_integer_to_index(51),'AZ')

class TestIncrCol(unittest.TestCase):
    """
    """
    def test_incr_col(self):
        self.assertEqual(incr_col('A'),'B')
        self.assertEqual(incr_col('C',2),'E')
        self.assertEqual(incr_col('C',-1),'B')
        self.assertEqual(incr_col('C',-2),'A')
        self.assertEqual(incr_col('Z'),'AA')
        self.assertEqual(incr_col('AA',-1),'Z')

class TestColumnRange(unittest.TestCase):
    """
    """
    def test_column_range(self):
        for expected,actual in itertools.izip(['A','B','C'],
                                              ColumnRange('A','C')):
            self.assertEqual(expected,actual)
    def test_column_range_implicit_start(self):
        for expected,actual in itertools.izip(['A','B','C'],
                                              ColumnRange('C')):
            self.assertEqual(expected,actual)
    def test_column_range_dont_include_end(self):
        for expected,actual in itertools.izip(['A','B','C'],
                                              ColumnRange('A','D',
                                                          include_end=False)):
            self.assertEqual(expected,actual)
    def test_column_range_reverse(self):
        for expected,actual in itertools.izip(['C','B','A'],
                                              ColumnRange('A','C',
                                                          reverse=True)):
            self.assertEqual(expected,actual)

class TestXLSStyle(unittest.TestCase):
    """
    """
    def setUp(self):
        self.text = "Some test text"
    def test_cell_style_no_style(self):
        self.assertEqual(XLSStyle().style(self.text),self.text)
    def test_cell_style_bold(self):
        self.assertEqual(XLSStyle(bold=True).style(self.text),
                         "<style font=bold>%s</style>" % self.text)
    def test_cell_style_number_format(self):
        self.assertEqual(XLSStyle(number_format=None).style(self.text),
                         "%s" % self.text)
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.THOUSAND_SEPARATOR).style(self.text),
                         "<style number_format=#,###>%s</style>" % self.text)
        self.assertEqual(XLSStyle(
            number_format=NumberFormats.PERCENTAGE).style(self.text),
                         "<style number_format=0.0%%>%s</style>" % self.text)
    def test_excel_number_format(self):
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
        self.assertEqual(XLSStyle.name,'')
        self.assertEqual(XLSStyle(bold=True),'__bold__')
        self.assertEqual(XLSStyle(color=True),'__bold__')
        self.assertEqual(XLSStyle(color='red'),'__color=red__')
        self.assertEqual(XLSStyle(bgcolor='blue'),'__bgcolor=blue__')
        self.assertEqual(XLSStyle(number_format=NumberFormats.PERCENTAGE),
                         '__number_format=1__')
        self.assertEqual(XLSStyle(border='thick'),'__border=thick__')
        self.assertEqual(XLSStyle(font_size=14),'__font_size=14__')
        self.assertEqual(XLSStyle(centre=True),'__centre__')
        self.assertEqual(XLSStyle(shrink_to_fit=True),'__shrink_to_fit__')
        self.assertEqual(XLSStyle(bold=True,bgcolor='green'),
                         '__bold__bgcolor=green__')
        self.assertEqual(XLSStyle(bold=True,font_size=14,centre=True),
                         '__bold__font_size=14__centre__')

class TestCmpColumnIndices(unittest.TestCase):
    """
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
    """
    def setUp(self):
        ws = XLSWorkSheet('Test Worksheet')
        ws.insert_column_data('A',['1.0','2.0','3.0'])
        ws.insert_column_data('B',['4.0','5.0','6.0'])
        ws.insert_column_data('C',['7.0','8.0','9.0'])
        self.ws = ws
    def test_simple_substitutions(self):
        self.assertEqual(eval_formula("123",self.ws),"123")
        self.assertEqual(eval_formula("123.0",self.ws),"123.0")
        self.assertEqual(eval_formula("",self.ws),"")
        self.assertEqual(eval_formula("not a number",self.ws),"not a number")
        self.assertEqual(eval_formula("=A1",self.ws),1.0)
    def test_operations(self):
        self.assertEqual(eval_formula("=A1+A2",self.ws),3.0)
        self.assertEqual(eval_formula("=A1-A2",self.ws),-1.0)
        self.assertEqual(eval_formula("=A1*A2",self.ws),2.0)
        self.assertEqual(eval_formula("=A1/A2",self.ws),0.5)
    def test_recursive_evaluation(self):
        self.ws.insert_column_data('D',['=C1','=C1+C2','=D1+D2'])
        self.assertEqual(eval_formula("=D1",self.ws),7.0)
        self.assertEqual(eval_formula("=D2",self.ws),15.0)
        self.assertEqual(eval_formula("=D3",self.ws),22.0)
    def test_bad_values(self):
        self.ws.insert_column_data('D',['one','two','=D1+D2'])
        self.assertEqual(eval_formula("=D1",self.ws),'one')
        self.assertEqual(eval_formula("=D3",self.ws),BAD_REF)
    def test_simple_substitutions_with_integers(self):
        self.ws.insert_column_data('D',['1','2','3'])
        self.assertEqual(eval_formula("=D1",self.ws),1)
        self.assertEqual(eval_formula("=D2",self.ws),2)
        self.assertEqual(eval_formula("=D3",self.ws),3)
    def test_operations_with_integers(self):
        self.ws.insert_column_data('D',['1','2','3'])
        self.assertEqual(eval_formula("=D1+D2",self.ws),3)
        self.assertEqual(eval_formula("=D1-D2",self.ws),-1)
        self.assertEqual(eval_formula("=D1*D2",self.ws),2)
        self.assertEqual(eval_formula("=D1/D2",self.ws),0.5)
    def test_operations_mixing_integers_and_floats(self):
        self.ws.insert_column_data('D',['1','2','3'])
        self.assertEqual(eval_formula("=A1+D2",self.ws),3.0)
        self.assertEqual(eval_formula("=A1-D2",self.ws),-1.0)
        self.assertEqual(eval_formula("=A1*D2",self.ws),2.0)
        self.assertEqual(eval_formula("=A1/D2",self.ws),0.5)

class TestFormatValue(unittest.TestCase):
    """
    """
    def test_no_format(self):
        self.assertEqual(format_value("value"),"value")
    def test_thousands_separator(self):
        self.assertEqual(format_value(1,NumberFormats.THOUSAND_SEPARATOR),"1")
        self.assertEqual(format_value(10,NumberFormats.THOUSAND_SEPARATOR),"10")
        self.assertEqual(format_value(100,NumberFormats.THOUSAND_SEPARATOR),"100")
        self.assertEqual(format_value(1000,NumberFormats.THOUSAND_SEPARATOR),"1,000")
        self.assertEqual(format_value(10000,NumberFormats.THOUSAND_SEPARATOR),"10,000")
        self.assertEqual(format_value(100000,NumberFormats.THOUSAND_SEPARATOR),"100,000")
        self.assertEqual(format_value(1000000,NumberFormats.THOUSAND_SEPARATOR),"1,000,000")
        self.assertEqual(format_value(12726554,NumberFormats.THOUSAND_SEPARATOR),"12,726,554")
    def test_percentage(self):
        self.assertEqual(format_value(0.5,NumberFormats.PERCENTAGE),"50.0%")
        self.assertEqual(format_value(0.872667,NumberFormats.PERCENTAGE),"87.3%")
