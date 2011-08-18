#!/bin/env python
#
#     macs_to_XLS.py: Convert MACS output file to XLS spreadsheet
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# macs_to_XLS.py
#
#########################################################################

"""macs_to_XLS.py

Convert MACS output file to XLS spreadsheet"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import string
import xlwt

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Functions
#######################################################################

def write_data_to_sheet(worksheet,data):
    """Write a list of data to an xlwt sheet

    Given a list of rows with tab-separated data items,
    write the data to an xlwt worksheet.

    Arguments:
      worksheet: an xlwt.Workbook object (i.e. XLS worksheet)
      data: Python list representing rows of tab-separated
        data items
    """
    rindex = 0
    for line in data:
        cindex = 0
        for item in line.split('\t'):
            if str(item).startswith('='):
                # Formula item
                formula = ''
                for c in item[1:]:
                    formula += c
                    if c.isalpha() and c.isupper:
                        # Add the row number afterwards
                        # NB xlwt takes row numbers from zero,
                        # while XLS starts from 1
                        formula += str(rindex+1)
                ##print "%s" % formula
                worksheet.write(rindex,cindex,xlwt.Formula(formula))
            else:
                # Data item
                worksheet.write(rindex,cindex,item)
            cindex += 1
        rindex += 1

def get_column_id(data,name):
    """Lookup XLS column id from name of column

    If there is no data, or if the name isn't in the header
    row of the data, then an exception is raised.
    """
    i = data[0].split('\t').index(name)
    return string.uppercase[i]

def insert_column_into_data(data,position,title='',insert_item=''):
    """Insert a column into a list of data

    This inserts a new column into each row of data, at the
    specified positional index (starting from 0).

    If insert_item starts with '=' then it's interpreted as a row-wise
    formula. Formulas can be written in the form e.g. "=A+B-C", where
    the letters indicate columns in the final XLS spreadsheet. When the
    formulae are written they are expanded to include the row number
    e.g. "=A1+B1-C1", "A2+B2-C2" etc.

    Arguments:
      data: Python list representing rows of tab-separated data items
      position: positional index for the column to be inserted
        at (0=A, 1=B etc)
      title: value to be written to the first row (i.e. a column
        title)
      insert_item: value to be inserted; can be blank, a constant
        value, or a formula.
    """
    insert_title = True
    new_data = []
    # Loop over rows
    for line in data:
        items = line.split('\t')
        new_items = []
        for i in range(len(items)):
            # Insert appropriate item at this position
            if i == position:
                if insert_title:
                    # Title for new column
                    new_items.append(title)
                    insert_title = False
                else:
                    # Data item
                    new_items.append(insert_item)
            new_items.append(items[i])
        new_data.append('\t'.join(new_items))
    return new_data

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Get input file name
    if len(sys.argv) != 2:
        print "Usage: %s <macs_file>" % sys.argv[0]
        sys.exit(1)
    macs_in = sys.argv[1]

    # Build output file name
    # XLS_<input_name>.xls
    # Note that MACS output file might already have an .xls extension
    # but we'll add an explicit .xls extension
    xls_out = "XLS_"+os.path.splitext(os.path.basename(macs_in))[0]+".xls"
    print "Input file: %s" % macs_in
    print "Output XLS: %s" % xls_out

    # Read in the MACS file and split into header and data
    header = []
    data = []
    fp = open(macs_in,'r')
    for line in fp:
        # Strip trailing newlines
        line0 = line.strip('\n')
        if line0.strip() == '':
            # Skip empty lines
            pass
        elif line0.startswith('#'):
            # Header line
            header.append(line0)
        else:
            # Data line
            if not data:
                # First line of data: prepend with '#'
                line0 = '#'+line0
            data.append(line0)
    fp.close()

    # Insert formulae columns
    #
    # Summit-100 = ("start"+"summit" columns) - 100
    data = insert_column_into_data(data,3,
                                   title="summit-100",
                                   insert_item="=(B+G)-100")
    # Summit+100 = ("start"+"summit" columns) + 100
    data = insert_column_into_data(data,4,
                                   title="summit+100",
                                   insert_item="=(B+G)+100")

    # Alternative (commented out)
    ##start = get_column_id(data,"start")
    ##end = get_column_id(data,"end")
    ##print "start = %s end = %s" % (start,end)
    ##formula = "=%s-%s+1" % (end,start)
    ##data = insert_column_into_data(data,3,insert_item=formula,title="Diff")

    # Notes text example
    # NB put tabs into the text to create new columns within a single line
    notes = """Here is some example text for\tIan

Edit this as you wish and it will be added to the "notes" page
of the spreadsheet, preserving the line breaks etc

(hopefully it will work okay :)
"""
    # Create a new spreadsheet
    wb = xlwt.Workbook()

    # Create sheets: notes, data and header
    ws_notes = wb.add_sheet("Notes")
    ws_data = wb.add_sheet("Data")
    ws_header = wb.add_sheet("Header")

    # Write data to the data sheet
    write_data_to_sheet(ws_data,data)
    
    # Write header to the header sheet
    write_data_to_sheet(ws_header,header)

    # Write notes to the note sheet
    write_data_to_sheet(ws_notes,notes.split('\n'))

    # Write the spreadsheet to file
    wb.save(xls_out)


