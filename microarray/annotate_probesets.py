#!/usr/bin/env python
#
#     annotate_probesets.py: add descriptions to probe set names
#     Copyright (C) University of Manchester 2012,2019 Peter Briggs, Leo Zeef
#
#######################################################################
#
# annotate_probesets.py
#
#######################################################################

#######################################################################
# Module metadata
#######################################################################

__version__ = "0.1.2"

#######################################################################
# Import modules that this module depends on
#######################################################################

import argparse
import os
import io
import logging

#######################################################################
# Module data
#######################################################################

# Put all the data into the 'descriptions' global dictionary
descriptions = {
    '_at'  : "Rank 1: _at : anti-sense target, unique for the gene",
    '_st'  : \
        "Control: _st : sense target (only some control probes are in sense orientation on " \
        "the array)",
    '_s_at':  \
        "Warning: _s_at : designates probe sets that share common probes among multiple " \
        "transcripts from different genes",
    '_a_at': \
        "Rank 2: _a_at : designates probe sets that recognize multiple alternative transcripts " \
        "from the same gene (splice variants)",
    '_x_at': \
        "Warning: _x_at : designates probe sets where it was not possible to select either a " \
        "unique probe set or a probe set with identical probes among multiple transcripts. " \
        "Rules for cross-hybridization were dropped. Therefore, these probe sets may " \
        "cross-hybridize in an unpredictable manner with other sequences",
    '_g_at': "Warning: _g_at : similar genes, also unique probe sets elsewhere on the array",
    '_f_at': \
        "Warning: _f_at : similarity rules dropped, probe set will recognize more than one gene",
    '_i_at': \
        "Rank3: _i_at : designates sequences for which there are fewer than the required " \
        "numbers of unique probes specified in the design",
    '_b_at': "Warning: _b_at : all probe selection rules were ignored. Withdrawn from GenBank",
    '_l_at': "Rank 1: _l_at : sequence represented by more than 20 probe pairs",
    '_r_'  : \
        "Warning: _r_ : designates sequences for which it was not possible to pick a full set " \
        "of unique probes using Affymetrix probe selection rules. Probes were picked after " \
        "dropping some of the selection rules"
}

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Functions
#######################################################################

def get_annotation_description(probeset_id):
    """Return the annotation description based on the probeset id

    Given the probe set name as 'probeset_id', return the description
    based on the extension.
    """
    try:
        return descriptions[get_probeset_extension(probeset_id)]
    except KeyError:
        # Lookup failed
        logging.error("No match for probe set name '%s'" % probeset_id)

def get_probeset_extension(probeset_id):
    """Return the extension component from a probeset id

    Given the probe set name as 'probeset_id', extract and return the
    extension (i.e. the trailing part of the name, e.g. '_a_at').

    Where multiple extensions might match (e.g. '_at' and '_a_at'),
    return the longest match.

    If the name contains '_r_' then this take precedence over other
    matches.
    """
    extension = None
    try:
        # Look for _r_
        probeset_id.index('_r_')
        extension = '_r_'
    except ValueError:
        for ext in descriptions:
            # Make sure we keep the longest match
            if probeset_id.endswith(ext):
                if not extension or len(ext) > len(extension):
                    extension = ext
    return extension

def main():
    """Main program
    """
    # Process command line
    p = argparse.ArgumentParser(
        description="Annotate probeset list based on name: reads in "
        "first column of tab-delimited input file 'probe_set_file' as a "
        "list of probeset names and outputs these names to another "
        "tab-delimited file with a description for each. "
        "Output file name can be specified with the -o option, otherwise "
        "it will be the input file name with '_annotated' appended.")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+__version__)
    p.add_argument('-o',action='store',dest='out_file',default=None,
                   help="specify output file name")
    p.add_argument('in_file',metavar='IN_FILE',action='store',
                   help="input probeset file")
    arguments = p.parse_args()

    # Input and output file
    in_file = arguments.in_file
    if arguments.out_file is not None:
        out_file = arguments.out_file
    else:
        out_file = os.path.splitext(os.path.basename(in_file))[0]+"_annotated" + \
            os.path.splitext(in_file)[1]

    # Process the file a line at a time
    read_first_line = False
    fp = io.open(in_file,'rt')
    fo = io.open(out_file,'wt')
    fo.write(u"Probe Set ID\tProbe Set Info\n")
    for line in fp:
        # Extract probeset name
        probeset = line.strip('\n').split('\t')[0]
        if not read_first_line:
            # Skip first line if it doesn't have a valid code
            read_first_line = True
            if not get_probeset_extension(probeset): continue
        # Construct and write output
        new_line = '\t'.join((probeset,get_annotation_description(probeset)))
        fo.write(new_line+'\n')
    fp.close()
    fo.close()

#######################################################################
# Tests
#######################################################################

import unittest

class TestProbesetAnnotation(unittest.TestCase):

    def test_get_basic_probeset_extension(self):
        """Check that the correct probeset extensions are identified
        """
        self.assertEqual(get_probeset_extension('123356_at'),'_at')
        self.assertEqual(get_probeset_extension('123356_st'),'_st')
        self.assertEqual(get_probeset_extension('123356_s_at'),'_s_at')
        self.assertEqual(get_probeset_extension('123356_a_at'),'_a_at')
        self.assertEqual(get_probeset_extension('123356_x_at'),'_x_at')
        self.assertEqual(get_probeset_extension('123356_g_at'),'_g_at')
        self.assertEqual(get_probeset_extension('123356_f_at'),'_f_at')
        self.assertEqual(get_probeset_extension('123356_i_at'),'_i_at')
        self.assertEqual(get_probeset_extension('123356_b_at'),'_b_at')
        self.assertEqual(get_probeset_extension('123356_l_at'),'_l_at')
        self.assertEqual(get_probeset_extension('123356'),None)

    def test_get_tricky_probeset_extension(self):
        """Check the correct extensions are identified in tricker cases
        """
        self.assertEqual(get_probeset_extension('123356b_at'),'_at')

    def test_get_probeset_extension_r(self):
        """Check that the _r_ component overrules other extensions
        """
        self.assertEqual(get_probeset_extension('123356_r_at'),'_r_')

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    main()
    ##test()
