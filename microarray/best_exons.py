#!/usr/bin/env python
#
#     best_exons.py: pick 'best' exons for gene symbols and average data
#     Copyright (C) University of Manchester 2013-2019 Peter Briggs
#
########################################################################

__version__ = "1.3.4"

"""
best_exons.py
=============

What it does
------------

Program to pick "top" three exons for each gene symbol from a TSV file
with the exon data (file has one exon per line) and output a single
line for that gene symbol with values averaged over the top three.

"Top" or "best" exons are determined by ranking on either the
log2FoldChange or pValue:

* For log2FoldChange, the "best" exon is the one with the biggest absolute
  log2FoldChange; if this is positive or zero then choose the top three
  largest fold change value. Otherwise choose the bottom three.

* For pValue, the "best" exon is the one with the smallest value.

Outputs a TSV file with one line per gene symbol plus the average of
each data value for the 3 "best" exons (as determined above).

Input file format
-----------------

Tab separated values (TSV) file, with first line optionally being a header
line.

By default the program assumes:

Column 1:  probeset name
Column 2:  gene symbol
Column 13: log2 fold change
Column 14: p-value

(column number starts from 1), but these can be configured using the
appropriate command line options.

Output file format
------------------

TSV file with one gene symbol per line plus averaged data.

"""

########################################################################
# Imports
#########################################################################

from builtins import str
import sys
import os
import io
import argparse
import logging
try:
    from collections.abc import Iterator
except ImportError:
    from collections import Iterator
from operator import attrgetter

# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.TabFile as TabFile
import bcftbx.utils as bcf_utils

########################################################################
# Classes
#########################################################################

class TabFileIterator(Iterator):
    """TabFileIterator

    Class to loop over all lines in a TSV file, returning a TabDataLine
    object for each record.

    """

    def __init__(self,filen=None,fp=None,column_names=None):
        """Create a new TabFileIterator

        The input file should be a tab-delimited text file, specified as
        either a file name (using the 'filen' argument), or a file-like
        object opened for line reading (using the 'fp' argument).

        Each iteration returns a TabDataLine populated with data from
        the file.

        Example usage:

        >>> for line in TabFileIterator(filen='data.tsv'):
        ...   print(line)

        Arguments:
          filen: name of the file to iterate through
          fp: file-like object opened for reading
          column_names: optional list of names to use as
            column headers in the returned TabDataLines

        """
        self.__filen = filen
        self.__column_names = column_names
        self.__lineno = 0
        if fp is None:
            self.__fp = io.open(filen,'rt')
        else:
            self.__fp = fp

    def next(self):
        """Return next record from TSV file as a TabDataLine object (Python 2)

        """
        return self.__next__()

    def __next__(self):
        """Return next record from TSV file as a TabDataLine object

        """
        line = self.__fp.readline()
        self.__lineno += 1
        if line != '':
            return TabFile.TabDataLine(line=line,
                                       column_names=self.__column_names,
                                       lineno=self.__lineno)
        else:
            # Reached EOF
            if self.__filen is not None:
                # Assume we opened the file originally
                self.__fp.close()
            raise StopIteration

class ExonList:
    """List of exons associated with a gene symbol

    Attributes:
    
    gene_symbol: gene symbol associated with the list
    exons: list of Exon objects

    Populate using the 'add_exon' method.

    Sort into order using the 'sort' method.

    Fetch 'best' exons using the 'best_exon' and 'best_exons'
    methods.

    Average data using the 'average' method.

    """
    def __init__(self,gene_symbol):
        """Create a new ExonList
        """
        self.gene_symbol = str(gene_symbol)
        self.exons = []

    def add_exon(self,exon):
        """Add an exon to the list

        'exon' should be a populated Exon object. The gene symbol of
        should match that of the ExonList.

        Arguments:
          exon: Exon object representing exon to be added to the list

        """
        if exon.gene_symbol != self.gene_symbol:
            raise Exception("Exon gene symbol doesn't match list symbol")
        self.exons.append(exon)

    def sort(self,attr):
        """Sort the exons in the list based on a specific attribute

        'attr' can be one of 'log2_fold_change' or 'p_value'.

        For log2_fold_change, the exons are sorted highest to lowest;
        for p_value, they are sorted lowest to highest.

        Arguments:
          attr: attribute to sort on ('log2_fold_change' or 'p_value')

        """
        reverse = True
        if attr == 'log2_fold_change':
            # Sorts largest to smallest
            reverse = True
        elif attr == 'p_value':
            # Sorts smallest to largest
            reverse = False
        else:
            # Unknown attribue
            raise AttributeError("Unknown attribute '%s'" % attr)
        self.exons.sort(key=attrgetter(attr),reverse=reverse)

    def best_exon(self,attr):
        """Fetch the 'best' exon based on the specified attribute

        'attr' can be one of 'log2_fold_change' or 'p_value'.

        Depending on the attribute chosen, the 'best' exon will be
        either the one with the largest absolute log2_fold_change,
        or the one with the smallest p_value.

        Arguments:
          attr: attribute to sort on ('log2_fold_change' or 'p_value')

        Returns:
          Exon object corresponding to the 'best' exon.

        """
        value = attrgetter(attr)
        if attr == 'log2_fold_change':
            f = lambda x,y: x if abs(value(x)) > abs(value(y)) else y
        elif attr == 'p_value':
            f = lambda x,y: x if abs(value(x)) < abs(value(y)) else y
        else:
            raise AttributeError("Unrecognised attribute '%s'" % attr)
        best = self.exons[0]
        for exon in self.exons[1:]:
            best = f(exon,best)
        return best

    def best_exons(self,attr,n=3):
        """Fetch the 'best' exons based on the specified attribute

        'attr' can be one of 'log2_fold_change' or 'p_value'.

        Depending on the attribute chosen, the 'best' exons will be
        either the one with the largest absolute log2_fold_change,
        or the one with the smallest p_value.

        Arguments:
          attr: attribute to sort on ('log2_fold_change' or 'p_value')
          n: optional, specify the number of best exons to return
            (defaults to 3)

        Returns:
          New ExonList object only containing the top Exons.

        """
        self.sort(attr)
        value = attrgetter(attr)
        best_exons = ExonList(self.gene_symbol)
        if value(self.best_exon(attr)) < 0:
            # Reverse the initial sort order
            self.exons = self.exons[::-1]
        exon_list = self.exons[:n]
        for exon in exon_list:
            best_exons.add_exon(exon)
        return best_exons

    def average(self):
        """Return data averaged across all Exons in the list

        Average the values stored in each Exon's 'data' attribute
        and return a new list with the averaged values.

        Where an average can't be produced (e.g. non-numerical
        data), None is assigned to the position of the data item
        in the list ofaveraged values.

        Returns:
          List with averaged values.

        """
        # Sum each data item across all Exons in the list
        summed_data = None
        for exon in self:
            if summed_data is None:
                summed_data = []
                for item in exon.data:
                    summed_data.append(item)
            else:
                for i in range(len(summed_data)):
                    try:
                        summed_data[i] += float(exon.data[i])
                    except ValueError:
                        summed_data[i] = None
        # Divide sums to get averages
        averaged_data = []
        if summed_data is not None:
            n = float(len(self))
            for s in summed_data:
                try:
                    averaged_data.append(s/n)
                except TypeError:
                    averaged_data.append(None)
        return averaged_data

    def __len__(self):
        return len(self.exons)

    def __getitem__(self,i):
        # Makes object iterable
        return self.exons[i]

class Exon:
    """Store data for a single exon

    Attributes:

    name: name associated with the exon (e.g. a probset)
    gene_symbol: gene symbol associated with the exon
    log2_fold_change: log2FoldChange (None if not set)
    p_value: p-value (None if not set)
    data: arbitrary list of data values associated with the exon

    """
    def __init__(self,name,gene_symbol,log2_fold_change=None,p_value=None,data=[]):
        """Create a new Exon instance

        Arguments:
          name: name associated with the exon (e.g. a probset)
          gene_symbol: gene symbol associated with the exon
          log2_fold_change: log2FoldChange (optional)
          p_value: p-value (optional)
          data: arbitrary list of data values associated with the
            exon (optional)

        """
        self.name = str(name)
        self.gene_symbol = str(gene_symbol)
        if log2_fold_change is not None:
            self.log2_fold_change = float(log2_fold_change)
        else:
            self.log2_fold_change = None
        if p_value is not None:
            self.p_value = float(p_value)
        else:
            self.p_value = None
        self.data = data

    def __repr__(self):
        return "%s:%s:log2FoldChange=%s;p-value=%s" % (self.name,
                                                       self.gene_symbol,
                                                       self.log2_fold_change,
                                                       self.p_value)

########################################################################
# Functions
#########################################################################

def best_exons(fp_in,fp_out,rank_by='log2_fold_change',
               probeset_col=0,gene_symbol_col=1,log2_fold_change_col=12,
               p_value_col=13):
    """Read exon data from file, find 'best' exons & output averaged data

    This function performs the 'best_exons' procedure: it reads exon
    data from a file, finds the 'best' exons for each gene symbol, and
    outputs averaged data for each gene symbol to a second file.

    Assumuptions are that the input file consists of tab separated values
    (with the first line optionally being a header line), and that the
    following column positions correspond to the data items below:

    Column 0:  probeset name
    Column 1:  gene symbol
    Column 12: log2 fold change
    Column 13: p-value

    (Columns numbered from 0.) These defaults can be changed using the
    appropriate function arguments.

    The final column of the output file is a flag indicating gene symbols
    for which there are only 4 exons or less in the input file.

    'rank_by' selects the criterion used to rank the exons. Possible
    values are any that are recognised by the 'best_exons' method of the
    ExonList class (currently only 'log2_fold_change' and 'p_value').

    Arguments:
      fp_in: file object for input file (must be opened for reading)
      fp_out: file object for output file (must be opened for writing)
      rank_by: (optional) criterion used to rank the exons

    """
    # Dictionary to store gene symbols
    gene_symbols = bcf_utils.OrderedDictionary()
    
    # Report lookup for specific columns
    print("Column assignments (numbered from zero):")
    print("* Probe set       : column %2d (%s column)" % (probeset_col,
                                                          ordinal(probeset_col+1)))
    print("* Gene symbol     : column %2d (%s column)" % (gene_symbol_col,
                                                          ordinal(gene_symbol_col+1)))
    print("* Log2 fold change: column %2d (%s column)" % (log2_fold_change_col,
                                                          ordinal(log2_fold_change_col+1)))
    print("* P-value         : column %2d (%s column)" % (p_value_col,
                                                          ordinal(p_value_col+1)))

    # Test if first line of file is a header line
    first_line_is_header = False
    header_line = None
    for line in TabFileIterator(fp=fp_in):
        break
    try:
        # Try to populate an Exon object as a test
        Exon(line[probeset_col],
             line[gene_symbol_col],
             log2_fold_change=line[log2_fold_change_col],
             p_value=line[p_value_col])
    except ValueError:
        first_line_is_header = True
        header_line = str(line)

    # Read data from file
    for line in TabFileIterator(fp=fp_in):
        ##print("%s" % line)
        if first_line_is_header:
            # Skip first line
            first_line_is_header = False
            continue
        # Process data
        gene_symbol = line[gene_symbol_col]
        if gene_symbol not in gene_symbols:
            logging.debug("Gene symbol: %s" % gene_symbol)
            gene_symbols[gene_symbol] = ExonList(gene_symbol)
        gene_symbols[gene_symbol].add_exon(
            Exon(line[probeset_col],
                 gene_symbol,
                 log2_fold_change=line[log2_fold_change_col],
                 p_value=line[p_value_col],
                 data=[x for x in line])
            )

    # Write output header line
    if header_line is not None:
        header_line = header_line.split('\t')
        header_line.append("Less than 4 exons")
        del(header_line[probeset_col])
        fp_out.write("%s\n" % tsv_line(header_line))

    # Iterate through gene symbols and find 'best' exons
    for gene_symbol in gene_symbols:
        # Sort by log2FoldChange
        logging.debug("*** Processing %s ***" % gene_symbol)
        exon_list = gene_symbols[gene_symbol]
        # Fetch best exons (i.e. 'top' three) based on log2 fold change
        best_exons = exon_list.best_exons(rank_by,n=3)
        logging.debug("Top exons ranked by %s" % rank_by)
        for exon in best_exons:
            logging.debug("%s" % exon)
        # Average data values and write to file
        line = best_exons.average()
        if len(exon_list) < 4:
            logging.warning("Less than 4 exons for gene symbol '%s'" % gene_symbol)
            line.append('*')
        logging.debug("%s" % tsv_line(best_exons.average()))
        line[gene_symbol_col] = exon_list.gene_symbol
        del(line[probeset_col])
        logging.debug("%s" % tsv_line(line))
        fp_out.write("%s\n" % tsv_line(line))

def tsv_line(value_list):
    """Create tab-delimited line from Python list

    Given a Python list, returns a tab-delimited string with
    each value in the last converted to a string.

    Arguments:
      value_list: Python list of values

    Returns:
      String with list values separated by tabs.

    """
    return '\t'.join([str(x) for x in value_list])

def ordinal(i):
    """Return ordinal representation of integer

    Given an integer, returns the ordinal representation e.g. '1st' for
    1, '2nd' for 2 etc.

    Arguments:
      i: integer number

    Returns:
      Ordinal represenation of i.

    """
    suffixes = { 1:'st',2:'nd',3:'rd', 11:'th', 12:'th', 13:'th' }
    try:
        suffix = suffixes[int(i)%100]
    except KeyError:
        try:
            suffix = suffixes[int(i)%10]
        except KeyError:
            suffix = 'th'
    return "%s%s" % (i,suffix)

########################################################################
# Main program
#########################################################################

if __name__ == "__main__":

    # Set up logging output format
    logging.basicConfig(format='%(levelname)s: %(message)s')

    # Process command line
    p = argparse.ArgumentParser(
        description="Read exon and gene symbol data from EXONS_IN "
        "and picks the top three exons for each gene symbol, then "
        "outputs averages of the associated values to BEST_EXONS.")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+__version__)
    p.add_argument("--rank-by",action="store",dest="criterion",
                   default='log2_fold_change',
                   choices=('log2_fold_change','p_value',),
                   help="select the criterion for ranking the 'best' "
                   "exons; possible options are: 'log2_fold_change' "
                   "(default), or 'p_value'.")
    p.add_argument("--probeset-col",action="store",dest="probeset_col",
                   type=int,default=0,
                   help="specify column with probeset names (default=0, "
                   "columns start counting from zero)")
    p.add_argument("--gene-symbol-col",action="store",dest="gene_symbol_col",
                   type=int,default=1,
                   help="specify column with gene symbols (default=1, "
                   "columns start counting from zero)")
    p.add_argument("--log2-fold-change-col",action="store",
                   dest="log2_fold_change_col",type=int,default=12,
                   help="specify column with log2 fold change (default=12, "
                   "columns start counting from zero)")
    p.add_argument("--p-value-col",action="store",dest="p_value_col",
                   type=int,default=13,
                   help="specify column with p-value (default=13; columns "
                   "start counting from zero)")
    p.add_argument("--debug",action="store_true",dest="debug",default=False,
                   help="Turn on debug output")
    p.add_argument('filein',metavar="EXONS_IN",action='store',
                   help="input file with exon and gene symbol data")
    p.add_argument('fileout',metavar="BEST_EXONS",action='store',
                   help="output file averages from top three exons for each"
                   "gene symbol")
    args = p.parse_args()

    # Turn on debugging output
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Deal with input and output files
    filein = args.filein
    fileout = args.fileout
    print("%s %s" % (os.path.basename(sys.argv[0]),__version__))
    print("Reading data from %s, writing output to %s" % (filein,fileout))

    # Open files
    fp_in = io.open(filein,'rt')
    fp_out = io.open(fileout,'wt')
    
    # Run the best_exons procedure
    best_exons(
        fp_in,fp_out,
        rank_by=args.criterion,
        probeset_col=args.probeset_col,
        gene_symbol_col=args.gene_symbol_col,
        log2_fold_change_col=args.log2_fold_change_col,
        p_value_col=args.p_value_col
    )
    
    # Finished, close files
    fp_in.close()
    fp_out.close()
