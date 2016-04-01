#     IlluminaData.py: module for handling data about Illumina sequencer runs
#     Copyright (C) University of Manchester 2012-2016 Peter Briggs
#
########################################################################
#
# IlluminaData.py
#
#########################################################################

"""
Provides classes for extracting data about runs of Illumina-based sequencers
(e.g. GA2x or HiSeq) from directory structure, data files and naming
conventions.

"""

__version__ = "1.2.2"

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import logging
import xml.dom.minidom
import shutil
import platforms
import utils
import TabFile
import cStringIO

#######################################################################
# Module constants
#######################################################################

SAMPLESHEET_ILLEGAL_CHARS = "?()[]/\=+<>:;\"',*^|&. \t"

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
    lanes             : list of (integer) lane numbers in the run

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
        elif self.platform not in ('illumina-ga2x','hiseq','miseq','nextseq'):
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

        Returns one of 'bcl', 'bcl.gz', 'bcl.bgzf'

        Raises an exception if no matching files are found.

        """
        # Locate the directory for the first cycle in the first lane
        # (HiSeq and MiSeq)
        lane1_cycle1 = os.path.join(self.basecalls_dir,'L001','C1.1')
        if os.path.isdir(lane1_cycle1):
            for f in os.listdir(lane1_cycle1):
                for ext in ('.bcl','.bcl.gz',):
                    if str(f).endswith(ext):
                        return ext
        # Look in the directory for the first lane (NextSeq)
        lane1 = os.path.join(self.basecalls_dir,'L001')
        for f in os.listdir(lane1):
            for ext in ('.bcl.bgzf',):
                if str(f).endswith(ext):
                    return ext
        # Failed to match any known extension, raise exception
        raise Exception("Unable to determine bcl extension")

    @property
    def lanes(self):
        """
        Return list of lane numbers

        Returns a list of integer lane numbers found in the
        run directory

        """
        lanes = []
        for d in os.listdir(self.basecalls_dir):
            if d.startswith('L'):
                lanes.append(int(d[1:]))
        lanes.sort()
        return lanes

class IlluminaRunInfo:
    """Class for examining Illumina RunInfo.xml file

    Extracts basic information from a RunInfo.xml file:

    run_id     : the run id e.g.'130805_PJ600412T_0012_ABCDEZXDYY'
    run_number : the run number e.g. '12'
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
                   defined at the fastq creation stage)
    undetermined:  IlluminaProject object for the undetermined reads
    unaligned_dir: full path to the 'Unaligned' directory holding the
                   primary fastq.gz files
    paired_end:    True if at least one project is paired end, False otherwise
    format:        Format of the directory structure layout (either
                   'casava' or 'bcl2fastq2', or None if the format cannot
                   be determined)
    lanes:         List of lane numbers present; if there are no lanes
                   then this will be a list with 'None' as the only value

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
        self.paired_end = False
        self.format = None
        # Look for "Unaligned" data directory
        self.unaligned_dir = os.path.join(self.analysis_dir,unaligned_dir)
        if not os.path.exists(self.unaligned_dir):
            raise IlluminaDataError("Missing data directory %s" %
                                    self.unaligned_dir)
        # Raise an exception if no projects found
        try:
            self._populate_casava_style()
        except IlluminaDataError:
            self._populate_bcl2fastq2_style()
        if not self.projects:
            raise IlluminaDataError("No projects found")
        # Sort projects on name
        self.projects.sort(lambda a,b: cmp(a.name,b.name))
        # Determine whether data is paired end
        for p in self.projects:
            self.paired_end = (self.paired_end or p.paired_end)
        # Get list of lanes
        self.lanes = []
        for p in self.projects:
            for s in p.samples:
                for fq in s.fastq:
                    lane = IlluminaFastq(fq).lane_number
                    if lane not in self.lanes:
                        self.lanes.append(lane)
        self.lanes.sort()

    def _populate_casava_style(self):
        """
        Find projects for a CASAVA-style directory structure

        """
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
        if not self.projects :
            raise IlluminaDataError("No CASAVA-style projects found")
        else:
            self.format = 'casava'

    def _populate_bcl2fastq2_style(self):
        """
        Find projects for a bcl2fastq2-style directory structure

        The output from bcl2fastq2 can be "flat" (i.e. fastqs
        directly under project dirs) or it can contain "sample"
        subdirs within project dirs, or a mixture of both.

        In all cases we expect to find a number of 'undetermined'
        fastqs at the top level of the output (unaligned) directory,
        and the fastq names will contain the 'S1' sample number
        construct.

        """
        # Look for undetermined fastqs
        undetermined_fqs = filter(lambda f: f.startswith('Undetermined_S0_')
                                  and f.endswith('.fastq.gz'),
                                  os.listdir(self.unaligned_dir))
        if not undetermined_fqs:
            raise IlluminaDataError("No bcl2fastq2 undetermined fastqs found")
        # Look for potential projects
        project_dirs = []
        for d in os.listdir(self.unaligned_dir):
            dirn = os.path.join(self.unaligned_dir,d)
            if not os.path.isdir(dirn):
                continue
            # Get a list of fastq files
            fqs = filter(lambda f: f.endswith('.fastq.gz') and
                         IlluminaFastq(f).sample_number is not None,
                         os.listdir(dirn))
            if fqs:
                # Looks like a project
                project_dirs.append(dirn)
            else:
                # Look in subdirs
                subdirs = filter(lambda d:
                                 os.path.isdir(os.path.join(dirn,d)),
                                 os.listdir(dirn))
                if subdirs:
                    for sd in subdirs:
                        fqs = filter(lambda f: f.endswith('.fastq.gz') and
                                     IlluminaFastq(f).sample_number is not None,
                                     os.listdir(os.path.join(dirn,sd)))
                        if fqs:
                            # Looks like a project
                            project_dirs.append(dirn)
                            break; continue
        # Raise an exception if no projects found
        if not project_dirs:
            raise IlluminaDataError("No bcl2fastq2-style projects found")
        # Create project objects
        self.undetermined = IlluminaProject(self.unaligned_dir)
        for dirn in project_dirs:
            self.projects.append(IlluminaProject(dirn))
        self.format = 'bcl2fastq2'

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

    A project is a subset of fastq files from a run of an Illumina
    sequencer; in the first instance projects are defined within the
    SampleSheet.csv file which is output by the sequencer.

    Note that the "undetermined" fastqs (which hold reads for each lane
    which couldn't be assigned to a barcode during demultiplexing) is also
    considered as a project, and can be processed using an IlluminaProject
    object.

    Provides the following attributes:

    name:      name of the project
    dirn:      (full) path of the directory for the project
    expt_type: the application type for the project e.g. RNA-seq, ChIP-seq
               Initially set to None; should be explicitly set by the
               calling subprogram
    samples:   list of IlluminaSample objects for each sample within the
               project
    paired_end: True if all samples are paired end, False otherwise
    undetermined: True if 'samples' are actually undetermined reads

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
        self.undetermined = False
        # Test if this looks like a CASAVA/bcl2fastq v1.8 output
        self.project_prefix = "Project_"
        dirname = os.path.basename(self.dirn)
        if dirname.startswith(self.project_prefix) or \
           dirname == "Undetermined_indices":
            # CASAVA/bcl2fastq v1.8
            if dirname == "Undetermined_indices":
                # "Undetermined_indices" from CASAVA/bcl2fastq v1.8
                self.project_prefix = ""
                self.undetermined = True
                self.name = dirname
            else:
                # Standard project, strip prefix
                self.name = dirname[len(self.project_prefix):]
            logging.debug("CASAVA/bcl2fastq 1.8 project: %s" % self.name)
            # Look for samples
            self.sample_prefix = "Sample_"
            for f in os.listdir(self.dirn):
                sample_dirn = os.path.join(self.dirn,f)
                if f.startswith(self.sample_prefix) and \
                   os.path.isdir(sample_dirn):
                    self.samples.append(IlluminaSample(sample_dirn))
        else:
            # Examine fastq files in top-level dir to see if naming scheme
            # follows bcl2fastq v2 convention
            fastqs = filter(lambda f: f.endswith('.fastq.gz') and
                            IlluminaFastq(f).sample_number is not None,
                            os.listdir(self.dirn))
            if fastqs:
                # Check if this is the top level bcl2fastq v2 output
                # i.e. does it contain undetermined reads
                if reduce(lambda x,y: x and
                          os.path.basename(y).startswith('Undetermined_S'),
                          fastqs,True):
                    # These are undetermined fastqs
                    self.undetermined = True
            if not self.undetermined:
                # Even if we already have fastqs, we need to check
                # subdirs for more bcl2fastq v2 style fastqs
                subdirs = filter(lambda d:
                                 os.path.isdir(os.path.join(self.dirn,d)),
                                 os.listdir(self.dirn))
                for subdir in subdirs:
                    items = [os.path.join(subdir,x)
                             for x in
                             os.listdir(os.path.join(self.dirn,subdir))]
                    fastqs.extend(filter(lambda f: f.endswith('.fastq.gz') and
                                         IlluminaFastq(f).sample_number is not None,
                                         items))
            if not fastqs:
                raise IlluminaDataError("Not a project directory: %s " %
                                        self.dirn)
            # bcl2fastq v2 doesn't prefix project or sample dir names
            self.project_prefix = ""
            self.sample_prefix = ""
            # Determine project name
            if not self.undetermined:
                self.name = os.path.basename(self.dirn)
            else:
                self.name = "Undetermined_indices"
            logging.debug("bcl2fastq 2 project: %s" % self.name)
            # Determine samples from fastq paths/names
            sample_names = []
            for fq in fastqs:
                if not self.undetermined:
                    try:
                        sample_name,_ = fq.split(os.sep)
                    except ValueError:
                        sample_name = IlluminaFastq(fq).sample_name
                else:
                    # Use laneX as sample name for undetermined
                    try:
                        sample_name = "lane%d" % IlluminaFastq(fq).lane_number
                    except TypeError:
                        # No lane, use undetermined as sample name
                        sample_name = "undetermined"
                if sample_name not in sample_names:
                    sample_names.append(sample_name)
            # Create sample objects and populate with appropriate fastqs
            for sample_name in sample_names:
                sample_dirn = self.dirn
                if not self.undetermined:
                    # Assume no subdir
                    fqs = filter(lambda f: IlluminaFastq(f).sample_name
                                 == sample_name,
                                 fastqs)
                    if not fqs:
                        # Look for fastqs within a subdir
                        sample_dirn = os.path.join(self.dirn,sample_name)
                        fqs = filter(lambda f:
                                     f.startswith('%s/' % sample_name),
                                     fastqs)
                else:
                    # Handle 'undetermined' data
                    try:
                        fqs = filter(lambda f:
                                     "lane%d" % IlluminaFastq(f).lane_number
                                     == sample_name,
                                     fastqs)
                    except TypeError:
                        # No lane, take all fastqs
                        fqs = [fq for fq in fastqs]
                self.samples.append(IlluminaSample(sample_dirn,
                                                   fastqs=fqs,
                                                   name=sample_name,
                                                   prefix=''))
        # Raise an exception if no samples found
        if not self.samples:
            raise IlluminaDataError, "No samples found for project %s" % \
                self.name
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
        return utils.pretty_print_names(self.samples)

class IlluminaSample:
    """Class for storing information on a 'sample' within an Illumina project

    A sample is a fastq file generated within an Illumina sequencer run.

    Provides the following attributes:

    name:  sample name
    dirn:  (full) path of the directory for the sample
    fastq: name of the fastq.gz file (without leading directory, join to
           'dirn' to get full path)
    paired_end: boolean; indicates whether sample is paired end

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
        self.dirn = dirn
        self.fastq = []
        self.paired_end = False
        # Deal with fastq files
        if fastqs is None:
            fastqs = filter(lambda f: f.endswith(".fastq.gz"),
                            os.listdir(self.dirn))
        else:
            fastqs = [os.path.basename(f) for f in fastqs]
        self.sample_prefix = prefix
        # Set sample name
        if name is not None:
            # Supplied explicitly
            self.name = name
        elif self.sample_prefix and \
           os.path.basename(dirn).startswith(self.sample_prefix):
            # Determine from prefixed directory name
            self.name = os.path.basename(dirn)[len(self.sample_prefix):]
        else:
            # No prefix, obtain name from fastqs
            self.sample_prefix = ""
            self.name = IlluminaFastq(fastqs[0]).sample_name
            # Special case: undetermined 'sample' is 'laneX'
            if self.name == 'Undetermined':
                try:
                    self.name = "lane%d" % IlluminaFastq(fastqs[0]).lane_number
                except TypeError:
                    # No lane number
                    self.name = "undetermined"
        logging.debug("\tSample: %s" % self.name)
        # Add fastq files
        for f in fastqs:
            self.add_fastq(f)
            logging.debug("\tFastq : %s" % f)
        if not self.fastq:
            logging.debug("\tUnable to find fastq.gz files for %s" %
                          self.name)

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

class SampleSheet:
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

    FCID: flow cell ID
    Lane: lane number (integer from 1 to 8)
    SampleID: ID (name) for the sample
    SampleRef: reference used for alignment for the sample
    Index: index sequences (multiple index reads are separated by a
      hyphen e.g. ACCAGTAA-GGACATGA
    Description: Description of the sample
    Control: Y indicates this lane is a control lane, N means sample
    Recipe: Recipe used during sequencing
    Operator: Name or ID of the operator
    SampleProject: project the sample belongs to

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
    def __init__(self,sample_sheet=None,fp=None):
        """
        """
        # Input sample sheet
        self.sample_sheet = sample_sheet
        # Format-specific settings
        self._format = None
        self._sample_id = None
        self._sample_name = None
        self._sample_project = None
        # Sections for IEM-format sample sheets
        self._header = utils.OrderedDictionary()
        self._reads = list()
        self._settings = utils.OrderedDictionary()
        # Store raw data
        self._data = None
        # Read in file contents
        if fp is None:
            if self.sample_sheet is not None:
                with open(self.sample_sheet,'rU') as fp:
                    self._read_sample_sheet(fp)
        else:
            self._read_sample_sheet(fp)

    def __getitem__(self,key):
        """
        Implement __getitem__ built-in: read 'data' directly

        """
        return self._data[key]

    def __setitem__(self,key,value):
        """
        Implement __setitem__ built-in: write 'data' directly

        """
        self._data[key] = value

    def __delitem__(self,key):
        """
        Implement __delitem__ built-in: delete from 'data' directly

        """
        del(self._data[key])

    def __iter__(self):
        """
        """
        return iter(self._data)

    def __len__(self):
        """
        Implement len() built-in: returns number of lines of data

        """
        if self._data is not None:
            return len(self._data)
        else:
            return 0

    def append(self,*args):
        """
        Create and return a new line of data in the sample sheet

        """
        return self._data.append(*args)

    def _read_sample_sheet(self,fp):
        """
        Internal: consumes and stores sample sheet data

        Arguments:
          fp (File): File-like object for the sample sheet
            that has been opened for reading

        """
        # Assume that initial section is 'Data'
        section = 'Data'
        for i,line in enumerate(fp):
            line = line.rstrip()
            logging.debug(line)
            if not line:
                # Skip blank lines
                continue
            if line.startswith('['):
                # New section
                try:
                    ii = line.index(']')
                    section = line[1:ii]
                    if i == 0:
                        self._format = 'IEM'
                    continue
                except ValueError:
                    raise IlluminaDataError("Bad section line (#%d): %s" %
                                            (i+1,line))
            if section == 'Data':
                # Store data in TabFile object
                if self._data is None:
                    # Initialise TabFile using this first line
                    # to set the header
                    self._data = TabFile.TabFile(column_names=line.split(','),
                                                 delimiter=',')
                    # If this is the first line then assume CASAVA
                    if i == 0:
                        self._format = 'CASAVA'
                else:
                    self._data.append(tabdata=line)
            elif section == 'Header':
                # Header lines are comma-separated PARAM,VALUE lines
                self._set_section_param_value(line,self._header)
            elif section == 'Reads':
                # Read lines are one value per line
                value = line.rstrip(',')
                if value:
                    self._reads.append(value)
            elif section == 'Settings':
                # Settings lines are comma-separated PARAM,VALUE lines
                self._set_section_param_value(line,self._settings)
            elif section is None:
                raise IlluminaDataError("Not a valid sample sheet?")
            else:
                raise IlluminaDataError(
                    "Unrecognised section '%s': not a valid IEM sample sheet?" %
                    section)
        # Clean up data
        if self._data is not None:
            # Remove surrounding whitespace and double quotes from values
            for line in self._data:
                for item in self._data.header():
                    try:
                        line[item] = str(line[item]).strip('"').strip()
                    except AttributeError:
                        pass
            # Remove lines that appear to be commented (after quote removal)
            for i,line in enumerate(self._data):
                if str(line).startswith('#'):
                    del(self._data[i])
        # Guess the format if not already set
        if self._format is None:
            if not self._header and \
               not self._reads and \
               not self._settings:
                format_ = 'CASAVA'
            else:
                format_ = 'IEM'
        # Set the column names
        column_names = self.column_names
        if 'SampleID' in column_names:
            self._sample_id = 'SampleID'
        elif 'Sample_ID' in column_names:
            self._sample_id = 'Sample_ID'
        else:
            raise IlluminaDataError("Unable to locate sample id "
                                    "field in sample sheet header")
        if 'SampleProject' in column_names:
            self._sample_project = 'SampleProject'
        elif 'Sample_Project' in column_names:
            self._sample_project = 'Sample_Project'
        else:
            raise IlluminaDataError("Unable to locate sample project "
                                    "field in sample sheet header")
        if 'Sample_Name' in column_names:
            self._sample_name = 'Sample_Name'

    def _set_section_param_value(self,line,d):
        """
        Internal: process a 'key,value' line

        """
        fields = line.split(',')
        param = fields[0]
        value = fields[1]
        if param:
            d[param] = value

    @property
    def format(self):
        """
        Return format for sample sheet

        Returns:
          String: 'CASAVA', 'IEM' or None.

        """
        return self._format

    @property
    def has_lanes(self):
        """
        Indicates whether 'Lane' column is defined

        Returns:
          Boolean: True if 'Lane' is present, False if not.

        """
        return ('Lane' in self.column_names)

    @property
    def sample_id_column(self):
        """
        Return name of column with sample ID

        Returns:
          String: column label e.g. 'SampleID'.

        """
        return self._sample_id

    @property
    def sample_project_column(self):
        """
        Return name of column with sample project name

        Returns:
          String: column label e.g. 'SampleProject'.

        """
        return self._sample_project

    @property
    def header_items(self):
        """
        Return list of items listed in the '[Header]' section

        If the sample sheet didn't contain a '[Header]' section
        then returns an empty list.

        Returns:
          List of item names.

        """
        return self._header.keys()

    @property
    def header(self):
        """Return ordered dictionary for the '[Header]' section

        If the sample sheet didn't contain a '[Header]' section
        then returns an empty OrderedDictionary.

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._header

    @property
    def reads(self):
        """
        Return list of values from the '[Reads'] section

        If the sample sheet didn't contain a '[Reads]' section
        then returns an empty list.
        
        Returns:
          List of values.

        """
        return self._reads

    @property
    def settings_items(self):
        """
        Return list of items listed in the '[Settings]' section

        If the sample sheet didn't contain a '[Settings]' section
        then returns an empty list.

        Returns:
          List of item names.

        """
        return self._settings.keys()

    @property
    def settings(self):
        """
        Return ordered dictionary for the '[Settings]' section

        If the sample sheet didn't contain a '[Settings]' section
        then returns an empty OrderedDictionary.

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._settings

    @property
    def data(self):
        """
        Return TabFile object for the sample information

        This returns the per-sample data from '[Data]' section (if
        the original sample sheet was in IEM format), or the
        entire file (if it was in CASAVA format).

        Returns:
          TabFile object.

        """
        return self._data

    @property
    def column_names(self):
        """
        Return list of column names for the data section

        Returns:
           List.

        """
        return [x for x in self._data.header()]

    @property
    def duplicated_names(self):
        """
        List duplicate samples within a project

        Returns a list where each item is another list with a group
        of lines from the sample sheet which together consitute a set
        of duplicates.

        """
        samples = {}
        for line in self._data:
            try:
                index = line['Index']
            except KeyError:
                try:
                    index = "%s-%s" % (line['index'],line['index2'])
                except KeyError:
                    index = line['index']
            try:
                lane = line['Lane']
            except KeyError:
                lane = None
            name = ((line[self._sample_id],
                     line[self._sample_project],
                     index,lane))
            if name not in samples:
                samples[name] = [line]
            else:
                samples[name].append(line)
        duplicates = filter(lambda s: len(s) > 1,
                            [samples[name] for name in samples])
        return duplicates

    @property
    def illegal_names(self):
        """
        List lines with illegal characters in sample names or projects

        Returns a list of lines where the sample names and/or sample project
        names contain illegal characters.

        """
        illegal_names = []
        for line in self._data:
            for c in SAMPLESHEET_ILLEGAL_CHARS:
                illegal = (str(line[self._sample_id]).count(c) > 0) \
                          or (str(line[self._sample_project]).count(c) > 0)
                if not illegal and self._sample_name is not None:
                    illegal = str(line[self._sample_name]).count(c) > 0
                if illegal:
                    illegal_names.append(line)
                    break
        return illegal_names

    @property
    def empty_names(self):
        """List lines with blank sample or project names

        Returns a list of lines with blank sample or project names.

        """
        empty_names = []
        for line in self._data:
            if str(line[self._sample_id]).strip() == '' \
               or str(line[self._sample_project]).strip() == '':
                empty_names.append(line)
        return empty_names

    def fix_duplicated_names(self):
        """
        Rename samples to remove duplicated sample names within a project

        Appends a numeric index to sample names in the duplicated lines
        in order to remove the duplication.

        """
        for duplicate in self.duplicated_names:
            for i in range(0,len(duplicate)):
                duplicate[i][self._sample_id] = "%s_%d" % \
                                                (duplicate[i][self._sample_id],
                                                 i+1)

    def fix_illegal_names(self):
        """
        Replace illegal characters in sample and project name pairs

        Replaces any illegal characters with underscores.

        """
        for line in self.illegal_names:
            for c in SAMPLESHEET_ILLEGAL_CHARS:
                line[self._sample_id] = \
                    str(line[self._sample_id]).strip().replace(c,'_').strip('_')
                line[self._sample_project] = \
                    str(line[self._sample_project]).strip().replace(c,'_').strip('_')
                if self._sample_name is not None:
                    line[self._sample_name] = \
                        str(line[self._sample_name]).strip().replace(c,'_').strip('_')

    def show(self,fmt=None):
        """
        Reconstructed version of original sample sheet

        Return a string containing a reconstructed version of
        the original sample sheet, after any cleaning operations
        (e.g. removal of unnecessary commas and whitespace) have
        been applied.

        The format of the output will be the same as that of the
        input, unless explicitly reset using the 'fmt' option.

        Arguments:
           fmt (str): optional, explicitly set the format for
             the output. Can be either 'CASAVA' or 'IEM'.

        Returns:
          String with the reconstructed sample sheet contents.

        """
        # Set output format
        if fmt is None:
            format_ = self._format
        else:
            format_ = str(fmt)
        # Reconstruct the sample sheet
        s = []
        if format_ == 'IEM':
            s.append('[Header]')
            for param in self._header:
                s.append('%s,%s' % (param,self._header[param]))
            s.append('')
            s.append('[Reads]')
            for value in self._reads:
                s.append(value)
            s.append('')
            s.append('[Settings]')
            for param in self._settings:
                s.append('%s,%s' % (param,self._settings[param]))
            s.append('')
            s.append('[Data]')
            s.append(','.join(self._data.header()))
            for line in self._data:
                s.append(str(line))
        else:
            header = ('FCID','Lane','SampleID','SampleRef','Index',
                      'Description','Control','Recipe','Operator',
                      'SampleProject')
            s.append(','.join(header))
            for line in self._data:
                values = []
                for item in header:
                    try:
                        values.append(str(line[item]))
                    except KeyError:
                        if item == 'FCID':
                            values.append('FC0001')
                        elif item == 'Lane':
                            values.append('1')
                        elif item == 'SampleID':
                            values.append(line['Sample_ID'])
                        elif item == 'Index':
                            try:
                                values.append("%s-%s" %
                                              (line['index'].strip(),
                                               line['index2'].strip()))
                            except KeyError:
                                # Assume not dual-indexed (no index2)
                                try:
                                    values.append(line['index'].strip())
                                except KeyError:
                                    # No index
                                    values.append('')
                        elif item == 'SampleProject':
                            values.append(line['Sample_Project'])
                        else:
                            values.append('')
                s.append(','.join([str(x) for x in values]))
        return '\n'.join(s)

    def write(self,filen=None,fp=None,fmt=None):
        """
        Output the sample sheet data to file or stream

        The format of the output will be the same as that of the
        input, unless explicitly reset using the 'fmt' option.

        Arguments:
          filen: (optional) name of file to write to; ignored if fp is
            also specified
          fp: (optional) a file-like object opened for writing; used in
            preference to filen if set to a non-null value
            Note that the calling program must close the stream in
            these cases.
          fmt (str): optional, explicitly set the format for
            the output. Can be either 'CASAVA' or 'IEM'.

        """
        if fp is None:
            if filen is None:
                fp = sys.stdout
            else:
                fp = open(filen,'w')
        fp.write("%s\n" % self.show(fmt=fmt))
        if filen is not None:
            fp.close()

    def predict_output(self,fmt='CASAVA'):
        """
        Predict the expected outputs from the sample sheet content

        Constructs and returns a simple dictionary-based data structure
        which predicts the output data structure that will produced by
        running the bcl2fastq conversion software using the sample sheet
        data.

        The return structure depends on the format specified via the
        ``fmt`` argument, either:

        - 'CASAVA': reproduce the structure when running either
          CASAVA or the bcl2fastq v1.8.* software, or
        - 'bcl2fastq2': reproduce the structure from bcl2fastq v2.

        For 'CASAVA' formatted output the returned structure is:

        { 'project_1': {
                         'sample_1': [ name1, name2, ... ],
                         'sample_2': [ ... ],
                         ... }
          'project_2': {
                         'sample_3': [ ... ],
                         ... }
          ... }

        For 'bcl2fastq2' formatted output it is:

        { 'project_1': [ name1, name2, ...],
          'project_2': [ name1, name2, ...],
          ... }

        or:

        { 'project_1': [ dir/name1, dir/name2, ...],
          'project_2': [ name1, name2, ...],
          ... }

        if some samples will be written will be written to
        subdirectories according to the sample sheet.

        """
        projects = {}
        if str(fmt).upper() == 'CASAVA':
            # CASAVA/bcl2fastq v1.8.*-style output
            for line in self.data:
                # Sample and project names
                project = "Project_%s" % line[self._sample_project]
                sample = "Sample_%s" % line[self._sample_id]
                if project not in projects:
                    samples = {}
                else:
                    samples = projects[project]
                if sample not in samples:
                    samples[sample] = []
                # Index sequence
                try:
                    # Try dual-indexed IEM4 format
                    indx = "%s-%s" %(line['index'].strip(),
                                     line['index2'].strip())
                except KeyError:
                    # Try single indexed IEM4 (no index2)
                    try:
                        indx = line['index'].strip()
                    except KeyError:
                        # Try CASAVA format
                        indx = line['Index'].strip()
                if not indx:
                    indx = "NoIndex"
                # Lane
                try:
                    lane = line['Lane']
                except KeyError:
                    lane = 1
                # Construct base name
                samples[sample].append("%s_%s_L%03d" % (line[self._sample_id],
                                                        indx,lane))
                projects[project] = samples
        elif fmt == 'bcl2fastq2':
            # bcl2fastq v2-style output
            sample_names = []
            for line in self.data:
                project = line[self._sample_project]
                if self._sample_name:
                    name = line[self._sample_name]
                else:
                    name = None
                id_ = line[self._sample_id]
                prefix = ''
                if name:
                    sample = name
                    if id_ != name:
                        prefix = '%s/' % id_
                else:
                    sample = id_
                if self.has_lanes:
                    lane_id = "_L%03d" % line['Lane']
                else:
                    lane_id = ""
                if project not in projects:
                    fqs = []
                else:
                    fqs = projects[project]
                try:
                    i = sample_names.index(sample) + 1
                except ValueError:
                    sample_names.append(sample)
                    i = len(sample_names)
                # Construct fastq basename
                fqs.append("%s%s_S%d%s" % (prefix,sample,i,lane_id))
                projects[project] = fqs
        else:
            # Unknown format
            raise IlluminaDataError("Unknown format: '%s'" % fmt)
        return projects

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
        SampleSheet.__init__(self,sample_sheet,fp)
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

class IlluminaFastq:
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
        # Store name
        self.fastq = fastq
        # Values derived from the name
        self.sample_name = None
        self.sample_number = None
        self.barcode_sequence = None
        self.lane_number = None
        self.read_number = None
        self.set_number = None
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
        if fields[-3].startswith('L') and fields[-3][1:].isdigit():
            self.lane_number = int(fields[-3][1:])
            fields = fields[:-3]
        else:
            fields = fields[:-2]
        # Either barcode sequence or sample number
        if fields[-1].startswith('S'):
            # Sample number: integer
            self.sample_number = int(fields[-1][1:])
        else:
            # Barcode sequence: string (or None if 'NoIndex')
            self.barcode_sequence = fields[-1]
            if self.barcode_sequence == 'NoIndex':
                self.barcode_sequence = None
        # Sample name: whatever's left over
        self.sample_name = '_'.join(fields[:-1])

    def __repr__(self):
        """Implement __repr__ built-in

        """
        if self.sample_number is not None:
            sample_identifier = "S%d" % self.sample_number
        elif self.barcode_sequence is not None:
            sample_identifier = self.barcode_sequence
        else:
            sample_identifier = "NoIndex"
        if self.lane_number is not None:
            lane_identifier = "L%03d_" % self.lane_number
        else:
            lane_identifier = ""
        return "%s_%s_%sR%d_%03d" % (self.sample_name,
                                         sample_identifier,
                                         lane_identifier,
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
    # Load file contents into memory
    sample_sheet_content = ''.join(sample_sheet_fp.readlines())
    # Try to load the sample sheet data assuming Experimental Manager format
    try:
        iem = IEMSampleSheet(fp=cStringIO.StringIO(sample_sheet_content))
        return iem.casava_sample_sheet()
    except IlluminaDataError:
        # Not experimental manager format - try CASAVA format
        return CasavaSampleSheet(fp=cStringIO.StringIO(sample_sheet_content))

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
    # Get predicted outputs based on directory structure format
    data_format = illumina_data.format
    sample_sheet = SampleSheet(sample_sheet)
    if data_format == 'casava':
        predicted_projects = sample_sheet.predict_output(fmt='CASAVA')
    elif data_format == 'bcl2fastq2':
        predicted_projects = sample_sheet.predict_output(fmt='bcl2fastq2')
    else:
        raise IlluminaDataError("Unknown format for directory structure: %s" %
                                data_format)
    # Loop through projects and check that predicted outputs exist
    verified = True
    for proj in predicted_projects:
        # Locate project directory
        proj_dir = os.path.join(illumina_data.unaligned_dir,proj)
        if os.path.isdir(proj_dir):
            if data_format == 'casava':
                predicted_samples = predicted_projects[proj]
                for smpl in predicted_samples:
                    # Locate sample directory
                    smpl_dir = os.path.join(proj_dir,smpl)
                    if os.path.isdir(smpl_dir):
                        # Check for output files
                        predicted_names = predicted_samples[smpl]
                        for name in predicted_names:
                            # Look for R1 file
                            f = os.path.join(smpl_dir,
                                             "%s_R1_001.fastq.gz" % name)
                            if not os.path.exists(f):
                                logging.warning("Verify: missing R1 file '%s'"
                                                % f)
                                verified = False
                            # Look for R2 file (paired end only)
                            if illumina_data.paired_end:
                                f = os.path.join(smpl_dir,
                                                 "%s_R2_001.fastq.gz" % name)
                                if not os.path.exists(f):
                                    logging.warning("Verify: missing R2 file '%s'"
                                                    % f)
                                    verified = False
                    else:
                        # Sample directory not found
                        logging.warning("Verify: missing %s" % smpl_dir)
                        verified = False
            elif data_format == 'bcl2fastq2':
                # Check for output files
                predicted_names = predicted_projects[proj]
                for name in predicted_names:
                    # Loop over lanes
                    for lane in illumina_data.lanes:
                        # Lane identifier
                        if not sample_sheet.has_lanes and \
                           lane is not None:
                            lane_id = "_L%03d" % lane
                        else:
                            lane_id = ""
                        # Look for R1 file
                        f = os.path.join(proj_dir,
                                         "%s%s_R1_001.fastq.gz" % (name,
                                                                   lane_id))
                        if not os.path.exists(f):
                            logging.warning("Verify: missing R1 file '%s'"
                                            % f)
                            verified = False
                        # Look for R2 file (paired end only)
                        logging.debug("Paired_end = %s" % illumina_data.paired_end)
                        if illumina_data.paired_end:
                            f = os.path.join(proj_dir,
                                             "%s%s_R2_001.fastq.gz" % (name,
                                                                       lane_id))
                            if not os.path.exists(f):
                                logging.warning("Verify: missing R2 file '%s'"
                                                % f)
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
