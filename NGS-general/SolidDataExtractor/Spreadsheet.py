#     Spreadsheet.py: write simple Excel spreadsheets
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# Spreadsheet.py
#
#########################################################################

"""Spreadsheet

Provides a Spreadsheet class for writing data to an Excel spreadsheet,
using the xlrd, xlwt and xlutils modules.

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

import os

#######################################################################
# Class definitions
#######################################################################

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
        self.workbook = xlwt.Workbook()
        self.name = name
        if not os.path.exists(self.name):
            # New spreadsheet
            self.sheet = self.workbook.add_sheet(title)
            self.current_row = 0
        else:
            # Already exists
            rb = xlrd.open_workbook(self.name,formatting_info=True)
            rs = rb.sheet_by_index(0)
            self.workbook = xlutils.copy.copy(rb)
            self.sheet = self.workbook.get_sheet(0)
            self.current_row = rs.nrows

    def addTitleRow(self,headers):
        """Add a title row to the spreadsheet.

        Arguments:
          headers: list of titles to be added.

        Returns:
          Integer index of row just written
        """
        self.headers = headers
        self.current_row += 1
        cindex = 0
        return self.addRow(headers)

    def addEmptyRow(self):
        """Add an empty row to the spreadsheet.

        This just advances the row index by one, effectively
        appending an empty row.

        Returns:
          Integer index of (empty) row just written
        """
        self.current_row += 1
        return self.current_row

    def addRow(self,data):
        """Add a row of data to the spreadsheet.

        Arguments:
          data: list of data items to be added.

        Returns:
          Integer index of row just written
        """
        self.current_row += 1
        cindex = 0
        for item in data:
            if str(item).startswith('='):
                # Formula
                print "Formulae not implemented"
                # Formula example code
                #
                #sheet.write(2,3,xlwt.Formula('%s/%s*100' %
                #                  (rowcol_to_cell(2,2),rowcol_to_cell(2,1))))
                #
                self.sheet.write(self.current_row,cindex_item)
            else:
                # Data
                self.sheet.write(self.current_row,cindex,item)
            cindex += 1
        return self.current_row

    def write(self):
        """Write the spreadsheet to file.
        """
        self.workbook.save(self.name)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Example writing spreadsheet
    wb = Spreadsheet('test.xls','test')
    wb.addTitleRow(['File','Total reads','Unmapped reads'])
    wb.addEmptyRow()
    wb.addRow(['DR_1',875897,713425])
    wb.write()

