#######################################################################
# Unit tests
#######################################################################

import unittest
import tempfile
import os
import io
from bcftbx.cli.manage_seqs import SeqDb
from bcftbx.cli.manage_seqs import split_line
from bcftbx.cli.manage_seqs import split_text

class TestSeqDb(unittest.TestCase):
    """Tests for the SeqDb class

    """
    def setUp(self):
        # Placeholder for temporary file used in some tests
        self.tmp_file = None
    def tearDown(self):
        # Remove temporary file after test completes, if it exists
        if self.tmp_file and os.path.exists(self.tmp_file):
            os.remove(self.tmp_file)
    def test_empty_seqdb(self):
        """Check 'empty' SeqDb instance
        """
        s = SeqDb()
        self.assertEqual(len(s),0)
        self.assertEqual(s.sequences(),[])
        self.assertEqual(s.names(),[])
    def test_seqdb_add(self):
        """Add sequence fragments to SeqDb programmatically
        """
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        self.assertEqual(len(s),1)
        self.assertEqual(s.sequences(),['ATAGAC'])
        self.assertEqual(s.names(),['Sequence #1'])
        s.add('Sequence #2','ATAGGC')
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_add_multiples(self):
        """Add repeated sequences to SeqDb
        """
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.add('Sequence #2','ATAGGC')
        s.add('Sequence #3','ATAGGC')
        s.add('Sequence #4','ATAGCC')
        s.add('Sequence #4','ATAGCA')
        self.assertEqual(len(s),4)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGCA','ATAGCC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2','Sequence #3','Sequence #4'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #4'),['ATAGCA','ATAGCC'])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2','Sequence #3'])
        self.assertEqual(s.names('ATAGCC'),['Sequence #4'])
        self.assertEqual(s.names('ATAGCA'),['Sequence #4'])
        self.assertEqual(s.redundant_entries(),['ATAGGC'])
        self.assertEqual(s.contradictory_entries(),['Sequence #4'])
    def test_seqdb_load(self):
        """Load sequences into SeqDb from FastQC-style input file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'wt')
        fp.write("Sequence #1\tATAGAC\nSequence #2\t\tATAGGC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.load(self.tmp_file)
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_load_from_fasta(self):
        """Load sequences into SeqDb from FASTA input file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'wt')
        fp.write(">Sequence #1\nATAGAC\n>Sequence #2\nATA\nGGC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.load_from_fasta(self.tmp_file)
        self.assertEqual(len(s),2)
        self.assertEqual(s.sequences(),['ATAGAC','ATAGGC'])
        self.assertEqual(s.names(),['Sequence #1','Sequence #2'])
        self.assertEqual(s.sequences('Sequence #1'),['ATAGAC'])
        self.assertEqual(s.sequences('Sequence #2'),['ATAGGC'])
        self.assertEqual(s.sequences('Sequence #3'),[])
        self.assertEqual(s.names('ATAGAC'),['Sequence #1'])
        self.assertEqual(s.names('ATAGGC'),['Sequence #2'])
        self.assertEqual(s.names('ATAGCC'),[])
    def test_seqdb_save(self):
        """Write sequences from SeqDb to new output file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        # Run test
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.save(self.tmp_file)
        content = io.open(self.tmp_file,'rt').read()
        self.assertEqual(content,"Sequence #1\tATAGAC\nSequence #2\tATAGGC\n")
    def test_seqdb_save_append(self):
        """Append sequences from SeqDb to an existing file
        """
        # Create temporary file
        fd,self.tmp_file = tempfile.mkstemp()
        fp = os.fdopen(fd,'w')
        fp.write("# Initial sequence\nSequence #3\tATAGCC\n")
        fp.close()
        # Run test
        s = SeqDb()
        s.add('Sequence #1','ATAGAC')
        s.add('Sequence #2','ATAGGC')
        s.save(self.tmp_file,append=True)
        content = io.open(self.tmp_file,'rt').read()
        self.assertEqual(content,"# Initial sequence\nSequence #3\tATAGCC\nSequence #1\tATAGAC\nSequence #2\tATAGGC\n")

class TestSplitLineFunction(unittest.TestCase):
    """Unit tests for the 'split_line' function
    """
    def test_split_line_defaults(self):
        """'split_line' works with default settings
        """
        self.assertEqual(split_text("Some text",10),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10),
                         ['This is','some text'])
        self.assertEqual(split_text("This is some even longer text",10),
                         ['This is','some even','longer','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10),
                         ['This is','some text','Over','multiple','lines'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_no_strip(self):
        """'split_line' works when delimiter stripping is turned off
        """
        self.assertEqual(split_text("Some text",10,strip=False),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,strip=False),
                         ['This is ','some text'])
        self.assertEqual(split_text("This is some even longer text",10,strip=False),
                         ['This is ','some even ','longer ','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10,strip=False),
                         ['This is ','some text\n','Over ','multiple ','lines\n'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_non_default_delimiter(self):
        """'split_line' works with non-default delimiter
        """
        self.assertEqual(split_text("Some text",10,delims=':'),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,delims=':'),
                         ['This is so','me text'])
        self.assertEqual(split_text("This:is:some:even:longer:text",10,delims=':'),
                         ['This:is','some:even','longer','text'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10,delims=':'),
                         ['Supercalif','ragilistic','expialidoc','ious'])
    def test_split_line_slack(self):
        """'split_line' works when 'slack' splitting is used
        """
        self.assertEqual(split_text("Some text",10,slack=True),
                         ['Some text'])
        self.assertEqual(split_text("This is some text",10,slack=True),
                         ['This is','some text'])
        self.assertEqual(split_text("This is some even longer text",10,slack=True),
                         ['This is','some even','longer','text'])
        self.assertEqual(split_text("This is some text\nOver multiple lines\n",10,slack=True),
                         ['This is','some text','Over','multiple','lines'])
        self.assertEqual(split_text("Supercalifragilisticexpialidocious",10,slack=True),
                         ['Supercalifragilisticexpialidocious'])
