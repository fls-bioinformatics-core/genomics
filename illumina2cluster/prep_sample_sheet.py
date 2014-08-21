#!/bin/env python
#
#     prep_sample_sheet.py: prepare sample sheet file for Illumina sequencers
#     Copyright (C) University of Manchester 2012-3 Peter Briggs
#
########################################################################
#
# prep_sample_sheet.py
#
#########################################################################

"""prep_sample_sheet.py

Prepare sample sheet file for Illumina sequencers.

"""

__version__ = "0.2.1"

#######################################################################
# Imports
#######################################################################

import os
import sys
import optparse
import logging
# Put .. onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..')))
sys.path.append(SHARE_DIR)
import bcftbx.IlluminaData as IlluminaData

#######################################################################
# Functions
#######################################################################

def parse_name_expression(name_expr):
    """Break up a 'name expression' into lane numbers and associated name

    name_expr: a string of the form '<lanes>:<name>', where <lanes> can
    be a single integer (e.g. 1), a set of comma-separated integers (e.g.
    1,2,3), a range (e.g. 1-4), or a combination (e.g. 1,3,5-8).

    Returns a tuple (lanes,name) where lanes is a Python list of integers
    representing lanes, and name is a string with the associated name.
    """
    # Name expressions are of the form 'expr:name'
    try:
        # Extract components
        i = str(name_expr).index(':')
        expr = str(name_expr)[:i]
        name = str(name_expr)[i+1:]
    except ValueError:
        raise Exception, "name expression '%s' has incorrect format" % name_expr
    # Extract lane numbers from leading expression
    lanes = parse_lane_expression(expr)
    # Return tuple
    return (lanes,name)

def parse_lane_expression(lane_expr):
    """Break up a 'lane expression' into a list of lane numbers

    lane_expr: a string consisting of a single integer (e.g. 1), a set of
    comma-separated integers (e.g. 1,2,3), a range (e.g. 1-4), or a
    combination (e.g. 1,3,5-8).

    Returns a list of integers representing lane numbers.

    """
    # Extract lane numbers
    fields = lane_expr.split(',')
    lanes = []
    for field in fields:
        # Check for ranges i.e. 1-3
        try:
            i = field.index('-')
            l1 = int(field[:i])
            l2 = int(field[i+1:])
            for i in xrange(l1,l2+1): lanes.append(i)
        except ValueError:
            # Not a range
            lanes.append(int(field))
    # Sort into order
    lanes.sort()
    return lanes

def truncate_barcode(seq,length):
    """Return barcode sequence truncated to requested length

    'seq' is a barcode sequence (note that dual index sequences
    are of the form e.g. 'AGGTAC-GGCCTT' i.e. the name includes
    a hyphen) and 'length' is the desired length (i.e. number of
    bases to keep).

    """
    try:
        i = seq.index('-')
        # Dual index barcode
        if i >= length:
            return seq[:length]
        else:
            return seq[:length+1]
    except ValueError:
        # No hyphen: single index barcode
        return seq[:length]

#######################################################################
# Unit tests
#######################################################################

import unittest

class TestParseNameExpressionFunction(unittest.TestCase):
    """Tests for the 'parse_name_expression' function

    """
    def test_parse_single_lane(self):
        self.assertEqual(parse_name_expression("1:Test"),([1],'Test'))
    def test_parse_list_of_lanes(self):
        self.assertEqual(parse_name_expression("1,2,4:Test"),([1,2,4],'Test'))
    def test_parse_range_of_lanes(self):
        self.assertEqual(parse_name_expression("2-4:Test"),([2,3,4],'Test'))
    def test_parse_mixtures_of_list_and_range(self):
        self.assertEqual(parse_name_expression("1-3,5:Test"),([1,2,3,5],'Test'))
        self.assertEqual(parse_name_expression("1,3-5:Test"),([1,3,4,5],'Test'))

class TestParseLaneExpressionFunction(unittest.TestCase):
    """Tests for the 'parse_lane_expression' function

    """
    def test_parse_single_lane(self):
        self.assertEqual(parse_lane_expression("1"),[1])
    def test_parse_list_of_lanes(self):
        self.assertEqual(parse_lane_expression("1,2,4"),[1,2,4])
    def test_parse_range_of_lanes(self):
        self.assertEqual(parse_lane_expression("2-4"),[2,3,4])
    def test_parse_mixtures_of_list_and_range(self):
        self.assertEqual(parse_lane_expression("1-3,5"),[1,2,3,5])
        self.assertEqual(parse_lane_expression("1,3-5"),[1,3,4,5])

class TestTruncateBarcodeFunction(unittest.TestCase):
    """Tests for the 'truncate_barcode' function

    """
    def test_truncate_single_index_barcode(self):
        self.assertEqual(truncate_barcode('CGTACTAG',0),'')
        self.assertEqual(truncate_barcode('CGTACTAG',6),'CGTACT')
        self.assertEqual(truncate_barcode('CGTACTAG',8),'CGTACTAG')
        self.assertEqual(truncate_barcode('CGTACTAG',10),'CGTACTAG')
    def test_truncate_dual_index_barcode(self):
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',0),'')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',6),'AGGCAG')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',8),'AGGCAGAA')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',10),'AGGCAGAA-TA')
        self.assertEqual(truncate_barcode('AGGCAGAA-TAGATCGC',16),'AGGCAGAA-TAGATCGC')

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Set up logging output
    logging.basicConfig(format="%(levelname)s %(message)s")

    # Set up option parser
    p = optparse.OptionParser(usage="%prog [OPTIONS] SampleSheet.csv",
                              version="%prog "+__version__,
                              description="Utility to prepare SampleSheet files from "
                              "Illumina sequencers. Can be used to view, validate and "
                              "update or fix information such as sample IDs and project "
                              "names before running BCL to FASTQ conversion.")
    p.add_option('-o',action="store",dest="samplesheet_out",default=None,
                 help="output new sample sheet to SAMPLESHEET_OUT")
    p.add_option('-v','--view',action="store_true",dest="view",
	         help="view contents of sample sheet")
    p.add_option('--fix-spaces',action="store_true",dest="fix_spaces",
                 help="replace spaces in SampleID and SampleProject fields with underscores")
    p.add_option('--fix-duplicates',action="store_true",dest="fix_duplicates",
                 help="append unique indices to SampleIDs where original "
                 "SampleID/SampleProject combination are duplicated")
    p.add_option('--fix-empty-projects',action="store_true",dest="fix_empty_projects",
                 help="create SampleProject names where these are blank in the original "
                 "sample sheet")
    p.add_option('--set-id',action="append",dest="sample_id",default=[],
                 help="update/set the values in the 'SampleID' field; "
                 "SAMPLE_ID should be of the form '<lanes>:<name>', where <lanes> is a single "
                 "integer (e.g. 1), a set of integers (e.g. 1,3,...), a range (e.g. 1-3), or "
                 "a combination (e.g. 1,3-5,7)")
    p.add_option('--set-project',action="append",dest="sample_project",default=[],
                 help="update/set values in the 'SampleProject' field; "
                 "SAMPLE_PROJECT should be of the form '<lanes>:<name>', where <lanes> is a "
                 "single integer (e.g. 1), a set of integers (e.g. 1,3,...), a range (e.g. 1-3), "
                 "or a combination (e.g. 1,3-5,7)")
    p.add_option('--ignore-warnings',action="store_true",dest="ignore_warnings",default=False,
                 help="ignore warnings about spaces and duplicated sampleID/sampleProject "
                 "combinations when writing new samplesheet.csv file")
    p.add_option('--include-lanes',action="store",dest="lanes",default=None,
                 help="specify a subset of lanes to include in the output sample sheet; "
                 "LANES should be single integer (e.g. 1), a list of integers (e.g. "
                 "1,3,...), a range (e.g. 1-3) or a combination (e.g. 1,3-5,7). Default "
                 "is to include all lanes")
    p.add_option('--truncate-barcodes',action="store",dest="barcode_len",default=None,
                 type='int',
                 help="trim barcode sequences in sample sheet to number of bases specified "
                 "by BARCODE_LEN. Default is to leave barcode sequences unmodified")
    deprecated_options = optparse.OptionGroup(p,"Deprecated options")
    deprecated_options.add_option('--miseq',action="store_true",dest="miseq",
                                  help="convert input MiSEQ sample sheet to CASAVA-compatible "
                                  "format (deprecated; conversion is performed automatically "
                                  "if required)")
    p.add_option_group(deprecated_options)
    # Process command line
    options,args = p.parse_args()
    if len(args) != 1:
        p.error("input is a single SampleSheet.csv file")
    if options.miseq:
        logging.warning("--miseq option no longer necessary; MiSEQ-style sample sheets "
                        "are now converted automatically")
    # Get input sample sheet file
    samplesheet = args[0]
    if not os.path.isfile(samplesheet):
        logging.error("sample sheet '%s': not found" % samplesheet)
        sys.exit(1)
    # Read in the data as CSV
    data = IlluminaData.get_casava_sample_sheet(samplesheet)
    # Remove lanes
    if options.lanes is not None:
        lanes = parse_lane_expression(options.lanes)
        print "Keeping lanes %s, removing the rest" % ','.join([str(x) for x in lanes])
        new_data = IlluminaData.CasavaSampleSheet()
        for line in data:
            if line['Lane'] in lanes:
                print "Keeping %s" % line
                new_data.append(tabdata="%s" % line)
        data = new_data
    # Update the SampleID and SampleProject fields
    for sample_id in options.sample_id:
        lanes,name = parse_name_expression(sample_id)
        for line in data:
            if line['Lane'] in lanes:
                print "Setting SampleID for lane %d: '%s'" % (line['Lane'],name)
                line['SampleID'] = name
    # Update the SampleProject field
    for sample_project in options.sample_project:
        lanes,name = parse_name_expression(sample_project)
        for line in data:
            if line['Lane'] in lanes:
                print "Setting SampleProject for lane %d: '%s'" % (line['Lane'],name)
                line['SampleProject'] = name
    # Truncate barcodes
    if options.barcode_len is not None:
        barcode_len = options.barcode_len
        for line in data:
            barcode = truncate_barcode(line['Index'],options.barcode_len)
            print "Lane %d '%s/%s': barcode '%s' -> '%s'" \
                % (line['Lane'],
                   line['SampleProject'],
                   line['SampleID'],
                   line['Index'],
                   barcode)
            line['Index'] = barcode
    # Fix spaces
    if options.fix_spaces:
        data.fix_illegal_names()
    # Fix empty projects
    if options.fix_empty_projects:
        for line in data:
            if not line['SampleProject']:
                line['SampleProject'] = line['SampleID']
    # Fix duplicates
    if options.fix_duplicates:
        data.fix_duplicated_names()
    # Print transposed data in tab-delimited format
    if options.view:
        data.transpose().write(fp=sys.stdout,delimiter='\t')
    # Check for non-unique id/project combinations, spaces and empty names
    check_status = 0
    # Duplicated names
    duplicates = data.duplicated_names
    if len(duplicates) > 0:
        check_status = 1
        for duplicate_set in duplicates:
            for lane in duplicate_set:
                logging.warning("Duplicated SampleID/SampleProject in lane %s (%s/%s)" % 
                                (lane['Lane'],lane['SampleID'],lane['SampleProject']))
    # Illegal characters/spaces in names
    illegal_names = data.illegal_names
    if len(illegal_names) > 0:
        check_status = 1
        for lane in illegal_names:
            logging.warning("Spaces in SampleID/SampleProject in lane %s (%s/%s)" %
                            (lane['Lane'],lane['SampleID'],lane['SampleProject']))
    # Empty names
    empty_names = data.empty_names
    if len(empty_names) > 0:
        check_status = 1
        for lane in empty_names:
            logging.warning("Empty SampleID and/or SampleProject name in lane %s (%s/%s)" %
                            (lane['Lane'],lane['SampleID'],lane['SampleProject']))
    # Predict outputs
    if check_status == 0 or options.ignore_warnings:
        projects = data.predict_output()
        print "Predicted output:"
        for project in projects:
            print "%s (%d samples)" % (project,len(projects[project]))
            for sample in projects[project]:
                print "\t%s" % sample
                for sub_sample in projects[project][sample]:
                    print "\t\t%s" % sub_sample

    # Write out new sample sheet
    if options.samplesheet_out:
        if check_status and not options.ignore_warnings:
            logging.error("please fix above errors in sample sheet data")
        else:
            data.write(options.samplesheet_out)
    # Finish
    sys.exit(check_status)
    
