#!/usr/bin/env python
#
#     prep_sample_sheet.py: prepare sample sheet file for Illumina sequencers
#     Copyright (C) University of Manchester 2012-2021 Peter Briggs

"""
Prepare sample sheet file for Illumina sequencers.
"""

#######################################################################
# Imports
#######################################################################

import os
import sys
import argparse
import logging
import pydoc
from ..IlluminaData import SampleSheet
from ..IlluminaData import SampleSheetPredictor
from ..utils import parse_lanes
from ..utils import parse_named_lanes
from .. import get_version

#######################################################################
# Constants
#######################################################################

# Complements for nucleotides
COMPLEMENT = {
    'A':'T',
    'C':'G',
    'G':'C',
    'T':'A',
}

#######################################################################
# Functions
#######################################################################

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

def reverse_complement(seq):
    """
    Return reverse complement of a sequence
    """
    return ''.join([COMPLEMENT[s] for s in str(seq)[::-1]])

#######################################################################
# Main program
#######################################################################

def main():
    # Set up logging output
    logging.basicConfig(format="%(levelname)s %(message)s")

    # Set up parser
    p = argparse.ArgumentParser(
        description="Utility to prepare SampleSheet files from "
        "Illumina sequencers. Can be used to view, validate and "
        "update or fix information such as sample IDs and project "
        "names before running BCL to FASTQ conversion.")
    p.add_argument('--version',action='version',
                   version=("%%(prog)s %s" % get_version()))
    p.add_argument('-o',action="store",dest="samplesheet_out",
                   default=None,
                   help="output new sample sheet to SAMPLESHEET_OUT")
    p.add_argument('-f','--format',action="store",dest="fmt",
                   help="specify the format of the output sample sheet "
                   "written by the -o option; can be either 'CASAVA' or "
                   "'IEM' (defaults to the format of the original file)")
    p.add_argument('-V','--view',action="store_true",dest="view",
                   help="view predicted outputs from sample sheet")
    p.add_argument('--fix-spaces',action="store_true",dest="fix_spaces",
                   help="replace spaces in sample ID and project fields "
                   "with underscores")
    p.add_argument('--fix-duplicates',action="store_true",
                   dest="fix_duplicates",
                   help="append unique indices to sample IDs where the "
                   "original ID and project name combination are "
                   "duplicated")
    p.add_argument('--fix-empty-projects',action="store_true",
                   dest="fix_empty_projects",
                   help="create sample project names where these are "
                   "blank in the original sample sheet")
    p.add_argument('--set-id',action="append",dest="sample_id",
                   default=[],
                   help="update/set the values in sample ID field; "
                   "SAMPLE_ID should be of the form '<lanes>:<name>', "
                   "where <lanes> is a single integer (e.g. 1), a set of "
                   "integers (e.g. 1,3,...), a range (e.g. 1-3), or "
                   "a combination (e.g. 1,3-5,7)")
    p.add_argument('--set-project',action="append",dest="sample_project",
                   default=[],
                   help="update/set values in the sample project field; "
                   "SAMPLE_PROJECT should be of the form '[<lanes>:]<name>', "
                   "where the optional <lanes> part can be a single "
                   "integer (e.g. 1), a set of integers (e.g. 1,3,...), a "
                   "range (e.g. 1-3), or a combination (e.g. 1,3-5,7). If no "
                   "lanes are specified then all samples will have their "
                   "project set to <name>")
    p.add_argument('--reverse-complement-i5',action="store_true",
                   help="replace i5 index sequences with their reverse "
                   "complement")
    p.add_argument('--ignore-warnings',action="store_true",
                   dest="ignore_warnings",default=False,
                   help="ignore warnings about spaces and duplicated "
                   "sampleID/sampleProject combinations when writing new "
                   "samplesheet.csv file")
    p.add_argument('--include-lanes',action="store",dest="lanes",
                   default=None,
                   help="specify a subset of lanes to include in the output "
                   "sample sheet; LANES should be single integer (e.g. 1), a "
                   "list of integers (e.g. 1,3,...), a range (e.g. 1-3) or a "
                   "combination (e.g. 1,3-5,7). Default is to include all "
                   "lanes")
    p.add_argument('--set-adapter',action="store",dest="adapter",default=None,
                   help="set the adapter sequence in the 'Settings' section "
                   "to ADAPTER")
    p.add_argument('--set-adapter-read2',action="store",dest="adapter_read2",
                   default=None,
                   help="set the adapter sequence for read 2 in the 'Settings'"
                   "section to ADAPTER_READ2")
    deprecated_options = p.add_argument_group("Deprecated options")
    deprecated_options.add_argument('--truncate-barcodes',
                                    action="store",dest="barcode_len",
                                    default=None,type=int,
                                    help="trim barcode sequences in sample "
                                    "sheet to number of bases specified by "
                                    "BARCODE_LEN. Default is to leave "
                                    "barcode sequences unmodified (deprecated; "
                                    "only works for CASAVA-style sample "
                                    "sheets)")
    deprecated_options.add_argument('--miseq',
                                    action="store_true",dest="miseq",
                                    help="convert input MiSEQ sample sheet to "
                                    "CASAVA-compatible format (deprecated; "
                                    "specify -f/--format CASAVA to convert "
                                    "IEM sample sheet to older format)")
    p.add_argument('sample_sheet',metavar="SAMPLE_SHEET",
                   help="input sample sheet file")
    # Process command line
    args = p.parse_args()
    if args.miseq:
        logging.warning("--miseq option no longer necessary; "
                        "MiSEQ-style sample sheets are now converted "
                        "automatically")
    # Get input sample sheet file
    samplesheet = args.sample_sheet
    if not os.path.isfile(samplesheet):
        logging.error("sample sheet '%s': not found" % samplesheet)
        sys.exit(1)
    # Read in the sample sheet
    data = IlluminaData.SampleSheet(samplesheet)
    if data.format is None:
        logging.error("Unable to determine samplesheet format")
        sys.exit(1)
    print("Sample sheet format: %s" % data.format)
    # Remove lanes
    if args.lanes is not None:
        if not data.has_lanes:
            logging.error("sample sheet doesn't define any lanes")
            sys.exit(1)
        lanes = parse_lanes(args.lanes)
        print("Keeping lanes %s, removing the rest" %
              ','.join([str(x) for x in lanes]))
        i = 0
        while i < len(data):
            line = data[i]
            if line['Lane'] in lanes:
                print("Keeping %s" % line)
                i += 1
            else:
                del(data[i])
    # Update the SampleID and SampleProject fields
    for sample_id in args.sample_id:
        if not data.has_lanes:
            logging.error("No lanes in sample sheet for assigning sample ids")
            sys.exit(1)
        lanes,name = parse_named_lanes(sample_id)
        if lanes is None:
            logging.error("No lanes specified for sample id assignment")
            sys.exit(1)
        for line in data:
            if line['Lane'] in lanes:
                print("Setting SampleID for lane %d: '%s'" % (line['Lane'],
                                                              name))
                line[data.sample_id_column] = name
    # Update the SampleProject field
    for sample_project in args.sample_project:
        lanes,name = parse_named_lanes(sample_project)
        if lanes is None:
            logging.warning("Setting project for all samples to '%s'" % name)
            for line in data:
                line[data.sample_project_column] = name
        else:
            if not data.has_lanes:
                logging.error("No lanes in sample sheet for assigning sample projects")
                sys.exit(1)
            for line in data:
                if line['Lane'] in lanes:
                    print("Setting SampleProject for lane %d: '%s' "
                          " (%s)"% (line['Lane'],
                                    name,
                                    line[data.sample_id_column]))
                    line[data.sample_project_column] = name
    # Truncate barcodes
    if args.barcode_len is not None:
        logging.warning("barcode truncation function is deprecated")
        if 'Index' not in data.column_names:
            logging.error("barcode truncation not possible without 'Index' column")
            sys.exit(1)
        barcode_len = args.barcode_len
        for line in data:
            barcode = truncate_barcode(line['Index'],args.barcode_len)
            print("Lane %d '%s/%s': barcode '%s' -> '%s'" %
                  (line['Lane'],
                   line['SampleProject'],
                   line['SampleID'],
                   line['Index'],
                   barcode))
            line['Index'] = barcode
    # Reverse complement index sequences
    if args.reverse_complement_i5:
        for line in data:
            line['index2'] = reverse_complement(line['index2'])
    # Set adapter sequences
    if args.adapter is not None:
        data.settings['Adapter'] = args.adapter
    if args.adapter_read2 is not None:
        data.settings['AdapterRead2'] = args.adapter_read2
    # Fix spaces
    if args.fix_spaces:
        data.fix_illegal_names()
    # Fix empty projects
    if args.fix_empty_projects:
        for line in data:
            if not line[data.sample_project_column]:
                line[data.sample_project_column] = line[data.sample_id_column]
    # Fix duplicates
    if args.fix_duplicates:
        data.fix_duplicated_names()
    # Check for non-unique id/project combinations, spaces and empty names
    check_status = 0
    # Duplicated names
    duplicates = data.duplicated_names
    if len(duplicates) > 0:
        check_status = 1
        for duplicate_set in duplicates:
            for line in duplicate_set:
                logging.warning("Duplicated %s/%s in line:\n%s" %
                                (data.sample_id_column,
                                 data.sample_project_column,
                                 line))
    # Illegal characters/spaces in names
    illegal_names = data.illegal_names
    if len(illegal_names) > 0:
        check_status = 1
        for line in illegal_names:
            logging.warning("Spaces in %s/%s in line:\n%s" %
                            (data.sample_id_column,
                             data.sample_project_column,
                             line))
    # Empty names
    empty_names = data.empty_names
    if len(empty_names) > 0:
        check_status = 1
        for line in empty_names:
            logging.warning("Empty %s and/or %s in line:\n%s" %
                            (data.sample_id_column,
                             data.sample_project_column,
                             line))
    # Predict outputs
    if check_status == 0 or args.ignore_warnings or args.view:
        # Generate prediction
        prediction = []
        predictor = IlluminaData.SampleSheetPredictor(sample_sheet=data)
        title = "Predicted projects:"
        prediction.append("%s\n%s" % (title,('='*len(title))))
        for project_name in predictor.project_names:
            prediction.append("- %s" % project_name)
        for project_name in predictor.project_names:
            project = predictor.get_project(project_name)
            title = "%s (%d samples)" % (project_name,
                                       len(project.sample_ids))
            prediction.append("\n%s\n%s" % (title,('-'*len(title))))
            for sample_id in project.sample_ids:
                sample = project.get_sample(sample_id)
                for barcode in sample.barcode_seqs:
                    lanes = sample.lanes(barcode)
                    if lanes:
                        lanes = "L%s" % (','.join([str(l)
                                                   for l in lanes]))
                    else:
                        lanes = "L*"
                    line = [sample_id,
                            "S%d" % sample.s_index,
                            barcode,
                            lanes]
                    prediction.append("%s" % '\t'.join([str(i) for i in line]))
        prediction = '\n'.join(prediction)
        # Handle paginated output
        if os.isatty(sys.stdout.fileno()):
            # Detected that stdout is a terminal
            prediction += '\n'
            # Acquire a pager command
            try:
                pager = os.environ["PAGER"]
            except KeyError:
                pager = None
            # Output the prediction with paging
            if pager is not None:
                pydoc.pipepager(prediction,cmd=pager)
            else:
                pydoc.pager(prediction)
        else:
            # Stdout not a terminal
            print(prediction)

    # Write out new sample sheet
    if args.samplesheet_out:
        if check_status and not args.ignore_warnings:
            logging.error("please fix above errors in sample sheet data")
        else:
            if args.fmt is not None:
                fmt = str(args.fmt).upper()
            else:
                fmt = data.format
            if fmt not in ('CASAVA','IEM'):
                logging.error("unknown output format '%s'" % fmt)
                sys.exit(1)
            print("Writing to %s in %s format" % (args.samplesheet_out,
                                                  fmt))
            data.write(args.samplesheet_out,fmt=fmt)
    # Finish
    sys.exit(check_status)
