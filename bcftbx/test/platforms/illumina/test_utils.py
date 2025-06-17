#######################################################################
# Tests for illumina.utils.py module
#######################################################################

from bcftbx.platforms.illumina.utils import *
import unittest


class TestIlluminaFastq(unittest.TestCase):

    def test_illumina_fastq(self):
        """
        IlluminaFastq: extract Fastq name components
        """
        fastq_name = 'NA10831_ATCACG_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_with_path_and_extension(self):
        """
        IlluminaFastq: extract name components with leading path and extension
        """
        fastq_name = '/home/galaxy/NA10831_ATCACG_L002_R1_001.fastq.gz'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),'NA10831_ATCACG_L002_R1_001')

    def test_illumina_fastq_r2(self):
        """
        IlluminaFastq: extract Fastq name components for R2 read
        """
        fastq_name = 'NA10831_ATCACG_L002_R2_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,2)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_no_index(self):
        """
        IlluminaFastq: extract Fastq name components without a barcode
        """
        fastq_name = 'NA10831_NoIndex_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_dual_index(self):
        """
        IlluminaFastq: extract Fastq name components with dual index
        """
        fastq_name = 'NA10831_ATCACG-GCACTA_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG-GCACTA')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_from_bcl2fastq2(self):
        """
        IlluminaFastq: extract Fastq name components for bcl2fastq2 output
        """
        fastq_name = 'NA10831_S7_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,7)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_from_bcl2fastq2_no_lane(self):
        """
        IlluminaFastq: extract Fastq name components for bcl2fastq2 output (no lane)
        """
        fastq_name = 'NA10831_S7_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,7)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,None)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertFalse(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_from_bcl2fastq2_index_read(self):
        """
        IlluminaFastq: extract Fastq name components for bcl2fastq2 index read (I1/2)
        """
        fastq_name = 'NA10831_S7_L002_I1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,7)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertTrue(fq.is_index_read)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_for_non_canonical_fastq_names(self):
        """
        IlluminaFastq: non-canonical Fastq names raise IlluminaError
        """
        self.assertRaises(IlluminaError,
                          IlluminaFastq,
                          "PB04_S4_R1_unpaired.fastq.gz")
        self.assertRaises(IlluminaError,
                          IlluminaFastq,
                          "PB04_trimmoPE_bowtie2_notHg38.1.fastq.gz")

class TestSplitRunName(unittest.TestCase):

    def test_split_run_name(self):
        """
        split_run_name: check splitting canonical run names
        """
        self.assertEqual(
            split_run_name('120919_SN7001250_0035_BC133VACXX'),
            ('120919','SN7001250','0035','B','C133VACXX'))
        self.assertEqual(
            split_run_name('121210_M00879_0001_000000000-A2Y1L'),
            ('121210','M00879','0001','','000000000-A2Y1L'))
        self.assertEqual(
            split_run_name('120518_ILLUMINA-73D9FA_00002_FC'),
            ('120518','ILLUMINA-73D9FA','00002','','FC'))
        self.assertEqual(split_run_name('151216_NB500968_0008_AH5CFGAFXX'),
                         ('151216','NB500968','0008','A','H5CFGAFXX'))
        self.assertEqual(
            split_run_name('20180829_FS10000171_3_BNT40323-1530'),
                         ('20180829','FS10000171','3','B','NT40323-1530'))

    def test_split_run_name_with_leading_path(self):
        """
        split_run_name: check run name with leading path
        """
        self.assertEqual(
            split_run_name(
                '/mnt/data/140210_M00879_0031_000000000-A69NA'),
            ('140210','M00879','0031','','000000000-A69NA'))

    def test_split_run_name_with_bad_names(self):
        """
        split_run_name: raises exception for 'bad' names
        """
        self.assertRaises(IlluminaError,
                          split_run_name,
                          'this_is_nonsense')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          'sixchr_10Xrun_BCLFiles_Download')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          '140210')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          '14021_M00879_0031_000000000-A69NA')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          '140210_M00879')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          '140210_M00879_0031')
        self.assertRaises(IlluminaError,
                          split_run_name,
                          '1402100_M00879_XYZ')


class TestFixBasesMask(unittest.TestCase):

    def test_fix_bases_mask_single_index(self):
        """
        fix_bases_mask: single index data
        """
        self.assertEqual(fix_bases_mask('y50,I6','ACAGTG'),'y50,I6')
        self.assertEqual(fix_bases_mask('y101,I7,y101','CGATGT'),'y101,I6n,y101')

    def test_fix_bases_mask_dual_index(self):
        """
        fix_bases_mask: dual index data
        """
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGCGA-TAGATCGC'),
                         'y250,I8,I8,y250')
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGC-GATCGC'),
                         'y250,I6nn,I6nn,y250')

    def test_fix_bases_mask_dual_index_to_single(self):
        """
        fix_bases_mask: dual index converted to single index
        """
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGCGA'),
                         'y250,I8,nnnnnnnn,y250')
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGC'),
                         'y250,I6nn,nnnnnnnn,y250')

    def test_fix_bases_mask_single_index_no_barcode(self):
        """
        fix_bases_mask: single index with no barcode
        """
        self.assertEqual(fix_bases_mask('y76,I8,y76',''),
                         'y76,nnnnnnnn,y76')
        
    def test_fix_bases_dual_index_no_barcode(self):
        """
        fix_bases_mask: dual index with no barcode
        """
        self.assertEqual(fix_bases_mask('y76,I8,I8,y76',''),
                         'y76,nnnnnnnn,nnnnnnnn,y76')


class TestNormaliseBarcode(unittest.TestCase):

    def test_normalise_barcode(self):
        """
        normalise_barcode: check barcodes are normalised
        """
        self.assertEqual(normalise_barcode('CGATGT'),'CGATGT')
        self.assertEqual(normalise_barcode('CGTGTAGG-GACCTGTA'),
                         'CGTGTAGGGACCTGTA')
        self.assertEqual(normalise_barcode('CGTGTAGG+GACCTGTA'),
                         'CGTGTAGGGACCTGTA')
        self.assertEqual(normalise_barcode('CGTGTAGGGACCTGTA'),
                         'CGTGTAGGGACCTGTA')


class TestUniqueFastqNames(unittest.TestCase):

    def test_unique_names_single_fastq(self):
        """
        get_unique_fastq_names: single Fastq
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E.fastq.gz')

    def test_unique_names_single_sample_paired_end(self):
        """
        get_unique_fastq_names: paired end Fastqs from single sample
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L001_R2_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                        'PJB-E_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R2_001.fastq.gz'],
                         'PJB-E_R2.fastq.gz')

    def test_unique_names_single_sample_multiple_lanes(self):
        """
        get_unique_fastq_names: multiple Fastqs from single sample
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E_L001.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R1_001.fastq.gz'],
                         'PJB-E_L002.fastq.gz')

    def test_unique_names_single_sample_multiple_lanes_paired_end(self):
        """
        get_unique_fastq_names: multiple Fastqs from single paired-end sample
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L001_R2_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R2_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E_L001_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R2_001.fastq.gz'],
                         'PJB-E_L001_R2.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R1_001.fastq.gz'],
                         'PJB-E_L002_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R2_001.fastq.gz'],
                         'PJB-E_L002_R2.fastq.gz')

    def test_unique_names_multiple_samples_single_fastq(self):
        """
        get_unique_fastq_names: multiple samples each with single Fastq
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-A_AGTCAA_L001_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E.fastq.gz')
        self.assertEqual(mapping['PJB-A_AGTCAA_L001_R1_001.fastq.gz'],
                         'PJB-A.fastq.gz')

