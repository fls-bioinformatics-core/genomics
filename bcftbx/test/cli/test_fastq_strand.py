#######################################################################
# Tests for cli/fastq_strand.py
#######################################################################

import unittest
import argparse
import os
import io
import tempfile
import shutil
from bcftbx.mock import mockSTAR
from bcftbx.cli.fastq_strand import fastq_strand
from bcftbx import get_version

fq_r1_data = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 1:N:0:CNATGT
GCCNGACAGCAGAAATGGAATGCGGACCCCTTCNACCACCANAATATTCTTNATNTTGGGTNTTGCNAANGTCTTC
+
AAF#FJJJJJJJJJJJJJJJJJJJJJJJJJJJJ#JJJJJJJ#JJJJJJJJJ#JJ#JJJJJJ#JJJJ#JJ#JJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21460:1121 1:N:0:CNATGT
GGGNGTCATTGATCATTTCTTCAGTCATTTCCANTTTCATGNTTTCCTTCTNGANATTCTGNATTGNTTNTAGTGT
+
AAF#FJJJJJJJJJJJJJJJJJJJJJJJJJJJJ#JJJJJJJ#JJJJJJJJJ#JJ#JJJJJJ#JJJJ#JJ#JJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 1:N:0:CNATGT
CCCNACCCTTGCCTACCCACCATACCAAGTGCTNGGATTACNGGCATGTATNGCNGCGTCCNGCTTNAANTTAA
+
AAF#FJJJJJJJJJJJJJJJJJJJJJJJJJJJJ#JJJJJJJ#JJJJJJJJJ#JJ#JJJAJJ#JJJJ#JJ#JJJJ
"""
fq_r2_data = u"""@K00311:43:HL3LWBBXX:8:1101:21440:1121 2:N:0:CNATGT
CAANANGGNNTCNCNGNTNTNCTNTNAGANCNNTGANCNGTTCTTCCCANCTGCACTCTGCCCCAGCTGTCCAGNC
+
AAF#F#JJ##JJ#J#J#J#J#JJ#J#JJJ#J##JJJ#J#JJJJJJJJJJ#JJJJJJJJJJJJJJJJJJJJJJJJ#J
@K00311:43:HL3LWBBXX:8:1101:21460:1121 2:N:0:CNATGT
ATANGNAANNGTNCNGNGNTNTANCNAAGNANNTTGNCNACCTACGGAAACAGAAGACAAGAACGTTCGCTGTA
+
AAF#F#JJ##JJ#J#J#J#J#JJ#J#JJJ#J##JJJ#J#JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ
@K00311:43:HL3LWBBXX:8:1101:21805:1121 2:N:0:CNATGT
GAANANGCNNACNGNGNTNANTGNTNATGNANNTAGNGNTTCTCTCTGAGGTGACAGAAATACTTTAAATTTAANC
+
AAF#F#JJ##JJ#J#J#J#J#JJ#J#JJJ#F##JJJ#J#JJJJJJFAJJJJFJJJJJJJJJJJJJJJJJFFFJJ#J
"""

__version__ = get_version()

class TestFastqStrand(unittest.TestCase):
    def setUp(self):
        # Make a temporary working directory
        self.wd = tempfile.mkdtemp(prefix="TestFastqStrand")
        # Move to the working directory
        self.pwd = os.getcwd()
        os.chdir(self.wd)
        # Store the initial PATH
        self.path = os.environ['PATH']
        # Make a mock STAR executable
        star_bin = os.path.join(self.wd,"mock_star")
        os.mkdir(star_bin)
        mock_star = os.path.join(star_bin,"STAR")
        self._make_mock_star(mock_star)
        # Prepend mock STAR location to the path
        os.environ['PATH'] = "%s:%s" % (star_bin,os.environ['PATH'])
        # Make some mock Fastqs
        self.fqs = []
        for r in ("R1","R2"):
            fq = os.path.join(self.wd,"mock_%s.fq" %r)
            with io.open(fq,'wt') as fp:
                if r == "R1":
                    fp.write(fq_r1_data)
                else:
                    fp.write(fq_r1_data)
            self.fqs.append(fq)
        # Make some mock STAR indices
        for i in ("Genome1","Genome2"):
            os.mkdir(os.path.join(self.wd,i))
        # Make a conf file
        self.conf_file = os.path.join(self.wd,"genomes.conf")
        with io.open(self.conf_file,'wt') as fp:
            for i in ("Genome1","Genome2"):
                fp.write(u"%s\t%s\n" % (i,os.path.join(self.wd,i)))
        # Make a "bad" Fastq
        self.bad_fastq = os.path.join(self.wd,"bad_R1.fq")
        with io.open(self.bad_fastq,'wt') as fp:
            fp.write(u"NOT A FASTQ FILE")
    def tearDown(self):
        # Move back to the original directory
        os.chdir(self.pwd)
        # Reset the PATH
        os.environ['PATH'] = self.path
        # Remove the working dir
        shutil.rmtree(self.wd)
    def _make_mock_star(self,path,unmapped_output=False):
        # Make a mock STAR executable
        with io.open(path,'wt') as fp:
            fp.write(u"""#!/bin/bash
export PYTHONPATH=%s:$PYTHONPATH
python -c "import sys ; from bcftbx.mock import mockSTAR ; mockSTAR(sys.argv[1:],unmapped_output=%s)" $@
exit $?
""" % (os.path.dirname(__file__),unmapped_output))
        os.chmod(path,0o775)
    def _make_failing_mock_star(self,path):
        # Make a failing mock STAR executable
        with io.open(path,'wt') as fp:
            fp.write(u"""#!/bin/bash
exit 1
""")
        os.chmod(path,0o775)
    def test_fastq_strand_one_genome_index_SE(self):
        """
        fastq_strand: test with single genome index (SE)
        """
        fastq_strand(["-g","Genome1",self.fqs[0]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
""" % __version__)
    def test_fastq_strand_two_genome_indices_SE(self):
        """
        fastq_strand: test with two genome indices (SE)
        """
        fastq_strand(["-g","Genome1",
                      "-g","Genome2",
                      self.fqs[0]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
Genome2	13.13	93.21
""" % __version__)
    def test_fastq_strand_one_genome_index_PE(self):
        """
        fastq_strand: test with single genome index (PE)
        """
        fastq_strand(["-g","Genome1",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
""" % __version__)
    def test_fastq_strand_two_genome_indices_PE(self):
        """
        fastq_strand: test with two genome indices (PE)
        """
        fastq_strand(["-g","Genome1",
                      "-g","Genome2",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
Genome2	13.13	93.21
""" % __version__)
    def test_fastq_strand_using_conf_file(self):
        """
        fastq_strand: test with genome indices specified via conf file
        """
        fastq_strand(["-c",self.conf_file,
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
Genome2	13.13	93.21
""" % __version__)
    def test_fastq_strand_no_subset(self):
        """
        fastq_strand: test with no subset
        """
        fastq_strand(["-g","Genome1",
                      "--subset=0",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
""" % __version__)
    def test_fastq_strand_include_counts(self):
        """
        fastq_strand: test including the counts
        """
        fastq_strand(["-g","Genome1",
                      "--counts",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse	Unstranded	1st read strand aligned	2nd read strand aligned
Genome1	13.13	93.21	391087	51339	364535
""" % __version__)
    def test_fastq_strand_keep_star_output(self):
        """
        fastq_strand: test keeping the output from STAR
        """
        fastq_strand(["-g","Genome1",
                      "--keep-star-output",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
""" % __version__)
        self.assertTrue(os.path.exists(
            os.path.join(self.wd,
                         "STAR.mock_R1.outputs")))
        self.assertTrue(os.path.exists(
            os.path.join(self.wd,
                         "STAR.mock_R1.outputs",
                         "Genome1")))
        self.assertTrue(os.path.exists(
            os.path.join(self.wd,
                         "STAR.mock_R1.outputs",
                         "Genome1",
                         "fastq_strand_ReadsPerGene.out.tab")))
    def test_fastq_strand_overwrite_existing_output_file(self):
        """
        fastq_strand: test overwrite existing output file
        """
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        with io.open(outfile,'wt') as fp:
            fp.write(u"Pre-existing file should be overwritten")
        fastq_strand(["-g","Genome1",
                      self.fqs[0],
                      self.fqs[1]])
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	13.13	93.21
""" % __version__)
    def test_fastq_strand_handle_STAR_non_zero_exit_code(self):
        """
        fastq_strand: handle STAR exiting with non-zero exit code
        """
        # Make a failing mock STAR executable
        mock_star = os.path.join(self.wd,"mock_star","STAR")
        self._make_failing_mock_star(mock_star)
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        with io.open(outfile,'wt') as fp:
            fp.write(u"Pre-existing file should be removed")
        self.assertRaises(Exception,
                          fastq_strand,
                          ["-g","Genome1",self.fqs[0],self.fqs[1]])
        self.assertFalse(os.path.exists(outfile))
    def test_fastq_strand_no_output_file_on_failure(self):
        """
        fastq_strand: don't produce output file on failure
        """
        # Make a failing mock STAR executable
        mock_star = os.path.join(self.wd,"mock_star","STAR")
        self._make_failing_mock_star(mock_star)
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        with io.open(outfile,'wt') as fp:
            fp.write(u"Pre-existing file should be removed")
        self.assertRaises(Exception,
                          fastq_strand,
                          ["-g","Genome1",self.fqs[0],self.fqs[1]])
        self.assertFalse(os.path.exists(outfile))
    def test_fastq_strand_handle_bad_fastq(self):
        """
        fastq_strand: gracefully handle bad Fastq input
        """
        self.assertRaises(Exception,
                          fastq_strand,
                          ["-g","Genome1",self.bad_fastq,self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertFalse(os.path.exists(outfile))
    def test_fastq_strand_overwrite_existing_output_file_on_failure(self):
        """
        fastq_strand: test overwrite existing output file on failure
        """
        # Make a failing mock STAR executable
        mock_star = os.path.join(self.wd,"mock_star","STAR")
        self._make_failing_mock_star(mock_star)
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        with io.open(outfile,'wt') as fp:
            fp.write(u"Pre-existing file should be overwritten")
        self.assertRaises(Exception,
                          fastq_strand,
                          ["-g","Genome1",self.fqs[0],self.fqs[1]])
        self.assertFalse(os.path.exists(outfile))
    def test_fastq_strand_single_unmapped_read_PE(self):
        """
        fastq_strand: test single unmapped read from STAR (PE)
        """
        # Make a mock STAR executable which produces unmapped
        # output
        mock_star = os.path.join(self.wd,"mock_star","STAR")
        self._make_mock_star(mock_star,unmapped_output=True)
        fastq_strand(["-g","Genome1",
                      self.fqs[0],
                      self.fqs[1]])
        outfile = os.path.join(self.wd,"mock_R1_fastq_strand.txt")
        self.assertTrue(os.path.exists(outfile))
        self.assertEqual(io.open(outfile,'rt').read(),
                         """#fastq_strand version: %s	#Aligner: STAR	#Reads in subset: 3
#Genome	1st forward	2nd reverse
Genome1	0.00	0.00
""" % __version__)
