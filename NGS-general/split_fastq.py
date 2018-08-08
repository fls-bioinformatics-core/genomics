#!/usr/bin/env python
#
#     split_fastqs.py: split fastqs by specified criteria
#     Copyright (C) University of Manchester 2018 Peter Briggs
#

#######################################################################
# Imports
#######################################################################

import argparse
import re
import os
from bcftbx.IlluminaData import IlluminaFastq
from bcftbx.IlluminaData import IlluminaDataError
from bcftbx.utils import parse_lanes
from bcftbx.ngsutils import getreads
from bcftbx.ngsutils import getreads_regex

#######################################################################
# Unit tests
#######################################################################
import unittest
import tempfile
import shutil
import gzip

class TestGetFastqLanes(unittest.TestCase):
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.fastq_data = """@K00311:43:HL3LWBBXX:2:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:2:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:2:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
"""
        
    def tearDown(self):
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd)
    def test_get_fastq_lanes(self):
        # Make test Fastq
        fastq_in = os.path.join(self.wd,"Test_S1_R1_001.fastq")
        with open(fastq_in,'w') as fp:
            fp.write(self.fastq_data)
        # Extract lanes
        nreads,lanes = get_fastq_lanes(fastq_in)
        # Check results
        self.assertEqual(nreads,5)
        self.assertEqual(lanes,[2,8])
    def test_get_fastq_lanes_from_gzipped_input(self):
        # Make test gzipped Fastq
        fastq_in = os.path.join(self.wd,"Test_S1_R1_001.fastq.gz")
        with gzip.open(fastq_in,'w') as fp:
            fp.write(self.fastq_data)
        # Extract lanes
        nreads,lanes = get_fastq_lanes(fastq_in)
        # Check results
        self.assertEqual(nreads,5)
        self.assertEqual(lanes,[2,8])

class TestExtractReadsForLane(unittest.TestCase):
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.fastq_data_l2 = """@K00311:43:HL3LWBBXX:2:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:2:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:2:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
"""
        self.fastq_data_l8 = """@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
"""
        
    def tearDown(self):
        if os.path.exists(self.wd):
            shutil.rmtree(self.wd)
    def test_extract_reads_for_lane(self):
        # Make test Fastq
        fastq_in = os.path.join(self.wd,"Test_S1_R1_001.fastq")
        with open(fastq_in,'w') as fp:
            fp.write(self.fastq_data_l2)
            fp.write(self.fastq_data_l8)
        # Extract reads for lane 2
        reads_l2 = []
        for r in extract_reads_for_lane(fastq_in,2):
            reads_l2.append(r)
        self.assertEqual(len(reads_l2),3)
        self.assertEqual('\n'.join(reads_l2),self.fastq_data_l2.strip())
        # Extract reads for lane 8
        reads_l8 = []
        for r in extract_reads_for_lane(fastq_in,8):
            reads_l8.append(r)
        self.assertEqual(len(reads_l8),2)
        self.assertEqual('\n'.join(reads_l8),self.fastq_data_l8.strip())
    def test_get_fastq_lanes_from_gzipped_input(self):
        # Make test gzipped Fastq
        fastq_in = os.path.join(self.wd,"Test_S1_R1_001.fastq.gz")
        with gzip.open(fastq_in,'w') as fp:
            fp.write(self.fastq_data_l2)
            fp.write(self.fastq_data_l8)
        # Extract reads for lane 2
        reads_l2 = []
        for r in extract_reads_for_lane(fastq_in,2):
            reads_l2.append(r)
        self.assertEqual(len(reads_l2),3)
        self.assertEqual('\n'.join(reads_l2),self.fastq_data_l2.strip())
        # Extract reads for lane 8
        reads_l8 = []
        for r in extract_reads_for_lane(fastq_in,8):
            reads_l8.append(r)
        self.assertEqual(len(reads_l8),2)
        self.assertEqual('\n'.join(reads_l8),self.fastq_data_l8.strip())

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
    >>> ... print r

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

if __name__ == "__main__":
    # Process command line
    p = argparse.ArgumentParser(
        description="Split input Fastq file into multiple output Fastqs "
        "where each output only contains reads from a single lane.")
    p.add_argument("-l","--lanes",metavar="LANES",
                   help="lanes to extract")
    p.add_argument("fastq",metavar="FASTQ",
                   help="Fastq to split")
    args = p.parse_args()
    # Extract lanes from Fastq
    print "Determining lanes present in %s" % args.fastq
    nreads,fastq_lanes = get_fastq_lanes(args.fastq)
    print "-- %d reads" % nreads
    print "-- Lanes: %s" % ','.join([str(x) for x in fastq_lanes])
    # Lanes
    if args.lanes:
        lanes = parse_lanes(args.lanes)
        for lane in lanes:
            if lane not in fastq_lanes:
                raise Exception("Requested lane %s not found "
                                "in %s" % (lane,args.fastq))
    else:
        lanes = fastq_lanes
    print "Extracting lanes: %s" % ','.join([str(x) for x in lanes])
    # Split the fastq
    for lane in lanes:
        print "-- Lane %s" % lane
        nreads = 0
        outfile = output_fastq_name(args.fastq,lane)
        tmp_outfile = "%s.part" % outfile
        print "   %s" % outfile
        with open(tmp_outfile,'w') as fq:
            for i,read in enumerate(extract_reads_for_lane(args.fastq,lane)):
                nreads += 1
                fq.write("%s\n")
        os.rename(tmp_outfile,outfile)
        print "   %d reads" % nreads
    print "Done"
