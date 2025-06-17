#!/usr/bin/env python3
#
#     platforms.illumina.utils.py: Illumina-related utility functions
#     Copyright (C) University of Manchester 2011-2025 Peter Briggs
#
########################################################################
#
# platforms.illumina.utils.py
#
#########################################################################

"""
Provides utility classes and functions for working with Illumina
sequencing runs and derived data.

The following classes are available:

* IlluminaFastq: extract information from Fastq file names

The following functions are available:

* split_run_name: splits a canonical run directory name
* run_is_complete: checks if a sequencing run has completed
* fix_bases_mask: adjust bases mask to match index sequence lengths
* normalise_barcode: normalise index sequence information
* get_unique_fastq_names: generate shortened Fastq names
"""

#######################################################################
# Imports
#######################################################################

import os
from .. import RUN_COMPLETION_FILES
from .exceptions import IlluminaError


#######################################################################
# Classes
#######################################################################


class IlluminaFastq:
    """
    Class for extracting information from Fastq names

    Given the name of a Fastq file from CASAVA/Illumina platform,
    extract data about the sample name, barcode sequence, lane number,
    read number and set number.

    For Fastqs produced by CASAVA and bcl2fastq v1.8, the format of
    the names follows the general form:

    <sample_name>_<barcode_sequence>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_ATCACG_L002_R1_001.fastq.gz

    sample_name = 'NA10831'
    barcode_sequence = 'ATCACG'
    lane_number = 2
    read_number = 1
    set_number = 1

    For Fastqs produced by bcl2fast v2, the format looks like:

    <sample_name>_S<sample_number>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_S4_L002_R1_001.fastq.gz

    sample_name = 'NA10831'
    sample_number = 4
    lane_number = 2
    read_number = 1
    set_number = 1

    Provides the follow attributes:

    fastq:            the original fastq file name
    sample_name:      name of the sample (leading part of the name)
    sample_number:    number of the same (integer or None, bcl2fastq v2 only)
    barcode_sequence: barcode sequence (string or None, CASAVA/bcl2fast v1.8 only)
    lane_number:      integer
    read_number:      integer
    set_number:       integer

    Arguments:
      fastq (str): name of the fastq.gz file (optionally can include
        leading path)
    """
    def __init__(self,fastq):
        # Store name
        self.fastq = fastq
        # Values derived from the name
        self.sample_name = None
        self.sample_number = None
        self.barcode_sequence = None
        self.lane_number = None
        self.read_number = None
        self.set_number = None
        # Other properties
        self.is_index_read = False
        # Base name for sample (no leading path or extension)
        fastq_base = os.path.basename(fastq)
        try:
            i = fastq_base.index('.')
            fastq_base = fastq_base[:i]
        except ValueError:
            pass
        # Identify which part of the name is which
        fields = fastq_base.split('_')
        nfields = len(fields)
        # Set number: zero-padded 3 digit integer '001'
        try:
            self.set_number = int(fields[-1])
        except ValueError:
            raise IlluminaError(
                "%s: not a canonical Illumina Fastq name" % fastq_base)
        # Read number: single integer digit 'R1' or 'I1'
        if fields[-2].startswith('R') or fields[-2].startswith('I'):
            try:
                self.read_number = int(fields[-2][1])
            except ValueError:
                raise IlluminaError(
                    "%s: not a canonical Illumina Fastq name" % fastq_base)
            self.is_index_read = fields[-2].startswith('I')
        # Lane number: zero-padded 3 digit integer 'L001'
        if fields[-3].startswith('L') and fields[-3][1:].isdigit():
            self.lane_number = int(fields[-3][1:])
            fields = fields[:-3]
        else:
            fields = fields[:-2]
        # Either barcode sequence or sample number
        if fields[-1].startswith('S'):
            # Sample number: integer
            self.sample_number = int(fields[-1][1:])
        else:
            # Barcode sequence: string (or None if 'NoIndex')
            self.barcode_sequence = fields[-1]
            if self.barcode_sequence == 'NoIndex':
                self.barcode_sequence = None
        # Sample name: whatever's left over
        self.sample_name = '_'.join(fields[:-1])

    def __repr__(self):
        """
        Implement __repr__ built-in
        """
        if self.sample_number is not None:
            sample_identifier = "S%d" % self.sample_number
        elif self.barcode_sequence is not None:
            sample_identifier = self.barcode_sequence
        else:
            sample_identifier = "NoIndex"
        if self.lane_number is not None:
            lane_identifier = "L%03d_" % self.lane_number
        else:
            lane_identifier = ""
        if self.is_index_read:
            read_type = "I"
        else:
            read_type = "R"
        return "%s_%s_%s%s%d_%03d" % (self.sample_name,
                                      sample_identifier,
                                      lane_identifier,
                                      read_type,
                                      self.read_number,
                                      self.set_number)


#######################################################################
# Functions
#######################################################################


def split_run_name(dirname):
    """
    Split an Illumina directory run name into components

    Given a directory for an Illumina run, split the name into
    components and return as a tuple:

    (date_stamp,
     instrument_name,
     run_number,
     flow_cell_prefix,
     flow_cell_id)

    e.g.

    >>> split_run_name_full("140210_M00879_0031_000000000-A69NA")
    ('140210', 'M00879', '0031', '', '000000000-A69NA')

    Note on flow cell IDs
    =====================

    For run names of the form e.g.

    151216_NB500968_0008_AH5CFGAFXX

    the flow cell component of the name (i.e. 'AH5CFGAFXX')
    is broken down into a prefix part ('A') and an ID part
    ('H5CFGAFXX'). The ID (i.e. without the prefix) is the
    flow cell ID that is used in FASTQ read headers.

    This function assumes that if the flow cell component of
    the name starts with an 'A' or 'B' then this is the prefix;
    otherwise the prefix is a blank. The remainder of the
    component is used as the ID.

    Arguments:
      dirname (str): path to the Illumina run directory

    Returns:
      Tuple: tuple of (date_stamp, instrument_name, run_number,
        flow_cell_prefix, flow_cell_id)
    """
    fields = os.path.basename(dirname).split("_")
    if len(fields) > 3 and fields[0].isdigit() and \
       (len(fields[0]) == 6 or len(fields[0]) == 8):
        date_stamp = fields[0]
    else:
        raise IlluminaError(f"Unable to extract date stamp from "
                            f"'{dirname}'")
    if len(fields) >= 2:
        instrument_name = fields[1]
    else:
        raise IlluminaError(f"Unable to extract instrument name "
                            f"from '{dirname}'")
    if len(fields) >= 3 and fields[2].isdigit:
        run_number = fields[2]
    else:
        raise IlluminaError(f"Unable to extract run number from "
                            f"'{dirname}'")
    if len(fields) > 3:
        flow_cell = fields[3]
    else:
        raise IlluminaError(f"Unable to extract flow cell ID from "
                            f"'{dirname}'")
    if flow_cell[0] in ("A", "B",):
        flow_cell_prefix = flow_cell[0]
        flow_cell = flow_cell[1:]
    else:
        flow_cell_prefix = ""
    return (date_stamp,
            instrument_name,
            run_number,
            flow_cell_prefix,
            flow_cell)


def run_is_complete(run_dir, platform=None):
    """
    Check if an Illumina sequencing run is complete

    Arguments:
      run_dir (str): path to the run directory
      platform (str): platform name

    Returns:
      Boolean: True if run is complete (i.e. all appropriate
        sentinel files are present), False if not (i.e. some
        sentinel files are missing).
    """
    # Acquire run completion files
    try:
        files = RUN_COMPLETION_FILES[platform]
    except KeyError:
        # Fallback to default
        files = RUN_COMPLETION_FILES["default"]
    # Check if all are present
    return all([os.path.exists(os.path.join(run_dir, f))
                for f in files])


def fix_bases_mask(bases_mask, barcode_sequence):
    """
    Adjust input bases mask to match actual barcode sequence lengths

    Updates the bases mask string extracted from RunInfo.xml so that the
    index read masks correspond to the index barcode sequence lengths
    given e.g. in the SampleSheet.csv file.

    For example: if the bases mask is 'y101,I7,y101' (i.e. assigning 7
    cycles to the index read) but the barcode sequence is 'CGATGT' (i.e.
    only 6 bases) then the adjusted bases mask should be 'y101,I6n,y101'.

    Arguments:
      bases_mask (str): bases mask e.g. 'y101,I7,y101','y250,I8,I8,y250'
      barcode_sequence (str): index barcode sequence e.g. 'CGATGT'
        (single index), 'TAAGGCGA-TAGATCGC' (dual index)

    Returns:
      String: updated bases mask string.
    """
    # Split barcode sequence string into components
    indexes = barcode_sequence.split('-')
    # Check input reads
    reads = []
    i = 0
    for read in bases_mask.split(','):
        new_read = read
        if read.startswith('I'):
            input_index_length = int(read[1:])
            try:
                actual_index_length = len(indexes[i])
            except IndexError:
                # No barcode for this read
                actual_index_length = 0
            if actual_index_length > 0:
                new_read = "I%d" % actual_index_length
            else:
                new_read = ""
            if input_index_length > actual_index_length:
                # Actual index sequence is shorter so adjust
                # bases mask and pad with 'n's
                new_read = new_read + \
                           'n'*(input_index_length-actual_index_length)
            i += 1
        reads.append(new_read)
    # Assemble and return updated index tags
    return ','.join(reads)


def normalise_barcode(seq):
    """
    Return normalised version of barcode sequence

    This standardises the sequence so that:

    - all bases are uppercase
    - dual index barcodes have '-' and '+' removed

    """
    return str(seq).upper().replace('-','').replace('+','')


def get_unique_fastq_names(fastqs):
    """
    Generate mapping of full Fastq names to shorter unique names
    
    Given an iterable list of Illumina file fastq names, return a
    dictionary mapping each name to its shortest unique form within
    the list.

    Arguments:
      fastqs (list): a list of Fastq file names

    Returns:
      Dictionary mapping fastq names to shortest unique versions
    """
    # Define a set of templates of increasing complexity,
    # from which to generate shortened names
    templates = ( "NAME",
                  "NAME LANE",
                  "NAME TAG",
                  "NAME TAG LANE",
                  "FULL" )
    # Check for paired end fastq set
    got_R1 = False
    got_R2 = False
    for fastq in fastqs:
        fq = IlluminaFastq(fastq)
        if fq.read_number == 1:
            got_R1 = True
        elif fq.read_number == 2:
            got_R2 = True
    paired_end = got_R1 and got_R2
    # Try each template in turn to see if it can generate
    # a unique set of short names
    for template in templates:
        name_mapping = {}
        unique_names = []
        # Process each fastq file name
        for fastq in fastqs:
            fq = IlluminaFastq(fastq)
            name = []
            if template == "FULL":
                name.append(str(fq))
            else:
                for t in template.split():
                    if t == "NAME":
                        name.append(fq.sample_name)
                    elif t == "TAG":
                        if fq.barcode_sequence is not None:
                            name.append(fq.barcode_sequence)
                    elif t == "LANE":
                        name.append("L%03d" % fq.lane_number)
                # Add the read number for paired end data
                if paired_end:
                    name.append("R%d" % fq.read_number)
            name = '_'.join(name) + ".fastq.gz"
            # Store the name
            if name not in unique_names:
                name_mapping[fastq] = name
                unique_names.append(name)
        # If the number of unique names matches total number
        # of files then we have a unique set
        if len(unique_names) == len(fastqs):
            return name_mapping
    # Failed to make a unique set of names
    raise Exception("Failed to make a set of unique fastq names")

