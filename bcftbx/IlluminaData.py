#     IlluminaData.py: module for handling data about Illumina sequencer runs
#     Copyright (C) University of Manchester 2012-2013 Peter Briggs
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
                   defined at the fastq creation stage, expected to be in
                   subdirectories "Project_...")
    undetermined:  IlluminaProject object for the undetermined reads
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
        self.package = None
        # Look for "unaligned" data directory
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
            self.paired_end = (self.paired_end and p.paired_end)

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

    def _populate_bcl2fastq2_style(self):
        """
        Find projects for a bcl2fastq2-style directory structure

        """
        # The output from bcl2fastq2 is flat
        # We expect to find a number of 'undetermined' fastqs at
        # the top level of the output (unaligned) directory,
        # and one or more projects in subdirectories - each of
        # which contains all the fastqs for all samples
        # The strategy is to look for all these things together
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
            fqs = filter(lambda f: f.endswith('.fastq.gz'),
                         os.listdir(dirn))
            if not fqs:
                continue
            # Check that fastqs have bcl2fastq2-style names
            for fq in fqs:
                if IlluminaFastq(fq).sample_number is None:
                    break; continue
            # Looks like a project
            project_dirs.append(dirn)
        # Raise an exception if no projects found
        if not project_dirs:
            raise IlluminaDataError("No bcl2fastq2-style projects found")
        print "Projects = %s" % project_dirs
        # Create project objects
        self.undetermined = IlluminaProject(self.unaligned_dir)
        for dirn in project_dirs:
            self.projects.append(IlluminaProject(dirn))

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
            # Examine fastq files to see if naming scheme follows
            # bcl2fastq v2 convention
            fastqs = filter(lambda f: f.endswith('.fastq.gz'),
                            os.listdir(self.dirn))
            if fastqs and reduce(lambda x,y: x and
                                 (IlluminaFastq(y).sample_number is not None),
                                 fastqs,True):
                # bcl2fastq v2
                self.project_prefix = ""
                if reduce(lambda x,y: x and
                          os.path.basename(y).startswith('Undetermined_S'),
                          fastqs,True):
                    # These are undetermined fastqs
                    self.undetermined = True
                    self.name = "Undetermined_indices"
                else:
                    # Fastqs from an actual set of samples
                    self.name = os.path.basename(self.dirn)
                logging.debug("bcl2fastq 2 project: %s" % self.name)
            else:
                raise IlluminaDataError, "Not a project directory: " % self.dir
            # Determine samples from fastq names
            self.sample_prefix = ""
            sample_names = []
            for fq in fastqs:
                if not self.undetermined:
                    sample_name = IlluminaFastq(fq).sample_name
                else:
                    # Use laneX as sample name for undetermined
                    sample_name = "lane%d" % IlluminaFastq(fq).lane_number
                if sample_name not in sample_names:
                    sample_names.append(sample_name)
            # Create sample objects and populate with appropriate fastqs
            for sample_name in sample_names:
                if not self.undetermined:
                    fqs = filter(lambda f:
                                 IlluminaFastq(f).sample_name == sample_name,
                                 fastqs)
                else:
                    fqs = filter(lambda f:
                                 "lane%d" % IlluminaFastq(f).lane_number
                                 == sample_name,
                                 fastqs)
                self.samples.append(IlluminaSample(self.dirn,
                                                   fastqs=fqs))
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

    def __init__(self,dirn,fastqs=None):
        """Create and populate a new IlluminaSample object

        Arguments:
          dirn:   path to the directory holding the fastq.gz files for
                  the sample
          fastqs: optional, a list of fastq files associated with the
                  sample (expected to be under the directory 'dirn')

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
        # Set sample name from directory name
        self.sample_prefix = "Sample_"
        if os.path.basename(dirn).startswith(self.sample_prefix):
            # Remove prefix
            self.name = os.path.basename(dirn)[len(self.sample_prefix):]
        else:
            # No prefix, obtain name from fastqs
            self.sample_prefix = ""
            self.name = IlluminaFastq(fastqs[0]).sample_name
            # Special case: undetermined 'sample' is 'laneX'
            if self.name == 'Undetermined':
                self.name = "lane%d" % IlluminaFastq(fastqs[0]).lane_number
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

class IEMSampleSheet:
    """Class for handling Experimental Manager format sample sheet
    
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

    Basic usage
    -----------

    To load data from a file:

    >>> iem = IEMSampleSheet('SampleSheet.csv')

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

    Sample sheet reconstruction
    ---------------------------

    Data is loaded it is also subjected to some basic cleaning
    up, including stripping of unnecessary commas and white space.
    The 'show' method returns a reconstructed version of the
    original sample sheet after the cleaning operations were
    performed.
    
    Conversion to CASAVA-style sample sheet
    ---------------------------------------

    The 'casava_sample_sheet' method can be used to convert the
    IEM format to CASAVA-style i.e. suitable for input into
    bcl2fastq in order to generate FASTQ files from raw bcls.

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
        # Input sample sheet
        self.sample_sheet = sample_sheet
        # Store file sections
        self._header = utils.OrderedDictionary()
        self._reads = list()
        self._settings = utils.OrderedDictionary()
        self._data = None
        # Read in file contents
        if fp is None and self.sample_sheet is not None:
            fp = open(self.sample_sheet,'rU')
        if fp is not None:
            self._load_data(fp)

    def _load_data(self,fp):
        """Internal: populate with data from external file

        Arguments
          fp: file-like object opened for reading which contains
             sample sheet data

        """
        section = None
        for i,line in enumerate(fp):
            line = line.rstrip()
            logging.debug(line)
            if not line:
                # Skip blank lines
                continue
            if line.startswith('['):
                # New section
                try:
                    i = line.index(']')
                    section = line[1:i]
                    continue
                except ValueError:
                    logging.error("Bad line (#%d): %s" % (i+1,line))
            if section == 'Header':
                # Header lines are comma-separated PARAM,VALUE lines
                self._set_param_value(line,self._header)
            elif section == 'Reads':
                # Read lines are one value per line
                value = line.rstrip(',')
                if value:
                    self._reads.append(value)
            elif section == 'Settings':
                # Settings lines are comma-separated PARAM,VALUE lines
                self._set_param_value(line,self._settings)
            elif section == 'Data':
                # Store data in TabFile object
                if self._data is None:
                    # Initialise TabFile using this first line
                    # to set the header
                    self._data = TabFile.TabFile(column_names=line.split(','),
                                                 delimiter=',')
                else:
                    self._data.append(tabdata=line)
            elif section is None:
                raise IlluminaDataError("Not a valid IEM sample sheet?")
            else:
                raise IlluminaDataError(
                    "Unrecognised section '%s': not a valid IEM sample sheet?" %
                    section)
        # Clean up data items: remove surrounding whitespace
        if self._data is not None:
            for line in self._data:
                for item in self._data.header():
                    try:
                        line[item] = line[item].strip()
                    except AttributeError:
                        pass

    def _set_param_value(self,line,d):
        """Internal: process a 'key,value' line

        """
        fields = line.split(',')
        param = fields[0]
        value = fields[1]
        if param:
            d[param] = value

    @property
    def header_items(self):
        """Return list of items listed in the '[Header]' section

        Returns:
          List of item names.

        """
        return self._header.keys()

    @property
    def header(self):
        """Return ordered dictionary for the '[Header]' section

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._header

    @property
    def reads(self):
        """Return list of values from the '[Reads'] section
        
        Returns:
          List of values.

        """
        return self._reads

    @property
    def settings_items(self):
        """Return list of items listed in the '[Settings]' section

        Returns:
          List of item names.

        """
        return self._settings.keys()

    @property
    def settings(self):
        """Return ordered dictionary for the '[Settings]' section

        Returns:
          OrderedDictionary where keys are data items.

        """
        return self._settings

    @property
    def data(self):
        """Return TabFile object for the '[Data]' section

        Returns:
          TabFile object.

        """
        return self._data

    def show(self):
        """Reconstructed version of original sample sheet

        Return a string containing a reconstructed version of
        the original sample sheet, after any cleaning operations
        (e.g. removal of unnecessary commas and whitespace) have
        been applied.

        Returns:
          String with the reconstructed sample sheet contents.

        """
        s = []
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
        return '\n'.join(s)

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
            if str(line['SampleID']).strip() == '' \
               or str(line['SampleProject']).strip() == '':
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
                illegal = (str(line['SampleID']).count(c) > 0) \
                          or (str(line['SampleProject']).count(c) > 0)
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
                line['SampleID'] = str(line['SampleID']).strip().replace(c,'_').strip('_')
                line['SampleProject'] = str(line['SampleProject']).strip().replace(c,'_').strip('_')

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
        self.lane_number = int(fields[-3][1:])
        # Either barcode sequence or sample number
        if fields[-4].startswith('S'):
            # Sample number: integer
            self.sample_number = int(fields[-4][1:])
        else:
            # Barcode sequence: string (or None if 'NoIndex')
            self.barcode_sequence = fields[-4]
            if self.barcode_sequence == 'NoIndex':
                self.barcode_sequence = None
        # Sample name: whatever's left over
        self.sample_name = '_'.join(fields[:-4])

    def __repr__(self):
        """Implement __repr__ built-in

        """
        if self.sample_number is not None:
            sample_identifier = "S%d" % self.sample_number
        elif self.barcode_sequence is not None:
            sample_identifier = self.barcode_sequence
        else:
            sample_identifier = "NoIndex"
        return "%s_%s_L%03d_R%d_%03d" % (self.sample_name,
                                         sample_identifier,
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
