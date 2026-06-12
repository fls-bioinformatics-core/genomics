#######################################################################
# Tests for utils/path.py module
#######################################################################


import unittest
import os
import gzip
import shutil
import tempfile
from bcftbx.utils.io import getlines
from bcftbx.utils.io import concatenate_fastq_files


class TestGetlinesFunction(unittest.TestCase):
    """
    Unit tests for the getlines function
    """

    def setUp(self):
        self.wd = tempfile.mkdtemp()
        self.example_text = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
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

    def test_getlines(self):
        """
        utils.io.getlines: read lines from a file
        """
        # Make an example file
        example_file = os.path.join(self.wd,"example.txt")
        with open(example_file,'wt') as fp:
            fp.write(self.example_text)
        # Read lines
        lines = getlines(example_file)
        for l1,l2 in zip(self.example_text.split('\n'),lines):
            self.assertEqual(l1,l2)

    def test_getlines_from_gzipped_file(self):
        """
        utils.io.getlines: read lines from a gzipped file
        """
        # Make an example gzipped file
        example_file = os.path.join(self.wd,"example.txt.gz")
        with gzip.open(example_file,'wt') as fp:
            fp.write(self.example_text)
        # Read lines
        lines = getlines(example_file)
        for l1,l2 in zip(self.example_text.split('\n'),lines):
            self.assertEqual(l1,l2)


class TestConcatenateFastqFiles(unittest.TestCase):
    """
    Unit tests for concatenate_fastq_files
    """
    def setUp(self):
        # Create a set of test files
        self.fastq_data1 = u""""@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 1:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 1:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
"""
        self.fastq_data2 = u"""@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

    def tearDown(self):
        os.remove(self.fastq1)
        os.remove(self.fastq2)
        os.remove(self.merged_fastq)

    def make_fastq_file(self,fastq,data):
        # Create a fastq file for the testing
        if os.path.splitext(fastq)[1] != '.gz':
            with open(fastq,'wt') as fp:
                fp.write(data)
        else:
            with gzip.open(fastq,'wt') as fp:
                fp.write(data)

    def test_concatenate_fastq_files(self):
        self.fastq1 = "concat.unittest.1.fastq"
        self.fastq2 = "concat.unittest.2.fastq"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        with open(self.merged_fastq,'rt') as fp:
            merged_fastq_data = fp.read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

    def test_concatenate_fastq_files_gzipped(self):
        self.fastq1 = "concat.unittest.1.fastq.gz"
        self.fastq2 = "concat.unittest.2.fastq.gz"
        self.make_fastq_file(self.fastq1,self.fastq_data1)
        self.make_fastq_file(self.fastq2,self.fastq_data2)
        self.merged_fastq = "concat.unittest.merged.fastq.gz"
        concatenate_fastq_files(self.merged_fastq,
                                [self.fastq1,self.fastq2],
                                overwrite=True,
                                verbose=False)
        merged_fastq_data = gzip.open(self.merged_fastq,'rt').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)