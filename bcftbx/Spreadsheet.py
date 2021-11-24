#     Spreadsheet.py: write simple Excel spreadsheets
#     Copyright (C) University of Manchester 2011-2019 Peter Briggs
#
########################################################################
#
# Spreadsheet.py
#
#########################################################################

"""
Provides classes for writing data to an Excel spreadsheet, using the 3rd party modules
xlrd, xlwt and xlutils.

The basic classes are 'Workbook' (representing an XLS spreadsheet) and 'Worksheet'
(representing a sheet within a workbook). There is also a 'Spreadsheet' class which is
built on top of the other two classes and offers a simplified interface to writing
line-by-line XLS spreadsheets.

Simple usage examples
---------------------

1. Writing a new XLS spreadsheet using the Workbook class

>>> wb = Workbook()
>>> ws = wb.addSheet('test1')
>>> ws.addText("Hello\tGoodbye\nGoodbye\tHello")
>>> wb.save('test2.xls')

2. Appending to an existing XLS spreadsheet using the Workbook class

>>> wb = Workbook('test2.xls')
>>> ws = wb.getSheet('test1')
>>> ws.addText("Some more data for you")
>>> ws = wb.addSheet('test2')
>>> ws.addText("<style font=bold bgcolor=gray25>Hahahah</style>")
>>> wb.save('test3.xls')

3. Creating or appending to an XLS spreadsheet using the Spreadsheet class

>>> wb = Spreadsheet('test.xls','test')
>>> wb.addTitleRow(['File','Total reads','Unmapped reads'])
>>> wb.addEmptyRow()
>>> wb.addRow(['DR_1',875897,713425])
>>> wb.write()

Module constants
----------------

MAX_LEN_WORKSHEET_TITLE: maximum length allowed by xlwt for worksheet titles
MAX_LEN_WORKSHEET_CELL_VALUE: maximum number of characters allowed for cell value
MAX_NUMBER_ROWS_PER_WORKSHEET: maximum number of rows allowed per worksheet by xlwt

Dependencies
------------

The Spreadsheet module depends on the xlwt, xlrd and xlutils libraries which
can be found at:

* http://pypi.python.org/pypi/xlwt/0.7.2
* http://pypi.python.org/pypi/xlrd/0.7.1
* http://pypi.python.org/pypi/xlutils/1.4.1

Note that xlutils also needs functools:
http://pypi.python.org/pypi/functools

but if you're using Python<2.5 then you need a backported version of
functools, try:

https://github.com/dln/pycassa/blob/90736f8146c1cac8287f66e8c8b64cb80e011513/pycassa/py25_functools.py

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import re
import logging
try:
    # Python 3
    from string import ascii_uppercase
except ImportError:
    # Fallback for Python 2
    from string import uppercase as ascii_uppercase

import xlwt, xlrd
import xlutils, xlutils.copy
from xlwt.Utils import rowcol_to_cell
from xlwt import easyxf

#######################################################################
# Constants
#######################################################################

# Maximum length for worksheet title allowed by xlwt
MAX_LEN_WORKSHEET_TITLE = 31

# Maximum number of characters allowed for cell value
MAX_LEN_WORKSHEET_CELL_VALUE = 250

# Maximum number of rows allowed per worksheet by xlwt
MAX_NUMBER_ROWS_PER_WORKSHEET = 65536

#######################################################################
# Class definitions
#######################################################################

class Workbook:
    """Class for writing data to an XLS spreadsheet.

    A Workbook represents an XLS spreadsheet, which conists of sheets
    (represented by Worksheet instances).
    """

    def __init__(self,xls_name=''):
        """Create a new Workbook instance.

        If the name of an existing XLS file is specified then the new
        content will be appended to whatever is already in that
        spreadsheet (note that the original spreadsheet will only be
        overwritten if the same name is provided in the 'save' method).
        Otherwise a new (empty) spreadsheet will be created.
        """
        self.name = xls_name
        self.sheets = []
        if not os.path.exists(self.name):
            # New spreadsheet
            self.workbook = xlwt.Workbook()
        else:
            # Spreadsheet already exists - convert into an xlwt workbook
            logging.warning("Appending to XLS file '%s'" % self.name)
            rb = xlrd.open_workbook(self.name,formatting_info=True)
            self.workbook = xlutils.copy.copy(rb)
            # Collect the sheets in the workbook
            i = 0
            for s in rb.sheets():
                logging.debug("Adding existing sheet: '%s'" % s.name)
                sheet = self.addSheet(s.name,xlrd_sheet=s,xlrd_index=i)
                i += 1

    def addSheet(self,title,xlrd_sheet=None,xlrd_index=None):
        """Add a new sheet to the spreadsheet.

        Arguments:
          title: title for the sheet
          xlrd_sheet: (optional) an xlrd sheet from an existing XLS
            workbook.
        """
        # Check if a sheet with this name already exists
        logging.debug("Adding sheet '%s'" % title)
        if xlrd_index is None and xlrd_sheet is None:
            try:
                ws = self.getSheet(title)
                logging.warning("Sheet called '%s' already exists" % title)
                return ws
            except KeyError:
                # Not found
                ws = Worksheet(self.workbook,title)
        else:
            # Sheet already exists from original XLS
            ws = Worksheet(self.workbook,title,xlrd_sheet=xlrd_sheet,
                           xlrd_index=xlrd_index)
        self.sheets.append(ws)
        return ws

    def getSheet(self,title):
        """Retrieve a sheet from the spreadsheet.
        """
        for s in self.sheets:
            logging.debug("Searching: sheet '%s'" % s.title)
            if title == s.title: return s
        raise KeyError("No sheet called '%s' found" % title)

    def save(self,xls_name):
        """Finish adding data and write the spreadsheet to disk.

        Note that for a spreadsheet based on an existing XLS file, this
        doesn't have to be the same name.

        Arguments:
          xls_name: the file name to write the spreadsheet to. Note that if a
            file already exists with this name then it will be overwritten.
        """
        # Write data for each sheet
        for s in self.sheets:
            s.save()
        # Save workbook
        if os.path.exists(xls_name):
            logging.debug("Overwriting existing file: '%s'" % xls_name)
        self.workbook.save(xls_name)

class Worksheet:
    """Class for writing to a sheet in an XLS spreadsheet.

    A Worksheet object represents a sheet in an XLS spreadsheet.

    Adding data
    ------------

    Data can be inserted into the worksheet in a variety of ways:

    * addTabData: a Python list of tab-delimited lines; each line forms a
      line in the output XLS, with each field forming a column.

    * addText: a string representing arbitrary text, with newlines delimiting
      lines and tabs (if any) in each line delimiting fields.

    Each can be called multiple times in any order on the same spreadsheet
    before it is saved, and the data will be appended.

    For new Worksheet objects (i.e. those which weren't read from a
    pre-existing XLS file), it is also possible to insert new columns:

    * insertColumn: if a single value is specified then all columns are filled
      with that value; alternatively a list of values can be supplied which
      are written one-per-row.

    Formulae
    --------

    Formulae can be specified using a variation on Excel's '=' notation, e.g.

      =A1+B2

    adds the values from cells A1 and B2 in the final spreadsheet.

    Formulae are written directly as supplied unless they contain special
    characters '?' (indicates the current line number) or '#' (indicates the
    current column).

    Using '?' allows simple row-wise formulae to be added, e.g.

      =A?+B?

    will be converted to substitute the row index (e.g. '=A1+B1' for row 1,
    '=A2+B2' for row 2 etc).

    Using '#' allows simple column-wise formulae to be added, e.g.

      =#1-#2

    will be converted to substitue the column id (e.g. '=A1-A2' for column A,
    '=B1-B2' for column B etc).

    Note that the substitution occurs when the spreadsheet is saved.

    Styles
    ------

    Individual items can have basic styles applied to them by wrapping them
    in <style ...>...</style> tags. Within the leading style tag the following
    attributes can be specified:
    
    font=bold (sets bold face)
    color=<color> (sets the text colour)
    bgcolor=<color> (sets the background colour)
    border=<style> (sets the cell border style to 'thin', 'medium', 'thick' etc)
    wrap (specifies that text should wrap)
    number_format=<format_string> (specifies how to display numbers, see below)
    font_height=<height> (sets font size in points)
    centre (specifies that text should be centred)
    shrink_to_fit (specifies that cells should shrink to fit their contents)

    For example <style font=bold bgcolor=gray25>...</style>

    Note that styles can also be applied to formulae.

    Number display formats
    ----------------------

    The 'number_format' style attribute allows the calling program to specify how
    numbers should be displayed, for example:

    number_format=0.00 (displays values to 2 decimal places)
    number_format=0.0% (displays values as percentages to 1 decimal place)
    number_format=#,### (displays values with , as the delimiter for thousands)

    Internal representation
    -----------------------

    The spreadsheet data is held internally as a list of rows, with each row
    represented by a tab-delimited string.
    """

    def __init__(self,workbook,title,xlrd_index=None,xlrd_sheet=None):
        """Create a new Worksheet instance.

        Note that xlwt imposes a limit of the length of title strings; if
        the supplied title exceeds this limit then the title will be
        truncated.

        Arguments:
          workbook: 'parent' xlwt.workbook instance
          title: title text for the sheet
          xlrd_index: (optional, but must accompany xlrd_sheet if supplied)
            index for the sheet in the parent workbook
          xlrd_sheet: (optional, but must accompany xlrd_sheet if supplied)
            xlrd.worksheet instance
        """
        self.title = title
        if len(self.title) > MAX_LEN_WORKSHEET_TITLE:
            # Truncate too-long title string
            self.title = self.title[:MAX_LEN_WORKSHEET_TITLE]
            logging.warning("Worksheet title > %d characters" % MAX_LEN_WORKSHEET_TITLE)
            logging.warning("Truncated to '%s'" % self.title)
        self.workbook = workbook
        if xlrd_index is None and xlrd_sheet is None:
            # New worksheet
            self.worksheet = self.workbook.add_sheet(self.title)
            self.is_new = True
            self.current_row = -1
            self.ncols = 0
        else:
            # Existing worksheet
            self.worksheet = self.workbook.get_sheet(xlrd_index)
            self.is_new = False
            self.current_row = xlrd_sheet.nrows - 1
            self.ncols = xlrd_sheet.ncols
        self.data = []
        # Regular expressions for format tags
        self.re_style = re.compile(r"^<style +([^>]*)>(.*)</style>$")
        # Generate and store styles
        self.styles = Styles()
        # Maximum column widths
        self.max_col_width = []
        # Freeze panes
        self.freeze_row = 0
        self.freeze_col = 0

    def addTabData(self,rows):
        """Write a list of tab-delimited data rows to the sheet.

        Given a list of rows with tab-separated data items,
        append the data to the worksheet.

        Arguments:
          data: Python list representing rows of tab-separated
            data items
        """
        for row in rows:
            self.data.append(row)
            # Update number of columns
            self.ncols = max(self.ncols,len(row.split('\t')))

    def addText(self,text):
        """Append and populate rows from text.

        Given some arbitrary text as a string, the data it contains
        will be appended to the worksheet using newlines to indicate
        multiple rows and tabs to delimit data items.

        This method is useful for turning tab-delimited data read
        from a CSV-type file into a spreadsheet.

        Arguments:
          text: a string representing the data to add: rows are
            delimited by newlines, and items by tabs
        """
        return self.addTabData(text.split('\n'))

    def insertColumn(self,position,insert_items=None,title=None):
        """Insert a new column into the spreadsheet.
        
        This inserts a new column into each row of data, at the
        specified positional index (starting from 0).

        Note: at present columns can only be inserted into worksheets that have
        been created from scratch via Worksheet class (i.e. cannot insert into
        an existing worksheet read in from a file).

        Arguments:
          position: positional index for the column to be inserted
            at (0=A, 1=B etc)
          title: (optional) value to be written to the first row (i.e. a column
            title)
          insert_items: value(s) to be inserted; either a single item, or a
            list of items. Each item can be blank, a constant value, or a
            formula.
        """
        if not self.is_new:
            logging.error("Cannot insert data into pre-existing worksheet")
            return False
        # Deal with row title and number of rows
        if title is None:
            # No explicit title, use first item in list
            if isinstance(insert_items,list):
                title = insert_items[0]
                nrows = max(len(self.data),len(insert_items))
            else:
                title = insert_items
                nrows = len(self.data)
            offset = 0
        else:
            # Title must be factored into row count
            if isinstance(insert_items,list):
                nrows = max(len(self.data),len(insert_items)+1)
            else:
                nrows = len(self.data)
            offset = -1
        # Loop over rows
        insert_title = True
        for i in range(nrows):
            # Split the existing row into items
            try:
                row = self.data[i]
                items = row.split('\t')
            except IndexError:
                # Ran out of rows in current worksheet
                items = []
            # Rebuild the row
            new_items = []
            for j in range(max(len(items),position+1)):
                # Insert appropriate item at this position
                if j == position:
                    if insert_title:
                        # Title for new column
                        new_items.append(title)
                        insert_title = False
                    else:
                        # Data item
                        if isinstance(insert_items,list):
                            try:
                                insert_item = insert_items[i+offset]
                            except IndexError:
                                # Ran out of items?
                                insert_item = ''
                        else:
                            insert_item = insert_items
                        new_items.append(insert_item)
                # Append the existing row data
                try:
                    new_items.append(items[j])
                except IndexError:
                    if j < position:
                        # Ran out of existing items, pad with blanks
                        new_items.append('')
            # Replace old row with new one
            row = '\t'.join([str(x) for x in new_items])
            try:
                self.data[i] = row
            except IndexError:
                self.data.append(row)
            # Update number of columns
            self.ncols = max(self.ncols,len(row.split('\t')))
        # Finished successfully
        return True

    def setCellValue(self,row,col,value):
        """Set the value of a cell

        Given row and column coordinates (using integer indices starting from zero
        for both), replace the existing value with a new one.

        The new value can include style information.

        Arguments:
          row: integer row index (starting at zero)
          col: integer column index (starting at zero, i.e. 0=A, 1=B etc)
          value: new value to be written into the cell
        """
        # First: add new (empty) rows if required
        while len(self.data) < row + 1:
            self.data.append('')
        # Then: extend the row if required
        new_row = self.data[row].split('\t')
        while len(new_row) < col + 1:
            new_row.append('')
        # Update number of columns
        self.ncols = max(self.ncols,len(new_row))
        # Insert the new value
        new_row[col] = str(value)
        new_row = '\t'.join(new_row)
        self.data[row] = new_row

    def getColumnId(self,name):
        """Lookup XLS column id from name of column.

        If there is no data, or if the name isn't in the header
        row of the data, then an exception is raised.

        Returns the column identifier (i.e. 'A', 'B' etc) for the
        column with the matching name.
        """
        try:
            i = self.data[0].split('\t').index(name)
            return self.column_id_from_index(i)
        except IndexError:
            # Column name not found
            raise IndexError("Column '%s' not found" % name)

    def freezePanes(self,row=None,column=None):
        """Split panes and mark as frozen

        'row' and 'column' are integer indices specifying the
        cell which defines the pane to be marked as frozen

        """
        self.freeze_row = int(row)
        self.freeze_col = int(column)

    def column_id_from_index(self,i):
        """Get XLS column id from index of column

        cindex is the zero-based column index (an integer); this
        method returns the matching XLS column identifier (i.e.
        'A', 'B', 'AA', 'BA' etc).

        """
        name = ''
        try:
            while i >= 0:
                name += ascii_uppercase[i%26]
                i = i//26-1
            return name[::-1]
        except IndexError as ex:
            print("Exception getting column name for index %d: %s" % (i,ex))
            raise ex

    def save(self):
        """Write the new data to the spreadsheet.
        """
        for row in self.data:
            self.current_row += 1
            cindex = 0
            for item in row.split('\t'):
                # Extract any formatting data for the item and
                # retrieve easy_xf object for styling
                bold = False
                color=None
                bg_color = None
                wrap = False
                border_style = None
                style_match = self.re_style.match(item)
                num_format_str = None
                font_size = None
                centre = False
                shrink_to_fit = False
                if style_match:
                    item = style_match.group(2)
                    styles = style_match.group(1)
                    for style in styles.split(' '):
                        if style.strip().startswith('bgcolor='):
                            bg_color = style.split('=')[1].strip()
                        elif style.strip().startswith('color='):
                            color = style.split('=')[1].strip()
                        elif style.strip() == 'font=bold':
                            bold = True
                        elif style.strip().startswith('border='):
                            border_style = style.split('=')[1].strip()
                        elif style.strip() == 'wrap':
                            wrap = True
                        elif style.strip().startswith('number_format='):
                            num_format_str = style.split('=')[1].strip()
                        elif style.strip().startswith('font_size='):
                            font_size = style.split('=')[1].strip()
                        elif style.strip() == 'centre':
                            centre = True
                        elif style.strip() == 'shrink_to_fit':
                            shrink_to_fit = True
                style = self.styles.getXfStyle(bold=bold,color=color,bg_color=bg_color,
                                               wrap=wrap,border_style=border_style,
                                               num_format_str=num_format_str,
                                               font_size=font_size,centre=centre,
                                               shrink_to_fit=shrink_to_fit)
                # Deal with the item
                if str(item).startswith('='):
                    # Formula item
                    # Remove leading '=' which xlwt doesn't want
                    formula = item[1:]
                    # Substitute '?' with current line number
                    # NB xlwt takes row numbers from zero,
                    # while XLS starts from 1
                    formula = formula.replace('?',str(self.current_row+1))
                    # Substitute '#' with current column
                    formula = formula.replace('#',self.column_id_from_index(cindex))
                    # Create the item
                    try:
                        item = xlwt.Formula(formula)
                    except Exception as ex:
                        logging.warning("Error writing formula '%s' to cell %s%s: %s",
                                        formula,
                                        self.column_id_from_index(cindex),
                                        self.current_row+1,
                                        ex)
                        item = "FORMULA_ERROR"
                else:
                    # Deal with a data item
                    # Attempt to convert to a number type i.e. integer/float
                    converted = str(item)
                    try:
                        # Try integer
                        converted = int(converted)
                    except ValueError:
                        # Not an integer, try float
                        try:
                            converted = float(converted)
                        except ValueError:
                            # Not a float, leave as a string BUT check
                            # the length
                            if len(converted) > MAX_LEN_WORKSHEET_CELL_VALUE:
                                logging.warning("Saving sheet '%s' (row %d, col %d)" %
                                                (self.title,self.current_row,cindex))
                                logging.warning("Truncating value '%s...' to %d characters" %
                                                (converted[:15],
                                                 MAX_LEN_WORKSHEET_CELL_VALUE))
                                converted = converted[:MAX_LEN_WORKSHEET_CELL_VALUE]
                    item = converted
                # Write the item to the current line
                try:
                    self.worksheet.write(self.current_row,cindex,item,style)
                    # Set the column widths
                    len_item = len(str(item))
                    try:
                        if len_item > self.max_col_width[cindex]:
                            self.max_col_width[cindex] = len_item
                    except IndexError:
                        self.max_col_width.append(len_item)
                    self.worksheet.col(cindex).width = \
                        256*(self.max_col_width[cindex] + 5)
                    cindex += 1
                except ValueError as ex:
                    logging.error("couldn't write item to sheet '%s' (row %d col %d)" %
                                  (self.title,self.current_row+1,cindex+1))
        # Freeze panes
        self.worksheet.set_horz_split_pos(self.freeze_row)
        self.worksheet.set_vert_split_pos(self.freeze_col)
        if self.freeze_row or self.freeze_col:
            self.worksheet.set_panes_frozen(True)
        # Update/reset the sheet properties etc
        self.data = []
        self.is_new = False
        # Finished
        return

class Styles:
    """Class for creating and caching EasyXfStyle objects.

    XLS files have a limit of 4,000 styles, so cache and reuse EasyXfStyle
    objects to avoid exceeding this limit.
    """
    def __init__(self):
        self.styles = {}

    def getXfStyle(self,bold=False,wrap=False,color=None,bg_color=None,
                   border_style=None,num_format_str=None,font_size=None,
                   centre=False,shrink_to_fit=False):
        """Return EasyXf object to apply styles to spreadsheet cells.

        Arguments:
          bold: indicate whether font should be bold face
          wrap: indicate whether text should wrap in the cell
          color: set text colo(u)r
          bg_color: set colo(u)r for cell background.
          border_style: set line type for cell borders (thin, medium, thick, etc)
          font_size: font size (in points)
          centre: centre the cell content horizontally
          shrink_to_fit: shrink cell to fit contents

        Note that colours must be a valid name as recognised by xlwt.
        """
        # Make a key to represent the style
        style_key = "%s:%s:%s:%s:%s:%s:%s:%s:%s" % \
            (bold,wrap,color,bg_color,border_style,num_format_str,
             font_size,centre,shrink_to_fit)

        # Check whether we already have an EasyXf object for this
        try:
            return self.styles[style_key]
        except KeyError:
            # Style not found
            pass
        # Create the style
        style = {'font': [],
                 'alignment': [],
                 'pattern': [],
                 'borders': []}
        if bold:
            style['font'].append('bold True');
        if wrap:
            style['alignment'].append('wrap True')
        if bg_color:
            style['pattern'].append('pattern solid')
            style['pattern'].append('fore_color %s' % bg_color)
        if color:
            style['font'].append('color %s' % color)
        if border_style:
            for border in ('left','right','top','bottom'):
                style['borders'].append('%s %s' % (border,border_style))
        if font_size:
            style['font'].append('height %s' % (int(font_size)*20))
        if centre:
            style['alignment'].append('horizontal centre')
        if shrink_to_fit:
            style['alignment'].append('shrink_to_fit True')
        # Build easyfx object to apply styles
        easyxf_style = ''
        for key in style.keys():
            if style[key]:
                easyxf_style += '%s: ' % key
                easyxf_style += ', '.join(style[key])
                easyxf_style += '; '
        try:
            xf_style = easyxf(easyxf_style,num_format_str=num_format_str)
        except xlwt.Style.EasyXFCallerError as ex:
            logging.warning("Unable to get style: '%s'" % ex)
            xf_style = easyxf()
        # Store and return
        self.styles[style_key] = xf_style
        return xf_style

class Spreadsheet:
    """Class for creating and writing a spreadsheet.

    This creates a very simple single-sheet workbook.
    """

    def __init__(self,name,title):
        """Create a new Spreadsheet instance.

        If the named spreadsheet already exists then any new
        data is appended to the it.

        Arguments:
          name: name of the XLS format spreadsheet to be created. 
          title: title for the new sheet.
        """
        self.workbook = Workbook(name)
        self.name = name
        self.headers = []
        try:
            self.sheet = self.workbook.getSheet(title)
        except KeyError:
            self.sheet = self.workbook.addSheet(title)

    def addTitleRow(self,headers):
        """Add a title row to the spreadsheet.

        The title row will have the font style set to bold for all
        cells.

        Arguments:
          headers: list of titles to be added.

        Returns:
          Integer index of row just written
        """
        header_line = []
        for item in headers:
            header_line.append("<style font=bold>%s</style>" % item)
        self.sheet.addText('\t'.join(header_line))

    def addEmptyRow(self,color=None):
        """Add an empty row to the spreadsheet.

        Inserts an empty row into the next position in the
        spreadsheet.

        Arguments:
          color: optional background color for the empty row

        Returns:
          Integer index of (empty) row just written
        """
        if not color:
            self.sheet.addText("")
        else:
            empty_row = []
            ncols = min(self.sheet.ncols,256)
            for i in range(ncols):
                empty_row.append("<style bgcolor=%s> </style>" % color)
            self.sheet.addText('\t'.join(empty_row))

    def addRow(self,data,set_widths=False,bold=False,wrap=False,bg_color=''):
        """Add a row of data to the spreadsheet.

        Arguments:
          data: list of data items to be added.

          set_widths: (optional) Boolean; if True then set the column
            width to the length of the cell contents for each cell
            in the new row

          bold: (optional) use bold font for cells

          wrap: (optional) wrap the cell content

          bg_color: (optional) set the background color for the cell

        Returns:
          Integer index of row just written
        """
        # Set up style attributes
        style_str = []
        if bold:
            style_str.append('font=bold')
        if wrap:
            style_str.append('wrap')
        if bg_color:
            style_str.append('bg_color=%' % bg_color)
        style_str = ' '.join(style_str)
        # Create line
        items = []
        for item in data:
            if style_str:
                items.append("<style %s>%s</style>" % (style_str,item))
            else:
                items.append(str(item))
        self.sheet.addText('\t'.join(items))

    def write(self):
        """Write the spreadsheet to file.
        """
        self.workbook.save(self.name)
