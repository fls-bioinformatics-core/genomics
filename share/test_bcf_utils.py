#######################################################################
# Tests for bcf_utils.py module
#######################################################################
import unittest
from bcf_utils import *

class TestFileSystemFunctions(unittest.TestCase):
    """Unit tests for file system wrapper and utility functions

    """

    def test_commonprefix(self):
        self.assertEqual('/mnt/stuff',commonprefix('/mnt/stuff/dir1',
                                                   '/mnt/stuff/dir2'))
        self.assertEqual('',commonprefix('/mnt1/stuff/dir1',
                                         '/mnt2/stuff/dir2'))

    def test_is_gzipped_file(self):
        self.assertTrue(is_gzipped_file('hello.gz'))
        self.assertTrue(is_gzipped_file('hello.tar.gz'))
        self.assertFalse(is_gzipped_file('hello'))
        self.assertFalse(is_gzipped_file('hello.txt'))
        self.assertFalse(is_gzipped_file('hello.gz.part'))
        self.assertFalse(is_gzipped_file('hellogz'))

    def test_rootname(self):
        self.assertEqual('name',rootname('name'))
        self.assertEqual('name',rootname('name.fastq'))
        self.assertEqual('name',rootname('name.fastq.gz'))
        self.assertEqual('/path/to/name',rootname('/path/to/name.fastq.gz'))

class TestFormatFileSize(unittest.TestCase):
    """Unit tests for formatting file sizes

    """

    def test_bytes_to_kb(self):
        self.assertEqual("0.9K",format_file_size(900))
        self.assertEqual("4.0K",format_file_size(4096))

    def test_bytes_to_mb(self):
        self.assertEqual("186.0M",format_file_size(195035136))

    def test_bytes_to_gb(self):
        self.assertEqual("1.6G",format_file_size(1717986919))

class TestNameFunctions(unittest.TestCase):
    """Unit tests for name handling utility functions

    """

    def test_extract_initials(self):
        self.assertEqual('DR',extract_initials('DR1'))
        self.assertEqual('EP',extract_initials('EP_NCYC2669'))
        self.assertEqual('CW',extract_initials('CW_TI'))

    def test_extract_prefix(self):
        self.assertEqual('LD_C',extract_prefix('LD_C1'))

    def test_extract_index_as_string(self):
        self.assertEqual('1',extract_index_as_string('LD_C1'))
        self.assertEqual('07',extract_index_as_string('DR07'))
        self.assertEqual('',extract_index_as_string('DROHSEVEN'))

    def test_extract_index(self):
        self.assertEqual(1,extract_index('LD_C1'))
        self.assertEqual(7,extract_index('DR07'))
        self.assertEqual(None,extract_index('DROHSEVEN'))
        self.assertEqual(0,extract_index('HUES1A0'))

    def test_pretty_print_names(self):
        self.assertEqual('JC_SEQ26-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ27',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26',pretty_print_names(('JC_SEQ26',)))
        self.assertEqual('JC_SEQ26, JC_SEQ28-29',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ29')))
        self.assertEqual('JC_SEQ26, JC_SEQ28, JC_SEQ30',pretty_print_names(('JC_SEQ26',
                                                           'JC_SEQ28',
                                                           'JC_SEQ30')))

    def test_name_matches(self):
        # Cases which should match
        self.assertTrue(name_matches('PJB','PJB'))
        self.assertTrue(name_matches('PJB','PJB*'))
        self.assertTrue(name_matches('PJB123','PJB*'))
        self.assertTrue(name_matches('PJB456','PJB*'))
        self.assertTrue(name_matches('PJB','*'))
        # Cases which shouldn't match
        self.assertFalse(name_matches('PJB123','PJB'))
        self.assertFalse(name_matches('PJB','IDJ'))

class TestConcatenateFastqFiles(unittest.TestCase):
    """Unit tests for concatenate_fastq_files

    """
    def setUp(self):
        # Create a set of test files
        self.fastq_data1 = """"@73D9FA:3:FC:1:1:7507:1000 1:N:0:
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
        self.fastq_data2 = """@73D9FA:3:FC:1:1:7488:1000 1:N:0:
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
            open(fastq,'wt').write(data)
        else:
            gzip.GzipFile(fastq,'wt').write(data)

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
        merged_fastq_data = open(self.merged_fastq,'r').read()
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
        merged_fastq_data = gzip.GzipFile(self.merged_fastq,'r').read()
        self.assertEqual(merged_fastq_data,self.fastq_data1+self.fastq_data2)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
