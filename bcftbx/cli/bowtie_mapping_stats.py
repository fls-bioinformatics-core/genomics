#!/usr/bin/env python
#
#     bowtie_mapping_stats.py: write Bowtie mapping stats to a spreadsheet
#     Copyright (C) University of Manchester 2011-2021 Peter Briggs
#

"""
bowtie_mapping_stats

Extract mapping statistics from a bowtie log file and write to an XLS
spreadsheet, and (optionally) a tab-delimited file.

The mapping statistics can come from either Bowtie or Bowtie2. For
Bowtie the input log file should contain multiple blocks of the form:

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

For Bowtie2 (single end data) the expected input is multiple blocks
of the form:

Multiseed full-index search: 00:20:27
117279034 reads; of these:
  117279034 (100.00%) were unpaired; of these:
    1937614 (1.65%) aligned 0 times
    115341420 (98.35%) aligned exactly 1 time
    0 (0.00%) aligned >1 times
98.35% overall alignment rate
Time searching: 00:21:01
Overall time: 00:21:02

For Bowtie2 (paired end data) the expected input is multiple blocks
of the form:

85570063 reads; of these:
  85570063 (100.00%) were paired; of these:
    56052776 (65.51%) aligned concordantly 0 times
    22792207 (26.64%) aligned concordantly exactly 1 time
    6725080 (7.86%) aligned concordantly >1 times
    ----
    56052776 pairs aligned concordantly 0 times; of these:
      6635276 (11.84%) aligned discordantly 1 time
    ----
    49417500 pairs aligned 0 times concordantly or discordantly; of these:
      98835000 mates make up the pairs; of these:
        93969575 (95.08%) aligned 0 times
        1622693 (1.64%) aligned exactly 1 time
        3242732 (3.28%) aligned >1 times

In both cases any extraneous lines are ignored.

The program extracts data from the "reads processed"/"reads; of these",
"reads with at least one reported alignment"/"aligned exactly 1 time"",
and "reads that failed to align"/"aligned 0 times" lines for each block,
and then writes these to an output XLS file.

The program depends upon the simple_xls module, and the 3rd party
Python modules xlwt, xlrd and xlutils.
"""


#######################################################################
# Imports
#######################################################################

from builtins import str
import sys
import os
import io
import argparse
import glob
# Set default logging level and output
import logging
logging.basicConfig(format='%(levelname)s: %(message)s')
from ..simple_xls import XLSWorkBook
from ..simple_xls import XLSStyle
from ..simple_xls import cell
from ..simple_xls import column_integer_to_index
from ..simple_xls import NumberFormats
from .. import get_version

#######################################################################
# Classes
#######################################################################

class BowtieMappingStats:
    """Collect and output mapping statistics for multiple samples

    Read and store mapping stats from one or more samples from one
    or more bowtie log files (can be either bowtie or bowtie2 output),
    for example:

    >>> stats = BowtieMappingStats()
    >>> stats.add_samples('bowtie.123.log')
    >>> stats.add_samples('bowtie.456.log')
    
    Data for each sample found in each file is stored in a
    BowtieSample object.

    To create an XLS file summarising the statistics:

    >>> stats.xls('stats.xls')

    or to get the information as a tab-delimited file:

    >>> stats.tab_file('stats.tsv')

    """
    def __init__(self):
        """Create a new BowtieMappingStats instance

        """
        self.files = []
        self.samples = []

    @property
    def n_samples(self):
        """Return number of samples currently stored

        """
        return len(self.samples)

    def add_samples(self,filen=None,fp=None):
        """Read & store statistics for samples from a bowtie log file

        Given a bowtie or bowtie2 log file, reads the numbers of
        processed, unaligned etc reads for each sample, which are
        stored in a BowtieSample object (one per sample).

        The BowtieSample objects are appended to the list of samples
        held in the BowtieMappingStats object.

        The log file can be supplied as either a file name, or as a
        file-like object already opened for reading.

        Arguments
         filen  : name of bowtie/bowtie2 log file
         fp     : file-like object opened for reading with bowtie log
                  output (optional, used in preference to 'filen' if
                  supplied)
        
        Returns
          Number of samples acquired from this file.

        """
        sample = None
        n_samples = self.n_samples
        self.files.append(filen)
        if fp is None:
            fp = io.open(filen,'rt')
        for line in fp:
            if line.startswith("# reads processed: "):
                # Bowtie 1.* outputs
                # Lines of the form "# reads processed: 39808407"
                # Indicates a new sample record
                i = self.n_samples + 1
                sample = BowtieSample(i,bowtie_log=filen,bowtie_version='1')
                sample.total_reads = int(line.strip().split()[-1])
                self.samples.append(sample)
                continue
            elif line.strip().endswith(" reads; of these:"):
                # Bowtie 2.* outputs
                # Lines of the form "117279034 reads; of these:"
                # Indicates a new sample record
                i = self.n_samples + 1
                sample = BowtieSample(i,bowtie_log=filen,bowtie_version='2')
                sample.total_reads = int(line.strip().split()[0])
                self.samples.append(sample)
                continue
            if sample is None:
                # No more processing of this line
                continue
            if sample.bowtie_version == '1':
                if line.startswith("# reads that failed to align: "):
                    # Lines of the form "# reads that failed to align: 33721722 (84.71%)"
                    sample.didnt_align = int(line.strip().split()[-2])
                elif line.startswith("# reads with at least one reported alignment: "):
                    # Lines of the form "# reads with at least one reported alignment: 2737588 (6.88%)"
                    sample.uniquely_mapped = int(line.strip().split()[-2])
            elif sample.bowtie_version == '2':
                if line.strip().endswith(" were paired; of these:"):
                    # Indicates bowtie2 paired-end
                    sample.paired_end = True
                elif not sample.paired_end:
                    # Single-end data
                    if line.strip().endswith(" aligned exactly 1 time"):
                        # Lines of the form "    115341420 (98.35%) aligned exactly 1 time"
                        sample.uniquely_mapped = int(line.strip().split()[0])
                    elif line.strip().endswith(" aligned 0 times"):
                        # Lines of the form "    1937614 (1.65%) aligned 0 times"
                        sample.didnt_align = int(line.strip().split()[0])
                else:
                    # Paired-end data
                    if line.strip().endswith(" aligned concordantly exactly 1 time"):
                        # Lines of the form "    22792207 (26.64%) aligned concordantly exactly 1 time"
                        sample.uniquely_mapped = int(line.strip().split()[0])
                    elif line.strip().endswith(" aligned concordantly 0 times"):
                        # Lines of the form "   56052776 (65.51%) aligned concordantly 0 times"
                        sample.didnt_align = int(line.strip().split()[0])
        return self.n_samples - n_samples

    def xls(self,xls_out=None):
        """Output an XLS spreadsheet with the sample data

        Create and return a simple_xls.XLSWorkBook object
        representing the statistics for all the samples.

        If the 'xls_out' argument is supplied then an XLS
        spreadsheet file will also be written to the name
        it contains.

        Arguments:
          xls_out: (optional) specify the name of an XLS
            file to write the spreadsheet to. Will overwrite
            an existing file with the same name.

        Returns
          XLSWorkBook object.

        """
        # Set up reusable spreadsheet styles
        reads_style = XLSStyle(bgcolor='ivory',border='medium',
                               number_format=NumberFormats.THOUSAND_SEPARATOR,
                               centre=True)
        pcent_style = XLSStyle(bgcolor='ivory',border='medium',
                               number_format=NumberFormats.PERCENTAGE,
                               centre=True)
        headr_style = XLSStyle(color='red',bgcolor='ivory',border='medium')
        table_style = XLSStyle(bgcolor='ivory',border='medium',centre=True)
        # Create spreadsheet
        wb = XLSWorkBook()
        mapping = wb.add_work_sheet("mapping")
        mapping.insert_column('A',data=["Sample",
                                        '',
                                        "total reads",
                                        "didn't align",
                                        "total mapped reads",
                                        "  % of all reads",
                                        "uniquely mapped",
                                        "  % of all reads",
                                        "  % of mapped reads"],
                              from_row=3)
        mapping['A1'] = "MAPPING STATS"
        mapping.set_style(XLSStyle(bold=True),'A1','A11')
        # Build spreadsheet
        for sample in self.samples:
            sample_name = sample.name
            # Add input file names to sample ids if there were multiple input files
            if len(self.files) > 1 and sample.filen is not None:
                sample_name += " (" + sample.filen + ")"
            # Insert data into the spreadsheet
            col = mapping.append_column(data=[sample_name,
                                              '',
                                              sample.total_reads,
                                              sample.didnt_align,
                                              "=#5-#6",
                                              "=#7/#5",
                                              sample.uniquely_mapped,
                                              "=#9/#5",
                                              "=#9/#7"],
                                        from_row=3)
            mapping.set_style(headr_style,cell(col,3))
            mapping.set_style(table_style,cell(col,4))
            mapping.set_style(reads_style,cell(col,5),cell(col,7))
            mapping.set_style(pcent_style,cell(col,8))
            mapping.set_style(reads_style,cell(col,9))
            mapping.set_style(pcent_style,cell(col,10),cell(col,11))
        # Header
        mapping['C1'] = "Mapped with Bowtie"
        mapping.set_style(XLSStyle(centre=True),'C1')
        # Finished
        if xls_out is not None:
            print("Writing statistics to XLS file %s" % xls_out)
            wb.save_as_xls(xls_out)
        return wb

    def tab_file(self,tab_file=None):
        """Output a tab-delimited version of the spreadsheet data
 
        Creates and returns a string representation of the statistics
        in a tab-delimited format.

        If the tab_file argument is supplied then also writes this
        to the file specified.

        Arguments:
          tab_file: (optional) name of file to write tab-delimited
            data to

        Returns:
          String representing the statistics data.

        """
        # Fetch the xls
        xls = self.xls()
        # Remove the formatting for the read numbers
        xls.worksheet["mapping"].get_style('B5').number_format = None
        # Generate the tab file text
        end_cell = cell(column_integer_to_index(self.n_samples),
                        xls.worksheet["mapping"].last_row)
        txt = xls.worksheet['mapping'].render_as_text(eval_formulae=True,
                                                      apply_format=True,
                                                      start='A3',
                                                      end=end_cell)
        if tab_file is not None:
            print("Writing statistics to tab-delimited file %s" % tab_file)
            io.open(tab_file,'wt').write(txt)
        return txt

class BowtieSample:
    """Store mapping statistics for a sample

    Simple holder for mapping statistics extracted from a bowtie
    or bowtie2 log file.

    Provides the properties:

    name           : name for the sample
    total_reads    : total number of reads processed
    didnt_align    : number of reads that failed to align
    uniquely_mapped: number of reads that mapped exactly once
    filen          : file name that the data was read from
    bowtie_version : version of bowtie (1 or 2, or None)
    paired_end     : True if output is for paired-end data

    """
    def __init__(self,name,bowtie_log=None,bowtie_version=''):
        """Create a new BowtieSample instance

        Arguments:
          name:       name for the sample
          bowtie_log: optional, name of the log file that the
            mapping statistics were read from
          bowtie_version: optional, version of bowtie (1 or 2)

        """
        self.name = str(name)
        self.filen = None
        if bowtie_log is not None:
            self.filen = os.path.basename(bowtie_log)
        self.total_reads = None
        self.didnt_align = None
        self.uniquely_mapped = None
        self.paired_end = False
        bowtie_verison = str(bowtie_version)
        if bowtie_version not in ("1","2"):
            bowtie_version = ''
        self.bowtie_version = bowtie_version

#######################################################################
# Main program
#######################################################################

def main():
    p = argparse.ArgumentParser(
        description=
        "Extract mapping statistics for each sample referenced in "
        "the input bowtie log files and summarise the data in an XLS "
        "spreadsheet. Handles output from both Bowtie and Bowtie2.")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument('-o',action="store",dest="stats_xls",metavar="xls_file",
                   default=None,
                   help="specify name of the output XLS file (otherwise "
                   "defaults to 'mapping_summary.xls').")
    p.add_argument('-t',action="store_true",dest="tab_file",
                   default=False,
                   help="write data to tab-delimited file in addition to "
                   "the XLS file. The tab file will have the same name as "
                   "the XLS file, with the extension replaced "
                   "by .txt")
    p.add_argument('bowtie_logs',metavar="BOWTIE_LOG_FILE",action='store',
                   nargs='+',
                   help="logfile output from Bowtie or Bowtie2")

    # Process the command line
    arguments = p.parse_args()

    # Input files
    # Check for wildcards in file names, to emulate linux shell globbing
    # on platforms such as Windows which don't have this built in
    bowtie_log_files = []
    for arg in arguments.bowtie_logs:
        for filen in glob.iglob(arg):
            if not os.path.exists(filen):
                p.error("Input file '%s' not found" % filen)
            bowtie_log_files.append(filen)
    if not bowtie_log_files:
        p.error("at least one input bowtie log file required")

    # Report version
    print("%s %s" % (os.path.basename(sys.argv[0]),get_version()))

    # Initialisations
    if arguments.stats_xls is not None:
        xls_out = arguments.stats_xls
    else:
        xls_out = "mapping_summary.xls"
    if arguments.tab_file:
        tab_file = os.path.splitext(xls_out)[0] + ".txt"
    else:
        tab_file = None

    # Acquire data
    stats = BowtieMappingStats()
    for bowtie_log in bowtie_log_files:
        print("Processing data from %s" % bowtie_log)
        n_samples = stats.add_samples(bowtie_log)
        if n_samples > 0:
            print("\tFound %d samples (total %d)" % (n_samples,stats.n_samples))
            print("\tBowtie version %s" % (stats.samples[-1].bowtie_version))
            print("\t%s" % ('Paired end' if stats.samples[-1].paired_end else 'Single end'))
        else:
            logging.warning("No samples found in %s" % bowtie_log)

    # Output files
    if stats.n_samples > 0:
        # Create spreadsheet
        stats.xls(xls_out)
        # Create tab-delimited file if requested
        if tab_file:
            stats.tab_file(tab_file)
    else:
        # No samples found
        logging.error("No samples found, nothing to output")
        sys.exit(1)
