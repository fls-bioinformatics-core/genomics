# Example code for generating a spreadsheet in XLS format
# Currently unused

try:
    import xlwt
    from xlwt.Utils import rowcol_to_cell
except ImportError:
    print "Unable to import xlwt module (ignored)"

class SpreadSheet:
    """Class for creating and writing a spreadsheet.

    This creates a very simple single-sheet workbook.
    """

    def __init__(self,name,title):
        """Create a new SpreadSheet instance.

        name: name of the XLS format spreadsheet to be created. 
        title: title for the new sheet.
        """
        self.workbook = xlwt.Workbook()
        self.name = name
        self.sheet = self.workbook.add_sheet(title)
        self.current_row = 1

    def addTitleRow(self,headers):
        """Add a title row to the spreadsheet.

        headers: list of titles to be added.
        """
        self.headers = headers
        cindex = 0
        for item in headers:
            self.sheet.write(self.current_row,cindex,item)
            cindex += 1
        self.current_row += 1

    def addEmptyRow(self):
        """Add an empty row to the spreadsheet.

        This just advances the row index by one, effectively
        appending an empty row.
        """
        self.current_row += 1

    def addRow(self,data):
        """Add a row of data to the spreadsheet.

        data: list of data items to be added.
        """
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
        self.current_row += 1

    def write(self):
        """Write the spreadsheet to file.
        """
        self.workbook.save(self.name)

if __name__ == "__main__":
    # Example writing spreadsheet
    wb = SpreadSheet('test.xls','test')
    wb.addTitleRow(['File','Total reads','Unmapped reads'])
    wb.addEmptyRow()
    wb.addRow(['DR_1',875897,713425])
    wb.write()

