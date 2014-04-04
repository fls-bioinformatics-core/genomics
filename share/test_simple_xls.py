#######################################################################
# Tests for simple_xls module
#######################################################################
from simple_xls import *
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

class TestColumnRange(unittest.TestCase):
    """
    """
    def test_column_range(self):
        for expected,actual in itertools.izip(['A','B','C'],
                                              ColumnRange('A','C')):
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
