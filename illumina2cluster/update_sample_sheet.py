#!/bin/env python
#
#     update_sample_sheet.py: edit sample sheet files from Illumina sequencer
#     Copyright (C) University of Manchester 2012 Peter Briggs
#
########################################################################
#
# update_sample_sheet.py
#
#########################################################################

"""update_sample_sheet.py

View and manipulate sample sheet files for Illumina GA2 sequencer.
"""

#######################################################################
# Imports
#######################################################################

import os
import sys
import optparse
import logging
# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
import IlluminaData

#######################################################################
# Imports
#######################################################################

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
    fields = expr.split(',')
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
    # Return tuple
    return (lanes,name)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Set up logging output
    logging.basicConfig(format="%(levelname)s %(message)s")

    # Set up option parser
    p = optparse.OptionParser(usage="%prog [OPTIONS] SampleSheet.csv",
                              description="Utility to view and edit SampleSheet file from "
                              "Illumina GA2 sequencer. Can be used to update sample IDs and "
                              "project names before running BCL to FASTQ conversion.")
    p.add_option('-o',action="store",dest="samplesheet_out",default=None,
                 help="output new sample sheet to SAMPLESHEET_OUT")
    p.add_option('-v','--view',action="store_true",dest="view",
	         help="view contents of sample sheet")
    p.add_option('--miseq',action="store_true",dest="miseq",
                 help="convert input sample sheet MiSEQ to CASAVA-compatible format")
    p.add_option('--fix-spaces',action="store_true",dest="fix_spaces",
                 help="replace spaces in SampleID and SampleProject fields with underscores")
    p.add_option('--fix-duplicates',action="store_true",dest="fix_duplicates",
                 help="append uniques indices to SampleIDs where original "
                 "SampleID/SampleProject combination are duplicated")
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
    # Process command line
    options,args = p.parse_args()
    if len(args) != 1:
        p.error("input is a single SampleSheet.csv file")
    # Get input sample sheet file
    samplesheet = args[0]
    if not os.path.isfile(samplesheet):
        logging.error("sample sheet '%s': not found" % samplesheet)
        sys.exit(1)
    # Read in the data as CSV
    if options.miseq:
        # Input sample sheet is from MiSEQ
        data = IlluminaData.convert_miseq_samplesheet_to_casava(samplesheet)
    else:
        # Standard CASAVA sample sheet
        data = IlluminaData.CasavaSampleSheet(samplesheet)
    # Update the SampleID and SampleProject fields
    for sample_id in options.sample_id:
        lanes,name = parse_name_expression(sample_id)
        for lane in lanes:
            print "Setting SampleID for lane %d: '%s'" % (lane,name)
            data[lane]['SampleID'] = name
    # Update the SampleProject field
    for sample_project in options.sample_project:
        lanes,name = parse_name_expression(sample_project)
        for lane_number in lanes:
            print "Setting SampleProject for lane %d: '%s'" % (lane_number,name)
            for lane in data:
                if lane['Lane'] == lane_number: lane['SampleProject'] = name
    # Fix spaces
    if options.fix_spaces:
        data.fix_illegal_names()
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
    # Write out new sample sheet
    if options.samplesheet_out:
        if check_status and not options.ignore_warnings:
            logging.error("please fix above errors in sample sheet data")
        else:
            data.write(options.samplesheet_out)
    # Finish
    sys.exit(check_status)
    
