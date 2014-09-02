#######################################################################
# Tests for qc/report.py
#######################################################################

import unittest
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
