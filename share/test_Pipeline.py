#######################################################################
# Tests for Pipeline.py module
#######################################################################
import unittest
from Pipeline import *

class TestGetFastqFiles(unittest.TestCase):
    """Unit tests for GetFastqFiles function

    """

    def test_get_fastq_files(self):
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample3.fastq',),
                    ('sample4.fastq',)]
        fastqs = GetFastqFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_files_paired_end(self):
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3_R1.fastq',
                     'sample3_R2.fastq',
                     'sample4_R1.fastq',
                     'sample4_R2.fastq',
                     'out.log',
                     'README']
        expected = [('sample3_R1.fastq',),
                    ('sample3_R2.fastq',),
                    ('sample4_R1.fastq',),
                    ('sample4_R2.fastq',)]
        fastqs = GetFastqFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

class TestGetFastqGzFiles(unittest.TestCase):
    """Unit tests for GetFastqGzFiles function

    """

    def test_get_fastq_gz_files(self):
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample1.fastq.gz',),
                    ('sample2.fastq.gz',)]
        fastqgzs = GetFastqGzFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_gz_files_paired_end(self):
        file_list = ['sample1_R1.fastq.gz',
                     'sample1_R2.fastq.gz',
                     'sample2_R1.fastq.gz',
                     'sample2_R2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample1_R1.fastq.gz',),
                    ('sample1_R2.fastq.gz',),
                    ('sample2_R1.fastq.gz',),
                    ('sample2_R2.fastq.gz',)]
        fastqgzs = GetFastqGzFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
