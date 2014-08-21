#!/bin/env python
#
#     best_exons.py: pick 'best' exons for gene symbols and average data
#     Copyright (C) University of Manchester 2013 Peter Briggs
#
########################################################################

__version__ = "1.2.0"

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

import sys
import os
import optparse
import logging
import TabFile
import bcf_utils
from collections import Iterator
from operator import attrgetter

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
        ...   print line

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
            self.__fp = open(filen,'rU')
        else:
            self.__fp = fp

    def next(self):
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
            raise Exception,"Exon gene symbol doesn't match list symbol"
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
            raise AttributeError, "Unknown attribute '%s'" % attr
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
            raise AttributeError, "Unrecognised attribute '%s'" % attr
        return reduce(f,self.exons)

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
    print "Column assignments (numbered from zero):"
    print "* Probe set       : column %2d (%s column)" % (probeset_col,
                                                          ordinal(probeset_col+1))
    print "* Gene symbol     : column %2d (%s column)" % (gene_symbol_col,
                                                          ordinal(gene_symbol_col+1))
    print "* Log2 fold change: column %2d (%s column)" % (log2_fold_change_col,
                                                          ordinal(log2_fold_change_col+1))
    print "* P-value         : column %2d (%s column)" % (p_value_col,
                                                          ordinal(p_value_col+1))

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
        ##print "%s" % line
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
# Tests
#########################################################################

import unittest
import cStringIO

class TestExon(unittest.TestCase):
    """Tests for the Exon class
    """
    def test_exon_no_data(self):
        exon = Exon("PSR19025918.hg.1","A1BG")
        self.assertEqual(exon.name,"PSR19025918.hg.1")
        self.assertEqual(exon.gene_symbol,"A1BG")
        self.assertEqual(exon.log2_fold_change,None)
        self.assertEqual(exon.p_value,None)
        self.assertEqual(str(exon),
                         "PSR19025918.hg.1:A1BG:log2FoldChange=None;p-value=None")

    def test_exon_with_data(self):
        log2_fold_change = -0.056323333
        p_value = 0.5347865
        exon = Exon("PSR19025918.hg.1","A1BG",
                    log2_fold_change=log2_fold_change,
                    p_value=p_value)
        self.assertEqual(exon.name,"PSR19025918.hg.1")
        self.assertEqual(exon.gene_symbol,"A1BG")
        self.assertEqual(exon.log2_fold_change,log2_fold_change)
        self.assertEqual(exon.p_value,p_value)
        self.assertEqual(str(exon),
                         "PSR19025918.hg.1:A1BG:log2FoldChange=%s;p-value=%s" %
                         (float(log2_fold_change),float(p_value)))

class TestExonList(unittest.TestCase):
    """Tests for the ExonList class
    """
    def test_exon_list(self):
        exon_list = ExonList("A1BG")
        self.assertEqual(exon_list.gene_symbol,"A1BG")
        self.assertEqual(len(exon_list),0)
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG"))
        self.assertEqual(len(exon_list),2)

    def test_exon_list_iteration(self):
        exon_list = ExonList("A1BG")
        self.assertEqual(exon_list.gene_symbol,"A1BG")
        self.assertEqual(len(exon_list),0)
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG"))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG"))
        for exon,name in zip(exon_list,
                             ("PSR19025918.hg.1",
                              "PSR19025921.hg.1",
                              "PSR19025922.hg.1")):
            self.assertEqual(name,exon.name)

    def test_exon_list_sort_on_log2_fold_change(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        exon_list.sort('log2_fold_change')
        last_log2_fold_change = None
        for exon in exon_list.exons:
            if last_log2_fold_change is not None:
                self.assertTrue(last_log2_fold_change >= exon.log2_fold_change)
            last_log2_fold_change = exon.log2_fold_change

    def test_exon_list_sort_on_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",p_value=0.6550312))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",p_value=0.5002532))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",p_value=0.3521274))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",p_value=0.7720515))
        exon_list.sort('p_value')
        last_p_value = None
        for exon in exon_list.exons:
            if last_p_value is not None:
                self.assertTrue(last_p_value <= exon.p_value)
            last_p_value = exon.p_value

    def test_get_best_exon_from_log2_fold_change(self):
        # First example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exon = exon_list.best_exon('log2_fold_change')
        self.assertEqual(best_exon.name,"PSR19025927.hg.1")
        # Second example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exon = exon_list.best_exon('log2_fold_change')
        self.assertEqual(best_exon.name,"PSR19025925.hg.1")

    def test_get_best_exon_from_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",p_value=0.6550312))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",p_value=0.5002532))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",p_value=0.3521274))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",p_value=0.7720515))
        best_exon = exon_list.best_exon('p_value')
        self.assertEqual(best_exon.name,"PSR19025928.hg.1")

    def test_get_best_exons_from_log2_fold_change(self):
        # First example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025925.hg.1",
                                         "PSR19025918.hg.1",
                                         "PSR19025929.hg.1")):
            self.assertEqual(name,exon.name)
        # Second example
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025926.hg.1","A1BG",log2_fold_change=0.059556667))
        exon_list.add_exon(Exon("PSR19025927.hg.1","A1BG",log2_fold_change=0.119746667))
        exon_list.add_exon(Exon("PSR19025928.hg.1","A1BG",log2_fold_change=-0.090296667))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433))
        exon_list.add_exon(Exon("PSR19025930.hg.1","A1BG",log2_fold_change=0.02569))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025927.hg.1",
                                         "PSR19025926.hg.1",
                                         "PSR19025930.hg.1")):
            self.assertEqual(name,exon.name)

    def test_get_best_exons_from_p_value(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",p_value=0.5347865))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",p_value=0.5820691))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",p_value=0.7582407))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",p_value=0.4111732))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",p_value=0.7716908))
        best_exons = exon_list.best_exons('p_value')
        self.assertEqual(len(best_exons),3)
        for exon,name in zip(best_exons,("PSR19025925.hg.1",
                                         "PSR19025918.hg.1",
                                         "PSR19025921.hg.1")):
            self.assertEqual(name,exon.name)

    def test_get_best_exons_small_list(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333))
        best_exons = exon_list.best_exons('log2_fold_change')
        self.assertEqual(len(best_exons),2)
        for exon,name in zip(best_exons,("PSR19025921.hg.1",
                                         "PSR19025918.hg.1")):
            self.assertEqual(name,exon.name)

    def test_average_numerical_data(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333,
                                data=[8.0,8.5,9.0]))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333,
                                data=[7.0,7.0,7.5]))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667,
                                data=[7.0,7.5,7.0]))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211,
                                data=[7.0,7.5,7.5]))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433,
                                data=[5.0,6.0,6.5]))
        averaged_data = exon_list.average()
        for average,expected in zip(averaged_data,(6.8,
                                                   7.3,
                                                   7.5,)):
            self.assertEqual(average,expected)

    def test_average_mixed_data(self):
        exon_list = ExonList("A1BG")
        exon_list.add_exon(Exon("PSR19025918.hg.1","A1BG",log2_fold_change=-0.056323333,
                                data=["PSR19025918.hg.1","A1BG",8.0,8.5,9.0]))
        exon_list.add_exon(Exon("PSR19025921.hg.1","A1BG",log2_fold_change=0.075113333,
                                data=["PSR19025921.hg.1","A1BG",7.0,7.0,7.5]))
        exon_list.add_exon(Exon("PSR19025922.hg.1","A1BG",log2_fold_change=0.037316667,
                                data=["PSR19025922.hg.1","A1BG",7.0,7.5,7.0]))
        exon_list.add_exon(Exon("PSR19025925.hg.1","A1BG",log2_fold_change=-0.10211,
                                data=["PSR19025925.hg.1","A1BG",7.0,7.5,7.5]))
        exon_list.add_exon(Exon("PSR19025929.hg.1","A1BG",log2_fold_change=-0.02433,
                                data=["PSR19025929.hg.1","A1BG",5.0,6.0,6.5]))
        averaged_data = exon_list.average()
        for average,expected in zip(averaged_data,(None,
                                                   None,
                                                   6.8,
                                                   7.3,
                                                   7.5,)):
            self.assertEqual(average,expected)

class TestBestExonsFunction(unittest.TestCase):
    """Tests for the best_exons function
    """
    def setUp(self):
        self.fp_in = cStringIO.StringIO(
"""Probeset ID	Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value
PSR19025918.hg.1	A1BG	8.66755	8.57167	8.67935	8.73928	8.8101	8.67708	8.719	8.66267	0.961711	-1.03981	-0.056323333	0.5347865	0.725553
PSR19025921.hg.1	A1BG	7.41787	7.17961	7.40133	7.6528	7.28002	7.49215	7.36641	7.44152	1.05344	1.05344	0.075113333	0.5820691	0.7383465
PSR19025922.hg.1	A1BG	7.50871	7.57826	7.30645	7.61757	7.62477	7.35605	7.47998	7.51729	1.02621	1.02621	0.037316667	0.7582407	0.779675
PSR19025925.hg.1	A1BG	7.63027	7.58905	7.47073	7.30594	7.72141	7.62109	7.60747	7.50536	0.93167	-1.07334	-0.10211	0.4111732	0.6843703
PSR19025926.hg.1	A1BG	5.81209	5.89395	5.54714	5.50756	5.68944	5.82583	5.68289	5.74245	1.04215	1.04215	0.059556667	0.6550312	0.7570314
PSR19025927.hg.1	A1BG	6.36444	6.68116	6.4564	6.72256	6.32783	6.10419	6.38289	6.50264	1.08654	1.08654	0.119746667	0.5002532	0.7148393
PSR19025928.hg.1	A1BG	6.81897	6.76408	6.71385	6.55553	6.81366	6.75598	6.78216	6.69186	0.939329	-1.06459	-0.090296667	0.3521274	0.6606918
PSR19025929.hg.1	A1BG	8.45677	8.48843	8.44105	8.35951	8.52791	8.5048	8.47524	8.45091	0.983278	-1.01701	-0.02433	0.7716908	0.7822665
PSR19025930.hg.1	A1BG	6.86999	7.02037	6.87301	6.80701	6.86267	6.85536	6.86856	6.89425	1.01797	1.01797	0.02569	0.7720515	0.7823363
PSR19013233.hg.1	A1BG-AS1	7.08364	6.81108	6.98058	6.70364	6.85819	6.65799	6.97414	6.72424	0.840952	-1.18913	-0.2499	0.02997736	0.3577892
PSR19013235.hg.1	A1BG-AS1	6.55169	6.35594	6.37204	6.43176	6.53112	6.39524	6.48495	6.39432	0.939112	-1.06484	-0.090636667	0.3146458	0.6438243
PSR19013236.hg.1	A1BG-AS1	6.42098	5.92741	6.46143	6.36713	6.25817	6.65999	6.38019	6.31818	0.957924	-1.04392	-0.062016667	0.742372	0.7767089
""")

    def test_best_exons_by_log2_fold_change(self):
        expected_output = \
"""Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value	Less than 4 exons
A1BG	6.53146666667	6.58490666667	6.46829	6.62764	6.43243	6.47405666667	6.47739666667	6.56220333333	1.06071	1.06071	0.0848055556667	0.579117833333	0.736739066667
A1BG-AS1	6.68543666667	6.36481	6.60468333333	6.50084333333	6.54916	6.57107333333	6.61309333333	6.47891333333	0.912662666667	-1.09929666667	-0.134184444667	0.36233172	0.592774133333	*
"""
        fp_out = cStringIO.StringIO()
        best_exons(self.fp_in,fp_out,rank_by='log2_fold_change')
        output = fp_out.getvalue()
        for obs,exp in zip(output.split(),expected_output.split()):
            ##print "%s, %s" % (obs,exp)
            self.assertEqual(obs,exp)

    def test_best_exons_by_p_value(self):
        expected_output = \
"""Gene Symbol	1_1	1_2	2_1	2_2	3_1	3_2	Mean(Cntl)	Mean(siETV4)	Ratio(siETV4 vs. Cntl)	Fold-Change(siETV4 vs. Cntl)	log2FoldChange	p-value	q-value	Less than 4 exons
A1BG	6.93789333333	7.01143	6.88032666667	6.86134333333	6.9543	6.82708666667	6.92417333333	6.89995333333	0.985846333333	-0.350463333333	-0.02422	0.4211846	0.6866338
A1BG-AS1	6.68543666667	6.36481	6.60468333333	6.50084333333	6.54916	6.57107333333	6.61309333333	6.47891333333	0.912662666667	-1.09929666667	-0.134184444667	0.36233172	0.592774133333	*
"""
        fp_out = cStringIO.StringIO()
        best_exons(self.fp_in,fp_out,rank_by='p_value')
        output = fp_out.getvalue()
        for obs,exp in zip(output.split(),expected_output.split()):
            ##print "%s, %s" % (obs,exp)
            self.assertEqual(obs,exp)

class TestTSVLineFunction(unittest.TestCase):
    """Tests for the tsv_line function
    """
    def test_tsv_line(self):
        data = ['one',2,'3']
        self.assertEqual(tsv_line(data),"one\t2\t3")

class TestOrdinalFunction(unittest.TestCase):
    """Tests for the ordinal function
    """
    def test_ordinal(self):
        self.assertEqual('1st',ordinal(1))
        self.assertEqual('2nd',ordinal(2))
        self.assertEqual('3rd',ordinal(3))
        self.assertEqual('4th',ordinal(4))
        self.assertEqual('10th',ordinal(10))
        self.assertEqual('11th',ordinal(11))
        self.assertEqual('12th',ordinal(12))
        self.assertEqual('13th',ordinal(13))
        self.assertEqual('21st',ordinal(21))
        self.assertEqual('22nd',ordinal(22))
        self.assertEqual('23rd',ordinal(23))

########################################################################
# Main program
#########################################################################

if __name__ == "__main__":

    # Set up logging output format
    logging.basicConfig(format='%(levelname)s: %(message)s')

    # Process command line
    p = optparse.OptionParser(usage="%prog [OPTIONS] EXONS_IN BEST_EXONS",
                              version="%prog "+__version__,
                              description="Read exon and gene symbol data from EXONS_IN "
                              "and picks the top three exons for each gene symbol, then "
                              "outputs averages of the associated values to BEST_EXONS.")

    p.add_option("--rank-by",action="store",dest="criterion",default='log2_fold_change',
                 choices=('log2_fold_change','p_value',),
                 help="select the criterion for ranking the 'best' exons; possible options "
                 "are: 'log2_fold_change' (default), or 'p_value'.")
    p.add_option("--probeset-col",action="store",dest="probeset_col",
                 type='int',default=0,
                 help="specify column with probeset names (default=0, columns start "
                 "counting from zero)")
    p.add_option("--gene-symbol-col",action="store",dest="gene_symbol_col",
                 type='int',default=1,
                 help="specify column with gene symbols (default=1, columns start counting "
                 "from zero)")
    p.add_option("--log2-fold-change-col",action="store",dest="log2_fold_change_col",
                 type='int',default=12,
                 help="specify column with log2 fold change (default=12, columns start "
                 "counting from zero)")
    p.add_option("--p-value-col",action="store",dest="p_value_col",
                 type='int',default=13,
                 help="specify column with p-value (default=13; columns start counting "
                 "from zero)")
    p.add_option("--test",action="store_true",dest="test",default=False,
                 help="Run unit tests")
    p.add_option("--debug",action="store_true",dest="debug",default=False,
                 help="Turn on debug output")
    options,args = p.parse_args()

    # Turn on debugging output
    if options.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run unit tests
    if options.test:
        logging.getLogger().setLevel(logging.ERROR)
        suite = unittest.TestSuite(unittest.TestLoader().\
                                   discover(os.path.dirname(sys.argv[0]), \
                                            pattern=os.path.basename(sys.argv[0]))
)
        unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit()

    # Deal with input and output files
    if len(args) < 2:
        p.error("Need to supply input and output file names")
    filein = args[0]
    fileout = args[1]
    print "Reading data from %s, writing output to %s" % (filein,fileout)

    # Open files
    fp_in = open(filein,'rU')
    fp_out = open(fileout,'w')
    
    # Run the best_exons procedure
    best_exons(
        fp_in,fp_out,
        rank_by=options.criterion,
        probeset_col=options.probeset_col,
        gene_symbol_col=options.gene_symbol_col,
        log2_fold_change_col=options.log2_fold_change_col,
        p_value_col=options.p_value_col
    )
    
    # Finished, close files
    fp_in.close()
    fp_out.close()
