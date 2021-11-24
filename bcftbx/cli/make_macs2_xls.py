#!/usr/bin/env python
#
#     make_macs2_xls.py: Convert MACS output file to XLS(X) spreadsheet
#     Copyright (C) University of Manchester 2013-2021 Peter Briggs, Ian Donaldson
#

"""
make_macs2_xls.py

Convert MACS output file to XLS(X) spreadsheet

Given tab-delimited output from MACS, creates an Excel spreadsheet with
3 sheets: one containing the tabulated data plus extra columns derived
from that data (e.g. summit+/-100bps); one containing the header
information from the input; and one describing what each of the columns
in the data sheet are.

This is a modified version of make_macs_xls.py updated to work with
output from MACS 2.0.10.
"""

#######################################################################
# Imports
#######################################################################

from builtins import str
import os
import io
import sys
import argparse
import logging
# Configure logging output
logging.basicConfig(format="%(levelname)s %(message)s")
from ..TabFile import TabFile
from ..simple_xls import Limits
from ..simple_xls import ColumnRange
from ..simple_xls import XLSLimits
from ..simple_xls import XLSXLimits
from ..simple_xls import XLSStyle
from ..simple_xls import XLSWorkBook
from .. import get_version

#######################################################################
# Classes
#######################################################################

class MacsXLS:
    """Class for reading and manipulating XLS output from MACS

    Reads the XLS output file from the MACS peak caller and
    processes and stores the information for subsequent manipulation
    and output.

    To read in data from a MACS output file:

    >>> macs = MacsXLS("macs.xls")

    This reads in the data and prepends an additional 'order'
    column (a list of numbers from one to the number of data
    lines).

    To get the MACS version:

    >>> macs.macs_version
    2.0.10

    To access the 'header' information (as a Python list):

    >>> macs.header

    To see the column names (as a Python list):

    >>> macs.columns

    The data is stored as a TabFile object; to access the data
    use the 'data' property, e.g.

    >>> for line in macs.data:
    ...    print("Chr %s Start %s End" % (line['chr'],line['start'],line['end']))

    To sort the data on a particular column use the 'sort_on'
    method, e.g.

    >>> macs.sort_on('chr')

    (Note that the order column is always recalculated after
    sorting.)

    """

    def __init__(self,filen=None,fp=None,name=None):
        """Create a new MacsXLS instance

        Arguments:
          filen: name of the file to read the MACS output from.
            If None then fp argument must be supplied instead.
          fp: file-like object opened for reading. If None then
            filen argument must be supplied instead. If both filen
            and fp are supplied then fp will be used preferentially.

        """
        # Store data
        self.__filen = filen
        self.__name = name
        self.__macs_version = None
        self.__command_line = None
        self.__header = []
        self.__data = None
        # Open file, if necessary
        if fp is None:
            fp = io.open(filen,'rt')
        else:
            filen = None
        # Iterate over header lines
        for line in fp:
            line = line.strip()
            if line.startswith('#') or line == '':
                # Header line
                self.__header.append(line)
                # Detect/extract data from header
                if line.startswith("# This file is generated by MACS version "):
                    # Look for MACS version
                    self.__macs_version = line.split()[8]
                elif self.__name is None and line.startswith("# name = "):
                    # Look for 'name' if none set
                    self.__name = line[len("# name = "):]
                elif line.startswith("# Command line: "):
                    # Look for command line
                    self.__command_line = line[16:]
            else:
                if self.__data is None:
                    # First line of actual data should be the column names
                    columns = line.split('\t')
                    # Insert an additional column called 'order'
                    columns.insert(0,"order")
                    # Set up TabFile to handle actual data
                    self.__data = TabFile(column_names=columns)
                else:
                    # Assume it's actual data and store it
                    self.__data.append(tabdata="\t%s" % line)
        # Close the file handle, if we opened it
        if filen is not None:
            fp.close()
        # Check that we actually got a version line
        if self.macs_version is None:
            raise Exception("Failed to extract MACS version, not a MACS "
                            "output file?")
        # Populate the 'order' column
        self.update_order()

    @property
    def filen(self):
        """Return the source file name

        """
        return self.__filen

    @property
    def name(self):
        """Return the name property

        """
        return self.__name

    @property
    def macs_version(self):
        """Return the MACS version extracted from the file

        """
        return self.__macs_version

    @property
    def command_line(self):
        """Return the command line string extracted from the header

        This is the value associated with the "# Command line: ..."
        header line.

        Will be 'None' if no matching header line is found, else is
        the string following the ':'.

        """
        return self.__command_line

    @property
    def columns(self):
        """Return the column names for the MACS data

        Returns a list of the column names from the data
        extracted from the file.

        """
        return self.__data.header()

    @property
    def columns_as_xls_header(self):
        """Returns the column name list, with hash prepended

        """
        return ['#'+self.columns[0]] + self.columns[1:]

    @property
    def header(self):
        """Return the header data from the file

        Returns a list of lines comprising the header
        extracted from the file.

        """
        return self.__header

    @property
    def data(self):
        """Return the data from the file

        Returns a TabFile object comprising the data
        extracted from the file.

        """
        return self.__data

    @property
    def with_broad_option(self):
        """Returns True if MACS was run with --broad option

        If --broad wasn't detected then returns False.

        """
        if self.macs_version.startswith('1.'):
            # Not an option in MACS 1.*
            return False
        try:
            # Was --broad specified in the command line?
            return '--broad' in self.command_line.split()
        except AttributeError:
            # No command line? Check for 'abs_summit' column
            return 'abs_summit' not in self.columns

    def sort_on(self,column,reverse=True):
        """Sort data on specified column

        Sorts the data in-place, by the specified column.

        By default data is sorted in descending order; set
        'reverse' argument to False to sort values in ascending
        order instead
 
        Note that the 'order' column is automatically updated
        after each sorting operation.

        Arguments:
          column: name of the column to sort on
          reverse: if True (default) then sort in descending
            order (i.e. largest to smallest). Otherwise sort in
            ascending order.

        """
        # Sort the data
        self.__data.sort(lambda line: line[column],reverse=reverse)
        # Update the 'order' column
        self.update_order()

    def update_order(self):
        # Set/update values in 'order' column
        for i in range(0,len(self.__data)):
            self.__data[i]['order'] = i+1

#######################################################################
# Functions
#######################################################################

def xls_for_macs2(macs_xls,row_limit=None,cell_char_limit=None):
    """Create and return XLS workbook object for MACS2 output

    Arguments:
      macs_xls: populated MacsXLS object (must be from MACS2)
      row_limit: explicitly specify maximum number of rows per
        output sheet
      cell_character_limit: explicitly specify maximum number
        of characters per cell

    Returns:
      XLSWorkBook

    """

    # Check MACS version - can't handle MACS 1.*
    if macs_xls.macs_version.startswith("1."):
        raise Exception("Only handles output from MACS 2.0*")

    # Sort into order by fold_enrichment column
    macs_xls.sort_on('fold_enrichment',reverse=True)

    # Maximum number of rows per data sheet
    if row_limit is None:
        row_limit = Limits.MAX_NUMBER_ROWS_PER_WORKSHEET
    if len(macs_xls.data) > row_limit:
        logging.warning("Data will be split over multiple worksheets on output")

    # Maximum number of characters per cell
    if cell_char_limit is None:
        cell_char_limit = Limits.MAX_LEN_WORKSHEET_CELL_VALUE

    # Maximum length of a data sheet title
    sheet_title_limit = Limits.MAX_LEN_WORKSHEET_TITLE

    # Legend descriptions for all possible columns
    legends_text = { 'order': "Sorting order FE",
                     'chr': "Chromosome location of binding region",
                     'start': "Start coordinate of binding region",
                     'end': "Start coordinate of binding region",
                     'summit+100': "Summit + 100bp",
                     'summit-1': "Summit of binding region - 1",
                     'summit': "Summit of binding region",
                     'abs_summit+100': "Summit + 100bp",
                     'abs_summit-100': "Summit of binding region - 100bp",
                     'abs_summit': "Summit of binding region",
                     'length': "Length of binding region",
                     'abs_summit': "Coordinate of region summit",
                     'pileup': "Number of non-degenerate and position corrected reads at summit",
                     '-log10(pvalue)': "Transformed Pvalue -log10(Pvalue) for the binding region (e.g. if Pvalue=1e-10, then this value should be 10)",
                     'fold_enrichment': "Fold enrichment for this region against random Poisson distribution with local lambda",
                     '-log10(qvalue)': "Transformed Qvalue -log10(Pvalue) for the binding region (e.g. if Qvalue=0.05, then this value should be 1.3)",
                     'name': "Name"
                 }

    # Create a new spreadsheet
    xls = XLSWorkBook()

    # Set up styles
    boldstyle = XLSStyle(bold=True)

    # Create and populate the 'data' sheet(s)
    # If there are more records than will fit into a single spreadsheet
    # then make multiple sheets
    data_sheets = []
    sheet_number = 1
    data = xls.add_work_sheet("data",macs_xls.name)
    for line in macs_xls.data:
        # If we've reached the row limit then make a new sheet
        if data.last_row == row_limit:
            sheet_number += 1
            name = "data%d" % sheet_number
            title = "%s(%d)" % (macs_xls.name[:sheet_title_limit-4],
                                sheet_number)
            print("Making additional data sheet '%s'" % title)
            data = xls.add_work_sheet(name,title)
        # If this is an empty sheet add the column titles and
        # store in the list of data sheets
        if data.next_row == 1:
            data.write_row(1,data=macs_xls.columns_as_xls_header)
            data_sheets.append(data)
        # Write data to sheet
        data.append_row(line)
    
    # Insert and populate formulae columns for each data sheet
    for data in data_sheets:
        if not macs_xls.with_broad_option:
            # Copy of chr column
            data.insert_column('E',text="chr")
            data.write_column('E',fill="=B?",from_row=2)
            # Summit-100
            data.insert_column('F',text="abs_summit-100")
            data.write_column('F',fill="=L?-100",from_row=2)
            # Summit+100
            data.insert_column('G',text="abs_summit+100")
            data.write_column('G',fill="=L?+100",from_row=2)
            # Copy of chr column
            data.insert_column('H',text="chr")
            data.write_column('H',fill="=B?",from_row=2)
            # Summit-1
            data.insert_column('I',text="summit-1")
            data.write_column('I',fill="=L?-1",from_row=2)
            # Summit
            data.insert_column('J',text="summit")
            data.write_column('J',fill="=L?",from_row=2)
        else:
            # Copy of chr column
            data.insert_column('E',text="chr")
            data.write_column('E',fill="=B?",from_row=2)

    # Build the 'notes' sheet with the header data
    notes = xls.add_work_sheet('notes',"Notes")
    notes.write_row(1,text="MACS RUN NOTES:",style=boldstyle)
    notes.write_column('A',macs_xls.header,from_row=notes.next_row)
    notes.append_row(text="ADDITIONAL NOTES:",style=boldstyle)
    notes.append_row(text="By default regions are sorted by fold enrichment "
                     "(in descending order)")

    # Check for and address too-long "Command line" cell i.e. if it
    # exceeds maximum size for a spreadsheet cell
    for row in range(1,notes.last_row+1):
        if notes['A'][row].startswith("# Command line:"):
            command_line = notes['A'][row]
            if len(command_line) > cell_char_limit:
                # Chop up command line string over multiple cells
                logging.warning("Splitting command line over multiple cells")
                row_data = chunk(command_line,cell_char_limit,delimiter=' ')
                notes.write_row(row,data=row_data)
        
    # Build the 'legends' sheet based on content of 'data'
    data = data_sheets[0]
    legends = xls.add_work_sheet('legends',"Legends")
    for col in ColumnRange(data.last_column):
        name = data[col][1].lstrip('#')
        try:
            legends.append_row(data=(name,legends_text[name]))
        except KeyError:
            logging.warning("No legend description found for column '%s'" % name)
            legends.append_row(data=(name,name.title()))

    # "Freeze" top line of each 'data' sheet
    for data in data_sheets:
        data.freeze_panes = 'A2'

    # Return spreadsheet object
    return xls

def bed_for_macs2(macs_xls):
    """
    Create and return TabFile instance for MACS2 output

    Arguments:
      macs_xls: populated MacsXLS object (must be from MACS2)

    Returns:
      TabFile.TabFile
    """
    # Check MACS version - can't handle MACS 1.*
    if macs_xls.macs_version.startswith("1."):
        raise Exception("Only handles output from MACS 2.0*")

    if macs_xls.with_broad_option:
        raise Exception("BED output only available if MACS2 was "
                        "run without --broad option")

    # Sort into order by fold_enrichment column
    macs_xls.sort_on('fold_enrichment',reverse=True)

    # Create a new TabFile
    bed = TabFile(column_names=('chr',
                                'abs_summit-100',
                                'abs_summit+100',))
    for line in macs_xls.data:
        chrom = line['chr']
        start = line['abs_summit'] - 100
        end = line['abs_summit'] + 100
        bed.append(data=(chrom,start,end))
    return bed

def chunk(line,chunksize,delimiter=None):
    """Chop a string into 'chunks' no greater than a specified size

    Given a string, return a list where each item is a substring
    no longer than the specified 'chunksize'.

    If delimiter is not None then the chunking will attempt to
    chop the substrings on that delimiter. If a delimiter can't be
    located (or not is specified) then the substrings will all
    be of length 'chunksize'.

    """
    chunks = []
    # Loop over and chop up string until the remainder is shorter
    # than chunksize
    while len(line) > chunksize:
        if delimiter is not None:
            try:
                # Locate nearest delimiter before the chunksize limit
                i = line[:chunksize].rindex(' ')
            except ValueError:
                # Unable to locate delimiter so split on the chunksize
                # limit
                i = chunksize
        else:
            i = chunksize
        chunks.append(line[:i])
        line = line[i:]
    # Append the remainder and return
    chunks.append(line)
    return chunks

#######################################################################
# Main program
#######################################################################

def make_macs2_xls(macs_file,xls_out,xls_format="xlsx",bed_out=None):
    """Driver function

    Wraps core functionality of program to facilitate
    performance profiling
    
    Arguments:
      macs_file: output .xls file from MACS peak caller
      xls_out: name to write output XLS spreadsheet file to
      xls_format: optional, specify the XLS output format
        (either 'xls' or 'xlsx'; default is 'xlsx')
      bed_out: optional, name to write output BED file to
    
    """
    # Check requested XLS format
    if xls_format not in ('xls','xlsx'):
        raise Exception("Unrecognised XLS format: %s" % xls_format)

    # Load the data from the file
    print("Reading data...",end=' ')
    macs_xls = MacsXLS(macs_file)
    print("done")
    if macs_xls.macs_version is None:
        logging.error("couldn't detect MACS version")
        sys.exit(1)
    print("Input file is from MACS %s" % macs_xls.macs_version)
    print("Found %d records" % len(macs_xls.data))
    if macs_xls.macs_version.startswith('2.'):
        if macs_xls.with_broad_option:
            print("MACS was run with --broad option")

    # Create XLS file
    print("Generating XLS file")
    if xls_format == "xlsx":
        xls_max_rows = XLSXLimits.MAX_NUMBER_ROWS_PER_WORKSHEET
        xls_cell_width = XLSXLimits.MAX_LEN_WORKSHEET_CELL_VALUE
    elif xls_format == "xls":
        xls_max_rows = XLSLimits.MAX_NUMBER_ROWS_PER_WORKSHEET
        xls_cell_width = XLSLimits.MAX_LEN_WORKSHEET_CELL_VALUE
    try:
        xls = xls_for_macs2(macs_xls,
                            row_limit=xls_max_rows,
                            cell_char_limit=xls_cell_width)
    except Exception as ex:
        logging.error("failed to convert to XLS: %s" % ex)
        sys.exit(1)
    if xls_format == "xlsx":
        xls.save_as_xlsx(xls_out)
    elif xls_format == "xls":
        xls.save_as_xls(xls_out)

    # Create BED file
    if bed_out is not None:
        print("Generate BED file")
        try:
            bed = bed_for_macs2(macs_xls)
        except Exception as ex:
            logging.error("failed to generate BED data: %s" % ex)
            sys.exit(1)
        bed.write(bed_out,include_header=True)
        print("Finished")

def main():
    # Process command line
    p = argparse.ArgumentParser(description=
                                "Create an XLS(X) spreadsheet from the output "
                                "of the MACS2 peak caller. MACS2_XLS is the "
                                "output '.xls' file from MACS2; if supplied "
                                "then XLS_OUT is the name to use for the output "
                                "file (otherwise it will be called "
                                "'XLS_<MACS2_XLS>.xls(x)').")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument("-f","--format",
                   action="store",dest="xls_format",default="xlsx",
                   help="specify the output Excel spreadsheet format; must be "
                   "one of 'xlsx' or 'xls' (default is 'xlsx')")
    p.add_argument("-b","--bed",
                   action="store_true",dest="bed",
                   help="write an additional TSV file with chrom, "
                   "abs_summit+100 and abs_summit-100 data as the columns. "
                   "(NB only possible for MACS2 run without --broad)")
    p.add_argument('macs2_xls',metavar="MACS2_XLS",
                   help="output '.xls' file from MACS2")
    p.add_argument('xls_out',metavar="XLS_OUT",nargs='?',
                   help="name to use for the output file (default is "
                   "'XLS_<MACS2_XLS>.xls(x)')")
    args = p.parse_args()
    # Get input file name
    macs_in = args.macs2_xls
    # Get output Excel format
    xls_format = str(args.xls_format).lower()
    if xls_format not in ('xls','xlsx'):
        p.error("Unrecognised Excel format: %s" % xls_format)
    # Report version
    print("%s %s" % (os.path.basename(sys.argv[0]),get_version()))
    # Build output file name: if not explicitly supplied on the command
    # line then use "XLS_<input_name>.<xls_format>"
    if args.xls_out:
        xls_out = args.xls_out
    else:
        # MACS output file might already have an .xls extension
        # but we'll add an explicit .xls extension
        xls_out = "XLS_"+os.path.splitext(os.path.basename(macs_in))[0]+\
                  "."+xls_format
    # Also generate BED file?
    if args.bed:
        bed_out = os.path.splitext(xls_out)[0]+".bed"
    else:
        bed_out = None
    print("Input file: %s" % macs_in)
    print("Output XLS: %s" % xls_out)
    if bed_out:
        print("Output BED: %s" % bed_out)
    make_macs2_xls(macs_in,
                   xls_out,
                   xls_format=xls_format,
                   bed_out=bed_out)
