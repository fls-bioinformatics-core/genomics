#!/bin/env python
#
#     sam2soap.py: convert from SAM to SOAP format
#     Copyright (C) University of Manchester 2012 Peter Briggs, Casey Bergman
#
#######################################################################
#
# sam2soap.py
#
#######################################################################

"""sam2soap.py

Convert SAM file into SOAP format:

SAM format specification v1.4: http://samtools.sourceforge.net/SAM1.pdf

SOAP format specification: http://soap.genomics.org.cn/soap1/#Formatofoutput
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os,sys
import logging
import optparse

#######################################################################
# Class definitions
#######################################################################

class SAMBitwiseFlag:
    """Class to decode bitwise flag from SAM file.

    Deconvolutes the decimal value of the bitwise flag from a
    SAM alignment line. The following class properties are set
    accordingly and can be queried:

    read_paired
    read_mapped_in_proper_pair
    read_unmapped
    mate_unmapped
    read_reverse_strand
    mate_reverse_strand
    first_in_pair
    second_in_pair
    not_primary_alignment
    failed_quality_checks
    pcr_or_optical_duplicate

    Properties will be either True or False depending on whether
    the bit was set or not in the flag.
    
    See also http://picard.sourceforge.net/explain-flags.html
    """
    def __init__(self,value):
        """Create new SAMBitwiseFlag instance

        Arguments:
          value: the decimal value of the bitwise flag which
            will be decoded and used to set the properties
        """
        data = str(bin(int(value)))[::-1]
        self.read_paired = self.__bitIsSet(data,0)
        self.read_mapped_in_proper_pair = self.__bitIsSet(data,1)
        self.read_unmapped = self.__bitIsSet(data,2)
        self.mate_unmapped = self.__bitIsSet(data,3)
        self.read_reverse_strand = self.__bitIsSet(data,4)
        self.mate_reverse_strand = self.__bitIsSet(data,5)
        self.first_in_pair = self.__bitIsSet(data,6)
        self.second_in_pair = self.__bitIsSet(data,7)
        self.not_primary_alignment = self.__bitIsSet(data,8)
        self.failed_quality_checks = self.__bitIsSet(data,9)
        self.pcr_or_optical_duplicate =  self.__bitIsSet(data,10)

    def __bitIsSet(self,data,bit):
        """Internal: return True or False based on list element value
        """
        try:
            return (data[bit] == '1')
        except IndexError:
            return False

class SAMLine:
    """Class to represent SAM alignment data line

    Decodes a SAM alignment data line and sets the class properties
    accordingly:

    qname: Query template NAME
    flag : bitwise FLAG
    rname: Reference sequence NAME
    pos  : 1-based leftmost mapping POSition
    mapq : MAPping Quality
    cigar: CIGAR string
    rnext: Ref. name of the mate/next segment
    pnext: Position of the mate/next segment
    tlen : observed Template LENgth
    seq  : segment SEQuence
    qual : ASCII of Phred-scaled base QUALity+33
    md   : MD tag (string for mismatching positions)
    nh   : NH tag (number of reported alignments that contains the
           query in the current record)

    These properties correspond to fields given in the SAM v1.4
    specification.

    Note that if set the 'flag' property will be a SAMBitwiseFlag
    instance.
    """
    def __init__(self,line=None):
        """Create new SAMLine instance

        Arguments:
          line: alignment data line from SAM file
        """
        self.qname = None
        self.flag  = None
        self.rname = None
        self.pos   = None
        self.mapq  = None
        self.cigar = None
        self.rnext = None
        self.pnext = None
        self.tlen  = None
        self.seq   = None
        self.qual  = None
        self.md    = None
        self.nh    = None
        self.optional = []
        # line is the string for a line of SAM data
        if line is not None:
            # Break into fields and store values
            data = line.rstrip().split('\t')
            # Alignment section: mandatory fields
            self.qname = data[0]
            self.flag  = data[1]
            self.rname = data[2]
            self.pos   = data[3]
            self.mapq  = data[4]
            self.cigar = data[5]
            self.rnext = data[6]
            self.pnext = data[7]
            self.tlen  = data[8]
            self.seq   = data[9]
            self.qual  = data[10]
            # Alignment section: optional fields
            for field in data[11:]:
                self.optional.append(field)
                if field.startswith('MD:Z:'):
                    self.md = field
                elif field.startswith('NH:i'):
                    self.nh = field
            # Derived class properties
            self.bitwiseFlag = SAMBitwiseFlag(self.flag)

class SOAPLine:
    """Class to represent SOAP file line

    The class has the following properties which can be set by
    the calling subprogram:

    id
    seq
    qual
    hits
    ab
    length
    direction
    chr
    location
    types

    These properties correspond to fields in the SOAP output
    format specification.

    Use e.g. str(SOAPLine) to return the SOAP line as a string.
    """
    def __init__(self):
        """Create a new SOAPLine instance.
        """
        self.id        = None
        self.seq       = None
        self.qual      = None
        self.hits      = None
        self.ab        = None
        self.length    = None
        self.direction = None
        self.chr       = None
        self.location  = None
        self.types     = None

    def __repr__(self):
        """Implements __repr__ built-in
        """
        return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (self.id,
                                                           self.seq,
                                                           self.qual,
                                                           self.hits,
                                                           self.ab,
                                                           self.length,
                                                           self.direction,
                                                           self.chr,
                                                           self.location,
                                                           self.types)

#######################################################################
# Functions
#######################################################################

def recover_reference_sequence(aligned_seq,cigar_string,md_tag):
    """Recover the reference sequence given data from a SAM file

    Reconstructs the reference sequence given the CIGAR string, MD tag
    and aligned sequence from a SAM file.

    Developed using the examples from 
    http://davetang.org/muse/2011/01/28/perl-and-sam/

    Arguments:
      aligned_seq: the aligned sequence (SEQ field of the SAM file)
      cigar_string: the CIGAR string (e.g. 'M5I1M27')
      md_tag: the full MD tag (e.g. 'MD:Z:1A0C0C0C1T0C0T27')

    Returns:
      Recovered reference sequence.
    """
    for field in md_tag:
        if field.startswith('MD:Z:'):
            md = field.split(':')[2]
            break
    if not md_tag: return None
    # Build the reference sequence
    # Process the CIGAR string first
    # This consists of one or more sets of <number><letter>
    # pairs, e.g. 76M, 4M2I27M etc
    # each pair represents an operation
    # Apply the reverse operations to get first version of the
    # of the reference sequence
    operations = []
    logging.debug("CIGAR: %s" % cigar_string)
    op = ''
    for c in cigar_string:
        op += c
        if op and not c.isdigit():
            # Append operation and reset
            operations.append(op)
            op = ''
    # Get trailing operation
    if op: operations.append(op)
    logging.debug("CIGAR operations: %s" % operations)
    # Process the operations
    refseq = []
    index = 0
    for op in operations:
        count = int(op[:-1])
        code = op[-1]
        if code == 'M':
            # (Mis)match
            # Keep aligned sequence for now
            for i in xrange(count):
                refseq.append(aligned_seq[index])
                index += 1
        elif code == 'I':
            # Insertion
            # Skip bases in aligned sequence
            index += count
        elif code == 'D':
            # Deletion
            # Add placeholders for unknown bases
            for i in xrange(count):
                refseq.append('x')
        else:
            logging.error('Unknown operation: %s' % op)
    logging.debug("Reference seq after CIGAR: %s" % ''.join(refseq))
    # Apply the operations in the MD tag
    # These are strings of the form e.g. MD:Z:3C3T1^GCTCAG25T0
    # Numbers indicate unchanged bases, single letters indicate the
    # mutation of a base from the reference, and sequences starting
    # ^ indicate deletions from the reference
    md = md_tag.split(':')[2]
    operations = []
    logging.debug("MD: %s" % md)
    op = ''
    for c in md:
        if op.isdigit() and not c.isdigit():
            # End of base count operation
            operations.append(op)
            op = ''
        elif op.isalpha() and not c.isalpha():
            # End of mutation operation
            operations.append(op)
            op = ''
        elif op.startswith('^') and c.isdigit():
            # End of deletion operation
            operations.append(op)
            op = ''
        op += c
    # Get trailing operation
    if op: operations.append(op)
    logging.debug("MD tag operations: %s" % operations)
    # Process the operations
    index = 0
    for op in operations:
        if op.isdigit():
            # Skip bases
            index += int(op)
        elif op.isalpha():
            # Mutate base
            refseq[index] = op
            index += 1
        elif op.startswith('^'):
            # Add back deleted bases
            for c in op[1:]:
                refseq[index] = c
                index += 1
        else:
            logging.error('Unknown operation: %s' % op)
    logging.debug("Reference seq after MD tag: %s" % ''.join(refseq))
    return ''.join(refseq)

def soap_type_from_sam(aligned_seq,aligned_qual,cigar_string,md_tag):
    """Return SOAP 'type' field from data in SAM file alignment line

    Given the CIGAR string and MD tag from the SAM file, constructs the
    SOAP 'type' string e.g. '1	T->75C-23	76M	75T'

    Note that this version doesn't work for gapped alignments (i.e.
    insertions or deletions, i.e. CIGAR strings with I's or D's).

    Arguments:
      aligned_seq: the aligned sequence (SEQ field of the SAM file)
      aligned_qual: the base quality (QUAL field of the SAM file)
      cigar_string: the CIGAR string (e.g. 'M5I1M27')
      md_tag: the full MD tag (e.g. 'MD:Z:1A0C0C0C1T0C0T27')

    Returns:
      Recovered reference sequence.
    """
    md = md_tag.split(':')[2]
    operations = []
    logging.debug("MD: %s" % md)
    # Determine mumber of mismatches from number of mutations
    # in MD tag
    op = ''
    for c in md:
        if op.isdigit() and not c.isdigit():
            # End of base count operation
            operations.append(op)
            op = ''
        elif op.isalpha() and not c.isalpha():
            # End of mutation operation
            operations.append(op)
            op = ''
        elif op.startswith('^') and c.isdigit():
            # End of deletion operation
            operations.append(op)
            op = ''
        op += c
    # Get trailing operation
    if op: operations.append(op)
    logging.debug("MD tag operations: %s" % operations)
    # Convert the SAM mutation operations to the SOAP
    # equivalents
    soap_ops = []
    index = 0
    for op in operations:
        if op.isdigit():
            # Unchanged bases
            index += int(op)
        elif op.isalpha():
            # Mutation
            # Get the quality score: ascii encoded as quality+33 in SAM file
            quality = ord(aligned_qual[index]) - 33
            soap_ops.append("%s->%s%s%s" % (op,index,aligned_seq[index],quality))
            index += 1
        elif op.startswith('^'):
            # Deletion
            logging.error("Can't handle deletions")
            index += len(op[1:])
        else:
            logging.error('Unknown operation: %s' % op)
    logging.debug("SOAP operations: %s" % '\t'.join(soap_ops))
    # Number of mismatches
    nmismatches = len(soap_ops)
    # Transform the input MD tag
    md_soap = md.rstrip('0')
    # Create and return SOAP 'types'
    # This is nmismatches, SOAP operations (if present), CIGAR string and MD tag
    soap_types = [str(nmismatches)]
    if soap_ops: soap_types.append('\t'.join(soap_ops))
    soap_types.extend([cigar_string,md_soap])
    # Return the 'types' line
    return '\t'.join(soap_types)

def sam_to_soap(samline):
    """Convert a line of SAM data to the equivalent SOAP format

    Arguments:
      samline: SAMLine object populated from SAM file

    Returns:
      Equivalent SOAPLine object.
    """
    # Create an empty SOAP line
    soap = SOAPLine()
    soap.id = samline.qname
    soap.seq = samline.seq
    soap.qual = samline.qual
    if samline.nh:
        # Get number of hits from NH tag
        soap.hits = samline.nh.split(':')[-1]
    else:
        # No NH flag, assume a single hit
        soap.hits = 1
    soap.length = len(samline.seq) # Length of the sequence
    if samline.bitwiseFlag.second_in_pair:
        soap.ab = 'b'
    else:
        soap.ab = 'a'
    if samline.bitwiseFlag.read_reverse_strand:
        soap.direction = '-'
    else:
        soap.direction = '+'
    soap.chr = samline.rname
    soap.location = samline.pos
    soap.types = soap_type_from_sam(samline.seq,
                                    samline.qual,
                                    samline.cigar,
                                    samline.md)
    # Return populated SOAPLine
    return soap

#######################################################################
# Tests
#######################################################################

import unittest

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
                         "1\tT->75C-23\t76M\t75T")

class TestSamToSoap(unittest.TestCase):
    def test_sam_to_soap(self):
        sam = SAMLine("SRR189243_1-SRR189243.3751	81	gi|42410857|gb|AE017196.1|	60083	30	76M	*	0	0	TATAGTTATATAAAAGACCTGAGTAGTACGTTTTATATAATCTGATTTTATGGCTATACTTTTTTTGACATGTAGC	#####################AAAA7AAAA2AA7AAAAAAA1,:0/57:8855)))),''(03388*',''))))#	NM:i:1	MD:Z:75T0")
        self.assertEqual(str(sam_to_soap(sam)),
                         "SRR189243_1-SRR189243.3751	TATAGTTATATAAAAGACCTGAGTAGTACGTTTTATATAATCTGATTTTATGGCTATACTTTTTTTGACATGTAGC	#####################AAAA7AAAA2AA7AAAAAAA1,:0/57:8855)))),''(03388*',''))))#	1	a	76	-	gi|42410857|gb|AE017196.1|	60083	1	T->75C-23	76M	75T")

def run_tests():
    print "Running unit tests"
    suite = unittest.TestSuite(unittest.TestLoader().\
                                   discover(os.path.dirname(sys.argv[0]), \
                                                pattern=os.path.basename(sys.argv[0])))
    unittest.TextTestRunner(verbosity=2).run(suite)
    print "Tests finished"
    sys.exit()

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Process command line
    p = optparse.OptionParser(usage="%prog OPTIONS [ SAMFILE ]",
                              description="Convert SAM file to SOAP format - reads from stdin "
                              "(or SAMFILE, if specified), and writes output to stdout unless "
                              "-o option is specified.")
    p.add_option('-o',action="store",dest="soapfile",default=None,
                 help="Output SOAP file name")
    p.add_option('--debug',action="store_true",dest="debug",default=False,
                 help="Turn on debugging output")
    p.add_option('--test',action="store_true",dest="run_tests",default=False,
                 help="Run unit tests")
    opts,args = p.parse_args()
    # Check arguments
    if len(args) > 1:
        p.error("Too many arguments")
    # Debugging output
    if opts.debug: logging.getLogger().setLevel(logging.DEBUG)
    # Unit tests
    if opts.run_tests: run_tests()
    # Determine source of SAM data
    if args:
        # Read from file
        samfile = open(args[0],'r')
    else:
        # Read from stdin
        samfile = sys.stdin
    # Determine output target
    if opts.soapfile:
        soapfile = open(opts.soapfile,'w')
    else:
        soapfile = sys.stdout
    # Process the SAM data
    for line in samfile:
        # Skip header lines i.e. starting with '@'
        if line.startswith('@'):
            logging.debug("Skipped header line: %s" % line)
            continue
        # Process alignment lines and convert to SOAP
        soapfile.write("%s\n" % sam_to_soap(SAMLine(line)))
    # Finished
    if args: samfile.close()
    if opts.soapfile: soapfile.close()
