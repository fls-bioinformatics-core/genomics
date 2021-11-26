#######################################################################
# Unit tests
#######################################################################

import unittest
import os
import io
import tempfile
import shutil
import gzip
from bcftbx.cli.split_fastq import get_fastq_lanes
from bcftbx.cli.split_fastq import extract_reads_for_lane

class TestGetFastqLanes(unittest.TestCase):
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.fastq_data = u"""@K00311:43:HL3LWBBXX:2:1101:21440:1121 1:N:0:CNATGT
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
        with io.open(fastq_in,'wt') as fp:
            fp.write(self.fastq_data)
        # Extract lanes
        nreads,lanes = get_fastq_lanes(fastq_in)
        # Check results
        self.assertEqual(nreads,5)
        self.assertEqual(lanes,[2,8])
    def test_get_fastq_lanes_from_gzipped_input(self):
        # Make test gzipped Fastq
        fastq_in = os.path.join(self.wd,"Test_S1_R1_001.fastq.gz")
        with gzip.open(fastq_in,'wt') as fp:
            fp.write(self.fastq_data)
        # Extract lanes
        nreads,lanes = get_fastq_lanes(fastq_in)
        # Check results
        self.assertEqual(nreads,5)
        self.assertEqual(lanes,[2,8])

class TestExtractReadsForLane(unittest.TestCase):
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.fastq_data_l2 = u"""@K00311:43:HL3LWBBXX:2:1101:21440:1121 1:N:0:CNATGT
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
        self.fastq_data_l8 = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
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
        with io.open(fastq_in,'wt') as fp:
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
        with gzip.open(fastq_in,'wt') as fp:
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
