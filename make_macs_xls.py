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
import Spreadsheet

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Functions
#######################################################################

# No functions defined

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

    # Notes text example
    # NB put tabs into the text to create new columns within a single line
    notes = """Here is some example text for\tIan

Edit this as you wish and it will be added to the "notes" page
of the spreadsheet, preserving the line breaks etc

(hopefully it will work okay :)
"""
    # Create a new spreadsheet
    wb = Spreadsheet.Workbook()

    # Create sheets: "notes", "data" and "header"
    ws_notes = wb.addSheet("Notes")
    ws_data = wb.addSheet("Data")
    ws_header = wb.addSheet("Header")

    # Add data to the "data" sheet
    ws_data.addTabData(data)

    # Insert formulae columns
    #
    # Summit-100 = ("start"+"summit" columns) - 100
    ws_data.insertColumn(3,title="summit-100",
                         insert_items="=(B+G)-100")
    # Summit+100 = ("start"+"summit" columns) + 100
    ws_data.insertColumn(4,title="summit+100",
                         insert_items="=(B+G)+100")
    
    # Add header to the "header" sheet
    ws_header.addTabData(header)

    # Add notes to the "notes" sheet
    ws_notes.addText(notes)

    # Write the spreadsheet to file
    wb.save(xls_out)


