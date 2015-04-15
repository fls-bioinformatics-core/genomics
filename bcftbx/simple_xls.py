#     simple_xls.py: write simple Excel spreadsheets
#     Copyright (C) University of Manchester 2013-4 Peter Briggs
#
########################################################################
#
# simple_xls.py
#
#########################################################################

"""
Simple spreadsheet module intended to provide a nicer programmatic interface
to Excel spreadsheet generation.

It is currently built on top of SpreadSheet.py, which itself uses the xlwt,
xlrd and xlutils modules. In future the relevant parts may be rewritten to
remove the dependence on Spreadsheet.py and call the appropriate xl* classes
and functions directly.

Example usage
-------------

Start by making a workbook, represented by an XLSWorkBook object:

>>> wb = XLSWorkBook("Test")

Then add worksheets to this:

>>> wb.add_work_sheet('test')
>>> wb.add_work_sheet('data',"My Data")

Worksheets have an id and an optional title. Ids must be unique and can
be used to fetch the XLSWorkSheet object that represent the worksheet:

>>> data = wb.worksheet['data']

Cells can be addressed directly using various notations:

>>> data['A1'] = "Column 1"
>>> data['A']['1'] = "Updated value"
>>> data['AZ']['3'] = "Another value"

The extent of the sheet is defined by the outermost populated rows and
columns

>>> data.last_column # outermost populated column
>>> data.last_row    # outermost populated row

There are various other methods for returning the next row or column; see
the documentation for the XLSWorkSheet class.

Data can be added cell-wise (i.e. referencing individual cells as above),
row-wise, column-wise and block-wise.

Column-wise operations include inserting a column (shifting columns above
it along one to make space):

>>> data.insert_column('B',data=['hello','goodbye','whatev'])

Append a column (writing data to the first empty column at the end of
the sheet):

>>> data.append_column(data=['hello','goodbye','whatev'])

Write data to a column, overwriting any existing values:

>>> data.write_column(data=['hello','goodbye','whatev'])

Data can be specified as a list, text or as a single value which is
repeated for each cell (i.e. a "fill" value).

Similar row-wise operations also exist:

>>> data.insert_row(4,data=['Dozy','Beaky','Mick','Titch'])
>>> data.append_row(data=['Dozy','Beaky','Mick','Titch'])
>>> data.write_row(4,data=['Dozy','Beaky','Mick','Titch'])

Block-wise data can be added via a tab and newline-delimited string:

>>> data.insert_block_data("This\tis\t\tsome\n\trandom\n\tdata")
>>> data.insert_block_data("This\tis\t\tsome\n\tMORE\trandom\n\tdata",
...                        col='M',row=7)

Formulae can be specified by prefixing a '=' symbol to the start of the
cell contents, e.g.:

>>> data['A3'] = '=A1+A2'

'?' and '#' are special characters that can be used to indicate 'current
row' and 'current column' respectively, e.g.:

>>> data.fill_column('A','=B?+C?') # evaluates to 'B1+C1' (A1), 'B2+C2' (A2) etc

Styling and formatting information can be associated with a cell, either
when adding column, row or block data or by using the 'set_style' method.
In each case the styling information is passed via an XLSStyle object, e.g.

>>> data.set_style(XLSStyle(number_format=NumberFormats.PERCENTAGE),'A3')

The workbook can be saved to file:

>>> wb.save_as_xls('test.xls')

Alternatively the contents of a sheet (or a subset) can be rendered as text:

>>> data.render_as_text(include_columns_and_rows=True,
...                     eval_formulae=True,
...                     include_styles=True)
>>> data.render_as_text(start='B1',end='C6',include_columns_and_rows=True)

"""

__version__ = "0.0.8"

#######################################################################
# Import modules that this module depends on
#######################################################################
 
import re
from collections import Iterator
import logging
import Spreadsheet
from utils import OrderedDictionary

#######################################################################
# Constants
#######################################################################

# Value to assign to failed evaluations
BAD_REF="## !REF ##"

# Number formats
class NumberFormats:
    THOUSAND_SEPARATOR=0
    PERCENTAGE=1

# Spreadsheet limits
class Limits:
    MAX_LEN_WORKSHEET_TITLE = 31 # Max worksheet title length
    MAX_LEN_WORKSHEET_CELL_VALUE = 250 # Maximum no. of characters in cell
    MAX_NUMBER_ROWS_PER_WORKSHEET = 65536 # Max number of rows per worksheet

#######################################################################
# Class definitions
#######################################################################

class XLSWorkBook:
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
        self.title = title
        self.worksheet = OrderedDictionary()

    def add_work_sheet(self,name,title=None):
        """Create and append a new worksheet

        Creates a new XLSWorkSheet object and appends it
        to the workbook.

        Arguments:
          name: unique name for the worksheet
          title: optional, title for the worksheet - defaults to
            the name.

        Returns:
          New XLSWorkSheet object.

        """
        if name in self.worksheet:
            raise KeyError,"Worksheet called '%s' already exists" % name
        if title is None:
            title = name
        self.worksheet[name] = XLSWorkSheet(title)
        return self.worksheet[name]

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
        xls.save(filen)

class XLSWorkSheet:
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
    >>> ws.insert_block_data("This\tis\nthe\tdata")

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

    >>> print ws.render_cell('F46')

    All or part of the sheet can be rendered as a tab- and
    newline-delimited string by using the 'render_as_text'
    method:

    >>> print ws.render_as_text()

    """
    def __init__(self,title):
        """Create new XLSWorkSheet object

        Arguments:
          title: title string for the worksheet

        """
        self.title = str(title)[:Spreadsheet.MAX_LEN_WORKSHEET_TITLE]
        self.data = {}
        self.styles = {}
        self.rows = []
        self.columns = []

    def __setitem__(self,idx,value):
        """Implement 'x[idx] = value'

        """
        idx = CellIndex(idx)
        if not idx.is_full:
            raise KeyError,"Invalid index: '%s'" % idx
        self.data[idx.idx] = value
        if idx.column not in self.columns:
            self.columns.append(idx.column)
        self.columns.sort(cmp=cmp_column_indices)
        if idx.row not in self.rows:
            self.rows.append(idx.row)
        self.rows.sort()

    def __getitem__(self,idx):
        """Implement 'value = x[idx]'

        """
        if str(idx).isalpha():
            return XLSColumn(idx,parent=self)
        else:
            try:
                return self.data[idx]
            except Exception,ex:
                return None

    def __delitem__(self,idx):
        """Implement 'del(x[idx])'

        """
        try:
            del(self.data[idx])
        except KeyError:
            pass
        idx = CellIndex(idx)
        if self.column_is_empty(idx.column):
            self.columns.remove(idx.column)
        if self.row_is_empty(idx.row):
            self.rows.remove(idx.row)

    @property
    def last_column(self):
        """Return index of last column with data

        """
        try:
            return self.columns[-1]
        except IndexError:
            return 'A'

    @property
    def next_column(self):
        """Index of first empty column after highest index with data

        """
        if len(self.columns):
            return column_integer_to_index(column_index_to_integer(self.last_column)+1)
        else:
            return 'A'

    @property
    def last_row(self):
        """Return index of last row with data

        """
        try:
            return int(self.rows[-1])
        except IndexError:
            return 1

    @property
    def next_row(self):
        """Index of first empty row after highest index with data

        """
        if len(self.rows):
            return self.last_row + 1
        else:
            return 1

    def column_is_empty(self,col):
        """Determine whether a column is empty

        Returns False if any cells in the column are populated,
        otherwise returns True.

        """
        if col not in self.columns:
            return True
        for row in self.rows:
            if self[cell(col,row)] is not None:
                return False
        return True

    def row_is_empty(self,row):
        """Determine whether a row is empty

        Returns False if any cells in the row are populated,
        otherwise returns True.

        """
        if row not in self.rows:
            return True
        for col in self.columns:
            if self[cell(col,row)] is not None:
                return False
        return True

    def columnof(self,s,row=1):
        """Return column index for cell which matches string

        Return index of first column where the content matches
        the specified string 's'.

        Arguments:
          s: string to search for
          row: row to search in (defaults to 1)

        Returns:
          Column index of first matching cell. Raises LookUpError
          if no match is found.

        """
        for col in self.columns:
            if self[cell(col,row)] == s:
                return col
        raise LookupError,"No match for '%s' in row %d" % (s,row)

    def insert_column(self,position,data=None,text=None,fill=None,from_row=None,style=None):
        """Create a new column at the specified column position

        Inserts a new column at the specified column position,
        pushing up the column currently at that position plus all
        higher positioned columns.

        By default the inserted column is empty, however data can
        be specified to populate the column.

        Arguments:
          position: column index specifying position to insert the
            column at
          data: optional, list of data items to populate the
            inserted column
          text: optional, tab-delimited string of text to be used
            to populate the inserted column
          fill: optional, single data item to be repeated to fill
            the inserted column
          from_row: optional, if specified then inserted column is
            populated from that row onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        Returns:
          The index of the inserted column.

        """
        # Get list of all columns we want to move (in reverse order)
        columns_to_bump = []
        try:
            i = self.columns.index(position)
            columns_to_bump = self.columns[i:][::-1]
        except ValueError:
            for col in self.columns:
                if cmp_column_indices(col,position) > -1:
                    i = self.columns.index(col)
                    columns_to_bump = self.columns[i:][::-1]
                    break
        # Shift columns, if required
        for col in columns_to_bump:
            next_col = column_integer_to_index(column_index_to_integer(col)+1)
            for row in range(1,self.last_row+1):
                # Get cell index
                idx = cell(col,row)
                if idx in self.data:
                    # Copy contents to next column
                    self.data[cell(next_col,row)] = self.data[idx]
                    # Remove this cell
                    del(self.data[idx])
        # Append a new last column index to list of columns
        self.columns.append(self.next_column)
        # Remove the inserted column index from the list of columns
        if position in self.columns:
            self.columns.remove(position)
        # Now insert data at the new position
        self.write_column(position,data=data,text=text,fill=fill,from_row=from_row,style=style)
        return position

    def append_column(self,data=None,text=None,fill=None,from_row=None,style=None):
        """Create a new column at the end of the sheet

        Appends a new column at the end of the worksheet i.e. in the
        first available empty column.

        By default the appended column is empty, however data can
        be specified to populate the column.

        Arguments:
          data: optional, list of data items to populate the
            inserted column
          text: optional, tab-delimited string of text to be used
            to populate the inserted column
          fill: optional, single data item to be repeated to fill
            the inserted column
          from_row: optional, if specified then inserted column is
            populated from that row onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        Returns:
          The index of the appended column.

        """
        new_col = self.next_column
        # Now insert data into the new position
        self.write_column(new_col,data=data,text=text,fill=fill,from_row=from_row,style=style)
        return new_col

    def write_column(self,col,data=None,text=None,fill=None,from_row=None,style=None):
        """Write data to rows in a column

        Data can be specified as a list, a newline-delimited string, or
        as a single repeated data item.

        Arguments:
          data: optional, list of data items to populate the
            inserted column
          text: optional, newline-delimited string of text to be used
            to populate the inserted column
          fill: optional, single data item to be repeated to fill
            the inserted column
          from_row: optional, if specified then inserted column is
            populated from that row onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        """
        # Set initial row
        if from_row is None:
            from_row = 1
        # Write in data from a list
        if data is not None:
            items = data
        elif text is not None:
            items = text.split('\n')
        elif fill is not None:
            items = [fill for i in range(from_row,self.last_row+1)]
        else:
            # Nothing to do
            return
        # Add column index to list of columns
        if col not in self.columns:
            self.columns.append(col)
        # Write data items to cells
        row = from_row
        for item in items:
            self.data[cell(col,row)] = item
            if row not in self.rows:
                self.rows.append(row)
            if style is not None:
                self.set_style(style,cell(col,row))
            row += 1
        # Sort the column and row indices
        self.columns.sort(cmp=cmp_column_indices)
        self.rows.sort()

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
        # Insert data items from a list into a column in the spreadsheet
        if start is None:
            i = 1
        else:
            i = int(start)
        for item in data:
            self[cell(col,i)] = item
            if style is not None:
                self.set_style(style,cell(col,i))
            i += 1

    def rowof(self,s,column='A'):
        """Return row index for cell which matches string

        Return index of first row where the content matches
        the specified string 's'.

        Arguments:
          s: string to search for
          column: column to search in (defaults to 'A')

        Returns:
          Row index of first matching cell. Raises LookUpError
          if no match is found.

        """
        # Get row where cell in row matches 'name'
        # i.e. look up a row index
        for row in range(1,self.last_row+1):
            if self[cell(column,row)] == s:
                return row
        raise LookupError,"No match for '%s' in column '%s'" % (s,column)

    def insert_row(self,position,data=None,text=None,fill=None,from_column=None,style=None):
        """Create a new row at the specified row position

        Inserts a new row at the specified row position,
        pushing up the row currently at that position plus all
        higher positioned row.

        By default the inserted row is empty, however data can
        be specified to populate the column.

        Arguments:
          position: row index specifying position to insert the
            row at
          data: optional, list of data items to populate the
            inserted row
          text: optional, newline-delimited string of text to be used
            to populate the inserted row
          fill: optional, single data item to be repeated to fill
            the inserted row
          from_row: optional, if specified then inserted row is
            populated from that column onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        Returns:
          The index of the inserted row.

        """
        # Create a new row before the specified row
        # All rows above it move up one position
        # 'New' row position is actually 'before_row'
        # Bump all rows up one position
        # Get list of all rows we want to move (in reverse order)
        row_list = list(range(self.last_row,position-1,-1))
        for row in row_list:
            next_row = row + 1
            for col in self.columns:
                # Get cell index
                idx = cell(col,row)
                if idx in self.data:
                    # Copy contents to next row
                    self.data[cell(col,next_row)] = self.data[idx]
                    # Remove this cell
                    del(self.data[idx])
        # Add a new last row index to the list of rows
        self.rows.append(self.next_row)
        # Remove the inserted row index from the list
        if position in self.rows:
            self.rows.remove(position)
        # Now insert data at the new position
        self.write_row(position,data=data,text=text,fill=fill,from_column=from_column,style=style)
        return position

    def append_row(self,data=None,text=None,fill=None,from_column=None,style=None):
        """Create a new row at the end of the sheet

        Appends a new row at the end of the worksheet i.e. in the
        first available empty row.

        By default the appended row is empty, however data can
        be specified to populate the row.

        Arguments:
          data: optional, list of data items to populate the
            inserted row
          text: optional, newline-delimited string of text to be used
            to populate the inserted row
          fill: optional, single data item to be repeated to fill
            the inserted row
          from_row: optional, if specified then inserted row is
            populated from that column onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        Returns:
          The index of the inserted row.

        """
        # Create a new row at the end of the sheet
        new_row = self.next_row
        # Now insert data into the new position
        self.write_row(new_row,data=data,text=text,fill=fill,from_column=from_column,style=style)
        return new_row

    def write_row(self,row,data=None,text=None,fill=None,from_column=None,style=None):
        """Write data to rows in a column

        Data can be specified as a list, a tab-delimited string, or
        as a single repeated data item.

        Arguments:
          row: row index specifying which row
          data: optional, list of data items to populate the
            inserted row
          text: optional, tab-delimited string of text to be used
            to populate the inserted row
          from_column: optional, if specified then inserted row is
            populated from that column onwards
          style: optional, an XLSStyle object to associate with the
            data being inserted

        """
        # Set initial column
        if from_column is None:
            from_column = 'A'
        # Write in data from a list
        if data is not None:
            items = data
        elif text is not None:
            items = text.split('\t')
        elif fill is not None:
            items = [fill for i in range(from_row,self.last_row+1)]
        else:
            # Nothing to do
            return
        # Add row index to list of rows
        if row not in self.rows:
            self.rows.append(row)
        # Write data items to cells
        col = from_column
        for item in items:
            self.data[cell(col,row)] = item
            if col not in self.columns:
                self.columns.append(col)
            if style is not None:
                self.set_style(style,cell(col,row))
            col = incr_col(col)
        # Sort the column and row indices
        self.columns.sort(cmp=cmp_column_indices)
        self.rows.sort()

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
        # Insert data items from a list into a row in the spreadsheet
        if start is None:
            i = column_index_to_integer('A')
        else:
            i = column_index_to_integer(start)
        for item in data:
            self[cell(column_integer_to_index(i),row)] = item
            if style is not None:
                self.set_style(style,cell(column_integer_to_index(i),row))
            i += 1

    def insert_block_data(self,data,col=None,row=None,style=None):
        """Insert data items from a block of text

        Data items are supplied via a block of tab- and newline-delimited
        text. Each tab-delimited item is inserted into the next column in
        a row; newlines indicate that subsequent items are inserted into
        the next row.

        By default items are inserted starting from cell 'A1'; a different
        starting cell can be explicitly specified via the 'col' and 'row'
        arguments.

        Arguments:
          data: block of tab- and newline-delimited data
          col: (optional) first column to insert data into
          row: (optional) first row to insert data into
          style: (optional) XLSStyle object to be associated with each
            cell that has data inserted into it

        """
        # Insert data items from a block of text into the spreadsheet
        # Text must be tab and newline delimited
        if row is None:
            j = int(1)
        else:
            j = int(row)
        for line in data.split('\n'):
            if col is None:
                i = column_index_to_integer('A')
            else:
                i = column_index_to_integer(col)
            for item in line.strip('\n').split('\t'):
                icol = column_integer_to_index(i)
                if not item:
                    item = None
                self[cell(icol,j)] = item
                if style is not None:
                    self.set_style(style,cell(icol,j))
                i += 1
            j += 1

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
        for row in xrange(i,j+1):
            self[cell(column,row)] = item
            if style is not None:
                self.set_style(style,cell(column,row))

    def set_style(self,cell_style,start,end=None):
        """Associate style information with one or more cells
        
        Associates a specified XLSStyle object with a single
        cell, or with a range of cells (if a second cell index
        is supplied).

        The style associated with a cell can be fetched using
        the 'get_style' method.

        Arguments:
          cell_style: XLSStyle object
          start: cell index e.g. 'A1'
          end: (optional) second cell index; together with
            'start' this defines a range of cells to associate
            the style with.
        
        """
        if end is None:
            # Specified a single cell target
            self.styles[start] = cell_style
            return
        # Specify a range of cells
        start_cell = CellIndex(start)
        end_cell = CellIndex(end)
        for col in ColumnRange(start_cell.column,end_cell.column):
            for row in xrange(start_cell.row,end_cell.row+1):
                self.styles[cell(col,row)] = cell_style

    def get_style(self,idx):
        """Return the style information associated with a cell

        Returns an XLSStyle object associated with the specific
        cell.

        If no style was previously associated then return a new
        XLSStyle object.

        Arguments:
          idx: cell index e.g 'A1'

        Returns:
          XLSStyle object.

        """
        try:
            return self.styles[idx]
        except KeyError:
            # Return empty style object
            return XLSStyle()

    def render_cell(self,idx,eval_formulae=False,apply_format=False):
        """Text representation of value stored in a cell

        Create a text representation of a cell's contents. If the cell
        contains a formula then '?'s will be replaced with the row index
        and '#'s with the column index. Optionally the formula can also
        be evaluated, and any style information associated with the cell
        can also be rendered.

        Arguments:
          idx: cell index e.g. 'A1'
          eval_formulae: (optional) if True then if the cell contains
            a formula, attempt to evaluate it and return the result.
            Otherwise return the formula itself (this is the default)
          apply_format: (optional) if True then format numbers according
            to the formatting information associated with the cell
            (default is not to apply formatting).

        Returns:
          String representing the cell contents.

        """
        item = self[idx]
        if item is None:
            # Empty item
            return ''
        try:
            if item.startswith('='):
                # Formula
                item = item.replace('?',
                                    str(CellIndex(idx).row)).replace('#',
                                                                     str(CellIndex(idx).column))
                if eval_formulae:
                    logging.debug("Evaluating %s from %s" % (item,idx))
                    item = eval_formula(item,self)
        except AttributeError:
            pass
        if apply_format:
            style = self.get_style(idx)
            if style is not None:
                try:
                    return format_value(item,style.number_format)
                except Exception, ex:
                    logging.debug("Exception: %s" % ex)
                    raise ex
        else:
            return str(item)

    def render_as_text(self,include_columns_and_rows=False,
                       include_styles=False,
                       eval_formulae=False,
                       apply_format=False,
                       start=None,end=None):
        """Text representation of all or part of the worksheet

        All or part of the sheet can be rendered as a tab- and
        newline-delimited string.

        Arguments:
          include_columns_and_rows: (optional) if True then also output
            a header row of column indices, and a column of row indices
            (default is to not output columns and rows).
          include_styles: (optional) if True then also render the styling
            information associated with the cell (default is not to apply
            styling).
          apply_format: (optional) if True then format numbers according
            to the formatting information associated with the cell
            (default is not to apply formatting).
          eval_formulae: (optional) if True then if the cell contains
            a formula, attempt to evaluate it and return the result.
            Otherwise return the formula itself (this is the default)
          start: (optional) specify the top-lefthand most cell index to
            start rendering from (default is 'A1').
          end: (optional) specify the bottom-righthand most cell index
            to finish rendering at (default is the cell corresponding to
            the highest column and row indices. Note that this cell may
            be empty.)

        Returns:
          String containing the rendered sheet or sheet subset, with items
          within a row separated by tabs, and rows separated by newlines.

        """
        # Output worksheet as text (i.e. string)
        if start is None:
            start = CellIndex('A1')
        else:
            start = CellIndex(start)
        if end is None:
            end = CellIndex(cell(self.last_column,self.last_row))
        else:
            end = CellIndex(end)
        text = []
        if include_columns_and_rows:
            line = ['']
            for col in ColumnRange(start.column,end.column):
                line.append(col)
            text.append('\t'.join(line))
        for row in xrange(start.row,end.row+1):
            line = []
            if include_columns_and_rows:
                line.append('%s' % row)
            for col in ColumnRange(start.column,end.column):
                value = self.render_cell(cell(col,row),
                                         eval_formulae=eval_formulae,
                                         apply_format=apply_format)
                if include_styles:
                    value = self.get_style(cell(col,row)).style(value)
                line.append("%s" % value)
            text.append('\t'.join(line))
        return '\n'.join(text)

class XLSStyle:
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

    """
    def __init__(self,bold=False,color=None,bgcolor=None,wrap=False,
                 border=None,number_format=None,font_size=None,centre=False,
                 shrink_to_fit=False):
        """Create a new XLSStyle object

        The available arguments are the same as the attributes.

        """
        self.bold=bold
        self.color=color
        self.bgcolor=bgcolor
        self.wrap=wrap
        self.border=border
        self.number_format=number_format
        self.font_size = font_size
        self.centre = centre
        self.shrink_to_fit = shrink_to_fit

    def style(self,item):
        """Wrap 'item' with <style...>...</style> tags

        Given a string (or object that can be rendered as a string)
        return the string representation surrounded by <style...>
        </style> tags, where the tag attributes describe the style
        information stored in the XLSStyle object:

        font=bold
        color=(color)
        bgcolor=(color)
        wrap
        border=(border)
        number_format=(format)
        font_size=(size)
        centre
        shrink_to_fit

        """
        style = []
        if self.bold:
            style.append("font=bold")
        if self.color is not None:
            style.append("color=%s" % self.color)
        if self.bgcolor is not None:
            style.append("bgcolor=%s" % self.bgcolor)
        if self.wrap:
            style.append("wrap")
        if self.border is not None:
            style.append("border=%s" % self.border)
        if self.number_format is not None:
            style.append("number_format=%s" % self.excel_number_format)
        if self.font_size is not None:
            style.append("font_size=%s" % self.font_size)
        if self.centre:
            style.append("centre")
        if self.shrink_to_fit:
            style.append("shrink_to_fit")
        if style:
            return "<style %s>%s</style>" % (' '.join(style),item)
        else:
            return item

    @property
    def excel_number_format(self):
        """Return an Excel-style equivalent of the stored number format

        Returns an Excel-style number format, or None if the format
        isn't set or is unrecognised.

        """
        if self.number_format == NumberFormats.THOUSAND_SEPARATOR:
            return "#,###"
        elif self.number_format == NumberFormats.PERCENTAGE:
            return "0.0%"
        return None

class ColumnRange(Iterator):
    """Iterator for a range of column indices

    Range-style iterator for iterating over alphabetical column
    indices, e.g.

    >>> for c in ColumnRange('A','Z'):
    ...   print c

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
        self.incr = 1
        if j is None:
            self.start = column_index_to_integer('A')
            self.end = column_index_to_integer(i)
        else:
            self.start = column_index_to_integer(i)
            self.end = column_index_to_integer(j)
        if reverse:
            self.end,self.start = self.start,self.end
            self.incr = -1
        self.column = self.start-self.incr
        if include_end:
            self.end += self.incr

    def next(self):
        """Implements Iterator subclass 'next' method

        """
        self.column = self.column + self.incr
        if self.column == self.end:
            raise StopIteration
        return column_integer_to_index(self.column)

class CellIndex:
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
        self.idx = str(idx)
        try:
            r = re.compile(r'^([A-Z]+)([0-9]+)$').match(idx)
            self.column = r.group(1)
            self.row = int(r.group(2))
        except:
            self.column = None
            self.row = None
            if str(idx).isalpha():
                self.column = idx
            elif str(idx).isdigit():
                self.row = int(idx)

    @property
    def is_full(self):
        """Return True if index has both column and row information

        """        
        return not (self.column is None or self.row is None)

    def __repr__(self):
        """Implement __repr__ built-in; returns cell index

        """
        return "%s%s" % ('' if self.column is None else self.column,
                         '' if self.row is None else self.row)

class XLSColumn:
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
        self.index = column_index
        self.parent = parent

    def __setitem__(self,idx,value):
        """Implement set item i.e. x['key'] = value

        """
        self.parent[self.full_index(idx)] = value

    def __getitem__(self,idx):
        """Implement get item i.e. y['key'] returns value

        """
        try:
            return self.parent[self.full_index(idx)]
        except Exception,ex:
            return None

    def full_index(self,row):
        """Return the full index for a cell in the column

        Given a row index, returns the index of the cell
        that this addresses within the column (e.g. if the
        column is 'A' then row 2 addresses cell 'A2').

        """
        return cell(self.index,row)

#######################################################################
# Functions
#######################################################################

def cmp_column_indices(x,y):
    """Comparision function for column indices

    x and y are XLS-style column indices e.g. 'A', 'B', 'AA' etc.

    Returns -1 if x is a column index less than y, 1 if it is
    greater than y, and 0 if it's equal.

    """
    # Do string comparision on reverse of column indices
    return cmp(x[::-1],y[::-1])

def cell(col,row):
    """Return XLS cell index for column and row

    E.g. cell('A',3) returns 'A3'

    """
    return "%s%s" % (col,row)

def incr_col(col,incr=1):
    """Return column index incremented by specific number of positions

    Arguments:
      col: index of column to be incremented
      incr: optional, number of cells to shift by. Can be negative
        to go backwards. Defaults to 1 i.e. next column along.

    """
    return column_integer_to_index(column_index_to_integer(col)+incr)

def column_index_to_integer(col):
    """Convert XLS-style column index into equivalent integer

    Given a column index e.g. 'A', 'BZ' etc, converts it
    to the integer equivalent using zero-based counting
    system (so 'A' is equivalent to zero, 'B' to 1 etc).

    """
    # Convert column index e.g. 'A', 'BZ' etc to
    # integer equivalent
    idx = 0
    i = 0
    for c in col[::-1]:
        idx = idx + pow(26,i)*(ord(c)-64)
        i += 1
    return idx-1

def column_integer_to_index(idx):
    """Convert integer column index to XLS-style equivalent

    Given an integer index, converts it to the XLS-style
    equivalent e.g. 'A', 'BZ' etc, using a zero-based
    counting system (so zero is equivalent to 'A', 1 to 'B'
    etc).

    """
    # Convert integer column to index equivalent
    col = ''
    while idx >= 0:
        col += chr((idx%26)+65)
        idx = idx/26-1
    return col[::-1]

def eval_formula(item,worksheet):
    """Evaluate a formula using the contents of a worksheet

    Given an item, attempts an Excel-style evaluation.

    If the item doesn't start with '=' then it is returned as-is.
    Otherwise the function attempts to evaluate the formula,
    including looking up (and if necessary also evaluating) the
    contents of any cells that are referenced.

    *** Note that the implementation of the evaluation is very
        simplistic and cannot handle complex formulae or functions

    Currently it can only deal with:

    * basic mathematical operations (+-*/)

    """
    # Evaluate a formula from a cell item and return the computed value
    logging.debug("Item is %s" % item)
    if item.startswith('='):
        item = item[1:]
        logging.debug("Item reset to %s" % item)
    else:
        logging.debug("Returning %s" % item)
        return item
    ops = "+-/*"
    formula = ''
    arg = ''
    nargs = 0
    for c in item:
        logging.debug(c)
        if c not in ops:
            arg += c
        else:
            logging.debug("-> %s" % arg)
            if CellIndex(arg).is_full:
                arg = worksheet.render_cell(arg,eval_formulae=True)
            logging.debug("-> %s" % arg)
            try:
                arg = convert_to_number(arg) 
                if c == '/':
                    arg = float(arg)
            except ValueError:
                # Failed to convert to number
                logging.debug("Error converting %s to number" % arg)
                return BAD_REF
            formula = formula + str(arg) + c
            nargs += 1
            arg = ''
            logging.debug("-> %s" % formula)
    # End of string
    if CellIndex(arg).is_full:
        arg = worksheet.render_cell(arg,eval_formulae=True)
    if nargs:
        try:
            arg = convert_to_number(arg)
        except ValueError:
            # Failed to convert to float
            logging.debug("Error converting %s to number" % arg)
            return BAD_REF
    else:
        # Single value was referenced
        try:
            return convert_to_number(arg)
        except ValueError:
            return arg
    formula = formula + str(arg)
    logging.debug("Formula '%s'" % formula)
    if re.compile(r"^[0-9+\-\/\*]+").match(formula):
        try:
            item = eval(formula)
        except Exception,ex:
            logging.debug("Error processing %s: %s" % (item,ex))
            return BAD_REF
    else:
        item = formula
    return item

def convert_to_number(s):
    """Convert a number to float or int as appropriate

    Raises ValueError if neither conversion is possible.

    """
    if is_int(s):
        return int(s)
    elif is_float(s):
        return float(s)
    raise ValueError,"%s not a number?" % s

def is_float(s):
    """Test if a number is a float
    """
    try:
        return str(float(s)) == s
    except ValueError:
        return False

def is_int(s):
    """Test if a number is an integer
    """
    try:
        return str(int(s)) == s
    except ValueError:
        return False

def format_value(value,number_format=None):
    """Format a cell value based on the specified number format

    """
    logging.debug("format_value: %s (%s) %s" % (value,type(value),number_format))
    if number_format is None:
        return str(value)
    if number_format == NumberFormats.PERCENTAGE:
        # Convert to percentage
        logging.debug("Percentage")
        return "%.1f%%" % (float(value) * 100.0)
    if number_format == NumberFormats.THOUSAND_SEPARATOR:
        # Add thousands separator
        i = int(value)
        value = []
        while i >= 1000:
            value.append("%03d" % (i%1000))
            i = i/1000
        value.append(str(i))
        value = value[::-1]
        return ','.join(value)
    # Unknown, do nothing
    return str(value)

#######################################################################
# Example usage
#######################################################################

if __name__ == "__main__":
    wb = XLSWorkBook("Test")

    wb.add_work_sheet('test')
    wb.add_work_sheet('test2')
    wb.add_work_sheet('data',"Data")
    print "%s" % wb.worksheet['test'].title
    print "%s" % wb.worksheet['test2'].title
    print "%s" % wb.worksheet['data'].title

    data = wb.worksheet['data']
    data['A1'] = "Column 1"
    print "%s" % data['A1']
    print "%s" % data['A2']
    print "%s" % data['A']['1']
    data['A']['1'] = "Updated value"
    print "%s" % data['A1']

    data['B']['12'] = "Another value"
    data['Z']['5'] = "And another"
    data['AZ']['3'] = "Yet another"
    data['AB']['3'] = "And another again"
    
    print "%s,%s" % (data.columns,data.rows)

    print data.render_as_text(include_columns_and_rows=True,
                              eval_formulae=True,
                              include_styles=True)

    print data.render_as_text(start='B1',end='C6',include_columns_and_rows=True)

    wb.save_as_xls('test.xls')
                               
