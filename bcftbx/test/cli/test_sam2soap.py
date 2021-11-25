#######################################################################
# Tests
#######################################################################

import unittest
from bcftbx.cli.sam2soap import recover_reference_sequence
from bcftbx.cli.sam2soap import soap_type_from_sam
from bcftbx.cli.sam2soap import SAMLine
from bcftbx.cli.sam2soap import sam_to_soap

class TestRecoverReferenceSequence(unittest.TestCase):
    def test_mutations_only(self):
        self.assertEqual(recover_reference_sequence(
                "CGATACGGGGACATCCGGCCTGCTCCTTCTCACATG",
                "36M",
                "MD:Z:1A0C0C0C1T0C0T27"),
                         "CACCCCTCTGACATCCGGCCTGCTCCTTCTCACATG")
    def test_insertions(self):
        self.assertEqual(recover_reference_sequence(
                "GAGACGGGGTGACATCCGGCCTGCTCCTTCTCACAT",
                "6M1I29M",
                "MD:Z:0C1C0C1C0T0C27"),
                         "CACCCCTCTGACATCCGGCCTGCTCCTTCTCACAT")
    def test_deletions(self):
        self.assertEqual(recover_reference_sequence(
                "AGTGATGGGGGGGTTCCAGGTGGAGACGAGGACTCC",
                "9M9D27M",
                "MD:Z:2G0A5^ATGATGTCA27"),
                         "AGGAATGGGATGATGTCAGGGGTTCCAGGTGGAGACGAGGACTCC")
    def test_insertions_and_deletions(self):
        self.assertEqual(recover_reference_sequence(
                "AGTGATGGGAGGATGTCTCGTCTGTGAGTTACAGCA",
                "2M1I7M6D26M",
                "MD:Z:3C3T1^GCTCAG25T0"),
                         "AGGCTGGTAGCTCAGGGATGTCTCGTCTGTGAGTTACAGCT")

class TestSoapTypeFromSam(unittest.TestCase):
    def test_soap_type_from_sam(self):
        self.assertEqual(soap_type_from_sam(
                "TATAGTTATATAAAAGACCTGAGTAGTACGTTTTATATAATCTGATTTTATGGCTATACTTTTTTTGACATGTAGC",
                "#####################AAAA7AAAA2AA7AAAAAAA1,:0/57:8855)))),''(03388*',''))))#)",
                "76M","MD:Z:75T0"),
                         "1\tT->75C2\t76M\t75T")

class TestSamToSoap(unittest.TestCase):
    def test_sam_to_soap(self):
        sam = SAMLine("SRR189243_1-SRR189243.3751	81	gi|42410857|gb|AE017196.1|	60083	30	76M	*	0	0	TATAGTTATATAAAAGACCTGAGTAGTACGTTTTATATAATCTGATTTTATGGCTATACTTTTTTTGACATGTAGC	#####################AAAA7AAAA2AA7AAAAAAA1,:0/57:8855)))),''(03388*',''))))#	NM:i:1	MD:Z:75T0")
        self.assertEqual(str(sam_to_soap(sam)),
                         "SRR189243_1-SRR189243.3751	TATAGTTATATAAAAGACCTGAGTAGTACGTTTTATATAATCTGATTTTATGGCTATACTTTTTTTGACATGTAGC	#####################AAAA7AAAA2AA7AAAAAAA1,:0/57:8855)))),''(03388*',''))))#	1	a	76	-	gi|42410857|gb|AE017196.1|	60083	1	T->75C2	76M	75T")
