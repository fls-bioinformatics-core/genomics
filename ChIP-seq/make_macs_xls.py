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

import os
import sys
# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
from TabFile import TabFile
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
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print "Usage: %s <macs_file> [ <xls_out> ]" % sys.argv[0]
        sys.exit(1)
    macs_in = sys.argv[1]

    # Build output file name: if not explicitly supplied on the command
    # line then use "XLS_<input_name>.xls"
    if len(sys.argv) == 3:
        xls_out = sys.argv[2]
    else:
        # MACS output file might already have an .xls extension
        # but we'll add an explicit .xls extension
        xls_out = "XLS_"+os.path.splitext(os.path.basename(macs_in))[0]+".xls"
    print "Input file: %s" % macs_in
    print "Output XLS: %s" % xls_out

    # Extract the header from the MACS and feed actual data to
    # TabFile object
    header = []
    data = TabFile(column_names=['chr','start','end','length','summit','tags',
                                 '-10*log10(pvalue)','fold_enrichment','FDR(%)'])
    fp = open(macs_in,'r')
    for line in fp:
        if line.startswith('#') or line.strip() == '':
            # Header line
            header.append(line.strip())
        else:
            # Data
            data.append(tabdata=line.strip())
    fp.close()

    # Temporarily remove first line
    header_line = str(data[0])
    del(data[0])

    # Sort into order by fold_enrichment and then by -10*log10(pvalue) column
    data.sort(lambda line: line['fold_enrichment'],reverse=True)
    data.sort(lambda line: line['-10*log10(pvalue)'],reverse=True)

    # Restore first line
    data.insert(0,tabdata=header_line)

    # Insert "order" column
    data.appendColumn("order")
    # Perhaps confusingly must also insert initial value "#order"
    data[0]['order'] = "#order"
    for i in range(1,len(data)):
        data[i]['order'] = i
    # Reorder columns to put it at the start
    data = data.reorderColumns(['order','chr','start','end','length','summit','tags',
                                '-10*log10(pvalue)','fold_enrichment','FDR(%)'])

    # Legnds text
    legends_text = """order\tSorting order Pvalue and FE
chr\tChromosome location of binding region
start\tStart coordinate of binding region
end\tEnd coordinate of binding region
summit-100\tSummit - 100bp
summit+100\tSummit + 100bp
summit-1\tSummit of binding region - 1
summit\tSummit of binding region
length\tLength of binding region
summit\tPeak of summit region from the start position of the binding region
tags\tNumber of non-degenerate and position corrected reads in the binding region
-10*LOG10(pvalue)\tTransformed Pvalue -10*log10(Pvalue) for the binding region (e.g. if Pvalue=1e-10, then this value should be 100)
fold_enrichment\tFold enrichment for this region against random Poisson distribution with local lambda
FDR(%)\tFalse discovery rate (FDR) as a percentage
"""
    # Create a new spreadsheet
    wb = Spreadsheet.Workbook()

    # Create the sheets
    #
    # data = the actual data from MACS
    ws_data = wb.addSheet(os.path.basename(macs_in)[:min(30,len(os.path.basename(macs_in)))])
    #
    # note = the header data
    ws_notes = wb.addSheet("notes")
    ws_notes.addText("<style font=bold>MACS RUN NOTES:</style>")
    ws_notes.addTabData(header)
    ws_notes.addText("\n<style font=bold>ADDITIONAL NOTES:</style>\nBy default regions are sorted by Pvalue and fold enrichment (in descending order)")
    #
    # legends = static text explaining the column headers
    ws_legends = wb.addSheet("legends")
    ws_legends.addText(legends_text)

    # Add data to the "data" sheet
    ws_data.addText(str(data))

    # Insert formulae columns
    #
    # Copy of "chr" column
    ws_data.insertColumn(4,title="chr",insert_items="=B?")
    #
    # Summit-100
    ws_data.insertColumn(5,title="summit-100",insert_items="=J?-100")
    #
    # Summit+100
    ws_data.insertColumn(6,title="summit+100",insert_items="=J?+100")
    #
    # Copy of "chr" column
    ws_data.insertColumn(7,title="chr",insert_items="=B?")
    #
    # Summit-1
    ws_data.insertColumn(8,title="summit-1",insert_items="=J?-1")
    #
    # Summit
    ws_data.insertColumn(9,title="summit",insert_items="=C?+L?")

    # Write the spreadsheet to file
    wb.save(xls_out)


