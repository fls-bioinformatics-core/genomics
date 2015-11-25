#######################################################################
# Tests for IlluminaData.py module
#######################################################################
from bcftbx.IlluminaData import *
import bcftbx.utils
import unittest
import cStringIO
import tempfile
import shutil

class MockIlluminaRun:
    """
    Utility class for creating mock Illumina sequencer output dirctories

    Example usage:

    >>> mockrun = MockIlluminaData('151125_AB12345_001_CD256X','miseq')
    >>> mockrun.create()

    To delete the physical directory structure when finished:

    >>> mockrun.remove()

    """
    def __init__(self,name,platform,top_dir=None):
        """
        Create a new MockIlluminaRun instance

        Arguments:
          name (str): name for the run (used as top-level dir)
          platform (str): sequencing platform e.g. 'miseq', 'hiseq'
            'nextseq'
          top_dir (str): optionally specify a parent directory for
            the mock run (default is the current working directory)

        """
        self._created = False
        self._name = name
        if top_dir is not None:
            self._top_dir = os.path.abspath(top_dir)
        else:
            self._top_dir = os.getcwd()
        if platform not in ('miseq','hiseq','nextseq'):
            raise Exception("Unrecognised platform: %s" % platform)
        self._platform = platform

    @property
    def name(self):
        """
        Name of the mock run

        """
        return self._name

    @property
    def dirn(self):
        """
        Full path to the mock run directory

        """
        return os.path.join(self._top_dir,self._name)

    def _path(self,*dirs):
        """
        Return path under run directory

        """
        dirs0 = [self.dirn]
        dirs0.extend(dirs)
        return os.path.join(*dirs0)

    def _create_miseq(self):
        """Internal: creates mock MISeq run directory structure

        """
        # Constants for MISeq
        nlanes = 1
        ntiles = 12 #158
        ncycles = 218
        bcl_ext = '.bcl'
        # Basic directory structure
        bcftbx.utils.mkdir(self._path('Data'))
        bcftbx.utils.mkdir(self._path('Data','Intensities'))
        bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls'))
        # Lanes
        for i in xrange(1,nlanes+1):
            # .locs files
            bcftbx.utils.mkdir(self._path('Data','Intensities','L%03d' % i))
            for j in xrange(1101,1101+ntiles):
                open(self._path('Data','Intensities','L%03d' % i,
                                's_%d_%d.locs' % (i,j)),'wb+').close()
            # BaseCalls
            bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls',
                                          'L%03d' % i))
            for j in xrange(1101,1101+ntiles):
                open(self._path('Data','Intensities','BaseCalls',
                                'L%03d' % i,
                                's_%d_%d.control' % (i,j)),'wb+').close()
                open(self._path('Data','Intensities','BaseCalls',
                                'L%03d' % i,
                                's_%d_%d.filter' % (i,j)),'wb+').close()
            for k in xrange(1,ncycles+1):
                bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls',
                                              'L%03d' % i,'C%d.1' % k))
                for j in xrange(1101,1101+ntiles):
                    open(self._path('Data','Intensities','BaseCalls',
                                    'L%03d' % i,'C%d.1' % k,
                                    's_%d_%d.%s' % (i,j,bcl_ext)),'wb+').close()
                    open(self._path('Data','Intensities','BaseCalls',
                                    'L%03d' % i,'C%d.1' % k,
                                    's_%d_%d.stats' % (i,j)),'wb+').close()
        # RunInfo.xml
        run_info_xml = """<?xml version="1.0"?>
<RunInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="2">
  <Run Id="%s" Number="1">
    <Flowcell>00000000-ABCD1</Flowcell>
    <Instrument>M00001</Instrument>
    <Date>150729</Date>
    <Reads>
      <Read Number="1" NumCycles="101" IsIndexedRead="N" />
      <Read Number="2" NumCycles="8" IsIndexedRead="Y" />
      <Read Number="3" NumCycles="8" IsIndexedRead="Y" />
      <Read Number="4" NumCycles="101" IsIndexedRead="N" />
    </Reads>
    <FlowcellLayout LaneCount="1" SurfaceCount="2" SwathCount="1" TileCount="19" />
  </Run>
</RunInfo>
"""
        with open(self._path('RunInfo.xml'),'w') as fp:
            fp.write(run_info_xml % self.name)
        # SampleSheet.csv
        sample_sheet_csv = """[Header],,,,,,,,,
IEMFileVersion,4,,,,,,,,
Date,11/23/2015,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,
Application,FASTQ Only,,,,,,,,
Assay,TruSeq HT,,,,,,,,
Description,,,,,,,,,
Chemistry,Amplicon,,,,,,,,
,,,,,,,,,
[Reads],,,,,,,,,
101,,,,,,,,,
101,,,,,,,,,
,,,,,,,,,
[Settings],,,,,,,,,
ReverseComplement,0,,,,,,,,
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,,,,,,,,
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT,,,,,,,,
,,,,,,,,,
[Data],,,,,,,,,
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample_1,Sample_1,,,D701,CGTGTAGG,D501,GACCTGTA,,
Sample_2,Sample_2,,,D702,CGTGTAGG,D501,ATGTAACT,,
"""
        with open(self._path('Data','Intensities','BaseCalls',
                             'SampleSheet.csv'),'w') as fp:
            fp.write(sample_sheet_csv)
        # (Empty) config.xml files
        open(self._path('Data','Intensities','config.xml'),'wb+').close()
        open(self._path('Data','Intensities','BaseCalls','config.xml'),
             'wb+').close()

    def _create_hiseq(self):
        """
        Internal: creates mock HISeq run directory structure

        """
        # Constants for HISeq
        nlanes = 8
        ntiles = 12 #1216
        ncycles = 218
        bcl_ext = '.bcl.gz'
        # Basic directory structure
        bcftbx.utils.mkdir(self._path('Data'))
        bcftbx.utils.mkdir(self._path('Data','Intensities'))
        bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls'))
        # Lanes
        for i in xrange(1,nlanes+1):
            # .clocs files
            bcftbx.utils.mkdir(self._path('Data','Intensities','L%03d' % i))
            for j in xrange(1101,1101+ntiles):
                open(self._path('Data','Intensities','L%03d' % i,
                                's_%d_%d.clocs' % (i,j)),'wb+').close()
            # BaseCalls
            bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls',
                                          'L%03d' % i))
            for j in xrange(1101,1101+ntiles):
                open(self._path('Data','Intensities','BaseCalls',
                                'L%03d' % i,
                                's_%d_%d.control' % (i,j)),'wb+').close()
                open(self._path('Data','Intensities','BaseCalls',
                                'L%03d' % i,
                                's_%d_%d.filter' % (i,j)),'wb+').close()
            for k in xrange(1,ncycles+1):
                bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls',
                                              'L%03d' % i,'C%d.1' % k))
                for j in xrange(1101,1101+ntiles):
                    open(self._path('Data','Intensities','BaseCalls',
                                    'L%03d' % i,'C%d.1' % k,
                                    's_%d_%d.%s' % (i,j,bcl_ext)),'wb+').close()
                    open(self._path('Data','Intensities','BaseCalls',
                                    'L%03d' % i,'C%d.1' % k,
                                    's_%d_%d.stats' % (i,j)),'wb+').close()
        # RunInfo.xml
        run_info_xml = """<?xml version="1.0"?>
<RunInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" Version="2">
  <Run Id="%s" Number="2">
    <Flowcell>A00NAABXX</Flowcell>
    <Instrument>H00002</Instrument>
    <Date>151113</Date>
    <Reads>
      <Read Number="1" NumCycles="101" IsIndexedRead="N" />
      <Read Number="2" NumCycles="8" IsIndexedRead="Y" />
      <Read Number="3" NumCycles="8" IsIndexedRead="Y" />
      <Read Number="4" NumCycles="101" IsIndexedRead="N" />
    </Reads>
    <FlowcellLayout LaneCount="8" SurfaceCount="2" SwathCount="3" TileCount="16" />
    <AlignToPhiX>
      <Lane>1</Lane>
      <Lane>2</Lane>
      <Lane>3</Lane>
      <Lane>4</Lane>
      <Lane>5</Lane>
      <Lane>6</Lane>
      <Lane>7</Lane>
      <Lane>8</Lane>
    </AlignToPhiX>
  </Run>
</RunInfo>
"""
        with open(self._path('RunInfo.xml'),'w') as fp:
            fp.write(run_info_xml % self.name)
        # SampleSheet.csv
        sample_sheet_csv = """[Header],,,,,,,,,,
IEMFileVersion,4,,,,,,,,,
Date,11/11/2015,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,,,
Assay,Nextera XT,,,,,,,,,
Description,,,,,,,,,,
Chemistry,Amplicon,,,,,,,,,
,,,,,,,,,,
[Reads],,,,,,,,,,
101,,,,,,,,,,
101,,,,,,,,,,
,,,,,,,,,,
[Settings],,,,,,,,,,
ReverseComplement,0,,,,,,,,,
Adapter,CTGTCTCTTATACACATCT,,,,,,,,,
,,,,,,,,,,
[Data],,,,,,,,,,
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,AB1,AB1,,,N701,TAAGGCGA,S504,AGAGTAGA,AB,
2,TM2,TM1,,,N701,TAAGGCGA,S517,GCGTAAGA,TM,
3,CD3,CD3,,,N701,GTGAAACG,S503,TCTTTCCC,CD,
4,EB4,EB4,,A1,N701,TAAGGCGA,S501,TAGATCGC,EB,
5,EB5,EB5,,A3,N703,AGGCAGAA,S501,TAGATCGC,EB,
6,EB6,EB6,,F3,N703,AGGCAGAA,S506,ACTGCATA,EB,
7,ML7,ML7,,,N701,GCCAATAT,S502,TCTTTCCC,ML,
8,VL8,VL8,,,N701,GCCAATAT,S503,TCTTTCCC,VL,
"""
        with open(self._path('Data','Intensities','BaseCalls',
                             'SampleSheet.csv'),'w') as fp:
            fp.write(sample_sheet_csv)
        # (Empty) config.xml files
        open(self._path('Data','Intensities','config.xml'),'wb+').close()
        open(self._path('Data','Intensities','BaseCalls','config.xml'),
             'wb+').close()

    def _create_nextseq(self):
        """
        Internal: creates mock NextSeq run directory structure

        """
        # Constants for NextSeq
        nlanes = 4
        ntiles = 12 #158
        bcl_ext = '.bcl.bgzf'
        # Basic directory structure
        bcftbx.utils.mkdir(self._path('Data'))
        bcftbx.utils.mkdir(self._path('Data','Intensities'))
        bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls'))
        bcftbx.utils.mkdir(self._path('InterOp'))
        # Lanes
        for i in xrange(1,nlanes+1):
            # .locs files
            bcftbx.utils.mkdir(self._path('Data','Intensities','L%03d' % i))
            open(self._path('Data','Intensities','L%03d' % i,'s_%d.locs' % i),
                 'wb+').close()
            # BaseCalls
            bcftbx.utils.mkdir(self._path('Data','Intensities','BaseCalls',
                                          'L%03d' % i))
            open(self._path('Data','Intensities','BaseCalls','L%03d' % i,
                            's_%d.bci' % i),'wb+').close()
            open(self._path('Data','Intensities','BaseCalls','L%03d' % i,
                            's_%d.filter' % i),'wb+').close()
            for j in xrange(1,ntiles+1):
                open(self._path('Data','Intensities','BaseCalls','L%03d' % i,
                                '%04d%s' % (j,bcl_ext)),'wb+').close()
                open(self._path('Data','Intensities','BaseCalls','L%03d' % i,
                                '%04d%s.bci' % (j,bcl_ext)),'wb+').close()
        # RunInfo.xml
        run_info_xml = """<?xml version="1.0"?>
<RunInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.o
rg/2001/XMLSchema-instance" Version="4">
  <Run Id="%s" Number="1">
    <Flowcell>ABC1234XX</Flowcell>
    <Instrument>N000003</Instrument>
    <Date>151123</Date>
    <Reads>
      <Read Number="1" NumCycles="76" IsIndexedRead="N" />
      <Read Number="2" NumCycles="6" IsIndexedRead="Y" />
      <Read Number="3" NumCycles="76" IsIndexedRead="N" />
    </Reads>
    <FlowcellLayout LaneCount="4" SurfaceCount="2" SwathCount="3" TileCount="12"
 SectionPerLane="3" LanePerSection="2">
      <TileSet TileNamingConvention="FiveDigit">
        <Tiles>
          <Tile>1_11101</Tile>
          <Tile>1_21101</Tile></Tiles>
      </TileSet>
    </FlowcellLayout>
    <ImageDimensions Width="2592" Height="1944" />
    <ImageChannels>
      <Name>Red</Name>
      <Name>Green</Name>
    </ImageChannels>
  </Run>
</RunInfo>"""
        with open(self._path('RunInfo.xml'),'w') as fp:
            fp.write(run_info_xml % self.name)

    def create(self):
        """
        Build and populate the directory structure

        Creates the directory structure on disk which has been defined
        within the MockIlluminaRun object.

        Invoke the 'remove' method to delete the directory structure.

        'create' raises an OSError exception if any part of the directory
        structure already exists.

        """
        # Create top level directory
        if os.path.exists(self.dirn):
            raise OSError,"%s already exists" % self.dirn
        else:
            bcftbx.utils.mkdir(self.dirn)
            self._created = True
        # Make platform-specific directory structure
        if self._platform == 'miseq':
            self._create_miseq()
        elif self._platform == 'hiseq':
            self._create_hiseq()
        elif self._platform == 'nextseq':
            self._create_nextseq()

    def remove(self):
        """
        Delete the directory structure and contents

        This removes the directory structure from disk that has
        previously been created using the create method.

        """
        if self._created:
            shutil.rmtree(self.dirn)
            self._created = False

class MockIlluminaData:
    """Utility class for creating mock Illumina analysis data directories

    The MockIlluminaData class allows artificial Illumina analysis data
    directories to be defined, created and populated, and then destroyed.

    These artifical directories are intended to be used for testing
    purposes.

    Basic example usage:

    >>> mockdata = MockIlluminaData('130904_PJB_XXXXX')
    >>> mockdata.add_fastq('PJB','PJB1','PJB1_GCCAAT_L001_R1_001.fastq.gz')
    >>> ...
    >>> mockdata.create()

    This will make a directory structure:

    1130904_PJB_XXXXX/
        Unaligned/
            Project_PJB/
                Sample_PJB1/
                    PJB1_GCCAAT_L001_R1_001.fastq.gz
        ...

    Multiple fastqs can be more easily added using e.g.:

    >>> mockdata.add_fastq_batch('PJB','PJB2','PJB1_GCCAAT',lanes=(1,4,5))

    which creates 3 fastq entries for sample PJB2, with lane numbers 1, 4
    and 5.

    Paired-end mock data can be created using the 'paired_end' flag
    when instantiating the MockIlluminaData object.

    To delete the physical directory structure when finished:

    >>> mockdata.remove()

    """
    def __init__(self,name,unaligned_dir='Unaligned',paired_end=False,top_dir=None):
        """Create new MockIlluminaData instance

        Makes a new empty MockIlluminaData object.

        Arguments:
          name: name of the directory for the mock data
          unaligned_dir: directory holding the mock projects etc (default is
            'Unaligned')
          paired_end: specify whether mock data is paired end (True) or not
            (False) (default is False)
          top_dir: specify a parent directory for the mock data (default is
            the current working directory)

        """
        self.__created = False
        self.__name = name
        self.__unaligned_dir = unaligned_dir
        self.__paired_end = paired_end
        self.__undetermined_dir = 'Undetermined_indices'
        if top_dir is not None:
            self.__top_dir = os.path.abspath(top_dir)
        else:
            self.__top_dir = os.getcwd()
        self.__projects = {}

    @property
    def name(self):
        """Name of the mock data

        """
        return self.__name

    @property
    def dirn(self):
        """Full path to the mock data directory

        """
        return os.path.join(self.__top_dir,self.__name)

    @property
    def unaligned_dir(self):
        """Full path to the unaligned directory for the mock data

        """
        return os.path.join(self.dirn,self.__unaligned_dir)

    @property
    def paired_end(self):
        """Whether or not the mock data is paired ended

        """
        return self.__paired_end

    @property
    def projects(self):
        """List of project names within the mock data

        """
        projects = []
        for project_name in self.__projects:
            if project_name.startswith('Project_'):
                projects.append(project_name.split('_')[1])
        projects.sort()
        return projects

    @property
    def has_undetermined(self):
        """Whether or not undetermined indices are included

        """
        return (self.__undetermined_dir in self.__projects)

    def samples_in_project(self,project_name):
        """List of sample names associated with a specific project

        Arguments:
          project_name: name of a project

        Returns:
          List of sample names

        """
        project = self.__projects[self.__project_dir(project_name)]
        samples = []
        for sample_name in project:
            if sample_name.startswith('Sample_'):
                samples.append(sample_name.split('_')[1])
        samples.sort()
        return samples

    def fastqs_in_sample(self,project_name,sample_name):
        """List of fastq names associated with a project/sample pair

        Arguments:
          project_name: name of a project
          sample_name: name of a sample

        Returns:
          List of fastq names.

        """
        project_dir = self.__project_dir(project_name)
        sample_dir = self.__sample_dir(sample_name)
        return self.__projects[project_dir][sample_dir]

    def __project_dir(self,project_name):
        """Internal: convert project name to internal representation

        Project names are prepended with "Project_" if not already
        present, or if it is the "undetermined_indexes" directory.

        Arguments:
          project_name: name of a project

        Returns:
          Canonical project name for internal storage.

        """
        if project_name.startswith('Project_') or \
           project_name.startswith(self.__undetermined_dir):
            return project_name
        else:
            return 'Project_' + project_name

    def __sample_dir(self,sample_name):
        """Internal: convert sample name to internal representation

        Sample names are prepended with "Sample_" if not already
        present.

        Arguments:
          sample_name: name of a sample

        Returns:
          Canonical sample name for internal storage.

        """
        if sample_name.startswith('Sample_'):
            return sample_name
        else:
            return 'Sample_' + sample_name

    def add_project(self,project_name):
        """Add a project to the MockIlluminaData instance

        Defines a project within the MockIlluminaData structure.
        Note that any leading 'Project_' is ignored i.e. the project
        name is taken to be the remainder of the name.

        No error is raised if the project already exists.

        Arguments:
          project_name: name of the new project

        Returns:
          Dictionary object corresponding to the project.

        """
        project_dir = self.__project_dir(project_name)
        if project_dir not in self.__projects:
            self.__projects[project_dir] = {}
        return self.__projects[project_dir]

    def add_sample(self,project_name,sample_name):
        """Add a sample to a project within the MockIlluminaData instance

        Defines a sample with a project in the MockIlluminaData
        structure. Note that any leading 'Sample_' is ignored i.e. the
        sample name is taken to be the remainder of the name.

        If the parent project doesn't exist yet then it will be
        added automatically; no error is raised if the sample already
        exists.

        Arguments:
          project_name: name of the parent project
          sample_name: name of the new sample

        Returns:
          List object corresponding to the sample.
        
        """
        project = self.add_project(project_name)
        sample_dir = self.__sample_dir(sample_name)
        if sample_dir not in project:
            project[sample_dir] = []
        return project[sample_dir]

    def add_fastq(self,project_name,sample_name,fastq):
        """Add a fastq to a sample within the MockIlluminaData instance

        Defines a fastq within a project/sample pair in the MockIlluminaData
        structure.

        NOTE: it is recommended to use add_fastq_batch, which offers more
        flexibility and automatically maintains consistency e.g. when
        mocking a paired end data structure.

        Arguments:
          project_name: parent project
          sample_name: parent sample
          fastq: name of the fastq to add
        
        """
        sample = self.add_sample(project_name,sample_name)
        sample.append(fastq)
        sample.sort()

    def add_fastq_batch(self,project_name,sample_name,fastq_base,fastq_ext='fastq.gz',
                        lanes=(1,)):
        """Add a set of fastqs within a sample

        This method adds a set of fastqs within a sample with a single
        invocation, and is intended to simulate the situation where there
        are multiple fastqs due to paired end sequencing and/or sequencing
        of the sample across multiple lanes.

        The fastq names are constructed from a base name (e.g. 'PJB-1_GCCAAT'),
        plus a list/tuple of lane numbers. One fastq will be added for each
        lane number specified, e.g.:

        >>> d.add_fastq_batch('PJB','PJB-1','PJB-1_GCCAAT',lanes=(1,4,5))

        will add PJB-1_GCCAAT_L001_R1_001, PJB-1_GCCAAT_L004_R1_001 and
        PJB-1_GCCAAT_L005_R1_001 fastqs.

        If the MockIlluminaData object was created with the paired_end flag
        set to True then matching R2 fastqs will also be added.

        Arguments:
          project_name: parent project
          sample_name: parent sample
          fastq_base: base name of the fastq name i.e. just the sample name
            and barcode sequence (e.g. 'PJB-1_GCCAAT')
          fastq_ext: file extension to use (optional, defaults to 'fastq.gz')
          lanes: list, tuple or iterable with lane numbers (optional,
            defaults to (1,))

        """
        if self.__paired_end:
            reads = (1,2)
        else:
            reads = (1,)
        for lane in lanes:
            for read in reads:
                fastq = "%s_L%03d_R%d_001.%s" % (fastq_base,
                                                 lane,read,
                                                 fastq_ext)
                self.add_fastq(project_name,sample_name,fastq)

    def add_undetermined(self,lanes=(1,)):
        """Add directories and files for undetermined reads

        This method adds a set of fastqs for any undetermined reads from
        demultiplexing.

        Arguments:
          lanes: list, tuple or iterable with lane numbers (optional,
            defaults to (1,))

        """
        for lane in lanes:
            sample_name = "Sample_lane%d" % lane
            fastq_base = "lane%d_Undetermined" % lane
            self.add_sample(self.__undetermined_dir,sample_name)
            self.add_fastq_batch(self.__undetermined_dir,sample_name,fastq_base,
                                 lanes=(lane,))

    def create(self):
        """Build and populate the directory structure

        Creates the directory structure on disk which has been defined
        within the MockIlluminaData object.

        Invoke the 'remove' method to delete the directory structure.

        The contents of the MockIlluminaData object can be modified
        after the directory structure has been created, but changes will
        not be reflected on disk. Instead it is necessary to first
        remove the directory structure, and then re-invoke the create
        method.

        create raises an OSError exception if any part of the directory
        structure already exists.

        """
        # Create top level directory
        if os.path.exists(self.dirn):
            raise OSError,"%s already exists" % self.dirn
        else:
            bcftbx.utils.mkdir(self.dirn)
            self.__created = True
        # "Unaligned" directory
        bcftbx.utils.mkdir(self.unaligned_dir)
        # Populate with projects, samples etc
        for project_name in self.__projects:
            project_dirn = os.path.join(self.unaligned_dir,project_name)
            bcftbx.utils.mkdir(project_dirn)
            for sample_name in self.__projects[project_name]:
                sample_dirn = os.path.join(project_dirn,sample_name)
                bcftbx.utils.mkdir(sample_dirn)
                for fastq in self.__projects[project_name][sample_name]:
                    fq = os.path.join(sample_dirn,fastq)
                    # "Touch" the file (i.e. creates an empty file)
                    open(fq,'wb+').close()

    def remove(self):
        """Delete the directory structure and contents

        This removes the directory structure from disk that has
        previously been created using the create method.

        """
        if self.__created:
            shutil.rmtree(self.dirn)
            self.__created = False

class TestIlluminaRun(unittest.TestCase):
    """
    Tests for IlluminaRun against MISeq, HISeq and NextSeq

    """
    def setUp(self):
        # Create a mock Illumina run directory
        self.mock_illumina_run = None

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_run is not None:
            self.mock_illumina_run.remove()

    def test_illuminarun_miseq(self):
        # Make a mock run directory for MISeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_M00879_0001_000000000-ABCDE1','miseq')
        self.mock_illumina_run.create()
        # Load into an IlluminaRun object
        run = IlluminaRun(self.mock_illumina_run.name)
        # Check the properties
        self.assertEqual(run.run_dir,self.mock_illumina_run.dirn)
        self.assertEqual(run.platform,"miseq")
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data','Intensities','BaseCalls'))
        self.assertEqual(run.sample_sheet_csv,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data','Intensities','BaseCalls',
                                      'SampleSheet.csv'))
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.bcl_extension,".bcl")

    def test_illuminarun_hiseq(self):
        # Make a mock run directory for HISeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_SN700511R_0002_000000000-ABCDE1XX','hiseq')
        self.mock_illumina_run.create()
        # Load into an IlluminaRun object
        run = IlluminaRun(self.mock_illumina_run.name)
        # Check the properties
        self.assertEqual(run.run_dir,self.mock_illumina_run.dirn)
        self.assertEqual(run.platform,"hiseq")
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data','Intensities','BaseCalls'))
        self.assertEqual(run.sample_sheet_csv,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data','Intensities','BaseCalls',
                                      'SampleSheet.csv'))
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.bcl_extension,".bcl.gz")

    def test_illuminarun_nextseq(self):
        # Make a mock run directory for HISeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_NB500968_0003_000000000-ABCDE1XX','nextseq')
        self.mock_illumina_run.create()
        # Load into an IlluminaRun object
        run = IlluminaRun(self.mock_illumina_run.name)
        # Check the properties
        self.assertEqual(run.run_dir,self.mock_illumina_run.dirn)
        self.assertEqual(run.platform,"nextseq")
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data','Intensities','BaseCalls'))
        self.assertEqual(run.sample_sheet_csv,None)
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.bcl_extension,".bcl.bgzf")

class TestIlluminaData(unittest.TestCase):
    """Collective tests for IlluminaData, IlluminaProject and IlluminaSample

    Test methods use the following pattern:

    1. Invoke makeMockIlluminaData factory method to produce a variant
       of an artificial directory structure mimicking that produced by the
       bcl to fastq conversion process
    2. Populate an IlluminaData object from the resulting directory structure
    3. Invoke the assertIlluminaData method to check that the IlluminaData
       object is correct.

    assertIlluminaData in turn invokes assertIlluminaProject and
    assertIlluminaUndetermined; assertIlluminaProject invokes
    assertIlluminaSample.

    """

    def setUp(self):
        # Create a mock Illumina directory
        self.mock_illumina_data = None

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()

    def makeMockIlluminaData(self,paired_end=False,
                             multiple_projects=False,
                             multiplexed_run=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              paired_end=paired_end)
        # Add first project with two samples
        mock_illumina_data.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        mock_illumina_data.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        # Additional projects?
        if multiplexed_run:
            if multiplexed_run:
                lanes=(1,4,5)
                mock_illumina_data.add_undetermined(lanes=lanes)
            else:
                lanes=(1,)
            mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',lanes=lanes)
            mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',lanes=lanes)
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def assertIlluminaData(self,illumina_data,mock_illumina_data):
        """Verify that an IlluminaData object matches a MockIlluminaData object

        """
        # Check top-level attributes
        self.assertEqual(illumina_data.analysis_dir,mock_illumina_data.dirn,
                         "Directories differ: %s != %s" %
                         (illumina_data.analysis_dir,mock_illumina_data.dirn))
        self.assertEqual(illumina_data.unaligned_dir,mock_illumina_data.unaligned_dir,
                         "Unaligned dirs differ: %s != %s" %
                         (illumina_data.unaligned_dir,mock_illumina_data.unaligned_dir))
        self.assertEqual(illumina_data.paired_end,mock_illumina_data.paired_end,
                         "Paired ended-ness differ: %s != %s" %
                         (illumina_data.paired_end,mock_illumina_data.paired_end))
        # Check projects
        for project,pname in zip(illumina_data.projects,mock_illumina_data.projects):
            self.assertIlluminaProject(project,mock_illumina_data,pname)
        # Check undetermined indices
        self.assertIlluminaUndetermined(illumina_data.undetermined,mock_illumina_data)

    def assertIlluminaProject(self,illumina_project,mock_illumina_data,project_name):
        """Verify that an IlluminaProject object matches a MockIlluminaData object

        """
        # Check top-level attributes
        self.assertEqual(illumina_project.name,project_name)
        self.assertEqual(illumina_project.paired_end,mock_illumina_data.paired_end)
        # Check samples within projects
        for sample,sname in zip(illumina_project.samples,
                                mock_illumina_data.samples_in_project(project_name)):
            self.assertIlluminaSample(sample,mock_illumina_data,project_name,sname)

    def assertIlluminaSample(self,illumina_sample,mock_illumina_data,
                             project_name,sample_name):
        """Verify that an IlluminaSample object matches a MockIlluminaData object

        """
        # Check top-level attributes
        self.assertEqual(illumina_sample.name,sample_name)
        self.assertEqual(illumina_sample.paired_end,mock_illumina_data.paired_end)
        # Check fastqs
        for fastq,fq in zip(illumina_sample.fastq,
                            mock_illumina_data.fastqs_in_sample(project_name,
                                                                sample_name)):
            self.assertEqual(fastq,fq)
        # Check fastq subsets
        r1_fastqs = illumina_sample.fastq_subset(read_number=1)
        r2_fastqs = illumina_sample.fastq_subset(read_number=2)
        self.assertEqual(len(r1_fastqs)+len(r2_fastqs),
                         len(illumina_sample.fastq))
        if not illumina_sample.paired_end:
            # For single end data all fastqs are R1 and there are no R2
            for fastq,fq in zip(illumina_sample.fastq,r1_fastqs):
                self.assertEqual(fastq,fq)
            self.assertEqual(len(r2_fastqs),0)
        else:
            # For paired end data check R1 and R2 files match up
            for fastq_r1,fastq_r2 in zip(r1_fastqs,r2_fastqs):
                fqr1 = IlluminaFastq(fastq_r1)
                fqr2 = IlluminaFastq(fastq_r2)
                self.assertEqual(fqr1.read_number,1)
                self.assertEqual(fqr2.read_number,2)
                self.assertEqual(fqr1.sample_name,fqr2.sample_name)
                self.assertEqual(fqr1.barcode_sequence,fqr2.barcode_sequence)
                self.assertEqual(fqr1.lane_number,fqr2.lane_number)
                self.assertEqual(fqr1.set_number,fqr2.set_number)

    def assertIlluminaUndetermined(self,undetermined,mock_illumina_data):
        """Verify that Undetermined_indices project matches MockIlluminaData
        
        """
        self.assertEqual((undetermined is not None),mock_illumina_data.has_undetermined)
        if undetermined is not None:
            # Delegate checking to assertIlluminaProject
            self.assertIlluminaProject(undetermined,
                                       mock_illumina_data,undetermined.name)

    def test_illumina_data(self):
        """Basic test with single project

        """
        self.makeMockIlluminaData()
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

    def test_illumina_data_paired_end(self):
        """Test with single project & paired-end data

        """
        self.makeMockIlluminaData(paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

    def test_illumina_data_multiple_projects(self):
        """Test with multiple projects

        """
        self.makeMockIlluminaData(multiple_projects=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

    def test_illumina_data_multiple_projects_paired_end(self):
        """Test with multiple projects & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

    def test_illumina_data_multiple_projects_multiplexed(self):
        """Test with multiple projects & multiplexing

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

    def test_illumina_data_multiple_projects_multiplexed_paired_end(self):
        """Test with multiple projects, multiplexing & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True,
                                  paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)

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
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(sample_sheet.duplicated_names),0)
        # Create 3 duplicates by resetting lane numbers
        sample_sheet[4]['Lane'] = 2
        sample_sheet[5]['Lane'] = 3
        sample_sheet[6]['Lane'] = 4
        self.assertEqual(len(sample_sheet.duplicated_names),3)
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

    def test_remove_quotes(self):
        """Remove double quotes from values

        """
        # Set up
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO("""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
"D190HACXX",1,"PB","PB","CGATGT","RNA-seq","N",,,"Peter Briggs"
"""))
        self.assertEqual(sample_sheet[0]['FCID'],'D190HACXX')
        self.assertEqual(sample_sheet[0]['Lane'],1)
        self.assertEqual(sample_sheet[0]['SampleID'],'PB')
        self.assertEqual(sample_sheet[0]['SampleRef'],'PB')
        self.assertEqual(sample_sheet[0]['Index'],'CGATGT')
        self.assertEqual(sample_sheet[0]['Description'],'RNA-seq')
        self.assertEqual(sample_sheet[0]['Control'],'N')
        self.assertEqual(sample_sheet[0]['Recipe'],'')
        self.assertEqual(sample_sheet[0]['Operator'],'')
        self.assertEqual(sample_sheet[0]['SampleProject'],'Peter Briggs')

    def test_remove_quotes_and_comments(self):
        """Remove double quotes from values along with comment lines

        """
        # Set up
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO("""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
"D190HACXX",1,"PB","PB","CGATGT","RNA-seq","N",,,"Peter Briggs"
"#D190HACXX",2,"PB","PB","ACTGAT","RNA-seq","N",,,"Peter Briggs"
"""))
        self.assertEqual(len(sample_sheet),1)

    def test_numeric_names(self):
        """Check that purely numerical names can be handled

        """
        # Set up and introduce numeric names
        sample_sheet = CasavaSampleSheet(fp=cStringIO.StringIO(self.sample_sheet_text))
        sample_sheet[3]['SampleID'] = 8861
        sample_sheet[4]['SampleProject'] = 123
        # Check for illegal names
        self.assertEqual(len(sample_sheet.illegal_names),0)
        # Check for empty names
        self.assertEqual(len(sample_sheet.empty_names),0)
        # Check for duplicated names
        self.assertEqual(len(sample_sheet.duplicated_names),0)

class TestIlluminaFastq(unittest.TestCase):

    def test_illumina_fastq(self):
        """Check extraction of fastq name components

        """
        fastq_name = 'NA10831_ATCACG_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)

    def test_illumina_fastq_with_path_and_extension(self):
        """Check extraction of name components with leading path and extension

        """
        fastq_name = '/home/galaxy/NA10831_ATCACG_L002_R1_001.fastq.gz'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)

    def test_illumina_fastq_r2(self):
        """Check extraction of fastq name components for R2 read

        """
        fastq_name = 'NA10831_ATCACG_L002_R2_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,2)
        self.assertEqual(fq.set_number,1)

    def test_illumina_fastq_no_index(self):
        """Check extraction of fastq name components without a barcode

        """
        fastq_name = 'NA10831_NoIndex_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)

    def test_illumina_fastq_dual_index(self):
        """Check extraction of fastq name components with dual index

        """
        fastq_name = 'NA10831_ATCACG-GCACTA_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.barcode_sequence,'ATCACG-GCACTA')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)

class TestIEMSampleSheet(unittest.TestCase):
    def setUp(self):
        self.hiseq_sample_sheet_content = """[Header],,,,,,,,,,
IEMFileVersion,4,,,,,,,,,
Date,06/03/2014,,,,,,,,,
Workflow,GenerateFASTQ,,,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,,,
Assay,Nextera,,,,,,,,,
Description,,,,,,,,,,
Chemistry,Amplicon,,,,,,,,,
,,,,,,,,,,
[Reads],,,,,,,,,,
101,,,,,,,,,,
101,,,,,,,,,,
,,,,,,,,,,
[Settings],,,,,,,,,,
ReverseComplement,0,,,,,,,,,
Adapter,CTGTCTCTTATACACATCT,,,,,,,,,
,,,,,,,,,,
[Data],,,,,,,,,,
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT ,N501,TCTTTCCC,PeterBriggs,
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT ,N502,TCTTTCCC,PeterBriggs,
"""
        self.miseq_sample_sheet_content = """[Header]
IEMFileVersion,4
Date,4/11/2014
Workflow,Metagenomics
Application,Metagenomics 16S rRNA
Assay,Nextera XT
Description,
Chemistry,Amplicon

[Reads]
150
150

[Settings]
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
A8,A8,,,N701,TAAGGCGA,S501,TAGATCGC,PJB,
B8,B8,,,N702,CGTACTAG,S501,TAGATCGC,PJB,
"""

    def test_load_hiseq_sample_sheet(self):
        """IEMSampleSheet: load a HiSEQ sample sheet

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.hiseq_sample_sheet_content))
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Date'],'06/03/2014')
        self.assertEqual(iem.header['Workflow'],'GenerateFASTQ')
        self.assertEqual(iem.header['Application'],'HiSeq FASTQ Only')
        self.assertEqual(iem.header['Assay'],'Nextera')
        self.assertEqual(iem.header['Description'],'')
        self.assertEqual(iem.header['Chemistry'],'Amplicon')
        # Check reads
        self.assertEqual(iem.reads,['101','101'])
        # Check settings
        self.assertEqual(iem.settings_items,['ReverseComplement',
                                              'Adapter'])
        self.assertEqual(iem.settings['ReverseComplement'],'0')
        self.assertEqual(iem.settings['Adapter'],'CTGTCTCTTATACACATCT')
        # Check data
        self.assertEqual(iem.data.header(),['Lane','Sample_ID','Sample_Name',
                                            'Sample_Plate','Sample_Well',
                                            'I7_Index_ID','index',
                                            'I5_Index_ID','index2',
                                            'Sample_Project','Description'])
        self.assertEqual(len(iem.data),2)
        self.assertEqual(iem.data[0]['Lane'],1)
        self.assertEqual(iem.data[0]['Sample_ID'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Name'],'PJB1-1579')
        self.assertEqual(iem.data[0]['Sample_Plate'],'')
        self.assertEqual(iem.data[0]['Sample_Well'],'')
        self.assertEqual(iem.data[0]['I7_Index_ID'],'N701')
        self.assertEqual(iem.data[0]['index'],'CGATGTAT')
        self.assertEqual(iem.data[0]['I5_Index_ID'],'N501')
        self.assertEqual(iem.data[0]['index2'],'TCTTTCCC')
        self.assertEqual(iem.data[0]['Sample_Project'],'PeterBriggs')
        self.assertEqual(iem.data[0]['Description'],'')
    def test_show_hiseq_sample_sheet(self):
        """IEMSampleSheet: reconstruct a HiSEQ sample sheet

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.hiseq_sample_sheet_content))
        expected = """[Header]
IEMFileVersion,4
Date,06/03/2014
Workflow,GenerateFASTQ
Application,HiSeq FASTQ Only
Assay,Nextera
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1-1579,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,PJB2-1580,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""
        for l1,l2 in zip(iem.show().split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_convert_hiseq_sample_sheet_to_casava(self):
        """IEMSampleSheet: convert HiSEQ sample sheet to CASAVA format

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.hiseq_sample_sheet_content))
        casava = iem.casava_sample_sheet()
        self.assertEqual(casava.header(),['FCID','Lane','SampleID','SampleRef',
                                          'Index','Description','Control',
                                          'Recipe','Operator','SampleProject'])
        self.assertEqual(len(casava),2)
        self.assertEqual(casava[0]['FCID'],'FC1')
        self.assertEqual(casava[0]['Lane'],1)
        self.assertEqual(casava[0]['SampleID'],'PJB1-1579')
        self.assertEqual(casava[0]['SampleRef'],'')
        self.assertEqual(casava[0]['Index'],'CGATGTAT-TCTTTCCC')
        self.assertEqual(casava[0]['Description'],'')
        self.assertEqual(casava[0]['Control'],'')
        self.assertEqual(casava[0]['Recipe'],'')
        self.assertEqual(casava[0]['Operator'],'')
        self.assertEqual(casava[0]['SampleProject'],'PeterBriggs')
    def test_load_miseq_sample_sheet(self):
        """IEMSampleSheet: load a MiSEQ sample sheet

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.miseq_sample_sheet_content))
        # Check header
        self.assertEqual(iem.header_items,['IEMFileVersion',
                                           'Date',
                                           'Workflow',
                                           'Application',
                                           'Assay',
                                           'Description',
                                           'Chemistry'])
        self.assertEqual(iem.header['IEMFileVersion'],'4')
        self.assertEqual(iem.header['Date'],'4/11/2014')
        self.assertEqual(iem.header['Workflow'],'Metagenomics')
        self.assertEqual(iem.header['Application'],'Metagenomics 16S rRNA')
        self.assertEqual(iem.header['Assay'],'Nextera XT')
        self.assertEqual(iem.header['Description'],'')
        self.assertEqual(iem.header['Chemistry'],'Amplicon')
        # Check reads
        self.assertEqual(iem.reads,['150','150'])
        # Check settings
        self.assertEqual(iem.settings_items,['Adapter'])
        self.assertEqual(iem.settings['Adapter'],'CTGTCTCTTATACACATCT')
        # Check data
        self.assertEqual(iem.data.header(),['Sample_ID','Sample_Name',
                                            'Sample_Plate','Sample_Well',
                                            'I7_Index_ID','index',
                                            'I5_Index_ID','index2',
                                            'Sample_Project','Description'])
        self.assertEqual(len(iem.data),2)
        self.assertEqual(iem.data[0]['Sample_ID'],'A8')
        self.assertEqual(iem.data[0]['Sample_Name'],'A8')
        self.assertEqual(iem.data[0]['Sample_Plate'],'')
        self.assertEqual(iem.data[0]['Sample_Well'],'')
        self.assertEqual(iem.data[0]['I7_Index_ID'],'N701')
        self.assertEqual(iem.data[0]['index'],'TAAGGCGA')
        self.assertEqual(iem.data[0]['I5_Index_ID'],'S501')
        self.assertEqual(iem.data[0]['index2'],'TAGATCGC')
        self.assertEqual(iem.data[0]['Sample_Project'],'PJB')
        self.assertEqual(iem.data[0]['Description'],'')
    def test_show_miseq_sample_sheet(self):
        """IEMSampleSheet: reconstruct a MiSEQ sample sheet

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.miseq_sample_sheet_content))
        expected = self.miseq_sample_sheet_content
        for l1,l2 in zip(iem.show().split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_convert_miseq_sample_sheet_to_casava(self):
        """IEMSampleSheet: convert MiSEQ sample sheet to CASAVA format

        """
        iem = IEMSampleSheet(fp=cStringIO.StringIO(self.miseq_sample_sheet_content))
        casava = iem.casava_sample_sheet()
        self.assertEqual(casava.header(),['FCID','Lane','SampleID','SampleRef',
                                          'Index','Description','Control',
                                          'Recipe','Operator','SampleProject'])
        self.assertEqual(len(casava),2)
        self.assertEqual(casava[0]['FCID'],'FC1')
        self.assertEqual(casava[0]['Lane'],1)
        self.assertEqual(casava[0]['SampleID'],'A8')
        self.assertEqual(casava[0]['SampleRef'],'')
        self.assertEqual(casava[0]['Index'],'TAAGGCGA-TAGATCGC')
        self.assertEqual(casava[0]['Description'],'')
        self.assertEqual(casava[0]['Control'],'')
        self.assertEqual(casava[0]['Recipe'],'')
        self.assertEqual(casava[0]['Operator'],'')
        self.assertEqual(casava[0]['SampleProject'],'PJB')
    def test_bad_input_unrecognised_section(self):
        """IEMSampleSheet: raises exception for input with unrecognised section

        """
        fp = cStringIO.StringIO("""[Header]
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaDataError,IEMSampleSheet,fp=fp)
    def test_bad_input_not_IEM_sample_sheet(self):
        """IEMSampleSheet: raises exception for non-IEM formatted input

        """
        fp = cStringIO.StringIO("""Something random
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaDataError,IEMSampleSheet,fp=fp)

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
        # Example of single index data
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
        # Example of dual-indexed data
        self.miseq_data_dual_indexed = self.miseq_header + """
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description,GenomeFolder
PB1,,PB,A01,N701,TAAGGCGA,N501,TAGATCGC,,,
ID2,,PB,A02,N702,CGTACTAG,N502,CTCTCTAT,,,"""
        self.miseq_dual_indexed_sample_ids = ['PB1','ID2']
        self.miseq_dual_indexed_sample_projects = ['PB','ID']
        self.miseq_dual_indexed_index_ids = ['TAAGGCGA-TAGATCGC','CGTACTAG-CTCTCTAT']
        # Example of no-index data
        self.miseq_data_no_index = self.miseq_header + """
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,Sample_Project,Description
PB2,PB2,,,PB,"""
        self.miseq_no_index_sample_ids = ['PB2']
        self.miseq_no_index_sample_projects = ['PB']
        self.miseq_no_index_index_ids = ['']

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

    def test_convert_miseq_to_casava_dual_indexed(self):
        """Convert MiSeq SampleSheet to CASAVA SampleSheet (dual indexed)
        
        """
        # Make sample sheet from MiSEQ data
        sample_sheet = convert_miseq_samplesheet_to_casava(
            fp=cStringIO.StringIO(self.miseq_data_dual_indexed))
        # Check contents
        self.assertEqual(len(sample_sheet),2)
        for i in range(0,2):
            self.assertEqual(sample_sheet[i]['Lane'],1)
            self.assertEqual(sample_sheet[i]['SampleID'],self.miseq_dual_indexed_sample_ids[i])
            self.assertEqual(sample_sheet[i]['SampleProject'],
                             self.miseq_dual_indexed_sample_projects[i])
            self.assertEqual(sample_sheet[i]['Index'],
                             self.miseq_dual_indexed_index_ids[i])

    def test_convert_miseq_to_casava_no_index(self):
        """Convert MiSeq SampleSheet to CASAVA SampleSheet (no index)
        
        """
        # Make sample sheet from MiSEQ data
        sample_sheet = convert_miseq_samplesheet_to_casava(
            fp=cStringIO.StringIO(self.miseq_data_no_index))
        self.assertEqual(len(sample_sheet),1)
        for i in range(0,1):
            self.assertEqual(sample_sheet[i]['Lane'],1)
            self.assertEqual(sample_sheet[i]['SampleID'],self.miseq_no_index_sample_ids[i])
            self.assertEqual(sample_sheet[i]['SampleProject'],
                             self.miseq_no_index_sample_projects[i])            
            self.assertEqual(sample_sheet[i]['Index'],
                             self.miseq_no_index_index_ids[i])

class TestHiseqToCasavaConversion(unittest.TestCase):

    def setUp(self):
        self.hiseq_header = """[Header],,,,,,,,
IEMFileVersion,4,,,,,,,
Experiment Name,HiSeq2,,,,,,,
Date,08/01/2013,,,,,,,
Workflow,GenerateFASTQ,,,,,,,
Application,HiSeq FASTQ Only,,,,,,,
Assay,TruSeq LT,,,,,,,
Description,,,,,,,,
Chemistry,Default,,,,,,,
,,,,,,,,
[Reads],,,,,,,,
101,,,,,,,,
101,,,,,,,,
,,,,,,,,
[Settings],,,,,,,,
ReverseComplement,0,,,,,,,
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA,,,,,,,
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT,,,,,,,
,,,,,,,,
[Data],,,,,,,,"""
        # Example of single index data
        self.hiseq_data = self.hiseq_header + """
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
1,PJB3,PJB3,,,A006,GCCAAT,,
1,PJB4,PJB4,,,A007,CAGATC,,
2,PB1-input,PB1-input,,,A002,CGATGT,,
2,PB2,PB2,,,A004,TGACCA,,
3,PB1-input,PB1-input,,,A002,CGATGT,,
4,PJB3,PJB3,,,A006,GCCAAT,,
4,PJB4,PJB4,,,A007,CAGATC,,
5,PJB5,PJB5,,,A012,CTTGTA,,
5,PJB6,PJB6,,,A013,AGTCAA,,
6,PJB4,PJB4,,,A007,CAGATC,,
7,PJB5,PJB5,,,A012,CTTGTA,,
8,PJB6,PJB6,,,A013,AGTCAA,,"""
        self.hiseq_lanes = [1,1,2,2,3,4,4,5,5,6,7,8]
        self.hiseq_sample_ids = ['PJB3','PJB4','PB1-input','PB2','PB1-input','PJB3',
                                 'PJB4','PJB5','PJB6','PJB4','PJB5','PJB6']
        self.hiseq_sample_projects = ['PJB','PJB','PB','PB','PB','PJB',
                                      'PJB','PJB','PJB','PJB','PJB','PJB']
        self.hiseq_index_ids = ['GCCAAT','CAGATC','CGATGT','TGACCA',
                                'CGATGT','GCCAAT','CAGATC','CTTGTA',
                                'AGTCAA','CAGATC','CTTGTA','AGTCAA']

    def test_convert_hiseq_to_casava(self):
        """Convert Experimental Manager HiSeq SampleSheet to CASAVA SampleSheet
        
        """
        # Make sample sheet from HiSEQ data
        sample_sheet = get_casava_sample_sheet(fp=cStringIO.StringIO(self.hiseq_data))
        # Check contents
        self.assertEqual(len(sample_sheet),12)
        for i in range(0,12):
            self.assertEqual(sample_sheet[i]['Lane'],self.hiseq_lanes[i])
            self.assertEqual(sample_sheet[i]['SampleID'],self.hiseq_sample_ids[i])
            self.assertEqual(sample_sheet[i]['SampleProject'],self.hiseq_sample_projects[i])
            self.assertEqual(sample_sheet[i]['Index'],self.hiseq_index_ids[i])

    def test_hiseq_to_casava_handle_space_in_index_sequence(self):
        """Handle trailing space when converting Experimental Manager sample sheet

        """
        self.hiseq_data = self.hiseq_header + """
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
1,PJB1,PJB1,,,N703,CTTGTAAT ,N502,TCTTTCCC,PeterBriggs,"""
        # Make sample sheet from HiSEQ data
        sample_sheet = get_casava_sample_sheet(fp=cStringIO.StringIO(self.hiseq_data))
        # Check contents
        self.assertEqual(len(sample_sheet),1)
        line = sample_sheet[0]
        self.assertEqual(line['Lane'],1)
        self.assertEqual(line['SampleID'],'PJB1')
        self.assertEqual(line['SampleProject'],'PeterBriggs')
        self.assertEqual(line['Index'],'CTTGTAAT-TCTTTCCC')

class TestVerifyRunAgainstSampleSheet(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   paired_end=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',lanes=(2,3))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',lanes=(2,3))
        self.mock_illumina_data.add_undetermined(lanes=(1,2,3))
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
FC1,1,AB1,,GCCAAT,,,,,AB
FC1,1,AB2,,AGTCAA,,,,,AB
FC1,2,CDE3,,GCCAAT,,,,,CDE
FC1,2,CDE4,,AGTCAA,,,,,CDE
FC1,3,CDE3,,GCCAAT,,,,,CDE
FC1,3,CDE4,,AGTCAA,,,,,CDE""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_sample_sheet(self):
        """Verify sample sheet against a matching run
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_project(self):
        """Verify sample sheet against a run with a missing project
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "Project_AB"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_sample(self):
        """Verify sample sheet against a run with a missing sample
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "Project_AB","Sample_AB1"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_fastq(self):
        """Verify sample sheet against a run with a missing fastq file
        """
        os.remove(os.path.join(self.mock_illumina_data.dirn,
                               self.mock_illumina_data.unaligned_dir,
                               "Project_CDE","Sample_CDE4",
                               "CDE4_AGTCAA_L002_R2_001.fastq.gz"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))
    
class TestSummariseProjects(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   paired_end=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',lanes=(2,3))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',lanes=(2,3))
        self.mock_illumina_data.add_undetermined(lanes=(1,2,3))
        self.mock_illumina_data.create()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)

    def test_summarise_projects_paired_end_run(self):
        """Summarise projects for paired end run
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertEqual(summarise_projects(illumina_data),
                         "Paired end: AB (2 samples); CDE (2 samples)")

class TestDescribeProject(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   paired_end=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',lanes=(2,3))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',lanes=(2,3))
        self.mock_illumina_data.add_undetermined(lanes=(1,2,3))
        self.mock_illumina_data.create()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)

    def test_describe_project_paired_end_run(self):
        """Generate descriptions for projects in a paired end run
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertEqual(describe_project(illumina_data.projects[0]),
                         "AB: AB1-2 (2 paired end samples)")
        self.assertEqual(describe_project(illumina_data.projects[1]),
                         "CDE: CDE3-4 (2 paired end samples, multiple fastqs per sample)")

class TestUniqueFastqNames(unittest.TestCase):

    def test_unique_names_single_fastq(self):
        """Check name for a single fastq

        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E.fastq.gz')

    def test_unique_names_single_sample_paired_end(self):
        """Check names for paired end fastqs from single sample
        
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L001_R2_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                        'PJB-E_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R2_001.fastq.gz'],
                         'PJB-E_R2.fastq.gz')

    def test_unique_names_single_sample_multiple_lanes(self):
        """Check names for multiple fastqs from single sample
        
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E_L001.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R1_001.fastq.gz'],
                         'PJB-E_L002.fastq.gz')

    def test_unique_names_single_sample_multiple_lanes_paired_end(self):
        """Check names for multiple fastqs from single paired-end sample
        
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L001_R2_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R1_001.fastq.gz',
                  'PJB-E_GCCAAT_L002_R2_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E_L001_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R2_001.fastq.gz'],
                         'PJB-E_L001_R2.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R1_001.fastq.gz'],
                         'PJB-E_L002_R1.fastq.gz')
        self.assertEqual(mapping['PJB-E_GCCAAT_L002_R2_001.fastq.gz'],
                         'PJB-E_L002_R2.fastq.gz')

    def test_unique_names_multiple_samples_single_fastq(self):
        """Check names for multiple samples each with single fastq
        
        """
        fastqs = ['PJB-E_GCCAAT_L001_R1_001.fastq.gz',
                  'PJB-A_AGTCAA_L001_R1_001.fastq.gz']
        mapping = get_unique_fastq_names(fastqs)
        self.assertEqual(mapping['PJB-E_GCCAAT_L001_R1_001.fastq.gz'],
                         'PJB-E.fastq.gz')
        self.assertEqual(mapping['PJB-A_AGTCAA_L001_R1_001.fastq.gz'],
                         'PJB-A.fastq.gz')

class TestFixBasesMask(unittest.TestCase):

    def test_fix_bases_mask_single_index(self):
        """Check fix_bases_mask for single index data

        """
        self.assertEqual(fix_bases_mask('y50,I6','ACAGTG'),'y50,I6')
        self.assertEqual(fix_bases_mask('y101,I7,y101','CGATGT'),'y101,I6n,y101')

    def test_fix_bases_mask_dual_index(self):
        """Check fix_bases_mask for dual index data
        """
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGCGA-TAGATCGC'),
                         'y250,I8,I8,y250')
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGC-GATCGC'),
                         'y250,I6nn,I6nn,y250')

    def test_fix_bases_mask_dual_index_to_single(self):
        """Check fix_bases_mask for dual index converted to single index
        """
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGCGA'),
                         'y250,I8,nnnnnnnn,y250')
        self.assertEqual(fix_bases_mask('y250,I8,I8,y250','TAAGGC'),
                         'y250,I6nn,nnnnnnnn,y250')
        

class TestSplitRunName(unittest.TestCase):

    def test_split_run_name(self):
        """Check split_run_name for various cases

        """
        self.assertEqual(split_run_name('140210_M00879_0031_000000000-A69NA'),
                         ('140210','M00879','0031'))
        self.assertEqual(split_run_name('/mnt/data/140210_M00879_0031_000000000-A69NA'),
                         ('140210','M00879','0031'))

    def test_split_run_name_with_leading_path(self):
        """Check split_run_name with 'bad' names

        """
        self.assertEqual(split_run_name('this_is_nonesense'),(None,None,None))
        self.assertEqual(split_run_name('140210'),(None,None,None))
        self.assertEqual(split_run_name('14021_M00879_0031_000000000-A69NA'),
                         (None,None,None))
        self.assertEqual(split_run_name('140210_M00879'),
                         (None,None,None))
        self.assertEqual(split_run_name('140210_M00879_0031'),
                         (None,None,None))
        self.assertEqual(split_run_name('1402100_M00879_XYZ'),
                         (None,None,None))

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
