#!/usr/bin/env python3
#
#     simple_xls.py: write simple Excel spreadsheets
#     Copyright (C) University of Manchester 2013-2026 Peter Briggs
#
########################################################################
#
# simple_xls.py
#
#########################################################################

"""
Legacy module providing classes and functions for programmatic spreadsheet
generation.

The core functionality has been moved to the ``io.xls`` module, which now
implements the ``XLSWorkBook``, ``XLSWorkSheet``, ``XLSStyle`` and other
supporting classes and functions, and which are used within this module as
the basis for the backwards-compatible versions.

The classes in this module are now deprecated and should not be used in new
code; they are likely to be removed in a future release.

.. note::

   Some functionality has not been ported to ``io.xls``, specifically for
   generating older MS Excel spreadsheets (``.xls``). This functionality is
   retained in this legacy module using functionality from the ``Spreadsheet``
   module (also now deprecated).
"""

from . import Spreadsheet
from .io import xls

# Legacy spreadsheet limits
class XLSLimits:
    """
    Limits for XLS files
    """
    MAX_LEN_WORKSHEET_TITLE = 31 # Max worksheet title length
    MAX_LEN_WORKSHEET_CELL_VALUE = 250 # Maximum no. of characters in cell
    MAX_NUMBER_ROWS_PER_WORKSHEET = 65536 # Max number of rows per worksheet
    MAX_NUMBER_COLS_PER_WORKSHEET = 256 # Max nuber of columns per worksheet

class Limits(XLSLimits):
    """
    Limits for XLS files (kept for backwards compatibility)
    """

#######################################################################
# Constants
#######################################################################

# Value to assign to failed evaluations
BAD_REF = xls.BAD_REF

# Number formats
NumberFormats = xls.NumberFormats

# XLSX file limits
XLSXLimits = xls.XLSXLimits

#######################################################################
# Class definitions
#######################################################################

class XLSWorkBook(xls.XLSWorkBook):
    """Class for creating an Excel (xls) spreadsheet

    An XLSWorkBook instance provides an interface to creating an
    Excel spreadsheet.

    It consists of a collection of XLSWorkSheet objects, each
    of which represents a sheet in the workbook.

    Sheets are created and appended using the add_work_sheet
    method:

    >>> xls = XLSWorkBook()
    >>> sheet = xls('example')
    
    Sheets are kept in the 'worksheet' property and can be acquired
    by name:

    >>> sheet = xls.worksheet['example']

    Once the worksheet(s) have been populated an XLS file can be
    created using the 'save_as_xls' method:

    >>> xls.save_as_xls('example.xls')

    """
    def __init__(self,title=None):
        """Create a new XLSWorkBook instance

        Arguments:
          title: optional, a title for the work book

        """
        xls.XLSWorkBook.__init__(self, title=title)

    def save_as_xls(self,filen):
        """Output the workbook contents to an Excel-format file

        Arguments:
          filen: name of the file to write the workbook to.

        """
        xls = Spreadsheet.Workbook()
        for name in self.worksheet:
            worksheet = self.worksheet[name]
            ws = xls.addSheet(worksheet.title)
            ws.addText(worksheet.render_as_text(include_styles=True))
            if worksheet.freeze_panes is not None:
                col = column_index_to_integer(
                    CellIndex(worksheet.freeze_panes).column)
                row = CellIndex(worksheet.freeze_panes).row - 1
                ws.freezePanes(column=col,row=row)
        xls.save(filen)

    def save_as_xlsx(self,filen):
        """Output the workbook contents to an XLSX-format file

        Arguments:
          filen: name of the file to write the workbook to.

        """
        self.save(filen)

class XLSWorkSheet(xls.XLSWorkSheet):
    """Class for creating sheets within an XLS workbook.

    XLSWorkSheet objects represent a sheet within an Excel
    workbook.

    Cells are addressed within the sheet using Excel notation
    i.e. <column><row> (columns start at index 'A' and rows at
    '1', examples are 'A1' or 'D19'):

    >>> ws = XLSWorkSheet('example')
    >>> ws['A1'] = 'some data'
    >>> value = ws['A1']

    If there is no data stored for the cell then 'None' is
    returned. Any cell can addressed without errors.

    Data can also be added column-wise, row-wise or as a
    "block" of tab- and new-line delimited data:

    >>> ws.insert_column_data('B',[1,2,3])
    >>> ws.insert_row_data(4,['x','y','z'])
    >>> ws.insert_block_data("This\\tis\\nthe\\tdata")

    A column can be "filled" with a single repeating value:

    >>> ws.fill_column('D','single value')

    The extent of the sheet can be determined from the
    'last_column' and last_row' properties; the 'next_column'
    and 'next_row' properties report the next empty column
    and row respectively.

    Cells can contain Excel-style formula by adding an
    equals sign to the start of the value. Typically formulae
    reference other cells and perform mathematical operations
    on them, e.g.:

    >>> ws['E11'] = "=A1+A2"

    Wildcard characters can be used which will be automatically
    translated into the cell column ('#') or row ('?'), for
    example:

    >>> ws['F46'] = "=#47+#48"

    will be transformed to "=F47+F48".

    Styles can be applied to cells, using either the 'set_style'
    method or via the 'style' argument of some methods, to
    associate an XLSStyle object. Associated XLSStyle objects
    can be retrieved using the 'get_style' method.

    The value of an individual cell can be 'rendered' for
    output using the 'render_cell' method:

    >>> print(ws.render_cell('F46'))

    All or part of the sheet can be rendered as a tab- and
    newline-delimited string by using the 'render_as_text'
    method:

    >>> print(ws.render_as_text())

    """
    def __init__(self,title):
        """Create new XLSWorkSheet object

        Arguments:
          title: title string for the worksheet

        """
        xls.XLSWorkSheet.__init__(
            self, str(title)[:Spreadsheet.MAX_LEN_WORKSHEET_TITLE])

    def insert_column_data(self,col,data,start=None,style=None):
        """Insert list of data into a column

        Data items are supplied as a list, with each item in the list
        being inserted into the next row in the column.

        By default items are inserted starting from row 1, unless a
        starting row is explicitly specified via the 'start' argument.

        *** THIS METHOD IS DEPRECATED ***

        Consider using insert_column, append_column or write_data.

        Arguments:
          col: index of column to insert the data into (e.g. 'A','MZ')
          data: list of data items
          start: (optional) first row to insert data into
          style: (optional) XLSStyle object to be associated with each
            cell that has data inserted into it

        """
        self.insert_column(col,data,from_row=start,style=style)

    def insert_row_data(self,row,data,start=None,style=None):
        """Insert list of data into a row

        Data items are supplied as a list, with each item in the list
        being inserted into the next column in the row.

        By default items are inserted starting from column 'A', unless a
        starting column is explicitly specified via the 'start' argument.

        *** THIS METHOD IS DEPRECATED ***

        Consider using insert_row, append_row or write_row.

        Arguments:
          row: index of row to insert the data into (e.g. 1, 112)
          data: list of data items
          start: (optional) first column to insert data into
          style: (optional) XLSStyle object to be associated with each
            cell that has data inserted into it

        """
        self.insert_row(row,data,from_column=start,style=style)

    def fill_column(self,column,item,start=None,end=None,style=None):
        """Fill a column with a single repeated data item

        A single data item is inserted into all rows in the specified
        column which have at least one data item already in any column
        in the worksheet. A different range of rows can be specified
        via the 'start' and 'end' arguments.

        *** THIS METHOD IS DEPRECATED ***

        Consider using insert_column, append_column or write_data.

        Arguments:
          column: index of column to insert the item into  (e.g. 'A','MZ')
          item: data item to be repeated
          start: (optional) first row to insert data into
          end: (optional) last row to insert data into
          style: (optional) XLSStyle object to be associated with each
            cell that has data inserted into it

        """
        # Fill a column with the same data item
        if (start is None or end is None) and (not self.columns and not self.rows):
            # Empty sheet, nothing to fill
            return
        if start is None:
            i = 1
        else:
            i = int(start)
        if end is None:
            j = self.last_row
        else:
            j = int(end)
        for row in range(i,j+1):
            self[cell(column,row)] = item
            if style is not None:
                self.set_style(style,cell(column,row))

class XLSStyle(xls.XLSStyle):
    """Class representing a set of styling and formatting data

    An XLSStyle object represents a collection of data used for
    styling and formatting cell values on output to an Excel file.

    The style attributes can be set on instantiation, or queried
    and modified afterwards.

    The attributes are:

    bold: whether text is bold or not (boolean)
    color: text color (name)
    bgcolor: background color (name)
    wrap: whether text in a cell should wrap (boolean)
    border: style of cell border (thick, medium, thin etc)
    number_format: a format code from the NumbersFormat class
    font_size: font size in points (integer)
    centre: whether text is centred in the cell (boolean)
    shrink_to_fit: whether to shrink cell to fit the contents.

    The 'name' property can be used to generate a name for the style
    based on the attributes that have been set, for example:

    >>> XLSStyle(bold=true).name
    ... '__bold__'

    """
    def __init__(self,bold=False,color=None,bgcolor=None,wrap=False,
                 border=None,number_format=None,font_size=None,centre=False,
                 shrink_to_fit=False):
        """Create a new XLSStyle object

        The available arguments are the same as the attributes.

        """
        xls.XLSStyle.__init__(self,bold=bold,color=color,bgcolor=bgcolor,wrap=wrap,
                              border=border,number_format=number_format,font_size=font_size,
                              centre=centre,shrink_to_fit=shrink_to_fit)

class ColumnRange(xls.ColumnRange):
    """Iterator for a range of column indices

    Range-style iterator for iterating over alphabetical column
    indices, e.g.

    >>> for c in ColumnRange('A','Z'):
    ...   print(c)

    """
    def __init__(self,i,j=None,include_end=True,reverse=False):
        """Create an iterator for a range of column indices

        Acts like 'range' i.e.:

        ColumnRange('C'): equivalent to ['A','B','C']
        ColumnRange('C',include_end=False): ['A','B']
        ColumnRange('C','F'): ['C','D','E','F']
        ColumnRange(''C','F',include_end=False): ['C','D','E']

        Arguments:
          i: defines start column if j is not None, or
             end column if j is not None (in which case
             start column will be 'A')
          j: defines end column (if not None)
          include_end: if True then the end column is also
             included; otherwise it is omitted.
          reverse: if True then the columns are returned in
             descending order

        """
        xls.ColumnRange.__init__(self,i,j=j,include_end=include_end,
                                 reverse=reverse)

class CellIndex(xls.CellIndex):
    """Convenience class for handling XLS-style cell indices

    The CellIndex class provides a way of handling XLS-style
    cell indices i.e. 'A1', 'BZ112' etc.

    Given a putative cell index it extracts the column and
    row which can then be accessed via the 'column' and
    'row' attributes respectively.

    The 'is_full' property reports whether the supplied
    index is actually a 'full' index with both column and
    row specifiers. If it is just a column or just a row
    then only the appropriate 'column' or 'row' attributes
    will be set.

    """
    def __init__(self,idx):
        """Create a new CellIndex instance

        Arguments
          idx: cell index e.g. 'A1', 'BZ112'

        """
        xls.CellIndex.__init__(self,idx)

class XLSColumn(xls.XLSColumn):
    """Class representing a column in a XLSWorkSheet

    An XLSColumn object provides access to data in a column
    from a XLSWorkSheet object. Typically one can be returned
    by doing something like:

    >>> colA = ws['A']
    
    and individual cell values then accessed by row number
    alone, e.g.:

    >>> value = colA['1']
    >>> colA['2'] = "New value"
    
    """
    def __init__(self,column_index,parent=None):
        """Create a new XLSColumn instance

        Arguments
          column_index: column index
          parent: parent XLSWorkSheet object

        """
        xls.XLSColumn.__init__(self,column_index,parent=parent)

#######################################################################
# Functions
#######################################################################

def cmp_column_indices(x,y):
    """Comparision function for column indices

    x and y are XLS-style column indices e.g. 'A', 'B', 'AA' etc.

    Returns -1 if x is a column index less than y, 1 if it is
    greater than y, and 0 if it's equal.

    """
    return xls.cmp_column_indices(x,y)

def cell(col,row):
    """Return XLS cell index for column and row

    E.g. cell('A',3) returns 'A3'

    """
    return xls.cell(col,row)

def incr_col(col,incr=1):
    """Return column index incremented by specific number of positions

    Arguments:
      col: index of column to be incremented
      incr: optional, number of cells to shift by. Can be negative
        to go backwards. Defaults to 1 i.e. next column along.

    """
    return xls.incr_col(col,incr)

def column_index_to_integer(col):
    """Convert XLS-style column index into equivalent integer

    Given a column index e.g. 'A', 'BZ' etc, converts it
    to the integer equivalent using zero-based counting
    system (so 'A' is equivalent to zero, 'B' to 1 etc).

    """
    return xls.column_index_to_integer(col)

def column_integer_to_index(idx):
    """Convert integer column index to XLS-style equivalent

    Given an integer index, converts it to the XLS-style
    equivalent e.g. 'A', 'BZ' etc, using a zero-based
    counting system (so zero is equivalent to 'A', 1 to 'B'
    etc).

    """
    return xls.column_integer_to_index(idx)

def eval_formula(item,worksheet):
    """Evaluate a formula using the contents of a worksheet

    Given an item, attempts an Excel-style evaluation.

    If the item doesn't start with '=' then it is returned as-is.
    Otherwise the function attempts to evaluate the formula,
    including looking up (and if necessary also evaluating) the
    contents of any cells that are referenced.

    .. note::

       The implementation of the evaluation is very
       simplistic and cannot handle complex formulae
       or functions, it can only deal with basic
       mathematical operations (i.e. ``+``, ``-``,
       ``*`` and ``/``)

    """
    return xls.eval_formula(item,worksheet)

def convert_to_number(s):
    """Convert a number to float or int as appropriate

    Raises ValueError if neither conversion is possible.

    """
    return xls.convert_to_number(s)

def is_float(s):
    """Test if a number is a float
    """
    return xls.is_float(s)

def is_int(s):
    """Test if a number is an integer
    """
    return xls.is_int(s)

def format_value(value,number_format=None):
    """Format a cell value based on the specified number format

    """
    return xls.format_value(value, number_format)

