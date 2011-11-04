#     Spreadsheet.py: write simple Excel spreadsheets
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# Spreadsheet.py
#
#########################################################################

"""Spreadsheet

Provides a Workbook class for writing data to an Excel spreadsheet, using
the xlrd, xlwt and xlutils modules.

These can be found at:
http://pypi.python.org/pypi/xlwt/0.7.2
http://pypi.python.org/pypi/xlrd/0.7.1
http://pypi.python.org/pypi/xlutils/1.4.1

xlutils also needs functools:
http://pypi.python.org/pypi/functools

but if you're using Python<2.5 then you need a backported version of
functools, try:
https://github.com/dln/pycassa/blob/90736f8146c1cac8287f66e8c8b64cb80e011513/pycassa/py25_functools.py
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import xlwt, xlrd
import xlutils, xlutils.copy
from xlwt.Utils import rowcol_to_cell
from xlwt import easyxf

import os
import re
import logging

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
            if self.name:
                logging.warning("Specified XLS file '%s' not found" %
                                self.name)
        else:
            # Spreadsheet already exists - convert into an xlwt workbook
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
        raise KeyError, "No sheet called '%s' found" % title

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
            logging.warning("Overwriting existing file: '%s'" % xls_name)
        self.workbook.save(xls_name)

class Worksheet:
    """Class for writing to a sheet in an XLS spreadsheet.

    A Worksheet object represents a sheet in an XLS spreadsheet.

    Once created, data can be appended to the worksheet in a variety of
    ways:

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

    Formulae can also be added in a simple row-wise format: items of the form
    e.g.

      =A+B

    will be converted to add the row index (e.g. =A1+B1, =A2+B2) etc.

    Individual items can have basic styles applied to them by wrapping them
    in <style ...>...</style> tags. Within the leading style tag the following
    attributes can be specified:
    
    font=bold (sets bold face)
    bgcolor=<color> (sets the background colour)
    wrap (specifies that text should wrap)

    For example <style font=bold bgcolor=gray25>...</style>
    """

    def __init__(self,workbook,title,xlrd_index=None,xlrd_sheet=None):
        """Create a new Worksheet instance.

        Arguments:
          workbook: 'parent' xlwt.workbook instance
          title: title text for the sheet
          xlrd_index: (optional, but must accompany xlrd_sheet if supplied)
            index for the sheet in the parent workbook
          xlrd_sheet: (optional, but must accompany xlrd_sheet if supplied)
            xlrd.worksheet instance
        """
        self.title = title
        self.workbook = workbook
        if xlrd_index is None and xlrd_sheet is None:
            # New worksheet
            self.is_new = True
            self.worksheet = self.workbook.add_sheet(title)
            self.current_row = -1
            self.ncols = 0
        else:
            # Existing worksheet
            self.is_new = False
            self.worksheet = self.workbook.get_sheet(xlrd_index)
            self.current_row = xlrd_sheet.nrows - 1
            self.ncols = xlrd_sheet.ncols
        self.data = []
        # Regular expressions for format tags
        self.re_style = re.compile(r"^<style +([^>]*)>(.*)</style>$")
        # Generate and store styles
        self.styles = Styles()
        # Maximum column widths
        self.max_col_width = []

    def addTabData(self,rows):
        """Write a list of tab-delimited data rows to the sheet.

        Given a list of rows with tab-separated data items,
        write the data to the worksheet.

        Arguments:
          data: Python list representing rows of tab-separated
            data items
        """
        for row in rows:
            self.data.append(row)
            self.ncols = max(self.ncols,len(row.split('\t')))
        if self.ncols > 256:
            logging.warning("Number of columns exceeds 256")

    def addText(self,text):
        """Write text to the sheet.
        """
        return self.addTabData(text.split('\n'))

    def insertColumn(self,position,insert_items=None,title=''):
        """Insert a new column into the spreadsheet.
        
        This inserts a new column into each row of data, at the
        specified positional index (starting from 0).

        If insert_item starts with '=' then it's interpreted as a row-wise
        formula. Formulas can be written in the form e.g. "=A+B-C", where
        the letters indicate columns in the final XLS spreadsheet. When the
        formulae are written they are expanded to include the row number
        e.g. "=A1+B1-C1", "A2+B2-C2" etc.

        Note: at present columns can only be inserted into new sheets.

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
        insert_title = True
        # Loop over rows
        for i in range(len(self.data)):
            row = self.data[i]
            items = row.split('\t')
            new_items = []
            for j in range(len(items)):
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
                                insert_item = insert_items[j-1]
                            except IndexError:
                                # Ran out of items?
                                insert_item = ''
                        else:
                            insert_item = insert_items
                        new_items.append(insert_item)
                # Append the existing row data
                new_items.append(items[j])
            # Replace old row with new one
            self.data[i] = '\t'.join(new_items)
        # Finished successfully
        return True

    def getColumnId(self,name):
        """Lookup XLS column id from name of column.

        If there is no data, or if the name isn't in the header
        row of the data, then an exception is raised.

        Returns the column identifier (i.e. 'A', 'B' etc) for the
        column with the matching name.
        """
        try:
            i = self.data[0].split('\t').index(name)
            return string.uppercase[i]
        except IndexError:
            # Column name not found
            raise IndexError, "Column '%s' not found" % name

    def save(self):
        """Write the new data to the spreadsheet.
        """
        for row in self.data:
            self.current_row += 1
            cindex = 0
            for item in row.split('\t'):
                if str(item).startswith('='):
                    # Formula item
                    substitute_row = False
                    formula = ''
                    for c in item[1:]:
                        if c.isalpha() and c.isupper():
                            formula += c
                            substitute_row = True
                        elif c == '?' and substitute_row:
                            # Add the row number afterwards
                            # NB xlwt takes row numbers from zero,
                            # while XLS starts from 1
                            formula += str(self.current_row+1)
                        else:
                            formula += c
                            substitute_row = False
                    self.worksheet.write(self.current_row,cindex,
                                         xlwt.Formula(formula))
                else:
                    # Data item
                    #
                    # Extract formatting data for individual items
                    bold = False
                    bg_color = None
                    wrap = False
                    style_match = self.re_style.match(item)
                    if style_match:
                        item = style_match.group(2)
                        styles = style_match.group(1)
                        for style in styles.split(' '):
                            if style.strip().startswith('bgcolor='):
                                bg_color = style.split('=')[1].strip()
                            elif style.strip() == 'font=bold':
                                bold = True
                            elif style.strip() == 'wrap':
                                wrap = True
                    # Get the easy_xf object for the styling
                    style = self.styles.getXfStyle(bold=bold,bg_color=bg_color,
                                                   wrap=wrap)
                    self.worksheet.write(self.current_row,cindex,item,style)
                    # Set the column widths
                    try:
                        if len(item) > self.max_col_width[cindex]:
                            self.max_col_width[cindex] = len(item)
                    except IndexError:
                        self.max_col_width.append(len(item))
                    self.worksheet.col(cindex).width = \
                        256*(self.max_col_width[cindex] + 5)
                cindex += 1
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

    def getXfStyle(self,bold=False,wrap=False,bg_color=None):
        """Return EasyXf object to apply styles to spreadsheet cells.

        Arguments:
          bold: indicate whether font should be bold face
          wrap: indicate whether text should wrap in the cell
          bg_color: set colo(u)r for cell background. Must be a valid
           color name as recognised by xlwt.
        """
        # Make a key to represent the style
        style_key = "%s:%s:%s" % (bold,wrap,bg_color)

        # Check whether we already have an EasyXf object for this
        try:
            return self.styles[style_key]
        except KeyError:
            # Style not found
            pass
        # Create the style
        style = {'font': [],
                 'alignment': [],
                 'pattern': []}
        if bold:
            style['font'].append('bold True');
        if wrap:
            style['alignment'].append('wrap True')
        if bg_color:
            style['pattern'].append('pattern solid')
            style['pattern'].append('fore_color %s' % bg_color)
        # Build easyfx object to apply styles
        easyxf_style = ''
        for key in style.keys():
            if style[key]:
                easyxf_style += '%s: ' % key
                easyxf_style += ', '.join(style[key])
                easyxf_style += '; '
        try:
            xf_style = easyxf(easyxf_style)
        except xlwt.Style.EasyXFCallerError, ex:
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

#######################################################################
# Functions
#######################################################################

# No functions defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Example writing XLS with Spreadsheet class
    if os.path.exists('test.xls'):
        os.remove('test.xls')
    wb = Spreadsheet('test.xls','test')
    wb.addTitleRow(['File','Total reads','Unmapped reads'])
    wb.addEmptyRow()
    wb.addRow(['DR_1',875897,713425])
    wb.write()
    # Example writing new XLS with Workbook class
    wb = Workbook()
    ws = wb.addSheet('test1')
    ws.addText("Hello\tGoodbye\nGoodbye\tHello")
    wb.save('test2.xls')
    # Example appending to existing XLS with Workbook class
    wb = Workbook('test2.xls')
    ws = wb.getSheet('test1')
    ws.addText("Some more data for you")
    ws = wb.addSheet('test2')
    ws.addText("<style font=bold bgcolor=gray25>Hahahah</style>")
    wb.save('test3.xls')

