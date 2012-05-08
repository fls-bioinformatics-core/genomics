#!/bin/env python
#
#     bowtie_mapping_stats.py: write Bowtie mapping stats to a spreadsheet
#     Copyright (C) University of Manchester 2011 Peter Briggs
#
########################################################################
#
# bowtie_mapping_stats.py
#
#########################################################################

"""bowtie_mapping_stats

Extract mapping statistics from a bowtie log file and write to an XLS
spreadsheet.

The input log file should contain multiple blocks of bowtie output of
the form:

<Sample>
Time loading reference: 00:00:01
Time loading forward index: 00:00:00
Time loading mirror index: 00:00:02
Seeded quality full-index search: 00:10:20
# reads processed: 39808407
# reads with at least one reported alignment: 2737588 (6.88%)
# reads that failed to align: 33721722 (84.71%)
# reads with alignments suppressed due to -m: 3349097 (8.41%)
Reported 2737588 alignments to 1 output stream(s)
Time searching: 00:10:27
Overall time: 00:10:27

The program extracts data from the "reads processed", "reads with at
least one reported alignment", and "reads that failed to align" lines
for each block, and then writes these to an output XLS file.

The program depends upon the Spreadsheet module, and the 3rd party
Python modules xlwt, xlrd and xlutils.
"""

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.1.4"

#######################################################################
# Import
#######################################################################

import sys
import os
import optparse
import glob

# Set default logging level and output
import logging
logging.basicConfig(format='%(levelname)s: %(message)s')

# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)

# Get the Spreadsheet module
try:
    import Spreadsheet
except ImportError:
    logging.error("Failed to import the Spreadsheet module")
    logging.error("Set your PYTHONPATH to include the directory with this module, or get the")
    logging.error("latest version from github via:")
    logging.error("https://github.com/fls-bioinformatics-core/genomics/blob/master/share/Spreadsheet.py")
    logging.error("and ensure that the underlying xlwt, xlrd and xlutils libraries are installed")
    sys.exit(1)

#######################################################################
# Classes
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

    p = optparse.OptionParser(usage="%prog [options] <bowtie_log_file> [ <bowtie_log_file> ... ]",
                              version="%prog "+__version__,
                              description=
                              "Extract mapping statistics for each sample referenced in "
                              "the input bowtie log files and summarise the data in an XLS "
                              "spreadsheet.")

    p.add_option('-o',action="store",dest="stats_xls",metavar="xls_file",default=None,
                 help="specify name of the output XLS file (otherwise defaults to"
                 "'mapping_summary.xls').")
    p.add_option('-t',action="store_true",dest="tab_file",metavar="tab_file",default=False,
                 help="write data to tab-delimited file (same name as XLS file with .txt "
                 "extension).")

    # Process the command line
    options,arguments = p.parse_args()

    # Input files
    # Check for wildcards in file names, to emulate linux shell globbing
    # on platforms such as Windows which don't have this built in
    bowtie_log_files = []
    for arg in arguments:
        for filen in glob.iglob(arg):
            if not os.path.exists(filen):
                p.error("Input file '%s' not found" % filen)
            bowtie_log_files.append(filen)
    if not bowtie_log_files:
        p.error("at least one input bowtie log file required")

    # Report version
    p.print_version()

    # Initialisations
    if options.stats_xls is not None:
        xls_out = options.stats_xls
    else:
        xls_out = "mapping_summary.xls"
    if options.tab_file:
        tab_file = os.path.splitext(xls_out)[0] + ".txt"
    else:
        tab_file = None

    # Loop over input files and acquire data
    data = []
    for bowtie_log in bowtie_log_files:
        print "Reading data from %s" % bowtie_log
        fp = open(bowtie_log,'rU')
        for line in fp:
            if line.startswith("# reads processed: "):
                # Lines of the form "# reads processed: 39808407"
                data.append({'total_reads': None,
                             'didnt_align': None,
                             'uniquely_mapped': None })
                data[-1]['total_reads'] = int(line.strip().split()[-1])
            elif line.startswith("# reads that failed to align: "):
                # Lines of the form "# reads that failed to align: 33721722 (84.71%)"
                data[-1]['didnt_align'] = int(line.strip().split()[-2])
            elif line.startswith("# reads with at least one reported alignment: "):
                # Lines of the form "# reads with at least one reported alignment: 2737588 (6.88%)"
                data[-1]['uniquely_mapped'] = int(line.strip().split()[-2])
        # Finished, close file
        fp.close()

    # Look at what we got
    if len(data) == 0:
        logging.error("No samples found")
        sys.exit(1)
    else:
        print "Found %d samples" % len(data)

    # Create the spreadsheet
    xls = Spreadsheet.Workbook()
    ws = xls.addSheet("mapping")
    ws.insertColumn(0,insert_items=["MAPPING STATS",
                                    '',
                                    "Sample",
                                    '',
                                    "total reads",
                                    "didn't align",
                                    "total mapped reads",
                                    "% of all reads",
                                    "uniquely mapped",
                                    "% of all reads",
                                    "% of mapped reads"])
    for i in range(len(data)):
        n = i+1
        ws.insertColumn(n,insert_items=\
                            ['',
                             '',
                             "<style color=red bgcolor=ivory border=medium>"+str(n)+"</style>",
                             '<style bgcolor=ivory border=medium></style>',
                             "<style bgcolor=ivory border=medium number_format=#,###>"+\
                                 str(data[i]['total_reads'])+"</style>",
                             "<style  bgcolor=ivory border=medium number_format=#,###>"+\
                                 str(data[i]['didnt_align'])+"</style>",
                             "<style bgcolor=ivory border=medium number_format=#,###>"
                             "=#5-#6</style>",
                             "<style bgcolor=ivory border=medium number_format=0.0%>"
                             "=#7/#5</style>",
                             "<style bgcolor=ivory border=medium number_format=#,###>"+\
                                 str(data[i]['uniquely_mapped'])+"</style>",
                             "<style bgcolor=ivory border=medium number_format=0.0%>"
                             "=#9/#5</style>",
                             "<style bgcolor=ivory border=medium number_format=0.0%>"
                             "=#9/#7</style>"])
    ws.setCellValue(0,2,"Mapped with Bowtie")
    # Finished
    print "Writing statistics to %s" % xls_out
    xls.save(xls_out)

    # Create tab-delimited file if requested
    if tab_file:
        print "Writing tab-delimited file %s" % tab_file
        tab_data = []
        # Create leading column
        for item in ("sample",
                     "total reads",
                     "didn't align",
                     "total mapped reads",
                     "% of all reads",
                     "uniquely mapped",
                     "% of all reads",
                     "% of mapped reads"):
            tab_data.append([item])
        # Add columns for each sample
        for i in xrange(len(data)):
            tab_data[0].append(str(i+1))
            tab_data[1].append(data[i]['total_reads'])
            tab_data[2].append(data[i]['didnt_align'])
            total_mapped_reads = data[i]['total_reads'] - data[i]['didnt_align']
            tab_data[3].append(total_mapped_reads)
            percent_of_all_reads = "%.1f%%" % (float(total_mapped_reads)/
                                               float(data[i]['total_reads'])*100.0)
            tab_data[4].append(percent_of_all_reads)
            tab_data[5].append(data[i]['uniquely_mapped'])
            percent_of_all_reads = "%.1f%%" % (float(data[i]['uniquely_mapped'])/
                                               float(data[i]['total_reads'])*100.0)
            tab_data[6].append(percent_of_all_reads)
            percent_of_all_reads = "%.1f%%" % (float(data[i]['uniquely_mapped'])/
                                               float(total_mapped_reads)*100.0)
            tab_data[7].append(percent_of_all_reads)
            
        # Write to file
        fp = open(tab_file,'w')
        for line in tab_data:
            fp.write("%s\n" % '\t'.join([str(x) for x in line]))
        fp.close()
