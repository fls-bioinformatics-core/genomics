#######################################################################
# Tests for Pipeline.py module
#######################################################################
import unittest
from bcftbx.Pipeline import *

class TestGetSolidDataFiles(unittest.TestCase):
    """Unit tests for GetSolidDataFiles function

    """

    def test_get_solid_files(self):
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_PB1_QV.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_PB2_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_PB1_QV.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_PB2_QV.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_old_qual_naming(self):
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_QV_PB1.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_QV_PB2.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_QV_PB1.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_QV_PB2.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_ignore_filtered_files(self):
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_PB1_QV.qual',
                     'solid0123_20131023_PB1_T_F3.csfasta',
                     'solid0123_20131023_PB1_T_F3_QV.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_PB2_QV.qual',
                     'solid0123_20131023_PB2_T_F3.csfasta',
                     'solid0123_20131023_PB2_T_F3_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_PB1_QV.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_PB2_QV.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_short_names(self):
        file_list = ['PB1.csfasta',
                     'PB1.qual',
                     'PB2.csfasta',
                     'PB2.qual',
                     'out.log',
                     'README']
        expected = [('PB1.csfasta','PB1.qual'),
                    ('PB2.csfasta','PB2.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

class TestGetSolidPairedEndFiles(unittest.TestCase):
    """Unit tests for GetSolidPairedEndFiles function

    """

    def test_get_solid_files_paired_end(self):
        file_list = ['solid0123_20131023_F3_PB1.csfasta',
                     'solid0123_20131023_F3_PB1_QV.qual',
                     'solid0123_20131023_F5-BC_PB1.csfasta',
                     'solid0123_20131023_F5-BC_PB1_QV.qual',
                     'solid0123_20131023_F3_PB2.csfasta',
                     'solid0123_20131023_F3_PB2_QV.qual',
                     'solid0123_20131023_F5-BC_PB2.csfasta',
                     'solid0123_20131023_F5-BC_PB2_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_F3_PB1.csfasta',
                     'solid0123_20131023_F3_PB1_QV.qual',
                     'solid0123_20131023_F5-BC_PB1.csfasta',
                     'solid0123_20131023_F5-BC_PB1_QV.qual'),
                    ('solid0123_20131023_F3_PB2.csfasta',
                     'solid0123_20131023_F3_PB2_QV.qual',
                     'solid0123_20131023_F5-BC_PB2.csfasta',
                     'solid0123_20131023_F5-BC_PB2_QV.qual')]
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_files_paired_end_ignore_filtered_files(self):
        file_list = ['solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual',
                     'solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual',
                     'solid0123_20131023_PB1_F3_T_F3.csfasta',
                     'solid0123_20131023_PB1_F3_T_F3_QV.qual',
                     'solid0123_20131023_PB1_F5_T_F3.csfasta',
                     'solid0123_20131023_PB1_F5_T_F3_QV.qual',
                     'solid0123_20131023_PB2_F3_T_F3.csfasta',
                     'solid0123_20131023_PB2_F3_T_F3_QV.qual',
                     'solid0123_20131023_PB2_F5_T_F3.csfasta',
                     'solid0123_20131023_PB2_F5_T_F3_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual'),
                    ('solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual')]
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_files_paired_end_shortened_names(self):
        file_list = ['solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual',
                     'solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual'),
                    ('solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual')]
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

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
