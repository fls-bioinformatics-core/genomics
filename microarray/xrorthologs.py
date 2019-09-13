#!/usr/bin/env python
#
#     xrorthologs.py: cross-reference data for two species given probeset lookup
#     Copyright (C) University of Manchester 2012-2019 Peter Briggs, Leo Zeef
#
#     This code is free software; you can redistribute it and/or modify it
#     under the terms of the Artistic License 2.0 (see the file LICENSE
#     included with the distribution).
#
########################################################################
#
# xrorthologs.py
#
#########################################################################

"""xrorthlogs

Cross-references data for two species given a look-up file matching probe
set IDs for one species to those for the other.

Input is a look up file consisting of tab-delimited columns, where the
first column contains the probe set id from the first species and the
fourth column contains the matching ids (separated by commas) from the
second, e.g.:

...
121_at	7849	18510	1418208_at,1446561_at
1255_g_at	2978	14913	1421061_a
1316_at	7067	21833	1426997_at,1443952_at,1454675_at
1320_at	11099	24000	1419054_a_at,1419055_a_at,1453298_at
1405_i_at	6352	20304	1418126_at
...

The program then expects tab-delimited data files for each species, where
the first column in each is a probe set id.

The outputs are versions of the two input files with data from the other
appended based on matching up the probe set ids.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import sys
import os
import io
import logging
import argparse
from builtins import range

#######################################################################
# Class definitions
#######################################################################

class ProbeSetLookup(object):

    def __init__(self,lookup_data_file=None,lookup_data_fp=None,
                 cols=(0,3), major_delimiter='\t',minor_delimiter=',',
                 null_ids=('NA')):
        """Create and populate a ProbeSetLookup instance

        Read data from the specified look up file and construct
        look up tables which map probe_set names from one species
        to another.

        The input file can either be specified as a file name or
        as a file-like object already opened for reading.

        By default the look up file is expected to consist of
        tab-delimited columns, with the first column being the
        probe_set name for the first species and the 4th column
        being a comma-separated list of matching probe_set names
        for the second species.

        Arguments:
          lookup_data_file: name of file to read data from
          lookup_data_fp: file-like object opened for reading
            (alternative to supplying lookup_data_file).
            lookup_data_fp will be used preferentially if non-null
          cols: (optional) tuple indicating which columns to
            read probe_set IDs from for each species
          major_delimiter: (optional) delimiter character for
            splitting file into columns
          minor_delimiter: (optional) delimiter character for
            splitting into further columns
          null_ids: (optional) tuple of IDs that should be ignored
            (i.e. treated as 'null' values)
        """
        # Initialise
        self.__lookup = {}
        self.__reverse_lookup = {}
        # Open file and read in data
        if lookup_data_fp is None:
            fp = io.open(lookup_data_file,'rt')
        else:
            fp = lookup_data_fp
        for line in fp:
            # Split into columns on major delimiter
            data = line.strip().split(major_delimiter)
            # Get the data
            key = data[cols[0]]
            # Split again on minor delimiter
            values = []
            if minor_delimiter:
                for item in data[cols[1]].strip().split(minor_delimiter):
                    values.append(item)
            else:
                values.append(data[cols[1]])
            for value in values:
                # Check for 'null' values
                if value in null_ids:
                    continue
                # Store the data
                try:
                    self.__lookup[key].append(value)
                except KeyError:
                    self.__lookup[key] = [value]
                try:
                    self.__reverse_lookup[value].append(key)
                except KeyError:
                    self.__reverse_lookup[value] = [key]
        # Finished - close the file
        if lookup_data_fp is None:
            fp.close()

    def lookup(self,probe_set_id):
        """Return probe_set_ids from second species that match one from first
        """
        try:
            return self.__lookup[probe_set_id]
        except KeyError:
            # Not found, return empty list
            return []

    def reverse_lookup(self,probe_set_id):
        """Return probe_set_ids from first species that match one from second
        """
        try:
            return self.__reverse_lookup[probe_set_id]
        except KeyError:
            # Not found, return empty list
            return []

class IndexedFile(object):
    """Read a file into memory and index for fast retrieval of lines
    """
    def __init__(self,filen=None,fp=None,first_line_is_header=False):
        """Create a new IndexedFile instance

        Arguments:
          filen: name of file to read data from
          fp: open file-like object to read data from (used in
            preference to filen, if supplied)
          first_line_is_header: skip first line of the input
            data file
        """
        self.__header = None
        self.__keys = []
        self.__content = {}
        if fp is None:
            fp = io.open(filen,'rt')
            close_fp = True
        else:
            close_fp = False
        for line in fp:
            if first_line_is_header and self.__header is None:
                # Capture first line as header
                self.__header = line.rstrip('\n')
                continue
            # Get index for line
            try:
                key = line.rstrip('\n').split('\t')[0]
            except IndexError:
                # Can't be indexed
                pass
            # Store line against key
            if self.__content.has_key(key):
                print("*** Multiple lines with same index ***")
                sys.exit(1)
            self.__keys.append(key)
            self.__content[key] = line.rstrip('\n')
        # Done
        if close_fp: fp.close()
    
    def fetch(self,key):
        """Fetch a line from the indexed file matching the specified key
        """
        try:
            return self.__content[key]
        except KeyError:
            return None

    def keys(self):
        """Return the keys in file order
        """
        return self.__keys

    def header(self):
        """Return the header
        """
        return self.__header

#######################################################################
# Functions
#######################################################################

def combine_data(data_file_1,data_file_2,lookup,outfile):
    """Append data from one file to another using a lookup

    This is a wrapper for the combine_data_main function, which
    opens the specified file objects for reading the input and
    writing the output.

    Arguments:
      data_file_1: tab-delimited data file with first column being
        probe set ids
      data_file_2: tab-delimited data file with first column being
        probe set ids
      lookup: function object instance which returns probe set ids
        in data_file_2 that match a probe set id in data_file_1.
        (Note that the 'lookup' and 'reverse_lookup' methods of the
        ProbeSetLookup class can fulfill this function.)
      outfile: name of output file to write lines from data_file_1
        appended with data from data_file_2
    """
    # Read in tabbed data
    print("Reading in data from %s" % data_file_1)
    data1 = IndexedFile(data_file_1,first_line_is_header=True)
    print("Reading in data from %s" % data_file_2)
    data2 = IndexedFile(data_file_2,first_line_is_header=True)

    # Open output file
    fp = io.open(outfile,'wt')

    # Call main function to do the actual work
    combine_data_main(data1,data2,lookup,fp)

    # Finished
    fp.close()
    print("Output written to '%s'" % outfile)

def combine_data_main(data1,data2,lookup,foutput):
    """Append data from one file to another using a lookup

    Arguments:
      data1: IndexedFile object populated with data from
        tab-delimited file with first column being probe set ids
      data2: IndexedFile object populated with data from
        tab-delimited file with first column being probe set ids
        probe set ids
      lookup: function object instance which returns probe set ids
        in data2 that match a probe set id in data1.
        (Note that the 'lookup' and 'reverse_lookup' methods of the
        ProbeSetLookup class can fulfill this function.)
      fout: file-like object opened for writing, to output lines
        from data1 appended with data from data2
    """

    # Get the maximum number of ortholog probesets we'll have to append
    max_orthologs = 0
    for probe_set_id in data1.keys():
        max_orthologs = max(max_orthologs,len(lookup(probe_set_id)))
    logging.debug("Max_orthologs = %d" % max_orthologs)
    
    # Write header line
    line = [data1.header()]
    for i in range(1,max_orthologs+1):
        logging.debug("Adding header set #%d" % i)
        for item in data2.header().split('\t'): line.append("%s_%s" % (item,i))
    foutput.write("%s\n" % '\t'.join(line))

    # Append data
    for probe_set_id in data1.keys():
        # Build line to output to file
        line = [data1.fetch(probe_set_id)]
        # Get the corresponding ortholog probe set ID(s)
        logging.debug("Processing probe set ID %s" % probe_set_id)
        for ortholog_probe_set_id in lookup(probe_set_id):
            ortholog_data = data2.fetch(ortholog_probe_set_id)
            if ortholog_data is not None:
                line.append(ortholog_data)
        # Write line to file
        foutput.write("%s\n" % '\t'.join(line))

#######################################################################
# Tests
#######################################################################

import unittest

class TestProbeSetLookup(unittest.TestCase):
    """Test the ProbeSetLookup class
    """

    def setUp(self):
        # Example look up data
        self.fp1 = io.StringIO(u"""ps_1	gid_1	gid_2	ps_2
1053_at	5982	19718	1417503_at,1457638_x_at,1457669_x_at
117_at	3310	NA	NA
121_at	7849	18510	1418208_at,1446561_at
1255_g_at	2978	14913	1421061_at
1294_at	7318	74153	1426970_a_at,1426971_at,1437317_at
203281_s_at	7318	74153	1426970_a_at,1426971_at,1437317_at
""")
        self.fp2 = io.StringIO(u"""ps_1	gid_1	gid_2	ps_2
1053_at	1417503_at,1457638_x_at,1457669_x_at
117_at	NA
121_at	1418208_at,1446561_at
1255_g_at	1421061_at
1294_at	1426970_a_at,1426971_at,1437317_at
203281_s_at	1426970_a_at,1426971_at,1437317_at
""")

    def test_lookup(self):
        """Test forward lookup
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.lookup('1255_g_at'),['1421061_at'])
        self.assertEqual(lookup.lookup('1294_at'),['1426970_a_at',
                                                   '1426971_at',
                                                   '1437317_at'])

    def test_reverse_lookup(self):
        """Test reverse lookup
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.reverse_lookup('1421061_at'),['1255_g_at'])
        self.assertEqual(lookup.reverse_lookup('1437317_at'),['1294_at','203281_s_at'])

    def test_null_value(self):
        """Test checking for null value
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp1)
        self.assertEqual(lookup.reverse_lookup('117_at'),[])

    def test_lookup_different_columns(self):
        """Test using different columns from input file
        """
        lookup = ProbeSetLookup(lookup_data_fp=self.fp2,cols=(0,1))
        self.assertEqual(lookup.lookup('1255_g_at'),['1421061_at'])
        self.assertEqual(lookup.lookup('1294_at'),['1426970_a_at',
                                                   '1426971_at',
                                                   '1437317_at'])

class TestIndexedFile(unittest.TestCase):
    """Test the IndexedFile class
    """
    def setUp(self):
        # Example data
        self.fp = io.StringIO(u"""1007_s_at	U48705	chr6:30856165-30867931 (+) // 95.63 // p21.33	discoidin domain receptor tyrosine kinase 1	DDR1	900.8253051	1002.945639	0.898179	-1.11336
1053_at	M87338	chr7:73646002-73668732 (-) // 70.86 // q11.23	"replication factor C (activator 1) 2, 40kDa"	RFC2	953.0037594	1100.132756	0.866288	-1.15435
117_at	X51757	chr1:161494448-161496380 (+) // 99.59 // q23.3 /// chr1:161576080-161578007 (+) // 98.03 // q23.3	heat shock 70kDa protein 6 (HSP70B')	HSPA6	37.34984439	43.5182996	0.858256	-1.16515
121_at	X69699	chr2:113974939-114036488 (-) // 98.3 // q13	paired box 8	PAX8	293.4040238233.8182798	1.25484	1.25484
""")

    def test_indexed_file(self):
        """Test IndexedFile methods
        """
        indexed_file = IndexedFile(fp=self.fp)
        self.assertEqual(indexed_file.keys(),['1007_s_at',
                                              '1053_at',
                                              '117_at',
                                              '121_at'])
        self.assertEqual(indexed_file.fetch('117_at'),"""117_at	X51757	chr1:161494448-161496380 (+) // 99.59 // q23.3 /// chr1:161576080-161578007 (+) // 98.03 // q23.3	heat shock 70kDa protein 6 (HSP70B')	HSPA6	37.34984439	43.5182996	0.858256	-1.16515""")

class TestCombineData(unittest.TestCase):
    def setUp(self):
        # Example data
        self.species1 = u"""Probe_Set_ID	Public_ID
1053_at	M87338
117_at	X51757
121_at	X69699
1255_g_at	L36861
"""
        self.species2 = u"""Probe_Set_ID	Public_ID
1417503_at	NM_020022
1457638_x_at	AV039064
1457669_x_at	AV096765
1418208_at	NM_011040
1446561_at	BB497767
1421061_at	NM_008189
1426970_a_at	AK004894
1426971_at	AK004894
1437317_at	BB735820
"""
        self.lookup_data = u"""ps_1	gid_1	gid_2	ps_2
1053_at	5982	19718	1417503_at,1457638_x_at,1457669_x_at
117_at	3310	NA	NA
121_at	7849	18510	1418208_at,1446561_at
1255_g_at	2978	14913	1421061_at
1294_at	7318	74153	1426970_a_at,1426971_at,1437317_at
"""
        self.expected_output = u"""Probe_Set_ID	Public_ID	Probe_Set_ID_1	Public_ID_1	Probe_Set_ID_2	Public_ID_2	Probe_Set_ID_3	Public_ID_3
1053_at	M87338	1417503_at	NM_020022	1457638_x_at	AV039064	1457669_x_at	AV096765
117_at	X51757
121_at	X69699	1418208_at	NM_011040	1446561_at	BB497767
1255_g_at	L36861	1421061_at	NM_008189
"""

    def test_combine_data(self):
        """Test combine_data function
        """
        # Input data
        data1 = IndexedFile(fp=io.StringIO(self.species1),first_line_is_header=True)
        data2 = IndexedFile(fp=io.StringIO(self.species2),first_line_is_header=True)
        lookup = ProbeSetLookup(lookup_data_fp=io.StringIO(self.lookup_data))
        # Output "file"
        output_fp = io.StringIO()
        # Run data combination
        combine_data_main(data1,data2,lookup.lookup,output_fp)
        # Check output
        self.assertEqual(output_fp.getvalue(),self.expected_output)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":

    # Set up logging format
    logging.basicConfig(format='%(levelname)s: %(message)s')

    # Set up parser for command line
    p = argparse.ArgumentParser(
        description=
        "Cross-reference data from two species given a lookup "
        "file that maps probeset IDs from one species onto those "
        "onto the other. LOOKUPFILE is tab-delimited file with "
        "one probe set for species 1 per line in first column "
        "and a comma-separated list of the equivalent probe sets "
        "for species 2 in the fourth column. Data for the two "
        "species are in tab-delimited files SPECIES1 and "
        "SPECIES2. Output is two files: SPECIES1_appended.txt "
        "(SPECIES1 with the cross-referenced data from SPECIES2 "
        "appended to each line) and SPECIES2_appended.txt "
        "(SPECIES2 with SPECIES1 data appended).")

    p.add_argument("--debug",action="store_true",dest="debug",
                   default=False,
                   help="Turn on debugging output")
    p.add_argument('lookup',metavar="LOOKUPFILE",
                   help="tab-delimited file with one probe set "
                   "for species 1 per line in first column and a "
                   "comma-separated list of the equivalent probe "
                   "sets for species 2 in the fourth column")
    p.add_argument('species1',metavar="SPECIES1",
                   help="data for species 1")
    p.add_argument('species2',metavar="SPECIES2",
                   help="data for species 2")

    # Parse command line
    arguments = p.parse_args()

    # Debugging output
    if arguments.debug: logging.getLogger().setLevel(logging.DEBUG)

    # Construct lookup object from data file
    print("Building lookup tables from %s" % arguments.lookup)
    lookup = ProbeSetLookup(arguments.lookup,cols=(0,3))

    # Get files
    species1_data_file = arguments.species1
    species2_data_file = arguments.species2

    # Append the ortholog probe set(s) and data for 2nd species to first species
    print("### Appending species 2 data to species 1 ###")
    outfile = os.path.splitext(os.path.basename(species1_data_file))[0]+'_appended.txt'
    combine_data(species1_data_file,species2_data_file,lookup.lookup,outfile)

    # Append the ortholog probe set(s) and data for 1st species to second species
    print("### Appending species 1 data to species 2 ###")
    outfile = os.path.splitext(os.path.basename(species2_data_file))[0]+'_appended.txt'
    combine_data(species2_data_file,species1_data_file,lookup.reverse_lookup,outfile)

    # Finished
    print("Done")
    sys.exit()
