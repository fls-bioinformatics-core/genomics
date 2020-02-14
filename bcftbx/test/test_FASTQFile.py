#######################################################################
# Tests for FASTQFile.py module
#######################################################################
from builtins import str
from bcftbx.FASTQFile import *
import unittest
import io
import os
import tempfile
import shutil
import gzip

fastq_data = u"""@73D9FA:3:FC:1:1:7507:1000 1:N:0:
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
@73D9FA:3:FC:1:1:7488:1000 1:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

fastq_data2 = u"""@73D9FA:3:FC:1:1:7507:1000 2:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<
@73D9FA:3:FC:1:1:15740:1000 2:N:0:
NTCTTGCTGGTGGCGCCATGTCTAAATTGTTTGGAG
+
#+.))/0200<<<<<:::::CC@@C@CC@@@22@@@
@73D9FA:3:FC:1:1:8103:1000 2:N:0:
NGACCGATTAGAGGCGTTTTATGATAATCCCAATGC
+
#(,((,)*))/.0--2255282299@@@@@@@@@@@
@73D9FA:3:FC:1:1:7488:1000 2:N:0:
NTGATTGTCCAGTTGCATTTTAGTAAGCTCTTTTTG
+
#,,,,33223CC@@@@@@@C@@@@@@@@C@CC@222
@73D9FA:3:FC:1:1:6680:1000 2:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

fastq_empty_sequence = u"""@73D9FA:3:FC:1:1:7507:1000 1:N:0:
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
@73D9FA:3:FC:1:1:7488:1000 1:N:0:

+

@73D9FA:3:FC:1:1:6680:1000 1:N:0:
NATAAATCACCTCACTTAAGTGGCTGGAGACAAATA
+
#--,,55777@@@@@@@CC@@C@@@@@@@@:::::<
"""

class TestFastqIterator(unittest.TestCase):
    """Tests of the FastqIterator class
    """
    def setUp(self):
        # Temporary working dir
        self.wd = tempfile.mkdtemp(suffix='.TestFastqIterator')

    def tearDown(self):
        # Remove temporary working dir
        if os.path.isdir(self.wd):
            shutil.rmtree(self.wd)

    def test_fastq_iterator(self):
        """Check iteration over small FASTQ file
        """
        fp = io.StringIO(fastq_data)
        fastq = FastqIterator(fp=fp)
        nreads = 0
        fastq_source = io.StringIO(fastq_data)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

    def test_fastq_iterator_empty_sequence(self):
        """Check iteration over small FASTQ file with 'empty' sequence
        """
        fp = io.StringIO(fastq_empty_sequence)
        fastq = FastqIterator(fp=fp)
        nreads = 0
        fastq_source = io.StringIO(fastq_empty_sequence)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

    def test_fastq_iterator_empty_sequence_at_buffer_start(self):
        """Check iteration over small FASTQ file with 'empty' sequence (small buffer)

        Checks we can handle an edge case where the newline
        terminating the 'empty' sequence falls at the start
        of the read buffer.
        """
        fp = io.StringIO(fastq_empty_sequence)
        fastq = FastqIterator(fp=fp,bufsize=2)
        nreads = 0
        fastq_source = io.StringIO(fastq_empty_sequence)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

    def test_fastq_iterator_file_from_disk(self):
        """Check iteration over small FASTQ file from disk
        """
        self.fastq_in = os.path.join(self.wd,'test.fq')
        with open(self.fastq_in,'w') as fp:
            fp.write(fastq_data)
        fastq = FastqIterator(self.fastq_in)
        nreads = 0
        fastq_source = io.StringIO(fastq_data)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

    def test_fastq_iterator_gzipped_file_from_disk(self):
        """Check iteration over small gzipped FASTQ file from disk
        """
        self.fastq_in = os.path.join(self.wd,'test.fq.gz')
        with gzip.GzipFile(self.fastq_in,'wb') as fp:
            fp.write(fastq_data.encode())
        fastq = FastqIterator(self.fastq_in)
        nreads = 0
        fastq_source = io.StringIO(fastq_data)
        for read in fastq:
            nreads += 1
            self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
            self.assertEqual(str(read.seqid),fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.sequence,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.optid,fastq_source.readline().rstrip('\n'))
            self.assertEqual(read.quality,fastq_source.readline().rstrip('\n'))
        self.assertEqual(nreads,5)

class TestFastqRead(unittest.TestCase):
    """Tests of the FastqRead class
    """

    def test_fastqread(self):
        """Check FastqRead stores input correctly
        """
        seqid = "@HWI-ST1250:47:c0tr3acxx:4:1101:1283:2323 1:N:0:ACAGTGATTCTTTCCC\n"
        seq = "GGTGTCTTCAAAAAGGCCAACCAGATAGGCCTCACTTGCCTCCTGCAAAGCACCGATAGCTGCGCTCTGGAAGCGCAGATCTGTTTTAAAGTCCTGAGCAA\n"
        optid = "+\n"
        quality = "=@@D;DDFFHDHHIJIIIIIIGIGIGDIHGGEIGICFGIGHIIGII@?FGIGIEI@EHEFFEEBAACD;@ACCDDBDBDDACCC3>CD>:ADCCDDD?C@\n"
        read = FastqRead(seqid,seq,optid,quality)
        self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
        self.assertEqual(str(read.seqid),seqid.rstrip('\n'))
        self.assertEqual(read.raw_seqid,seqid)
        self.assertEqual(read.sequence,seq.rstrip('\n'))
        self.assertEqual(read.optid,optid.rstrip('\n'))
        self.assertEqual(read.quality,quality.rstrip('\n'))
        self.assertEqual(read.seqlen,len(seq.rstrip('\n')))
        self.assertEqual(read.maxquality,'J')
        self.assertEqual(read.minquality,'3')
        self.assertFalse(read.is_colorspace)

    def test_fastqread_empty_sequence(self):
        """Check FastqRead handles 'empty' sequence
        """
        seqid = "@HWI-ST1250:47:c0tr3acxx:4:1101:1283:2323 1:N:0:ACAGTGATTCTTTCCC"
        seq = ""
        optid = "+"
        quality = ""
        read = FastqRead(seqid,seq,optid,quality)
        self.assertTrue(isinstance(read.seqid,SequenceIdentifier))
        self.assertEqual(str(read.seqid),seqid.rstrip('\n'))
        self.assertEqual(read.raw_seqid,seqid)
        self.assertEqual(read.sequence,seq.rstrip('\n'))
        self.assertEqual(read.optid,optid.rstrip('\n'))
        self.assertEqual(read.quality,quality.rstrip('\n'))
        self.assertEqual(read.seqlen,len(seq.rstrip('\n')))
        self.assertEqual(read.maxquality,'')
        self.assertEqual(read.minquality,'')
        self.assertFalse(read.is_colorspace)

    def test_is_colorspace(self):
        """Check FastqRead detects colorspace correctly
        """
        read = FastqRead("@1_14_622",
                         "T221.0033033232320030021103233332300123110201010031",
                         "+",
                         "BBA!>AA,B>;;=A%39%B8====>0?-?%9A2<)3?(4*36%A%4&+9%")
        self.assertTrue(read.is_colorspace)

    def test_equality(self):
        """Check FastqRead handles equality operator ('==')
        """
        readn1_data = """@73D9FA:3:FC:1:1:7507:1000 1:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<"""
        readn1 = FastqRead(*readn1_data.split('\n'))
        readn2 = FastqRead(*readn1_data.split('\n'))
        readn3_data = """@73D9FA:3:FC:1:1:7507:1000 2:N:0:
NACAACCTGATTAGCGGCGTTGACAGATGTATCCAT
+
#))))55445@@@@@C@@@@@@@@@:::::<<:::<"""
        readn3 = FastqRead(*readn3_data.split('\n'))
        self.assertTrue(readn1 == readn2)
        self.assertTrue(readn1 == readn1_data)
        self.assertFalse(readn1 == readn3)
        self.assertFalse(readn1 == readn3_data)

class TestSequenceIdentifier(unittest.TestCase):
    """Tests of the SequenceIdentifier class
    """

    def test_read_illumina18_id(self):
        """Process an 'illumina18'-style sequence identifier
        """
        seqid_string = "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('EAS139',seqid.instrument_name)
        self.assertEqual('136',seqid.run_id)
        self.assertEqual('FC706VJ',seqid.flowcell_id)
        self.assertEqual('2',seqid.flowcell_lane)
        self.assertEqual('2104',seqid.tile_no)
        self.assertEqual('15343',seqid.x_coord)
        self.assertEqual('197393',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('Y',seqid.bad_read)
        self.assertEqual('18',seqid.control_bit_flag)
        self.assertEqual('ATCACG',seqid.index_sequence)

    def test_read_illumina18_id_no_index_sequence(self):
        """Process an 'illumina18'-style sequence id with no index sequence (barcode)
        """
        seqid_string = "@73D9FA:3:FC:1:1:7507:1000 1:N:0:"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('73D9FA',seqid.instrument_name)
        self.assertEqual('3',seqid.run_id)
        self.assertEqual('FC',seqid.flowcell_id)
        self.assertEqual('1',seqid.flowcell_lane)
        self.assertEqual('1',seqid.tile_no)
        self.assertEqual('7507',seqid.x_coord)
        self.assertEqual('1000',seqid.y_coord)
        self.assertEqual('1',seqid.pair_id)
        self.assertEqual('N',seqid.bad_read)
        self.assertEqual('0',seqid.control_bit_flag)
        self.assertEqual('',seqid.index_sequence)        

    def test_read_illumina_id(self):
        """Process an 'illumina'-style sequence identifier
        """
        seqid_string = "@HWUSI-EAS100R:6:73:941:1973#0/1"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('HWUSI-EAS100R',seqid.instrument_name)
        self.assertEqual('6',seqid.flowcell_lane)
        self.assertEqual('73',seqid.tile_no)
        self.assertEqual('941',seqid.x_coord)
        self.assertEqual('1973',seqid.y_coord)
        self.assertEqual('0',seqid.multiplex_index_no)
        self.assertEqual('1',seqid.pair_id)

    def test_read_illumina18_id_fastq_screen_tags(self):
        """Process an 'illumina18'-style sequence id with fastq_screen tags
        """
        # Format for first read in a tagged FASTQ
        seqid_string = "@NB500968:70:HCYMKBGX2:1:11101:22672:1659 2:N:0:1#FQST:Human:Mouse:01"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('NB500968',seqid.instrument_name)
        self.assertEqual('70',seqid.run_id)
        self.assertEqual('HCYMKBGX2',seqid.flowcell_id)
        self.assertEqual('1',seqid.flowcell_lane)
        self.assertEqual('11101',seqid.tile_no)
        self.assertEqual('22672',seqid.x_coord)
        self.assertEqual('1659',seqid.y_coord)
        self.assertEqual('2',seqid.pair_id)
        self.assertEqual('N',seqid.bad_read)
        self.assertEqual('0',seqid.control_bit_flag)
        self.assertEqual('1#FQST:Human:Mouse:01',seqid.index_sequence)
        # Format of second and subsequent read IDs
        seqid_string = "@NB500968:70:HCYMKBGX2:1:11101:24365:2047 2:N:0:1#FQST:22"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual('illumina18',seqid.format)
        # Check attributes were correctly extracted
        self.assertEqual('NB500968',seqid.instrument_name)
        self.assertEqual('70',seqid.run_id)
        self.assertEqual('HCYMKBGX2',seqid.flowcell_id)
        self.assertEqual('1',seqid.flowcell_lane)
        self.assertEqual('11101',seqid.tile_no)
        self.assertEqual('24365',seqid.x_coord)
        self.assertEqual('2047',seqid.y_coord)
        self.assertEqual('2',seqid.pair_id)
        self.assertEqual('N',seqid.bad_read)
        self.assertEqual('0',seqid.control_bit_flag)
        self.assertEqual('1#FQST:22',seqid.index_sequence)

    def test_unrecognised_id_format(self):
        """Process an unrecognised sequence identifier
        """
        seqid_string = "@SEQID"
        seqid = SequenceIdentifier(seqid_string)
        # Check we get back what we put in
        self.assertEqual(str(seqid),seqid_string)
        # Check the format
        self.assertEqual(None,seqid.format)

    def test_is_pair_of(self):
        """Check that paired sequence identifiers are recognised as such
        """
        seqid1 = "@HWI-700511R:183:D2C8UACXX:1:1101:1115:2123 1:N:0:GCCAAT"
        seqid2 = "@HWI-700511R:183:D2C8UACXX:1:1101:1115:2123 2:N:0:GCCAAT"
        seqid3 = "@HWI-700511R:183:D2C8UACXX:5:1101:1496:2199 2:N:0:GCCAAT"
        self.assertTrue(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid2)))
        self.assertTrue(SequenceIdentifier(seqid2).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid2).is_pair_of(SequenceIdentifier(seqid2)))
        self.assertFalse(SequenceIdentifier(seqid1).is_pair_of(SequenceIdentifier(seqid1)))
        self.assertFalse(SequenceIdentifier(seqid3).is_pair_of(SequenceIdentifier(seqid1)))

class TestFastqAttributes(unittest.TestCase):
    """Tests of the FastqAttributes class
    """

    def test_fastq_attributes_nreads(self):
        """Check number of reads
        """
        fp = io.StringIO(fastq_data)
        attrs = FastqAttributes(fp=fp)
        self.assertEqual(attrs.nreads,5)

class TestNReads(unittest.TestCase):
    """Tests of the nreads function
    """
    def setUp(self):
        # Temporary working dir
        self.wd = tempfile.mkdtemp(suffix='.TestNReads')

    def tearDown(self):
        # Remove temporary working dir
        if os.path.isdir(self.wd):
            shutil.rmtree(self.wd)

    def test_nreads(self):
        """nreads: check that nreads returns correct read count
        """
        fp = io.StringIO(fastq_data)
        self.assertEqual(nreads(fp=fp),5)

    def test_nreads_from_file_on_disk(self):
        """nreads: check nreads from FASTQ on disk
        """
        self.fastq_in = os.path.join(self.wd,'test.fq')
        with open(self.fastq_in,'w') as fp:
            fp.write(fastq_data)
        self.assertEqual(nreads(self.fastq_in),5)

    def test_nreads_from_gzipped_file_on_disk(self):
        """nreads: check nreads from gzipped FASTQ on disk
        """
        self.fastq_in = os.path.join(self.wd,'test.fq.gz')
        with gzip.GzipFile(self.fastq_in,'wb') as fp:
            fp.write(fastq_data.encode())
        self.assertEqual(nreads(self.fastq_in),5)

class TestFastqsArePair(unittest.TestCase):
    """Tests of the fastqs_are_pair function
    """
    
    def test_fastqs_are_pair(self):
        """Check that fastq pair is recognised as such
        """
        fp1 = io.StringIO(fastq_data)
        fp2 = io.StringIO(fastq_data2)
        self.assertTrue(fastqs_are_pair(fp1=fp1,fp2=fp2,verbose=False))

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Run the tests
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()
