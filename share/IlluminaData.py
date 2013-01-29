#     IlluminaData.py: module for handling data about Illumina sequencer runs
#     Copyright (C) University of Manchester 2012-2013 Peter Briggs
#
########################################################################
#
# IlluminaData.py
#
#########################################################################

"""IlluminaData

Provides classes for extracting data about runs of Illumina-based sequencers
(e.g. GA2x or HiSeq)from directory structure, data files and naming
conventions.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import bcf_utils
import TabFile

#######################################################################
# Class definitions
#######################################################################

class IlluminaData:
    """Class for examining Illumina data post bcl-to-fastq conversion

    Provides the following attributes:

    analysis_dir:  top-level directory holding the 'Unaligned' subdirectory
                   with the primary fastq.gz files
    projects:      list of IlluminaProject objects (one for each project
                   defined at the fastq creation stage, expected to be in
                   subdirectories "Project_...")
    unaligned_dir: full path to the 'Unaligned' directory holding the
                   primary fastq.gz files

    Provides the following methods:

    get_project(): lookup and return an IlluminaProject object corresponding
                   to the supplied project name

    """

    def __init__(self,illumina_analysis_dir,unaligned_dir="Unaligned"):
        """Create and populate a new IlluminaData object

        Arguments:
          illumina_analysis_dir: path to the analysis directory holding
            the fastq files (expected to be in a subdirectory called
            'Unaligned').
          unaligned_dir: (optional) alternative name for the subdirectory
            under illumina_analysis_dir holding the fastq files

        """
        self.analysis_dir = os.path.abspath(illumina_analysis_dir)
        self.projects = []
        # Look for "unaligned" data directory
        self.unaligned_dir = os.path.join(illumina_analysis_dir,unaligned_dir)
        if not os.path.exists(self.unaligned_dir):
            raise IlluminaDataError, "Missing data directory %s" % self.unaligned_dir
        # Look for projects
        for f in os.listdir(self.unaligned_dir):
            dirn = os.path.join(self.unaligned_dir,f)
            if f.startswith("Project_") and os.path.isdir(dirn):
                logging.debug("Project dirn: %s" % f)
                self.projects.append(IlluminaProject(dirn))
        # Raise an exception if no projects found
        if not self.projects:
            raise IlluminaDataError, "No projects found"
        # Sort projects on name
        self.projects.sort(lambda a,b: cmp(a.name,b.name))

    def get_project(self,name):
        """Return project that matches 'name'

        Arguments:
          name: name of a project

        Returns:
          IlluminaProject object with the matching name; raises
          'IlluminaDataError' exception if no match is found.

        """
        for project in self.projects:
            if project.name == name: return project
        raise IlluminaDataError, "No matching project for '%s'" % name

class IlluminaProject:
    """Class for storing information on a 'project' within an Illumina run

    A project is a subset of fastq files from a run of the Illumina GA2
    sequencer; in the first instance projects are defined within the
    SampleSheet.csv file which is output by the sequencer.

    Provides the following attributes:

    name:      name of the project
    dirn:      (full) path of the directory for the project
    expt_type: the application type for the project e.g. RNA-seq, ChIP-seq
               Initially set to None; should be explicitly set by the
               calling subprogram
    samples:   list of IlluminaSample objects for each sample within the
               project

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaProject object

        Arguments:
          dirn: path to the directory holding the samples within the
                project (expected to be in subdirectories "Sample_...")
        """
        self.dirn = dirn
        self.expt_type = None
        self.samples = []
        # Get name by removing prefix
        self.project_prefix = "Project_"
        if not os.path.basename(self.dirn).startswith(self.project_prefix):
            raise IlluminaDataError, "Bad project name '%s'" % self.dirn
        self.name = os.path.basename(self.dirn)[len(self.project_prefix):]
        logging.debug("Project name: %s" % self.name)
        # Look for samples
        self.sample_prefix = "Sample_"
        for f in os.listdir(self.dirn):
            sample_dirn = os.path.join(self.dirn,f)
            if f.startswith(self.sample_prefix) and os.path.isdir(sample_dirn):
                self.samples.append(IlluminaSample(sample_dirn))
        # Raise an exception if no samples found
        if not self.samples:
            raise IlluminaDataError, "No samples found for project %s" % \
                project.name
        # Sort samples on name
        self.samples.sort(lambda a,b: cmp(a.name,b.name))

    def prettyPrintSamples(self):
        """Return a nicely formatted string describing the sample names

        Wraps a call to 'pretty_print_names' function.
        """
        return bcf_utils.pretty_print_names(self.samples)

class IlluminaSample:
    """Class for storing information on a 'sample' within an Illumina project

    A sample is a fastq file generated within an Illumina GA2 sequencer run.

    Provides the following attributes:

    name:  sample name
    dirn:  (full) path of the directory for the sample
    fastq: name of the fastq.gz file (without leading directory, join to
           'dirn' to get full path)

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaSample object

        Arguments:
          dirn: path to the directory holding the fastq.gz file for the
                sample

        """
        self.dirn = dirn
        self.fastq = []
        # Get name by removing prefix
        self.sample_prefix = "Sample_"
        self.name = os.path.basename(dirn)[len(self.sample_prefix):]
        logging.debug("\tSample: %s" % self.name)
        # Look for fastq files
        for f in os.listdir(self.dirn):
            if f.endswith(".fastq.gz"):
                self.fastq.append(f)
                logging.debug("\tFastq : %s" % f)
        if not self.fastq:
            raise IlluminaDataError, "Unable to find fastq.gz files for %s" % \
                self.name

    def __repr__(self):
        """Implement __repr__ built-in

        Return string representation for the IlluminaSample -
        i.e. the sample name."""
        return str(self.name)

class CasavaSampleSheet(TabFile.TabFile):
    """Class for reading and manipulating sample sheet files for CASAVA

    Sample sheets are CSV files with a header line and then one line per sample
    with the following fields:

    FCID: flow cell ID
    Lane: lane number (integer from 1 to 8)
    SampleID: ID (name) for the sample
    SampleRef: reference used for alignment for the sample
    Index: index sequences (multiple index reads are separated by a hyphen e.g.
           ACCAGTAA-GGACATGA
    Description: Description of the sample
    Control: Y indicates this lane is a control lane, N means sample
    Recipe: Recipe used during sequencing
    Operator: Name or ID of the operator
    SampleProject: project the sample belongs to

    The key fields are 'Lane', 'Index' (needed for demultiplexing), 'SampleID' (used
    to name the output FASTQ files from CASAVA) and 'SampleProject' (used to name the
    output directories that group together FASTQ files from samples with the same
    project name).

    The standard TabFile methods can be used to interrogate and manipulate the data:

    >>> s = CasavaSampleSheet('SampleSheet.csv')
    >>> print "Number of lines = %d" % len(s)
    >>> line = s[0]   # Fetch reference to first line
    >>> print "SampleID = %s" % line['SampleID']
    >>> line['SampleID'] = 'New_name'

    'SampleID' and 'SampleProject' must not contain any 'illegal' characters (e.g.
    spaces, asterisks etc). The full set of illegal characters is listed in the
    'illegal_characters' property of the CasavaSampleSheet object.

    """

    def __init__(self,samplesheet=None,fp=None):
        """Create a new CasavaSampleSheet instance

        Creates a new CasavaSampleSheet and populates it using data from the
        named sample sheet file, or from a file-like object opened by the
        calling program.

        If neither a file name nor a file object are supplied then an empty
        sample sheet is created.

        Arguments:

          samplesheet (optional): name of the sample sheet file to load data
              from (ignored if fp is also specified)
          fp: (optional) a file-like object which data can be loaded from like
              a file; used in preference to samplesheet.
              (Note that the calling program must close the stream itself)

        """
        TabFile.TabFile.__init__(self,filen=samplesheet,fp=fp,
                                 delimiter=',',skip_first_line=True,
                                 column_names=('FCID','Lane','SampleID','SampleRef',
                                               'Index','Description','Control',
                                               'Recipe','Operator','SampleProject'))
        # Characters that can't be used in SampleID and SampleProject names
        self.illegal_characters = "?()[]/\=+<>:;\"',*^|&. \t" 

    def write(self,filen=None,fp=None):
        """Output the sample sheet data to file or stream

        Overrides the TabFile.write method.

        Arguments:
          filen: (optional) name of file to write to; ignored if fp is
            also specified
          fp: (optional) a file-like object opened for writing; used in
            preference to filen if set to a non-null value
              Note that the calling program must close the stream in
              these cases.
        
        """
        TabFile.TabFile.write(self,filen=filen,fp=fp,include_header=True,no_hash=True)

    @property
    def duplicated_names(self):
        """List lines where the SampleID/SampleProject pairs are identical

        Returns a list of lists, with each sublist consisting of the lines with
        identical SampleID/SampleProject pairs.

        """
        samples = {}
        for line in self:
            name = ((line['SampleID'],line['SampleProject']))
            if name not in samples:
                samples[name] = [line]
            else:
                samples[name].append(line)
        duplicates = []
        for name in samples:
            if len(samples[name]) > 1: duplicates.append(samples[name])
        return duplicates

    @property
    def empty_names(self):
        """List lines with blank SampleID or SampleProject names

        Returns a list of lines with blank SampleID or SampleProject names.

        """
        empty_names = []
        for line in self:
            if line['SampleID'].strip() == '' or line['SampleProject'].strip() == '':
                empty_names.append(line)
        return empty_names

    @property
    def illegal_names(self):
        """List lines with illegal characters in SampleID or SampleProject names

        Returns a list of lines with SampleID or SampleProject names containing
        illegal characters.

        """
        illegal_names = []
        for line in self:
            for c in self.illegal_characters:
                illegal = (line['SampleID'].count(c) > 0) or (line['SampleProject'].count(c) > 0)
                if illegal:
                    illegal_names.append(line)
                    break
        return illegal_names

    def fix_duplicated_names(self):
        """Rename samples to remove duplicated SampleID/SampleProject pairs

        Appends numeric index to SampleIDs in duplicated lines to remove the
        duplication.

        """
        for duplicate in self.duplicated_names:
            for i in range(0,len(duplicate)):
                duplicate[i]['SampleID'] = "%s_%d" % (duplicate[i]['SampleID'],i+1)

    def fix_illegal_names(self):
        """Replace illegal characters in SampleID and SampleProject pairs

        Replaces any illegal characters with underscores.
        
        """
        for line in self.illegal_names:
            for c in self.illegal_characters:
                line['SampleID'] = line['SampleID'].strip().replace(c,'_').strip('_')
                line['SampleProject'] = line['SampleProject'].strip().replace(c,'_').strip('_')

class IlluminaFastq:
    """Class for extracting information about Fastq files

    Given the name of a Fastq file from CASAVA/Illumina platform, extract
    data about the sample name, barcode sequence, lane number, read number
    and set number.

    The format of the names follow the general form:

    <sample_name>_<barcode_sequence>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_ATCACG_L002_R1_001.fastq.gz

    sample_name = 'NA10831_ATCACG_L002_R1_001'
    barcode_sequence = 'ATCACG'
    lane_number = 2
    read_number = 1
    set_number = 1

    Provides the follow attributes:

    fastq:            the original fastq file name
    sample_name:      name of the sample (leading part of the name)
    barcode_sequence: barcode sequence (string or None)
    lane_number:      integer
    read_number:      integer
    set_number:       integer

    """
    def __init__(self,fastq):
        """Create and populate a new IlluminaFastq object

        Arguments:
          fastq: name of the fastq.gz (optionally can include leading path)

        """
        # Store name
        self.fastq = fastq
        # Values derived from the name
        self.sample_name = None
        barcode_sequence = None
        lane_number = None
        read_number = None
        set_number = None
        # Base name for sample (no leading path or extension)
        fastq_base = os.path.basename(fastq)
        try:
            i = fastq_base.index('.')
            fastq_base = fastq_base[:i]
        except ValueError:
            pass
        # Identify which part of the name is which
        fields = fastq_base.split('_')
        nfields = len(fields)
        # Set number: zero-padded 3 digit integer '001'
        self.set_number = int(fields[-1])
        # Read number: single integer digit 'R1'
        self.read_number = int(fields[-2][1])
        # Lane number: zero-padded 3 digit integer 'L001'
        self.lane_number = int(fields[-3][1:])
        # Barcode sequence: string (or None if 'NoIndex')
        self.barcode_sequence = fields[-4]
        if self.barcode_sequence == 'NoIndex':
            self.barcode_sequence = None
        # Sample name: whatever's left over
        self.sample_name = '_'.join(fields[:-4])

class IlluminaDataError(Exception):
    """Base class for errors with Illumina-related code"""

#######################################################################
# Module Functions
#######################################################################

def convert_miseq_samplesheet_to_casava(samplesheet=None,fp=None):
    """Convert a Miseq sample sheet file to CASAVA format

    Reads the data in a Miseq-format sample sheet file and returns a
    CasavaSampleSheet object with the equivalent data.

    The MiSeq sample sheet consists of various sections delimited by
    headers of the form "[Header]", "[Reads]" etc. The information
    about the sample names and barcodes are in the "[Data]" section,
    which is essentially a list of CSV format lines with the following
    fields:

    Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,
    Sample_Project,Description

    The conversion maps a subset of these onto fields in the Casava
    format:

    Sample_ID -> SampleID
    index -> Index
    Sample_Project -> SampleProject
    Description -> Description

    Lane is always set to 1 and the FCID is set to an arbitrary value.
    All other fields are left empty.

    Arguments:
      samplesheet: name of the Miseq sample sheet file
    
    Returns:
      A populated CasavaSampleSheet object.
    """
    # Read MiSEQ data into a TabFile
    if fp is not None:
        # Use file object already provided
        miseq_fp = fp
    else:
        # Open file
        miseq_fp = open(samplesheet,'rU')
    # Skip through the header until we get to the [Data] section
    for line in miseq_fp:
        if line.startswith('[Data]'):
            # Feed the rest of the file to a TabFile
            miseq_sample_sheet = TabFile.TabFile(fp=miseq_fp,delimiter=',',
                                                 first_line_is_header=True)
            break
    # Close file, if we opened it
    if fp is None:
        miseq_fp.close()
    # Check for paired end data
    if 'index2' in miseq_sample_sheet.header():
        paired_end = True
    else:
        paired_end = False
    # Create an empty CASAVA-style sample sheet
    casava_sample_sheet = CasavaSampleSheet()
    # Reformat each line of the Miseq samplesheet into CASAVA format
    for line in miseq_sample_sheet:
        casava_line = casava_sample_sheet.append()
        casava_line['FCID'] = '660DMAAXX'
        casava_line['Lane'] = 1
        casava_line['SampleID'] = line['Sample_ID']
        casava_line['Description'] = line['Description']
        # Deal with index sequences
        if not paired_end:
            casava_line['Index'] = line['index']
        else:
            casava_line['Index'] = "%s-%s" % (line['index'],line['index2'])
        # Deal with project name
        if casava_line['SampleProject'] == '':
            # No project name - try to use initials from sample name
            casava_line['SampleProject'] = \
                bcf_utils.extract_initials(casava_line['SampleID'])
        else:
            casava_line['SampleProject'] = line['Sample_Project']
    return casava_sample_sheet

#######################################################################
# Tests
#######################################################################

import unittest
import cStringIO

class TestCasavaSampleSheet(unittest.TestCase):

    def setUp(self):
        # Set up test data with duplicated names
        self.sample_sheet_data = [
            ['DADA331XX',1,'PhiX','PhiX control','','Control','','','Peter','Control'],
            ['DADA331XX',2,'884-1','PB-884-1','AGTCAA','RNA-seq','','','Peter','AR'],
            ['DADA331XX',3,'885-1','PB-885-1','AGTTCC','RNA-seq','','','Peter','AR'],
            ['DADA331XX',4,'886-1','PB-886-1','ATGTCA','RNA-seq','','','Peter','AR'],
            ['DADA331XX',5,'884-1','PB-884-1','AGTCAA','RNA-seq','','','Peter','AR'],
            ['DADA331XX',6,'885-1','PB-885-1','AGTTCC','RNA-seq','','','Peter','AR'],
            ['DADA331XX',7,'886-1','PB-886-1','ATGTCA','RNA-seq','','','Peter','AR'],
            ['DADA331XX',8,'PhiX','PhiX control','','Control','','','Peter','Control']
            ]
        text = []
        for line in self.sample_sheet_data:
            text.append(','.join([str(x) for x in line]))
        self.sample_sheet_text = "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject\n" + '\n'.join(text)

    def test_read_sample_sheet(self):
        """Read valid sample sheet

        """
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO(self.sample_sheet_text))
        # Check number of lines read
        self.assertEqual(len(sample_sheet),8,"Wrong number of lines")
        # Check data items
        for i in range(0,8):
            self.assertEqual(sample_sheet[i]['FCID'],self.sample_sheet_data[i][0])
            self.assertEqual(sample_sheet[i]['Lane'],self.sample_sheet_data[i][1])
            self.assertEqual(sample_sheet[i]['SampleID'],self.sample_sheet_data[i][2])
            self.assertEqual(sample_sheet[i]['SampleRef'],self.sample_sheet_data[i][3])
            self.assertEqual(sample_sheet[i]['Index'],self.sample_sheet_data[i][4])
            self.assertEqual(sample_sheet[i]['Description'],self.sample_sheet_data[i][5])
            self.assertEqual(sample_sheet[i]['Control'],self.sample_sheet_data[i][6])
            self.assertEqual(sample_sheet[i]['Recipe'],self.sample_sheet_data[i][7])
            self.assertEqual(sample_sheet[i]['Operator'],self.sample_sheet_data[i][8])
            self.assertEqual(sample_sheet[i]['SampleProject'],self.sample_sheet_data[i][9])

    def test_duplicates(self):
        """Check and fix duplicated names

        """
        # Set up
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO(self.sample_sheet_text))
        # Check for duplicates (should be four sets)
        self.assertEqual(len(sample_sheet.duplicated_names),4)
        # Fix and check again (should be none)
        sample_sheet.fix_duplicated_names()
        self.assertEqual(sample_sheet.duplicated_names,[])

    def test_illegal_names(self):
        """Check for illegal characters in names

        """
        # Set up and introduce bad names
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO(self.sample_sheet_text))
        sample_sheet[3]['SampleID'] = '886 1'
        sample_sheet[4]['SampleProject'] = "AR?"
        # Check for illegal names
        self.assertEqual(len(sample_sheet.illegal_names),2)
        # Fix and check again
        sample_sheet.fix_illegal_names()
        self.assertEqual(sample_sheet.illegal_names,[])
        # Verify that character replacement worked correctly
        self.assertEqual(sample_sheet[3]['SampleID'],'886_1')
        self.assertEqual(sample_sheet[4]['SampleProject'],"AR")

class TestMiseqToCasavaConversion(unittest.TestCase):

    def setUp(self):
        self.miseq_header = """[Header]
IEMFileVersion,4
Investigator Name,
Project Name,
Experiment Name,
Date,1/18/2013
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,TruSeq LT
Description,
Chemistry,Default

[Reads]
50

[Settings]

[Data]"""
        # Example of single end data
        self.miseq_data = self.miseq_header + """
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
PB1,,PB,A01,A001,ATCACG,PB,
PB2,,PB,A02,A002,CGATGT,PB,
PB3,,PB,A03,A006,GCCAAT,PB,
PB4,,PB,A04,A008,ACTTGA,PB,
ID3,,PB,A05,A012,CTTGTA,ID,
ID4,,PB,A06,A019,GTGAAA,ID,"""
        self.miseq_sample_ids = ['PB1','PB2','PB3','PB4','ID3','ID4']
        self.miseq_sample_projects = ['PB','PB','PB','PB','ID','ID']
        self.miseq_index_ids = ['ATCACG','CGATGT','GCCAAT','ACTTGA','CTTGTA','GTGAAA']
        # Example of paired end data
        self.miseq_data_paired_end = self.miseq_header + """
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description,GenomeFolder
PB1,,PB,A01,N701,TAAGGCGA,N501,TAGATCGC,,,
ID2,,PB,A02,N702,CGTACTAG,N502,CTCTCTAT,,,"""
        self.miseq_paired_end_sample_ids = ['PB1','ID2']
        self.miseq_paired_end_sample_projects = ['PB','ID']
        self.miseq_paired_end_index_ids = ['TAAGGCGA-TAGATCGC','CGTACTAG-CTCTCTAT']

    def test_convert_miseq_to_casava(self):
        """Convert MiSeq SampleSheet to CASAVA SampleSheet
        
        """
        # Make sample sheet from MiSEQ data
        sample_sheet = convert_miseq_samplesheet_to_casava(
            fp=cStringIO.StringIO(self.miseq_data))
        # Check contents
        self.assertEqual(len(sample_sheet),6)
        for i in range(0,6):
            self.assertEqual(sample_sheet[i]['Lane'],1)
            self.assertEqual(sample_sheet[i]['SampleID'],self.miseq_sample_ids[i])
            self.assertEqual(sample_sheet[i]['SampleProject'],self.miseq_sample_projects[i])
            self.assertEqual(sample_sheet[i]['Index'],self.miseq_index_ids[i])

    def test_convert_miseq_to_casava_paired_end(self):
        """Convert MiSeq SampleSheet to CASAVA SampleSheet (paired end)
        
        """
        # Make sample sheet from MiSEQ data
        sample_sheet = convert_miseq_samplesheet_to_casava(
            fp=cStringIO.StringIO(self.miseq_data_paired_end))
        # Check contents
        self.assertEqual(len(sample_sheet),2)
        for i in range(0,2):
            self.assertEqual(sample_sheet[i]['Lane'],1)
            self.assertEqual(sample_sheet[i]['SampleID'],self.miseq_paired_end_sample_ids[i])
            self.assertEqual(sample_sheet[i]['SampleProject'],
                             self.miseq_paired_end_sample_projects[i])
            self.assertEqual(sample_sheet[i]['Index'],
                             self.miseq_paired_end_index_ids[i])

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
