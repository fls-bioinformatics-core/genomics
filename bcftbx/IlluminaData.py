#     IlluminaData.py: module for handling data about Illumina sequencer runs
#     Copyright (C) University of Manchester 2012-2025 Peter Briggs
#
########################################################################
#
# IlluminaData.py
#
#########################################################################

"""
Legacy module providing classes for extracting data about Illumina runs
from directory structure, data files and naming conventions, and
handling sample sheet files.

The functionality of the module has been moved to the
'platforms.illumina.data', 'platforms.illumina.samplesheet',
'platforms.illumina.utils' and 'platforms.illumina.exceptions' modules,
which supersede this one. This module is now deprecated and
will be removed in a future release.

The legacy classes have been reimplemented as wrappers to the classes
in the newer module, to preserve backwards compatibility.
"""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import sys
import logging
import xml.dom.minidom
import shutil
import io
from . import platforms
from . import utils
from . import TabFile
from functools import reduce
from builtins import str

from .platforms import RUN_COMPLETION_FILES
from .platforms.illumina import data as illumina
from .platforms.illumina import samplesheet as illumina_samplesheet
from .platforms.illumina import utils as illumina_utils
from .platforms.illumina.exceptions import IlluminaError
from .platforms.illumina.exceptions import IlluminaPlatformError
from .platforms.illumina.samplesheet import SAMPLESHEET_ILLEGAL_CHARS

#######################################################################
# Module constants
#######################################################################

KNOWN_PLATFORMS = ('illumina-ga2x',
                   'hiseq',
                   'hiseq4000',
                   'miseq',
                   'nextseq',
                   'novaseq6000',
                   'miniseq',
                   'iseq')

#######################################################################
# Class definitions
#######################################################################

class IlluminaRun(illumina.RunDir):
    """Class for examining 'raw' Illumina data directory.

    Provides the following properties:

    - run_dir: name and full path to the top-level data directory
    - basecalls_dir: name and full path to the subdirectory holding bcl files
    - sample_sheet_csv: full path of the SampleSheet.csv file
    - runinfo_xml: full path of the RunInfo.xml file
    - runparameters_xml: full path of the RunParameters.xml file
    - platform: platform e.g. 'miseq'
    - bcl_extension: file extension for bcl files (either "bcl" or "bcl.gz")
    - lanes: list of (integer) lane numbers in the run
    - sample_sheet: SampleSheet instance (if the run has an associated
      sample sheet file)
    - runinfo: IlluminaRunInfo instance (if the run has an associated
      RunInfo.xml file)
    - runparameters: IlluminaRunParameters instance (if the run has an
      associated RunParameters.xml file)
    """

    def __init__(self, illumina_run_dir, platform=None):
        """Create and populate a new IlluminaRun object

        Arguments:
          illumina_run_dir: path to the top-level directory holding
            the 'raw' sequencing data
          platform: (optional) string specifying the sequencer
            platform. The platform should be detected automatically
            so only specify this if the sequencer is not in the
            list in platforms.py.

        """
        # Initialise base class
        try:
            illumina.RunDir.__init__(self, illumina_run_dir)
        except IlluminaError as ex:
            raise IlluminaDataError(ex)
        # Update objects
        if self.runparameters_xml:
            self.runparameters = IlluminaRunParameters(
                self.runparameters_xml)
        if self.runinfo_xml:
            self.runinfo = IlluminaRunInfo(self.runinfo_xml)
        if self.sample_sheet_csv:
            self.sample_sheet = SampleSheet(self.sample_sheet_csv)
        # Platform
        if platform:
            # Supplied explicitly
            self.platform = str(platform)
        elif self.platform == "unknown":
            # Not an Illumina run?
            raise IlluminaDataPlatformError("%s: not an Illumina "
                                            "sequencing run?" %
                                            self.run_dir)
        if self.platform not in KNOWN_PLATFORMS:
            logging.warning("%s: not a recognised Illumina platform" %
                            self.run_dir)

    @property
    def run_dir(self):
        """
        Alias for 'path' property
        """
        return self.path

    @property
    def complete(self):
        """
        Check if run is complete

        Returns:
          Boolean: True if run is complete (i.e. all appropriate
            sentinel files are present), False if not (i.e.
            some sentiel files are missing).
        """
        # Acquire run completion files
        try:
            files = RUN_COMPLETION_FILES[self.platform]
        except KeyError:
            # Fallback to default
            files = RUN_COMPLETION_FILES["default"]
        # Check if all are present
        return all([os.path.exists(os.path.join(self.run_dir,f))
                    for f in files])


class IlluminaRunInfo(illumina.RunInfo):
    """Class for examining Illumina RunInfo.xml file

    Extracts basic information from a RunInfo.xml file:

    - run_id: the run id e.g.'130805_PJ600412T_0012_ABCDEZXDYY'
    - run_number: the run number e.g. '0012'
    - instrument: the instrument name e.g. 'PJ600412T'
    - date: the run date e.g. '130805'
    - flowcell: the flowcell id e.g. 'ABCDEZXDYY'
    - lane_count: the flowcell lane count e.g. 8
    - bases_mask: bases mask string derived from the read
      information e.g. 'y101,I6,y101'
    - reads: a list of Python dictionaries (one per read)

    Each dictionary in the 'reads' list has the following keys:

    - number: the read number (1,2,3,...)
    - num_cycles: the number of cycles in the read e.g. 101
    - is_indexed_read: whether the read is an index (i.e.
      barcode); either 'Y' or 'N'

    Arguments:
      runinfo_xml (str): path to the RunInfo.xml file
    """

    def __init__(self,runinfo_xml):
        """
        Create and populate a new IlluminaRunInfo object
        """
        illumina.RunInfo.__init__(self, runinfo_xml)


class IlluminaRunParameters(illumina.RunParameters):
    """Class for examining Illumina RunParameters.xml file

    Extracts basic information from a RunParameters.xml file:

    - flowcell_mode: the flowcell mode e.g. 'SP','S4'

    Arguments:
      runparameters_xml (str): path to the RunParameters.xml
        file
    """
    def __init__(self,runparameters_xml):
        """
        Create and populate a new IlluminaRunParameters object
        """
        illumina.RunParameters.__init__(self, runparameters_xml)


class IlluminaData(illumina.FastqDir):
    """Class for examining Illumina data post bcl-to-fastq conversion

    Provides the following attributes:

    - analysis_dir: top-level directory holding the 'Unaligned'
      subdirectory with the primary fastq.gz files
    - projects: list of IlluminaProject objects (one for each
      project defined at the fastq creation stage)
    - undetermined:  IlluminaProject object for the undetermined
      reads
    - unaligned_dir: full path to the 'Unaligned' directory
      holding the primary fastq.gz files
    - paired_end: True if at least one project is paired end,
      False otherwise
    - format: Format of the directory structure layout (either
      'casava' or 'bcl2fastq2', or None if the format cannot
      be determined)
    - lanes: List of lane numbers present; if there are no lanes
      then this will be a list with 'None' as the only value

    Provides the following methods:

    - get_project(): lookup and return an IlluminaProject object
      corresponding to the supplied project name

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
        ##analysis_dir = os.path.abspath(illumina_analysis_dir)
        ##unaligned_dir = os.path.join(analysis_dir, unaligned_dir)
        try:
            illumina.FastqDir.__init__(self, os.path.join(illumina_analysis_dir,
                                                          unaligned_dir))
        except IlluminaError as ex:
            raise IlluminaDataError(ex)
        ##self.analysis_dir = analysis_dir
        ##self.unaligned_dir = unaligned_dir

    @property
    def unaligned_dir(self):
        """
        Alias for 'path' property
        """
        return self.path

    @property
    def analysis_dir(self):
        """
        Path to parent directory
        """
        return os.path.dirname(self.path)


class IlluminaProject(illumina.FastqDirProject):
    """Class for storing information on a 'project' within an Illumina run

    A project is a subset of fastq files from a run of an Illumina
    sequencer; in the first instance projects are defined within the
    SampleSheet.csv file which is output by the sequencer.

    Note that the "undetermined" fastqs (which hold reads for each lane
    which couldn't be assigned to a barcode during demultiplexing) is also
    considered as a project, and can be processed using an IlluminaProject
    object.

    Provides the following attributes:

    - name: name of the project
    - dirn: (full) path of the directory for the project
    - expt_type: the application type for the project e.g. RNA-seq,
      ChIP-seq (initially set to None; should be explicitly set by
      the calling subprogram)
    - samples: list of IlluminaSample objects for each sample within
      the project
    - paired_end: True if all samples are paired end, False otherwise
    - undetermined: True if 'samples' are actually undetermined reads

    """

    def __init__(self,dirn):
        """Create and populate a new IlluminaProject object

        Arguments:
          dirn: path to the directory holding the samples within the
                project (expected to be in subdirectories "Sample_...")

        """
        illumina.FastqDirProject.__init__(self, dirn)

    def prettyPrintSamples(self):
        """Return a nicely formatted string describing the sample names
        """
        return illumina.FastqDirProject.pretty_print_names(self.samples)


class IlluminaSample(illumina.FastqDirSample):
    """Class for storing information on a 'sample' within an Illumina project

    A sample is a fastq file generated within an Illumina sequencer run.

    Provides the following attributes:

    - name: sample name
    - dirn: (full) path of the directory for the sample
    - fastq: name of the fastq.gz file (without leading directory,
      join to 'dirn' to get full path)
    - paired_end: boolean; indicates whether sample is paired end

    """

    def __init__(self,dirn,fastqs=None,name=None,prefix='Sample_'):
        """Create and populate a new IlluminaSample object

        Arguments:
          dirn:   path to the directory holding the fastq.gz files for
                  the sample
          fastqs: optional, a list of fastq files associated with the
                  sample (expected to be under the directory 'dirn')
          name: optional, the name of the sample (if not supplied then
                  will attempt to determine automatically)
          prefix: optional, explicitly specify the 'prefix' placed in
                  front of the sample name to generate the matching
                  directory

        """
        illumina.FastqDirSample.__init__(self, dirn, fastqs=fastqs,
                                         name=name, prefix=prefix)

class SampleSheet(illumina_samplesheet.SampleSheet):
    """
    Class for handling Illumina sample sheets

    This is a general class which tries to handle and convert
    between older (i.e. 'CASAVA'-style) and newer (IEM-style) sample
    sheet files for Illumina sequencers, in a transparent manner.

    Experimental Manager (IEM) sample sheet format
    ----------------------------------------------

    The Experimental Manager (IEM) samplel sheets are text files
    with data delimited by '[...]' lines e.g. '[Header]', '[Reads]'
    etc.

    The 'Header' section consists of comma-separated key-value pairs
    e.g. 'Application,HiSeq FASTQ Only'.

    The 'Reads' section consists of values (one per line) (possibly
    number of bases per read?) e.g. '101'.

    The 'Settings' section consists of comma-separated key-value
    pairs e.g. 'Adapter,CTGTCTCTTATACACATCT'.

    The 'Manifests' section consists of comma-separated key-filename
    pairs e.g. 'A,TruSeqAmpliconManifest-1.txt'.

    The 'Data' section contains the data about the lanes, samples
    and barcode indexes. It consists of lines of comma-separated
    values, with the first line being a 'header', and the remainder
    being values for each of those fields.

    CASAVA-style sample sheet format
    --------------------------------

    This older style of sample sheet is used by CASAVA and bcl2fastq
    v1.8.*. It consists of lines of comma-separated values, with the
    first line being a 'header' and the remainder being values for
    each of the fields:

    - FCID: flow cell ID
    - Lane: lane number (integer from 1 to 8)
    - SampleID: ID (name) for the sample
    - SampleRef: reference used for alignment for the sample
    - Index: index sequences (multiple index reads are separated by a
      hyphen e.g. ACCAGTAA-GGACATGA
    - Description: Description of the sample
    - Control: Y indicates this lane is a control lane, N means sample
    - Recipe: Recipe used during sequencing
    - Operator: Name or ID of the operator
    - SampleProject: project the sample belongs to

    Although the CASAVA-style sample sheet looks much like the IEM
    'Data' section, note that it has different fields and field
    names.

    Basic usage
    -----------

    To load data from an IEM-format file:

    >>> iem = SampleSheet('SampleSheet.csv')

    To access 'header' items:

    >>> iem.header_items
    ['IEMFileVersion','Date',..]
    >>> iem.header['IEMFileVersion']
    '4'

    To access 'reads' data:

    >>> iem.reads
    ['101','101']

    To access 'settings' items:

    >>> iem.settings_items
    ['ReverseComplement',...]
    >>> iem.settings['ReverseComplement']
    '0'

    To access 'manifests' items:

    >>> iem.manifests_items
    ['A',...]
    >>> iem.manifests['A']
    'TruSeqAmpliconManifest-1.txt'

    To access 'data' (the actual sample sheet information):

    >>> iem.data.header()
    ['Lane','Sample_ID',...]
    >>> iem.data[0]['Lane']
    1

    etc.

    To load data from a CASAVA style sample sheet:

    >>> casava = SampleSheet('SampleSheet.csv')

    To access the data use the 'data' property:

    >>> casava.data.header()
    ['Lane','SampleID',...]
    >>> casava.data[0]['Lane']
    1

    Accessing data directly
    -----------------------

    The data in the 'Data' section can be accessed directly
    from the SampleSheet instance, e.g.

    >>> iem[0]['Lane']

    is equivalent to

    >>> iem.data[0]['Lane']

    It is also possible to set new values for data items using
    this notation.

    The data lines can be iterated over using:

    >>> for line in iem:
    >>> ...

    To find the number of lines that are stored:

    >>> len(iem)

    To append a new line:

    >>> new_line = iem.append(...)

    Checking and clean-up methods
    -----------------------------

    A number of methods are available to check and fix common
    problems, specifically:

    - detect and replace 'illegal' characters in sample and project
      names
    - detect and fix duplicated sample name, project and lane
      combinations
    - detect blank sample and project names

    Sample sheet reconstruction
    ---------------------------

    Data is loaded it is also subjected to some basic cleaning
    up, including stripping of unnecessary commas and white space.
    The 'show' method returns a reconstructed version of the
    original sample sheet after the cleaning operations were
    performed.

    """
    def __init__(self, sample_sheet=None, fp=None):
        """
        Create a new SampleSheet instance

        The instance will be populated by reading data from
        either a stream opened for reading, or from a file.

        Arguments:
          sample_sheet (str): path to a sample file to load
            data from
          fp (File): File-like object opened for reading; if
            this is not None then the SampleSheet object will
            be populated from this even if a file is also
            specified

        """
        try:
            illumina_samplesheet.SampleSheet.__init__(
                self,
                sample_sheet=sample_sheet,
                fp=fp)
        except IlluminaError as ex:
            raise IlluminaDataError(ex)

class IEMSampleSheet(SampleSheet):
    """
    Class for handling Experimental Manager format sample sheet

    This class is a subclass of the SampleSheet class, and provides
    an additional method ('casava_sample_sheet') to convert to a
    CASAVA-style sample sheet, suitable for input into bcl2fastq
    version 1.8.*.

    """
    def __init__(self,sample_sheet=None,fp=None):
        """Create a new IEMSampleSheet instance

        Read in data from an Experimental Manager-format sample
        sheet and populate a data structure.
 
        Raises IlluminaDataError exception if the input data
        doesn't appear to be in the correct format.

        Arguments
          sample_sheet: name of a sample sheet file to read in
          fp: file-like object opened for reading which contains
             sample sheet data; if set then used in preference
             to 'sample_sheet' argument

        """
        try:
            SampleSheet.__init__(self,sample_sheet,fp)
        except IlluminaError as ex:
            raise IlluminaDataError(ex)
        if self._format != 'IEM':
            raise IlluminaDataError("Sample sheet is not IEM format")

    def casava_sample_sheet(self,FCID='FC1',fix_empty_projects=True):
        """Return data as a CASAVA formatted sample sheet

        Create a new CasavaSampleSheet instance populated
        with data from the IEM sample sheet.

        Arguments:
          FCID: set the flow cell ID for the output Casava
            sample sheet (defaults to 'FCID')
          fix_empty_projects: if True then attempt to populate
            blank 'SampleProject' fields with values derived
            from sample names

        Returns:
          CasavaSampleSheet object.

        """
        sample_sheet = CasavaSampleSheet()
        for line in self._data:
            sample_sheet_line = sample_sheet.append()
            # Set the lane
            try:
                lane = line['Lane']
            except KeyError:
                # No lane column (e.g. MiSEQ)
                lane = 1
            # Set the index tag (if any)
            index_tag = samplesheet_index_sequence(line)
            if not index_tag:
                index_tag = ''
            sample_sheet_line['FCID'] = FCID
            sample_sheet_line['Lane'] = lane
            sample_sheet_line['Index'] = index_tag
            sample_sheet_line['SampleID'] = line['Sample_ID']
            sample_sheet_line['Description'] = line['Description']
            # Deal with project name
            if line['Sample_Project'] == '' and fix_empty_projects:
                # No project name - try to use initials from sample name
                sample_sheet_line['SampleProject'] = \
                   utils.extract_initials(line['Sample_ID'])
            else:
                sample_sheet_line['SampleProject'] = line['Sample_Project']
        return sample_sheet

class CasavaSampleSheet(SampleSheet):
    """
    Class for reading and manipulating sample sheet files for CASAVA

    This class is a subclass of the SampleSheet class, and provides
    an additional method ('casava_sample_sheet') to convert to a
    CASAVA-style sample sheet, suitable for input into bcl2fastq
    version 1.8.*.

    Raises IlluminaDataError exception if the input data doesn't
    appear to be in the correct format.

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
        SampleSheet.__init__(self,samplesheet,fp)
        if self._data is None:
            self._data = TabFile.TabFile(delimiter=',',
                                         column_names=('FCID','Lane',
                                                       'SampleID','SampleRef',
                                                       'Index','Description',
                                                       'Control','Recipe',
                                                       'Operator','SampleProject'))
            self._format = 'CASAVA'
        if self._format != 'CASAVA':
            raise IlluminaDataError("Sample sheet is not CASAVA format")

    def header(self):
        """
        Return header items from the CASAVA sample sheet

        NB this over-rides the 'header' method from the base class.
        """
        return self._data.header()

    def write(self,filen=None,fp=None):
        """
        Output the sample sheet data to file or stream

        Arguments:
          filen: (optional) name of file to write to; ignored if fp is
            also specified
          fp: (optional) a file-like object opened for writing; used in
            preference to filen if set to a non-null value
            Note that the calling program must close the stream in
            these cases.

        """
        SampleSheet.write(self,filen=filen,fp=fp,fmt='CASAVA')

class SampleSheetPredictor(illumina_samplesheet.SampleSheetPredictor):
    """
    Class to predict outputs of a sample sheet file

    Supplied with a sample sheet file, or the contents of a
    sample sheet, this class can predict the expected output
    projects, sample names and Fastq file names according to
    the bcl-to-fastq conversion software that is used and the
    type of data that is present.

    By default the predicted outputs are for single-ended data
    converted using 'bcl2fastq2' with no lane information. The
    `set` method can be invoked to predict outputs for other
    configurations.

    It uses two additional helper classes `SampleSheetProject`
    and `SampleSheetSample`, which hold information about
    the predicted projects and samples.

    Example usage: create a new predictor object:

    >>> predictor = SampleSheetPredictor(sample_sheet_file="SampleSheet.txt")

    To get a list of the expected project names:

    >>> project_names = predictor.project_names

    To get a `SampleSheetProject` corresponding to a project
    name:

    >>> predicted_project = predictor.get_project("MyProject")

    To loop over the `SampleSheetSamples` in the project
    corresponding to the expected samples and get a list of the
    expected Fastqs:

    >>> for predicted_sample in predicted_project.samples:
    ...    for fq in predicted_sample.fastqs:
    ...       print("Predicted Fastq: %s" % fq)

    To predict Fastqs for paired-end data:

    >>> predictor.set(paired_end=True)
    >>> for p in predictor.projects:
    ...    for s in p.samples:
    ...       for fq in s.fastqs:
    ...          print(fq)

    (See also the `SampleSheetProject` and `SampleSheetSample`)

    Available properties:

    - projects: list of the associated SampleSheetProjects
    - nprojects: number of predicted projects
    - project_names: list of the predicted project names

    Available methods:

    - get_project: fetch SampleSheetProject for project name
    - set: configure the predictor for different bcl-to-fastq
        software, conversion options, and data endedness

    """
    def __init__(self,sample_sheet=None,sample_sheet_file=None):
        """
        Create a new SampleSheetPredictor instance

        Arguments:
          sample_sheet (SampleSheet): a SampleSheet instance to use
            for prediction (if None then must provide a file via
            the `sample_sheet_file` argument; if both are provided
            then `sample_sheet` takes precedence)
          sample_sheet_file (str): path to a sample sheet file, if
            `sample_sheet` argument is None

        """
        illumina_samplesheet.SampleSheetPredictor.__init__(
            self,
            sample_sheet=sample_sheet,
            sample_sheet_file=sample_sheet_file)


class SampleSheetProject(illumina_samplesheet.SampleSheetProject):
    """
    Class describing a project from a sample sheet file

    This class describes a predicted project from a
    samplesheet. It is normally created, managed and
    returned by a `SampleSheetPredictor` instance, rather
    than being created directly.

    The predicted samples within the project are
    described by a set of SampleSheetSample instances.

    Available properties:

    - name: project name
    - samples: list of associated SampleSheetSamples
    - sample_ids: list of associated sample IDs
    - dir_name: predicted subdirectory name for the
        project

    Available methods:

    - get_sample: fetch SampleSheetSample by sample ID
    - set: configure the predictor for different bcl-to-fastq
        software, conversion options, and data endedness
    
    """
    def __init__(self,project_name):
        """
        Create a new SampleSheetProject instance

        Arguments:
          project_name (str): name for the project

        """
        illumina_samplesheet.SampleSheetProject.__init__(
            self,
            project_name)


class SampleSheetSample(illumina_samplesheet.SampleSheetSample):
    """
    Class describing a sample from a sample sheet file

    This class describes a predicted sample from a
    samplesheet. It is normally created, managed and
    returned by a `SampleSheetProject` instance, rather
    than being created directly.

    Available properties and data:

    - sample_id: sample ID
    - sample_name: sample name
    - s_index: index number for the sample, for bcl2fastq
    - barcode_seqs: list of barcode sequences associated
        with the sample
    - barcodes: dictionary mapping barcodes to lists of
        lanes for the sample
    - dir_name: predicted subdirectory name for the sample

    Available methods:

    - lanes: list lanes associated with the sample, or with a
        specific barcode
    - fastqs: list of predicted Fastq files for the sample
    - set: configure the predictor for different bcl-to-fastq
        software, conversion options, and data endedness

    """
    def __init__(self,sample_id,sample_name=None,s_index=None):
        """
        Create a new SampleSheetSample instance

        Arguments:
          sample_id (str): id for the sample
          sample_name (str): (optional) corresponding sample
            name
          s_index (integer): (optional) the bcl2fastq sample
            index

        """
        illumina_samplesheet.SampleSheetSample.__init__(
            self,
            sample_id,
            sample_name=sample_name,
            s_index=s_index)


class IlluminaFastq(illumina_utils.IlluminaFastq):
    """Class for extracting information about Fastq files

    Given the name of a Fastq file from CASAVA/Illumina platform, extract
    data about the sample name, barcode sequence, lane number, read number
    and set number.

    For Fastqs produced by CASAVA and bcl2fastq v1.8, the format of the names
    follows the general form:

    <sample_name>_<barcode_sequence>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_ATCACG_L002_R1_001.fastq.gz

    sample_name = 'NA10831'
    barcode_sequence = 'ATCACG'
    lane_number = 2
    read_number = 1
    set_number = 1

    For Fastqs produced by bcl2fast v2, the format looks like:

    <sample_name>_S<sample_number>_L<lane_number>_R<read_number>_<set_number>.fastq.gz

    e.g. for

    NA10831_S4_L002_R1_001.fastq.gz

    sample_name = 'NA10831'
    sample_number = 4
    lane_number = 2
    read_number = 1
    set_number = 1

    Provides the follow attributes:

    fastq:            the original fastq file name
    sample_name:      name of the sample (leading part of the name)
    sample_number:    number of the same (integer or None, bcl2fastq v2 only)
    barcode_sequence: barcode sequence (string or None, CASAVA/bcl2fast v1.8 only)
    lane_number:      integer
    read_number:      integer
    set_number:       integer

    """
    def __init__(self,fastq):
        """Create and populate a new IlluminaFastq object

        Arguments:
          fastq: name of the fastq.gz (optionally can include leading path)

        """
        try:
            illumina_utils.IlluminaFastq.__init__(self, fastq)
        except IlluminaError as ex:
            raise IlluminaDataError(ex)


class IlluminaDataError(IlluminaError):
    """Base class for errors with Illumina-related code"""


class IlluminaDataPlatformError(IlluminaDataError):
    """Exception for errors due to platform issues"""


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

    Note that this function doesn't return the flow cell ID;
    use the ``split_run_name_full`` function to also extract
    the flow cell information.
    """
    try:
        date_stamp,instrument_name,run_number,flow_cell_prefix,flow_cell = \
            split_run_name_full(dirname)
        return (date_stamp,instrument_name,run_number)
    except IlluminaDataError as ex:
        return (None,None,None)


def split_run_name_full(dirname):
    """Split an Illumina directory run name into components

    Given a directory for an Illumina run, e.g.

    140210_M00879_0031_000000000-A69NA

    split the name into components and return as a tuple:

    (date_stamp,
     instrument_name,
     run_number,
     flow_cell_prefix,
     flow_cell_id)

    e.g.

    ('140210','M00879','0031','','000000000-A69NA')

    Note on flow cell IDs
    =====================

    For run names of the form e.g.

    151216_NB500968_0008_AH5CFGAFXX

    the flow cell component of the name (i.e. 'AH5CFGAFXX')
    is broken down into a prefix part ('A') and an ID part
    ('H5CFGAFXX'). The ID (i.e. without the prefix) is the
    flow cell ID that is used in FASTQ read headers.

    This function assumes that if the flow cell component of
    the name starts with an 'A' or 'B' then this is the prefix;
    otherwise the prefix is a blank. The remainder of the
    component is used as the ID.
    """
    try:
        return illumina_utils.split_run_name(dirname)
    except IlluminaError as ex:
        raise IlluminaDataError(ex)


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
    return illumina.summarise_projects(illumina_data)


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
    return illumina.describe_project(illumina_project)


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
        sample_sheet_fp = io.open(samplesheet,'rt')
    # Load file contents into memory
    sample_sheet_content = ''.join(sample_sheet_fp.readlines())
    # Try to load the sample sheet data assuming Experimental Manager format
    try:
        iem = IEMSampleSheet(fp=io.StringIO(sample_sheet_content))
        return iem.casava_sample_sheet()
    except IlluminaDataError:
        # Not experimental manager format - try CASAVA format
        return CasavaSampleSheet(fp=io.StringIO(sample_sheet_content))


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


def list_missing_fastqs(illumina_data,sample_sheet,
                        include_sample_dir=False):
    """
    Lists missing Fastq files predicted from sample sheet

    Arguments:
      illumina_data: a populated IlluminaData directory
      sample_sheet : path and name of a CSV sample sheet
      include_sample_dir: if True then always include a
        'sample_name' directory level when checking for
        bcl2fastq2 outputs

    Returns:
      List: list of paths of missing Fastq files, relative
        to the unaligned directory. List is empty if there
        are no missing files.

    """
    return illumina.list_missing_fastqs(
        illumina_data,
        sample_sheet,
        include_sample_dir=include_sample_dir)


def verify_run_against_sample_sheet(illumina_data, sample_sheet,
                                    include_sample_dir=False):
    """Checks existence of predicted outputs from a sample sheet

    Arguments:
      illumina_data: a populated IlluminaData directory
      sample_sheet : path and name of a CSV sample sheet
      include_sample_dir: if True then always include a
        'sample_name' directory level when checking for
        bcl2fastq2 outputs

    Returns:
      True if all the predicted outputs from the sample sheet are
        found, False otherwise.

    """
    return illumina.verify_against_sample_sheet(
        illumina_data,
        sample_sheet,
        include_sample_dir=include_sample_dir)


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
    return illumina_utils.get_unique_fastq_names(fastqs)


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
    return illumina_utils.fix_bases_mask(bases_mask, barcode_sequence)


def samplesheet_index_sequence(line):
    """
    Return the index sequence for a sample sheet line

    Arguments:
      line (TabDataLine): line from a SampleSheet instance

    Returns:
      String: barcode sequence, or 'None' if not defined.

    """
    return illumina_samplesheet.samplesheet_index_sequence(line)


def normalise_barcode(seq):
    """
    Return normalised version of barcode sequence

    This standardises the sequence so that:

    - all bases are uppercase
    - dual index barcodes have '-' and '+' removed

    """
    return illumina_utils.normalise_barcode(seq)
