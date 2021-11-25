#!/usr/bin/env python
#
#     split_fastq.py: split Fastq by lane
#     Copyright (C) University of Manchester 2018-2021 Peter Briggs
#

#######################################################################
# Imports
#######################################################################

from builtins import str
import argparse
import re
import os
import io
from ..IlluminaData import IlluminaFastq
from ..IlluminaData import IlluminaDataError
from ..utils import parse_lanes
from ..ngsutils import getreads
from ..ngsutils import getreads_regex
from .. import get_version

#######################################################################
# Functions
#######################################################################

def get_fastq_lanes(fastq):
    """
    Return list of lanes present in Fastq file

    Arguments:
      fastq (str): path to Fastq file (can
        be gzipped)

    Returns:
      Tuple: tuple (n,lanes) where ``n`` is a the
        number of reads and ``lanes`` is a list
        of integer lane numbers.
    """
    regex = re.compile(r"^([^:]*:){3}(\d*):")
    nreads = 0
    lanes = set()
    for read in getreads(fastq):
        nreads += 1
        try:
            lane = regex.match(''.join(read)).group(2)
            lanes.add(int(lane))
        except AttributeError:
            raise Exception("Failed to find lane in read %s: "
                            "not a valid Fastq file?"
                            % '\n'.join(read))
    return (nreads,sorted(list(lanes)))

def extract_reads_for_lane(fastq,lane):
    """
    Fetch reads from Fastq from specified lane

    Generator function which iterates through a
    Fastqe file and yields each read record where
    the lane number matches the specified lane.

    Example usage:

    >>> for r in extract_reads_for_lane('illumina_R1.fq',2):
    >>> ... print(r)

    Arguments:
      fastq (str): path to Fastq (can be gzipped)

    Yields:
      String: matching read record as a string.
    """
    regex_pattern = r"^([^:]*:){3}%s:" % lane
    for read in getreads_regex(fastq,regex_pattern):
        yield '\n'.join(read)

def output_fastq_name(fastq,lane):
    """
    Generate an output Fastq name

    If the input Fastq name is a canonical
    Illumina-style name then the output name
    will have the lane set to the specified
    lane number.

    Otherwise the output name will be the
    input name with the lane appended as 
    e.g. ".L001".
    """
    try:
        # Try canonical IlluminaFastq name
        fastq_name = IlluminaFastq(fastq)
        fastq_name.lane_number = int(lane)
        return "%s.fastq" % fastq_name
    except IlluminaDataError:
        # Non-standard name
        return "%s.L%03d.fastq" % (os.path.basename(fastq),
                                    lane)

#######################################################################
# Main program
#######################################################################

def main():
    # Process command line
    p = argparse.ArgumentParser(
        description="Split input Fastq file into multiple output Fastqs "
        "where each output only contains reads from a single lane.")
    p.add_argument('--version',action='version',
                   version="%(prog)s "+get_version())
    p.add_argument("-l","--lanes",metavar="LANES",
                   help="lanes to extract: can be a single integer, "
                   "a comma-separated list (e.g. 1,3), a range (e.g. "
                   "5-7) or a combination (e.g. 1,3,5-7). Default is "
                   "to extract all lanes in the Fastq")
    p.add_argument("fastq",metavar="FASTQ",
                   help="Fastq to split")
    args = p.parse_args()
    # Extract lanes from Fastq
    print("Determining lanes present in %s" % args.fastq)
    nreads,fastq_lanes = get_fastq_lanes(args.fastq)
    print("-- %d reads" % nreads)
    print("-- Lanes: %s" % ','.join([str(x) for x in fastq_lanes]))
    # Lanes
    if args.lanes:
        lanes = parse_lanes(args.lanes)
        for lane in lanes:
            if lane not in fastq_lanes:
                raise Exception("Requested lane %s not found "
                                "in %s" % (lane,args.fastq))
    else:
        lanes = fastq_lanes
    print("Extracting lanes: %s" % ','.join([str(x) for x in lanes]))
    # Split the fastq
    for lane in lanes:
        print("-- Lane %s" % lane)
        nreads = 0
        outfile = output_fastq_name(args.fastq,lane)
        tmp_outfile = "%s.part" % outfile
        print("   %s" % outfile)
        with io.open(tmp_outfile,'wt') as fq:
            for i,read in enumerate(extract_reads_for_lane(args.fastq,lane)):
                nreads += 1
                fq.write("%s\n" % read)
        os.rename(tmp_outfile,outfile)
        print("   %d reads" % nreads)
    print("Done")
