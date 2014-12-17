#######################################################################
# Tests for qc/report.py
#######################################################################

import unittest
from bcftbx.test.mock_data import TestUtils
from bcftbx.qc.report import *

# Example file names:
#
# SOLiD4 - single end
# JL_01.csfasta/JL_01.qual
# solid0127_20120614_SA1.csfasta/solid0127_20120614_SA1_QV.qual
# solid0127_20120614_FRAG_BC_2_SA_FB_KL_POOL_45_F3_SA2.csfasta/solid0127_20120614_FRAG_BC_2_SA_FB_KL_POOL_45_F3_QV_SA2.qual
#
# SOLiD4 - paired end
# SY1_F3.csfasta/SY1_F3_QV.qual
# SY1_F5.csfasta/SY1_F5_QV.qual
# solid0127_20120117_SH_JC1_pool_SH_SP6033.csfasta/solid0127_20120117_SH_JC1_pool_SH_SP6033_QV.qual
# solid0127_20120117_SH_JC1_pool_SH_SP6033_F5.csfasta/solid0127_20120117_SH_JC1_pool_SH_SP6033_F5_QV.qual
# solid0127_20120117_PE_BC_SH_JC1_pool_F3_SH_SP6033.csfasta/solid0127_20120117_PE_BC_SH_JC1_pool_F3_QV_SH_SP6033.qual
# solid0127_20120117_PE_BC_SH_JC1_pool_F5-BC_SH_SP6033.csfasta/solid0127_20120117_PE_BC_SH_JC1_pool_F5-BC_QV_SH_SP6033.qual

class TestStripNGSExtensions(unittest.TestCase):
    def test_strip_ngs_extensions_csfasta(self):
        self.assertEqual(strip_ngs_extensions("ED2.csfasta"),"ED2")
    def test_strip_ngs_extensions_qual(self):
        self.assertEqual(strip_ngs_extensions("ED2_QV.qual"),"ED2_QV")
    def test_strip_ngs_extensions_fastq(self):
        self.assertEqual(strip_ngs_extensions("ED2.fastq"),"ED2")
    def test_strip_ngs_extensions_fastq_gz(self):
        self.assertEqual(strip_ngs_extensions("ED2.fastq.gz"),"ED2")
    def test_strip_ngs_extensions_dots_in_name(self):
        self.assertEqual(strip_ngs_extensions("ED2.1.fastq"),"ED2.1")
        self.assertEqual(strip_ngs_extensions("ED2.1.fastq.gz"),"ED2.1")
    def test_strip_ngs_extensions_no_extension(self):
        self.assertEqual(strip_ngs_extensions("ED2-1_R1"),"ED2-1_R1")

class TestIsFastqc(unittest.TestCase):
    def test_is_fastqc(self):
        self.assertTrue(is_fastqc("ED2-1","ED2-1_fastqc"))
    def test_is_fastqc_with_extension(self):
        self.assertTrue(is_fastqc("ED2-1.fastq","ED2-1_fastqc"))
        self.assertTrue(is_fastqc("ED2-1.fastq.gz","ED2-1_fastqc"))
    def test_is_fastqc_with_leading_path(self):
        self.assertTrue(is_fastqc("/data/ED/ED2-1","ED2-1_fastqc"))
        self.assertTrue(is_fastqc("/data/ED/ED2-1.fastq","ED2-1_fastqc"))
    def test_is_fastqc_doesnt_match(self):
        self.assertFalse(is_fastqc("ED2-2","ED2-1_fastqc"))
    def test_is_fastqc_with_dots(self):
        self.assertTrue(is_fastqc("ED2.1.R1.fastq",
                                  "ED2.1.R1_fastqc"))
    def test_is_fastqc_with_underscores(self):
        self.assertTrue(is_fastqc("ED2_1_R1.fastq",
                                  "ED2_1_R1_fastqc"))
        self.assertTrue(is_fastqc("ED2-1_R2",
                                  "ED2-1_R2_fastqc"))
        self.assertFalse(is_fastqc("ED2_1_R2.fastq",
                                   "ED2_1_R1_fastqc"))

class TestIsFastqScreen(unittest.TestCase):
    def test_is_fastq_screen_illumina(self):
        self.assertTrue(is_fastq_screen("ED2-1.fastq",
                                        "ED2-1_model_organisms_screen.png"))
        self.assertTrue(is_fastq_screen("ED2-1.fastq.gz",
                                        "ED2-1_model_organisms_screen.png"))
        self.assertTrue(is_fastq_screen("ED2-1.fastq.gz",
                                        "ED2-1_other_organisms_screen.png"))
        self.assertTrue(is_fastq_screen("ED2-1.fastq.gz",
                                        "ED2-1_rRNA_screen.png"))
        self.assertFalse(is_fastq_screen("ED2-2.fastq.gz",
                                         "ED2-1_model_organisms_screen.png"))
    def test_is_fastq_screen_with_dots(self):
        self.assertTrue(is_fastq_screen("ED2.1.R1.fastq",
                                        "ED2.1.R1_model_organisms_screen.png"))

class TestIsBoxplot(unittest.TestCase):
    def test_is_boxplot(self):
         self.assertTrue(is_boxplot("SY5_F5","SY5_F5_QV.qual_seq-order_boxplot.png"))
         self.assertTrue(is_boxplot("solid0127_20120117_SH_JC1_pool_SH_SP6261",
                                    "solid0127_20120117_SH_JC1_pool_SH_SP6261_QV.qual_seq-order_boxplot.png"))

class TestIsProgramInfo(unittest.TestCase):
    def test_is_program_info(self):
         self.assertTrue(is_program_info(
             "solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK_F3_CKSEQ26",
             "solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK_F3_CKSEQ26.solid_qc.programs"
         ))
         self.assertTrue(is_program_info(
             "solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK_F3_CKSEQ26",
             "solid0127_20121204_FRAG_BC_Run_56_pool_LC_CK_F3_CKSEQ26.solid_qc.programs"
         ))
    def test_is_program_info_with_dots(self):
         self.assertTrue(is_program_info(
             "ED1.1","ED1.1.illumina_qc.programs"
         ))

SOLID_SAMPLE_NAMES = ['solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR',
                      'solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR']

SOLID_FILES = """qc.solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR.o682883
qc.solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR.o682884
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR.csfasta
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR.fastq
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV.qual
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV_T_F3.qual
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_T_F3.csfasta
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_T_F3.fastq
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR.csfasta
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR.fastq
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV.qual
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV_T_F3.qual
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_T_F3.csfasta
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_T_F3.fastq
SOLiD_preprocess_filter.stats"""

SOLID_QC_FILES = """solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_model_organisms_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_model_organisms_screen.txt
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_other_organisms_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_other_organisms_screen.txt
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV.qual_seq-order_boxplot.pdf
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV.qual_seq-order_boxplot.png
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV.qual_seq-order_boxplot.ps
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV_T_F3.qual_seq-order_boxplot.pdf
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV_T_F3.qual_seq-order_boxplot.png
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_QV_T_F3.qual_seq-order_boxplot.ps
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_rRNA_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_NO_SHEAR_rRNA_screen.txt
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_model_organisms_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_model_organisms_screen.txt
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_other_organisms_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_other_organisms_screen.txt
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV.qual_seq-order_boxplot.pdf
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV.qual_seq-order_boxplot.png
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV.qual_seq-order_boxplot.ps
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV_T_F3.qual_seq-order_boxplot.pdf
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV_T_F3.qual_seq-order_boxplot.png
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_QV_T_F3.qual_seq-order_boxplot.ps
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_rRNA_screen.png
solid0127_20111101_RR2_CM_pool_CM1Q_SHEAR_rRNA_screen.txt"""

class TestQCSampleForSolid(unittest.TestCase):
    def setUp(self):
        # Make an example directory with sample files
        # structured as for SOLiD data
        self.d = TestUtils.make_dir()
        # Add files
        for f in SOLID_FILES.split():
            TestUtils.make_file(f,"lorem ipsum",basedir=self.d)
        # Make an example QC dir
        self.qc_dir = TestUtils.make_sub_dir(self.d,'qc')
        for f in SOLID_QC_FILES.split():
            TestUtils.make_file(f,"lorem ipsum",basedir=self.qc_dir)
    def tearDown(self):
        # Remove the example dir
        TestUtils.remove_dir(self.d)
    def test_qcsample_with_solid_data(self):
        for name in SOLID_SAMPLE_NAMES:
            solid_qc_sample = SolidQCSample(name,self.qc_dir,False)
            self.assertTrue(solid_qc_sample.verify(),"Verify failed for %s" % name)

ILLUMINA_SAMPLE_NAMES = ['JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001',
                         'JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001',
                         'JB-9_GCTACGCT-GCGTAAGA_L004_R1_001',
                         'JB-9_GCTACGCT-GCGTAAGA_L004_R2_001']

ILLUMINA_FILES = """JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001.fastq.gz
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001.fastq.gz
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001.fastq.gz
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001.fastq.gz"""

ILLUMINA_QC_FILES = """JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_fastqc.html
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_fastqc.zip
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_model_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_model_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_other_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_other_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_rRNA_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_rRNA_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_fastqc.html
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_fastqc.zip
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_model_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_model_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_other_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_other_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_rRNA_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_rRNA_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_fastqc.html
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_fastqc.zip
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_model_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_model_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_other_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_other_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_rRNA_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_rRNA_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_fastqc.html
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_fastqc.zip
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001.illumina_qc.programs
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_model_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_model_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_other_organisms_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_other_organisms_screen.txt
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_rRNA_screen.png
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_rRNA_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_fastqc.html
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_fastqc.zip
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_model_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_model_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_other_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_other_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_rRNA_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_rRNA_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_fastqc.html
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_fastqc.zip
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_model_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_model_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_other_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_other_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_rRNA_screen.png
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_rRNA_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_fastqc.html
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_fastqc.zip
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_model_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_model_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_other_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_other_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_rRNA_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_rRNA_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_fastqc.html
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_fastqc.zip
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_model_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_model_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_other_organisms_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_other_organisms_screen.txt
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_rRNA_screen.png
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_rRNA_screen.txt
"""

ILLUMINA_FASTQC_DIRS="""JB-8_CAGAGAGG-GCGTAAGA_L004_R1_001_fastqc
JB-8_CAGAGAGG-GCGTAAGA_L004_R2_001_fastqc
JB-8_CAGAGAGG-GCGTAAGA_L005_R1_001_fastqc
JB-8_CAGAGAGG-GCGTAAGA_L005_R2_001_fastqc
JB-9_GCTACGCT-GCGTAAGA_L004_R1_001_fastqc
JB-9_GCTACGCT-GCGTAAGA_L004_R2_001_fastqc
JB-9_GCTACGCT-GCGTAAGA_L005_R1_001_fastqc
JB-9_GCTACGCT-GCGTAAGA_L005_R2_001_fastqc
"""

class TestQCSampleForIllumina(unittest.TestCase):
    def setUp(self):
        # Make an example directory with sample files
        # structured as for Illumina data
        self.d = TestUtils.make_dir()
        # Add fastq files
        self.fastq_dir = TestUtils.make_sub_dir(self.d,'fastqs')
        for f in ILLUMINA_FILES.split():
            TestUtils.make_file(f,"lorem ipsum",basedir=self.fastq_dir)
        # Make an example QC dir
        self.qc_dir = TestUtils.make_sub_dir(self.d,'qc')
        for f in ILLUMINA_QC_FILES.split():
            TestUtils.make_file(f,"lorem ipsum",basedir=self.qc_dir)
        for d in ILLUMINA_FASTQC_DIRS.split():
            TestUtils.make_sub_dir(self.qc_dir,d)
    def tearDown(self):
        # Remove the example dir
        TestUtils.remove_dir(self.d)
    def test_qcsample_with_illumina_data(self):
        for name in ILLUMINA_SAMPLE_NAMES:
            illumina_qc_sample = IlluminaQCSample(name,self.qc_dir)
            self.assertTrue(illumina_qc_sample.verify(),"Verify failed for %s" % name)
