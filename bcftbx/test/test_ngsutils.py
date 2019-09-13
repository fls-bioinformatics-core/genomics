#######################################################################
# Tests for ngsutils.py module
#######################################################################
import unittest
import os
import io
import tempfile
import shutil
import gzip
from bcftbx.ngsutils import *
from builtins import range

class TestGetreadsFunction(unittest.TestCase):
    """Tests for the 'getreads' function
    """
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.example_fastq_data = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
"""
        self.example_csfasta_data = u"""# Cwd: /home/pipeline
# Title: solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK
>1_51_38_F3
T3..3.213.12211.01..000..111.0210202221221121011..0
>1_51_301_F3
T0..3.222.21233.00..022..110.0210022323223202211..2
>1_52_339_F3
T1.311202211102.331233332113.23332233002223222312.2
"""
        self.example_qual_data = u"""# Cwd: /home/pipeline
# Title: solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK
>1_51_38_F3
16 -1 -1 5 -1 24 15 12 -1 21 12 16 22 19 -1 26 13 -1 -1 4 21 4 -1 -1 4 7 9 -1 4 5 4 4 4 4 4 13 4 4 4 5 4 4 10 4 4 4 4 -1 -1 4 
>1_51_301_F3
22 -1 -1 4 -1 24 30 7 -1 4 9 26 6 16 -1 25 25 -1 -1 17 18 13 -1 -1 4 14 24 -1 4 14 17 32 4 7 13 13 22 4 12 19 4 24 6 9 8 4 4 -1 -1 9 
>1_52_339_F3
27 -1 33 24 28 32 29 17 25 27 26 30 30 31 -1 28 33 19 19 13 4 20 21 13 5 4 12 -1 4 23 13 8 4 10 4 6 5 7 4 8 4 8 12 5 12 10 8 7 -1 4
"""
    def tearDown(self):
        shutil.rmtree(self.wd)
    def test_getreads_fastq(self):
        """getreads: read records from Fastq file
        """
        # Make an example file
        example_fastq = os.path.join(self.wd,"example.fastq")
        with io.open(example_fastq,'wt') as fp:
            fp.write(self.example_fastq_data)
        # Read lines
        fastq_reads = getreads(example_fastq)
        reference_reads = [self.example_fastq_data.split('\n')[i:i+4]
                           for i
                           in range(0,
                                    len(self.example_fastq_data.split('\n')),
                                    4)]
        for r1,r2 in zip(reference_reads,fastq_reads):
            self.assertEqual(r1,r2)
    def test_getreads_gzipped_fastq(self):
        """getreads: read records from gzipped Fastq file
        """
        # Make an example file
        example_fastq = os.path.join(self.wd,"example.fastq.gz")
        with gzip.open(example_fastq,'wt') as fp:
            fp.write(self.example_fastq_data)
        # Read lines
        fastq_reads = getreads(example_fastq)
        reference_reads = [self.example_fastq_data.split('\n')[i:i+4]
                           for i
                           in range(0,
                                    len(self.example_fastq_data.split('\n')),
                                    4)]
        for r1,r2 in zip(reference_reads,fastq_reads):
            self.assertEqual(r1,r2)
    def test_getreads_csfasta(self):
        """getreads: read records from csfasta file
        """
        # Make an example file
        example_csfasta = os.path.join(self.wd,"example.csfasta")
        with io.open(example_csfasta,'wt') as fp:
            fp.write(self.example_csfasta_data)
        # Read lines
        csfasta_reads = getreads(example_csfasta)
        reference_reads = [self.example_csfasta_data.split('\n')[i:i+2]
                           for i
                           in range(2,
                                    len(self.example_fastq_data.split('\n')),
                                    2)]
        for r1,r2 in zip(reference_reads,csfasta_reads):
            self.assertEqual(r1,r2)
    def test_getreads_qual(self):
        """getreads: read records from qual file
        """
        # Make an example file
        example_qual = os.path.join(self.wd,"example.qual")
        with io.open(example_qual,'wt') as fp:
            fp.write(self.example_qual_data)
        # Read lines
        qual_reads = getreads(example_qual)
        reference_reads = [self.example_qual_data.split('\n')[i:i+2]
                           for i
                           in range(2,
                                    len(self.example_qual_data.split('\n')),
                                    2)]
        for r1,r2 in zip(reference_reads,qual_reads):
            self.assertEqual(r1,r2)

class TestGetreadsSubsetFunction(unittest.TestCase):
    """Tests for the 'getreads_subset' function
    """
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.example_fastq_data = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
"""
    def tearDown(self):
        shutil.rmtree(self.wd)
    def test_getreads_subset_fastq(self):
        """getreads: get subset of reads from Fastq file
        """
        # Make an example file
        example_fastq = os.path.join(self.wd,"example.fastq")
        with io.open(example_fastq,'wt') as fp:
            fp.write(self.example_fastq_data)
        # Get subset
        fastq_reads = getreads_subset(example_fastq,
                                      indices=(0,2))
        reference_reads = [self.example_fastq_data.split('\n')[i:i+4]
                           for i in (0,8)]
        for r1,r2 in zip(reference_reads,fastq_reads):
            self.assertEqual(r1,r2)
    def test_getreads_subset_fastq_index_out_of_range(self):
        """getreads: requesting non-existent read raises exception
        """
        # Make an example file
        example_fastq = os.path.join(self.wd,"example.fastq")
        with io.open(example_fastq,'wt') as fp:
            fp.write(self.example_fastq_data)
        # Attempt to get subset with indices outside the range
        # of reads
        # NB would prefer to use assertRaises, however we need to
        # actually yeild the reads in order to raise the exceptions
        try:
            [r for r in getreads_subset(example_fastq,indices=(-1,0))]
            failed = True
        except Exception:
            # This is expected, test passes
            failed = False
        self.assertFalse(failed,"Exception not raised")
        try:
            [r for r in getreads_subset(example_fastq,indices=(0,99))]
            failed = True
        except Exception:
            # This is expected, test passes
            failed = False
        self.assertFalse(failed,"Exception not raised")

class TestGetreadsRegexpFunction(unittest.TestCase):
    """Tests for the 'getreads_regex' function
    """
    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.example_fastq_data = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCAT
+
AAF#FJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTAC
+
AAF#FJJJJJJJJJJJ
"""
    def tearDown(self):
        shutil.rmtree(self.wd)
    def test_getreads_regexp_fastq(self):
        """getreads: get reads from Fastq file matching pattern
        """
        # Make an example file
        example_fastq = os.path.join(self.wd,"example.fastq")
        with io.open(example_fastq,'wt') as fp:
            fp.write(self.example_fastq_data)
        # Get subset
        fastq_reads = getreads_regex(example_fastq,
                                      ":1101:21440:1121")
        reference_reads = [self.example_fastq_data.split('\n')[i:i+4]
                           for i in (0,)]
        for r1,r2 in zip(reference_reads,fastq_reads):
            self.assertEqual(r1,r2)
