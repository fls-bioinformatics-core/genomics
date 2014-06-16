#     IlluminaData.py: module for handling data about Illumina sequencer runs
#     Copyright (C) University of Manchester 2012-2013 Peter Briggs
#
########################################################################
#
# IlluminaData.py
#
#########################################################################

__version__ = "1.1.5"

"""IlluminaData

Provides classes for extracting data about runs of Illumina-based sequencers
(e.g. GA2x or HiSeq) from directory structure, data files and naming
conventions.

"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import xml.dom.minidom
import shutil
import platforms
import bcf_utils
import TabFile

#######################################################################
# Class definitions
#######################################################################

class IlluminaRun:
    """Class for examining 'raw' Illumina data directory.

    Provides the following properties:

    run_dir           : name and full path to the top-level data directory
    basecalls_dir     : name and full path to the subdirectory holding bcl files
    sample_sheet_csv  : full path of the SampleSheet.csv file
    runinfo_xml       : full path of the RunInfo.xml file
    platform          : platform e.g. 'miseq'
    bcl_extension     : file extension for bcl files (either "bcl" or "bcl.gz")

    """

    def __init__(self,illumina_run_dir):
        """Create and populate a new IlluminaRun object

        Arguments:
          illumina_run_dir: path to the top-level directory holding
            the 'raw' sequencing data

        """
        # Top-level directory
        self.run_dir = os.path.abspath(illumina_run_dir)
        # Platform
        self.platform = platforms.get_sequencer_platform(self.run_dir)
        if self.platform is None:
            raise Exception("Can't determine platform for %s" % self.run_dir)
        elif self.platform not in ('illumina-ga2x','hiseq','miseq'):
            raise Exception("%s: not an Illumina sequencer?" % self.run_dir)
        # Basecalls subdirectory
        self.basecalls_dir = os.path.join(self.run_dir,
                                          'Data','Intensities','BaseCalls')
        if os.path.isdir(self.basecalls_dir):
            # Locate sample sheet
            self.sample_sheet_csv = os.path.join(self.basecalls_dir,'SampleSheet.csv')
            if not os.path.isfile(self.sample_sheet_csv):
                self.sample_sheet_csv = None
        else:
            self.basecalls_dir = None
        # RunInfo.xml
        self.runinfo_xml = os.path.join(self.run_dir,'RunInfo.xml')
        if not os.path.isfile(self.runinfo_xml):
            self.runinfo_xml = None

    @property
    def bcl_extension(self):
        """Get extension of bcl files

        Returns either 'bcl' or 'bcl.gz'.

        """
        # Locate the directory for the first cycle in the first
        # lane, which should always be present
        lane1_cycle1 = os.path.join(self.basecalls_dir,'L001','C1.1')
        # Examine filename extensions
        for f in os.listdir(lane1_cycle1):
            if str(f).endswith('.bcl'):
                return 'bcl'
            elif str(f).endswith('.bcl.gz'):
                return 'bcl.gz'
        # Failed to match any known extension, raise exception
        raise Exception("No bcl files found in %s" % lane1_cycle1)

class IlluminaRunInfo:
    """Class for examining Illumina RunInfo.xml file

    Extracts basic information from a RunInfo.xml file:

    run_id     : the run id e.g.'130805_PJ600412T_0012_ABCDEZXDYY'
    run_number : the run numer e.g. '12'
    bases_mask : bases mask string derived from the read information
                 e.g. 'y101,I6,y101'
    reads      : a list of Python dictionaries (one per read)

    Each dictionary in the 'reads' list has the following keys:

    number          : the read number (1,2,3,...)
    num_cycles      : the number of cycles in the read e.g. 101
    is_indexed_read : whether the read is an index (i.e. barcode)
                      Either 'Y' or 'N'

    """

    def __init__(self,runinfo_xml):
        """Create and populate a new IlluminaRun object

        Arguments:
          illumina_run_dir: path to the top-level directory holding
            the 'raw' sequencing data

        """
        self.runinfo_xml = runinfo_xml
        self.run_id = None
        self.run_number = None
        self.reads = []
        # Process contents
        #
        doc = xml.dom.minidom.parse(self.runinfo_xml)
        run_tag = doc.getElementsByTagName('Run')[0]
        self.run_id = run_tag.getAttribute('Id')
        self.run_number = run_tag.getAttribute('Number')
        read_tags = doc.getElementsByTagName('Read')
        for read_tag in read_tags:
            self.reads.append({'number': read_tag.getAttribute('Number'),
                               'num_cycles': read_tag.getAttribute('NumCycles'),
                               'is_indexed_read': read_tag.getAttribute('IsIndexedRead')})

    @property
    def bases_mask(self):
        """Generate bases mask string from read information

        Returns a bases mask string of the form e.g. 'y68,I6' for input
        into bclToFastq, based on the read information.

        """
        bases_mask = []
        for read in self.reads:
            num_cycles = int(read['num_cycles'])
            if read['is_indexed_read'] == 'N':
                bases_mask.append("y%d" % num_cycles)
            elif read['is_indexed_read'] == 'Y':
                bases_mask.append("I%d" % num_cycles)
            else:
                raise Exception("Unrecognised value for is_indexed_read: '%s'"
                                % read['is_indexed_read'])
        return ','.join(bases_mask)

class IlluminaData:
    """Class for examining Illumina data post bcl-to-fastq conversion

    Provides the following attributes:

    analysis_dir:  top-level directory holding the 'Unaligned' subdirectory
                   with the primary fastq.gz files
    projects:      list of IlluminaProject objects (one for each project
                   defined at the fastq creation stage, expected to be in
                   subdirectories "Project_...")
    undetermined:  IlluminaProject object for the "Undetermined_indices"
                   subdirectory in the 'Unaligned' directry (or None if
                   no "Undetermined_indices" subdirectory was found e.g.
                   if the run wasn't multiplexed)
    unaligned_dir: full path to the 'Unaligned' directory holding the
                   primary fastq.gz files
    paired_end:    True if all projects are paired end, False otherwise

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
        self.undetermined = None
        self.paired_end = True
        # Look for "unaligned" data directory
        self.unaligned_dir = os.path.join(self.analysis_dir,unaligned_dir)
        if not os.path.exists(self.unaligned_dir):
            raise IlluminaDataError, "Missing data directory %s" % self.unaligned_dir
        # Look for projects
        for f in os.listdir(self.unaligned_dir):
            dirn = os.path.join(self.unaligned_dir,f)
            if f.startswith("Project_") and os.path.isdir(dirn):
                logging.debug("Project dirn: %s" % f)
                self.projects.append(IlluminaProject(dirn))
            elif f == "Undetermined_indices":
                logging.debug("Undetermined dirn: %s" %f)
                self.undetermined = IlluminaProject(dirn)
        # Raise an exception if no projects found
        if not self.projects:
            raise IlluminaDataError, "No projects found"
        # Sort projects on name
        self.projects.sort(lambda a,b: cmp(a.name,b.name))
        # Determine whether data is paired end
        for p in self.projects:
            self.paired_end = (self.paired_end and p.paired_end)

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

    Note that the "Undetermined_indices" directory (which holds fastq files
    for each lane where any reads that couldn't be assigned to a barcode
    during demultiplexing) is also considered as a project, and can be
    processed using an IlluminaData object.

    Provides the following attributes:

    name:      name of the project
    dirn:      (full) path of the directory for the project
    expt_type: the application type for the project e.g. RNA-seq, ChIP-seq
               Initially set to None; should be explicitly set by the
               calling subprogram
    samples:   list of IlluminaSample objects for each sample within the
               project
    paired_end: True if all samples are paired end, False otherwise

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
        self.paired_end = True
        # Get name by removing prefix
        self.project_prefix = "Project_"
        if os.path.basename(self.dirn).startswith(self.project_prefix):
            self.name = os.path.basename(self.dirn)[len(self.project_prefix):]
        else:
            # Check if this is the "Undetermined_indices" directory
            if os.path.basename(self.dirn) == "Undetermined_indices":
                self.name = os.path.basename(self.dirn)
                self.project_prefix = ""
            else:
                raise IlluminaDataError, "Bad project name '%s'" % self.dirn
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
        # Determine whether project is paired end
        for s in self.samples:
            self.paired_end = (self.paired_end and s.paired_end)

    @property
    def full_name(self):
        """Return full name for project

        The full name is "<name>_<expt_type>" (e.g. "PJB_miRNA"), but
        reverts to just "<name>" if no experiment type is set (e.g. "PJB").

        The full name is typically used as the name of the analysis
        subdirectory for the project in the analysis pipeline.

        """
        if self.expt_type is not None:
            return "%s_%s" % (self.name,self.expt_type)
        else:
            return self.name

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
    paired_end: boolean; indicates whether sample is paired end

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaSample object

        Arguments:
          dirn: path to the directory holding the fastq.gz file for the
                sample

        """
        self.dirn = dirn
        self.fastq = []
        self.paired_end = False
        # Get name by removing prefix
        self.sample_prefix = "Sample_"
        self.name = os.path.basename(dirn)[len(self.sample_prefix):]
        logging.debug("\tSample: %s" % self.name)
        # Look for fastq files
        for f in os.listdir(self.dirn):
            if f.endswith(".fastq.gz"):
                self.add_fastq(f)
                logging.debug("\tFastq : %s" % f)
        if not self.fastq:
            logging.debug("\tUnable to find fastq.gz files for %s" % self.name)

    def add_fastq(self,fastq):
        """Add a reference to a fastq file in the sample

        Arguments:
          fastq: name of the fastq file
        """
        self.fastq.append(fastq)
        # Sort fastq's into order
        self.fastq.sort()
        # Check paired-end status
        if not self.paired_end:
            fq = IlluminaFastq(fastq)
            if fq.read_number == 2:
                self.paired_end = True

    def fastq_subset(self,read_number=None,full_path=False):
        """Return a subset of fastq files from the sample

        Arguments:
          read_number: select subset based on read_number (1 or 2)
          full_path  : if True then fastq files will be returned
            with the full path, if False (default) then as file
            names only.

        Returns:
          List of fastq files matching the selection criteria.

        """
        # Build list of fastqs that match the selection criteria
        fastqs = []
        for fastq in self.fastq:
            fq = IlluminaFastq(fastq)
            if fq.read_number is None:
                raise IlluminaDataException, \
                    "Unable to determine read number for %s" % fastq
            if fq.read_number == read_number:
                if full_path:
                    fastqs.append(os.path.join(self.dirn,fastq))
                else:
                    fastqs.append(fastq)
        # Sort into dictionary order and return
        fastqs.sort()
        return fastqs

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
        # Remove double quotes from values
        for line in self:
            for name in self.header():
                line[name] = str(line[name]).strip('"')
        # Remove lines that appear to be commented, after quote removal
        for i,line in enumerate(self):
            if str(line).startswith('#'):
                del(self[i])

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
            name = ((line['SampleID'],line['SampleProject'],line['Index'],line['Lane']))
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

    def predict_output(self):
        """Predict the expected outputs from the sample sheet content

        Constructs and returns a simple dictionary-based data structure
        which predicts the output data structure that will produced by
        running CASAVA using the sample sheet data.

        The structure is:

        { 'project_1': {
                         'sample_1': [name1,name2...],
                         'sample_2': [...],
                         ... }
          'project_2': {
                         'sample_3': [...],
                         ... }
          ... }

        """
        projects = {}
        for line in self:
            project = "Project_%s" % line['SampleProject']
            sample = "Sample_%s" % line['SampleID']
            if project not in projects:
                samples = {}
            else:
                samples = projects[project]
            if sample not in samples:
                samples[sample] = []
            if line['Index'].strip() == "":
                indx = "NoIndex"
            else:
                indx = line['Index']
            samples[sample].append("%s_%s_L%03d" % (line['SampleID'],
                                                    indx,
                                                    line['Lane']))
            projects[project] = samples
        return projects

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

    def __repr__(self):
        """Implement __repr__ built-in

        """
        return "%s_%s_L%03d_R%d_%03d" % (self.sample_name,
                                         'NoIndex' if self.barcode_sequence is None else self.barcode_sequence,
                                         self.lane_number,
                                         self.read_number,
                                         self.set_number)

class IlluminaDataError(Exception):
    """Base class for errors with Illumina-related code"""

#######################################################################
# Module Functions
#######################################################################

def split_run_name(dirname):
    """Split an Illumina directory run name into components

    Given a directory for an Illumina run, e.g.

    140210_M00879_0031_000000000-A69NA

    split the name into components and return as a tuple:

    (date_stamp,instrument_name,run_number)

    e.g.

    ('140210','M00879','0031')

    """
    date_stamp = None
    instrument_name = None
    run_number = None
    fields = os.path.basename(dirname).split('_')
    if len(fields) > 3 and len(fields[0]) == 6 and fields[0].isdigit:
        date_stamp = fields[0]
    if len(fields) >= 2:
        instrument_name = fields[1]
    if len(fields) >= 3 and fields[2].isdigit:
        run_number = fields[2]
    if date_stamp and instrument_name and run_number:
        return (date_stamp,instrument_name,run_number)
    else:
        return (None,None,None)

def summarise_projects(illumina_data):
    """Short summary of projects, suitable for logging file

    The summary description is a one line summary of the project names
    along with the number of samples in each, and an indication if the
    run was paired-ended.

    Arguments:
      illumina_data: a populated IlluminaData directory

    Returns:
      Summary description.

    """
    summary = ""
    project_summaries = []
    if illumina_data.paired_end:
        summary = "Paired end: "
    for project in illumina_data.projects:
        n_samples = len(project.samples)
        project_summaries.append("%s (%d sample%s)" % (project.name,
                                                       n_samples,
                                                       's' if n_samples != 1 else ''))
    summary += "; ".join(project_summaries)
    return summary

def describe_project(illumina_project):
    """Generate description string for samples in a project

    Description string gives the project name and a human-readable
    summary of the sample names, plus number of samples and whether
    the data is paired end.

    Example output: "Project Control: PhiX_1-2  (2 samples)"

    Arguments
      illumina_project: IlluminaProject instance

    Returns
      Description string.

    """
    # Gather information
    paired_end = illumina_project.paired_end
    n_samples = len(illumina_project.samples)
    multiple_fastqs_per_sample = False
    for s in illumina_project.samples:
        n_fastqs = len(s.fastq)
        if (paired_end and n_fastqs > 2) or (not paired_end and n_fastqs > 1):
            multiple_fastqs_per_sample = True
            break
    # Build description
    description = "%s: %s" % (illumina_project.name,
                              illumina_project.prettyPrintSamples())
    sample_names = illumina_project.prettyPrintSamples()
    description += " (%d " % n_samples
    if paired_end:
        description += "paired end "
    if n_samples == 1:
        description += "sample"
    else:
        description += "samples"
    if multiple_fastqs_per_sample:
        description += ", multiple fastqs per sample"
    description += ")"
    return "%s" % description

def get_casava_sample_sheet(samplesheet=None,fp=None,FCID_default='FC1'):
    """Load data into a 'standard' CASAVA sample sheet CSV file

    Reads the data from an Illumina platform sample sheet CSV file and
    populates and returns a CasavaSampleSheet object which can be
    used to generate make a SampleSheet suitable for bcl-to-fastq
    conversion.

    The source sample sheet may be in the format output by the
    Experimental Manager software (needed when running BaseSpace) or
    may already be in "standard" format for bcl-to-fastq format.

    For Experimental Manager format, the sample sheet consists of
    sections delimited by headers of the form "[Header]", "[Reads]" etc.
    The information about the sample names and barcodes are in the
    "[Data]" section, which is essentially a list of CSV format lines
    with the following fields:

    MiSEQ:

    Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,
    Sample_Project,Description

    HiSEQ:

    Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,
    index,Sample_Project,Description

    (Note that for dual-indexed runs the fields are e.g.:

    Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,
    I5_Index_ID,index2,Sample_Project,Description

    i.e. there are an additional pair of fields describing the second
    index)
    
    The conversion maps a subset of these onto fields in the Casava
    format:

    Sample_ID -> SampleID
    index -> Index
    Sample_Project -> SampleProject
    Description -> Description

    If no lane information is present in the original file then this
    is set to 1. The FCID is set to an arbitrary value.

    For dual-indexed samples, the Index field is generated by putting
    together the index and index2 fields.

    All other fields are left empty.

    Arguments:
      samplesheet: name of the Miseq sample sheet file
      FCID_default: name to use for flow cell ID if not present in
        the source file (optional)
    
    Returns:
      A populated CasavaSampleSheet object.

    """
    # Open the file for reading (if necessary)
    if fp is not None:
        # Use file object already provided
        sample_sheet_fp = fp
    else:
        # Open file
        sample_sheet_fp = open(samplesheet,'rU')
    # Read the sample sheet file to see if we can identify
    # the format
    line = sample_sheet_fp.readline()
    if line.startswith('[Header]'):
        # "Experimental Manager"-style format with [...] delimited sections
        experiment_manager_format = True
        # Skip through until we reach a [Data] section
        while not line.startswith('[Data]'):
            line = sample_sheet_fp.readline()
        # Feed the rest of the file to a TabFile
        data = TabFile.TabFile(fp=sample_sheet_fp,delimiter=',',
                               first_line_is_header=True)
    elif line.count(',') > 0:
        # Looks like a comma-delimited header
        experiment_manager_format = False
        # Feed the rest of the file to a TabFile
        data = TabFile.TabFile(fp=sample_sheet_fp,delimiter=',',
                               column_names=line.split(','))
    else:
        # Don't know what to do with this
        raise Exception, "SampleSheet format not recognised"
    # Close file, if we opened it
    if fp is None:
        sample_sheet_fp.close()
    # Clean up data: remove double quotes from fields
    for line in data:
        for col in data.header():
            line[col] = str(line[col]).strip('"')
    # Try to make sense of what we've got
    header_line = ','.join(data.header())
    if experiment_manager_format:
        # Build new sample sheet with standard format
        sample_sheet = CasavaSampleSheet()
        for line in data:
            sample_sheet_line = sample_sheet.append()
            # Set the lane
            try:
                lane = line['Lane']
            except KeyError:
                # No lane column (e.g. MiSEQ)
                lane = 1
            # Set the index tag (if any)
            try:
                index_tag = "%s-%s" % (line['index'].strip(),
                                       line['index2'].strip())
            except KeyError:
                # Assume not dual-indexed (no index2)
                try:
                    index_tag = line['index'].strip()
                except KeyError:
                    # No index
                    index_tag = ''
            sample_sheet_line['FCID'] = FCID_default
            sample_sheet_line['Lane'] = lane
            sample_sheet_line['Index'] = index_tag
            sample_sheet_line['SampleID'] = line['Sample_ID']
            sample_sheet_line['Description'] = line['Description']
            # Deal with project name
            if line['Sample_Project'] == '':
                # No project name - try to use initials from sample name
                sample_sheet_line['SampleProject'] = \
                   bcf_utils.extract_initials(line['Sample_ID'])
            else:
                sample_sheet_line['SampleProject'] = line['Sample_Project']
    else:
        # Assume standard format, convert directly to CasavaSampleSheet
        sample_sheet = CasavaSampleSheet()
        for line in data:
            if str(line[0]).startswith('#') or str(line).strip() == '':
                continue
            sample_sheet.append(tabdata=str(line))
    # Finished
    return sample_sheet

def convert_miseq_samplesheet_to_casava(samplesheet=None,fp=None):
    """Convert a Miseq sample sheet file to CASAVA format

    Reads the data in a Miseq-format sample sheet file and returns a
    CasavaSampleSheet object with the equivalent data.

    Note: this is now just a wrapper for the more general conversion
    function 'get_casava_sample_sheet' (which can handle the conversion
    without knowing a priori what the SampleSheet format is.

    Arguments:
      samplesheet: name of the Miseq sample sheet file
    
    Returns:
      A populated CasavaSampleSheet object.
    """
    return get_casava_sample_sheet(samplesheet=samplesheet,fp=fp,
                                   FCID_default='660DMAAXX')

def verify_run_against_sample_sheet(illumina_data,sample_sheet):
    """Checks existence of predicted outputs from a sample sheet

    Arguments:
      illumina_data: a populated IlluminaData directory
      sample_sheet : path and name of a CSV sample sheet

    Returns:
      True if all the predicted outputs from the sample sheet are
      found, False otherwise.

    """
    # Get predicted outputs
    predicted_projects = CasavaSampleSheet(sample_sheet).predict_output()
    # Loop through projects and check that predicted outputs exist
    verified = True
    for proj in predicted_projects:
        # Locate project directory
        proj_dir = os.path.join(illumina_data.unaligned_dir,proj)
        if os.path.isdir(proj_dir):
            predicted_samples = predicted_projects[proj]
            for smpl in predicted_samples:
                # Locate sample directory
                smpl_dir = os.path.join(proj_dir,smpl)
                if os.path.isdir(smpl_dir):
                    # Check for output files
                    predicted_names = predicted_samples[smpl]
                    for name in predicted_names:
                        # Look for R1 file
                        f = os.path.join(smpl_dir,"%s_R1_001.fastq.gz" % name)
                        if not os.path.exists(f):
                            logging.warning("Verify: missing R1 file '%s'" % f)
                            verified = False
                        # Look for R2 file (paired end only)
                        if illumina_data.paired_end:
                            f = os.path.join(smpl_dir,"%s_R2_001.fastq.gz" % name)
                            if not os.path.exists(f):
                                logging.warning("Verify: missing R2 file '%s'" % f)
                                verified = False
                else:
                    # Sample directory not found
                    logging.warning("Verify: missing %s" % smpl_dir)
                    verified = False
        else:
            # Project directory not found
            logging.warning("Verify: missing %s" % proj_dir)
            verified = False
    # Return verification status
    return verified

def get_unique_fastq_names(fastqs):
    """Generate mapping of full fastq names to shorter unique names
    
    Given an iterable list of Illumina file fastq names, return a
    dictionary mapping each name to its shortest unique form within
    the list.

    Arguments:
      fastqs: an iterable list of fastq names

    Returns:
      Dictionary mapping fastq names to shortest unique versions
    
    """
    
    # Define a set of templates of increasing complexity,
    # from which to generate shortened names
    templates = ( "NAME",
                  "NAME LANE",
                  "NAME TAG",
                  "NAME TAG LANE",
                  "FULL" )
    # Check for paired end fastq set
    got_R1 = False
    got_R2 = False
    for fastq in fastqs:
        fq = IlluminaFastq(fastq)
        if fq.read_number == 1:
            got_R1 = True
        elif fq.read_number == 2:
            got_R2 = True
    paired_end = got_R1 and got_R2
    # Try each template in turn to see if it can generate
    # a unique set of short names
    for template in templates:
        name_mapping = {}
        unique_names = []
        # Process each fastq file name
        for fastq in fastqs:
            fq = IlluminaFastq(fastq)
            name = []
            if template == "FULL":
                name.append(str(fq))
            else:
                for t in template.split():
                    if t == "NAME":
                        name.append(fq.sample_name)
                    elif t == "TAG":
                        if fq.barcode_sequence is not None:
                            name.append(fq.barcode_sequence)
                    elif t == "LANE":
                        name.append("L%03d" % fq.lane_number)
                # Add the read number for paired end data
                if paired_end:
                    name.append("R%d" % fq.read_number)
            name = '_'.join(name) + ".fastq.gz"
            # Store the name
            if name not in unique_names:
                name_mapping[fastq] = name
                unique_names.append(name)
        # If the number of unique names matches total number
        # of files then we have a unique set
        if len(unique_names) == len(fastqs):
            return name_mapping
    # Failed to make a unique set of names
    raise Exception,"Failed to make a set of unique fastq names"

def fix_bases_mask(bases_mask,barcode_sequence):
    """Adjust input bases mask to match actual barcode sequence lengths

    Updates the bases mask string extracted from RunInfo.xml so that the
    index read masks correspond to the index barcode sequence lengths
    given e.g. in the SampleSheet.csv file.

    For example: if the bases mask is 'y101,I7,y101' (i.e. assigning 7
    cycles to the index read) but the barcode sequence is 'CGATGT' (i.e.
    only 6 bases) then the adjusted bases mask should be 'y101,I6n,y101'.

    Arguments:
      bases_mask: bases mask string e.g. 'y101,I7,y101','y250,I8,I8,y250'
      barcode_sequence: index barcode sequence e.g. 'CGATGT' (single
      index), 'TAAGGCGA-TAGATCGC' (dual index)

    Returns:
      Updated bases mask string.

    """
    # Split barcode sequence string into components
    indexes = barcode_sequence.split('-')
    # Check input reads
    reads = []
    i = 0
    for read in bases_mask.split(','):
        new_read = read
        if read.startswith('I'):
            input_index_length = int(read[1:])
            try:
                actual_index_length = len(indexes[i])
                new_read = "I%d" % actual_index_length
            except IndexError:
                # No barcode for this read
                actual_index_length = 0
                new_read = ""
            if input_index_length > actual_index_length:
                # Actual index sequence is shorter so adjust
                # bases mask and pad with 'n's
                new_read = new_read + \
                           'n'*(input_index_length-actual_index_length)
            i += 1
        reads.append(new_read)
    # Assemble and return updated index tags
    return ','.join(reads)
