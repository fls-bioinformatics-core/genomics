#######################################################################
# Tests for IlluminaData.py module
#######################################################################
from bcftbx.IlluminaData import *
from bcftbx.mock import MockIlluminaRun
from bcftbx.mock import MockIlluminaData
from bcftbx.TabFile import TabDataLine
import bcftbx.utils
import unittest
import cStringIO
import tempfile
import shutil

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
        self.assertEqual(run.lanes,[1,])
        self.assertEqual(run.cycles,218)

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
        self.assertEqual(run.lanes,[1,2,3,4,5,6,7,8])
        self.assertEqual(run.cycles,218)

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
        self.assertEqual(run.lanes,[1,2,3,4])
        self.assertEqual(run.cycles,158)

    def test_illuminarun_miseq_missing_directory(self):
        # Check we can handle IlluminaRun when MISeq directory is missing
        run = IlluminaRun('/does/not/exist/151125_M00879_0001_000000000-ABCDE1')
        self.assertEqual(run.platform,"miseq")
        self.assertEqual(run.basecalls_dir,None)
        self.assertEqual(run.sample_sheet_csv,None)
        self.assertEqual(run.runinfo_xml,None)
        self.assertRaises(Exception,getattr,run,'bcl_extension')
        self.assertEqual(run.lanes,[])
        self.assertEqual(run.cycles,None)

    def test_illuminarun_nextseq_missing_directory(self):
        # Check we can handle IlluminaRun when NextSeq directory is missing
        run = IlluminaRun('/does/not/exist/151125_NB500968_0003_000000000-ABCDE1XX')
        self.assertEqual(run.platform,"nextseq")
        self.assertEqual(run.basecalls_dir,None)
        self.assertEqual(run.sample_sheet_csv,None)
        self.assertEqual(run.runinfo_xml,None)
        self.assertRaises(Exception,getattr,run,'bcl_extension')
        self.assertEqual(run.lanes,[])
        self.assertEqual(run.cycles,None)

class BaseTestIlluminaData(unittest.TestCase):
    """
    Base class for testing IlluminaData, IlluminaProject and IlluminaSample

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

    Tests of IlluminaData for different styles of processing software
    output can be based on this class. The subclass needs to implement
    its own 'test_...' methods but can use the assert methods here to
    verify that the results are correct.

    """
    def setUp(self):
        # Create a mock Illumina directory
        self.mock_illumina_data = None

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()

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
        # Check fastqs exist
        for fastq in illumina_sample.fastq:
            fq = os.path.join(illumina_sample.dirn,fastq)
            self.assertTrue(os.path.exists(fq),
                            "missing fastq: %s" % fq)
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

class TestIlluminaDataForCasava(BaseTestIlluminaData):
    """
    Test IlluminaData, IlluminaProject and IlluminaSample for CASAVA-style output

    """
    def setUp(self):
        # Create a container for the test directories
        self.top_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.top_dir)
        except Exception:
            pass

    def makeMockIlluminaData(self,paired_end=False,
                             multiple_projects=False,
                             multiplexed_run=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              'casava',paired_end=paired_end,
                                              top_dir=self.top_dir)
        # Add first project with two samples
        mock_illumina_data.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        mock_illumina_data.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        # Additional projects?
        if multiplexed_run:
            lanes = (1,4,5)
            mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',
                                               lanes=lanes)
            mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',
                                               lanes=lanes)
            mock_illumina_data.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def test_illumina_data(self):
        """Read CASAVA-style output with single project

        """
        self.makeMockIlluminaData()
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_paired_end(self):
        """Read CASAVA-style output with single project & paired-end data

        """
        self.makeMockIlluminaData(paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects(self):
        """Read CASAVA-style output with multiple projects

        """
        self.makeMockIlluminaData(multiple_projects=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects_paired_end(self):
        """Read CASAVA-style output with multiple projects & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects_multiplexed(self):
        """Read CASAVA-style output with multiple projects & multiplexing

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,4,5,])

    def test_illumina_data_multiple_projects_multiplexed_paired_end(self):
        """Read CASAVA-style output with multiple projects, multiplexing & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True,
                                  paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'casava')
        self.assertEqual(illumina_data.lanes,[1,4,5,])

class TestIlluminaDataForBcl2fastq2(BaseTestIlluminaData):
    """
    Test for IlluminaData, IlluminaProject and IlluminaSample for bcl2fastq2-style output

    """
    def setUp(self):
        # Create a container for the test directories
        self.top_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.top_dir)
        except Exception:
            pass

    def makeMockIlluminaData(self,paired_end=False,
                             multiple_projects=False,
                             multiplexed_run=False,
                             no_lane_splitting=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              'bcl2fastq2',
                                              paired_end=paired_end,
                                              no_lane_splitting=no_lane_splitting,
                                              top_dir=self.top_dir)
        # Lanes to add
        if not no_lane_splitting:
            if multiplexed_run:
                lanes=(1,4,5)
            else:
                lanes=(1,)
        else:
            lanes = None
        # Add first project with two samples
        mock_illumina_data.add_fastq_batch('AB','AB1','AB1_S1',lanes=lanes)
        mock_illumina_data.add_fastq_batch('AB','AB2','AB2_S2',lanes=lanes)
        # Additional projects
        if multiplexed_run:
            mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3',
                                               lanes=lanes)
            mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4',
                                               lanes=lanes)
        # Undetermined reads
        mock_illumina_data.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def test_illumina_data(self):
        """Read bcl2fastq2-style output with single project

        """
        self.makeMockIlluminaData()
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_paired_end(self):
        """Read bcl2fastq2-style output with single project & paired-end data

        """
        self.makeMockIlluminaData(paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects(self):
        """Read bcl2fastq2-style output with multiple projects

        """
        self.makeMockIlluminaData(multiple_projects=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects_paired_end(self):
        """Read bcl2fastq2-style output with multiple projects & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,])

    def test_illumina_data_multiple_projects_multiplexed(self):
        """Read bcl2fastq2-style output with multiple projects & multiplexing

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,4,5,])

    def test_illumina_data_multiple_projects_multiplexed_paired_end(self):
        """Read bcl2fastq2-style output with multiple projects, multiplexing & paired-end data

        """
        self.makeMockIlluminaData(multiple_projects=True,multiplexed_run=True,
                                  paired_end=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,4,5,])

    def test_illumina_data_no_lane_splitting(self):
        """Read bcl2fastq2-style output with single project (--no-lane-splitting)

        """
        self.makeMockIlluminaData(no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

    def test_illumina_data_paired_end_no_lane_splitting(self):
        """Read bcl2fastq2-style output with single project & paired-end data (--no-lane-splitting)

        """
        self.makeMockIlluminaData(paired_end=True,no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

    def test_illumina_data_multiple_projects_no_lane_splitting(self):
        """Read bcl2fastq2-style output with multiple projects (--no-lane-splitting)

        """
        self.makeMockIlluminaData(multiple_projects=True,no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

    def test_illumina_data_multiple_projects_paired_end_no_lane_splitting(self):
        """Read bcl2fastq2-style output with multiple projects & paired-end data (--no-lane-splitting)

        """
        self.makeMockIlluminaData(multiple_projects=True,paired_end=True,
                                  no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

class TestIlluminaDataForBcl2fastq2SpecialCases(BaseTestIlluminaData):
    """
    Tests for IlluminaData, IlluminaProject and IlluminaSample for special cases of bcl2fastq2-style output

    """
    def setUp(self):
        # Create a container for the test directories
        self.top_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.top_dir)
        except Exception:
            pass

    def makeMockIlluminaDataIdsDiffer(self,ids_differ_for_all=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              'bcl2fastq2',
                                              paired_end=True,
                                              top_dir=self.top_dir)
        lanes=(1,2,)
        # Add projects
        mock_illumina_data.add_fastq_batch('AB','AB1','AB1_input_S1',
                                           lanes=lanes)
        mock_illumina_data.add_fastq_batch('AB','AB2','AB2_chip_S2',
                                           lanes=lanes)
        if ids_differ_for_all:
            mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_rep1_S3',
                                               lanes=lanes)
            mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_rep2_S4',
                                               lanes=lanes)
        else:
            mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3',
                                               lanes=lanes)
            mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4',
                                               lanes=lanes)
        # Undetermined reads
        mock_illumina_data.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def makeMockIlluminaDataOnlyUndetermined(self,no_lane_splitting=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              'bcl2fastq2',
                                              paired_end=True,
                                              no_lane_splitting=no_lane_splitting,
                                              top_dir=self.top_dir)
        # Add undetermined reads
        mock_illumina_data.add_undetermined(lanes=[1,2,3,4])
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def makeMockIlluminaDataSingleSampleNoUndetermined(self,no_lane_splitting=False):
        # Create initial mock dir
        mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                              'bcl2fastq2',
                                              paired_end=True,
                                              no_lane_splitting=no_lane_splitting,
                                              top_dir=self.top_dir)
        # Add projects
        mock_illumina_data.add_fastq_batch('KL','KL_all','KL_all_S1',
                                           lanes=[1,2,3,4])
        # Create and finish
        self.mock_illumina_data = mock_illumina_data
        self.mock_illumina_data.create()

    def makeNonIlluminaDataDirectoryWithFastqs(self):
        # Create a non-bcl2fastq directory which looks like
        # a BCF-style 'analysis project'
        os.mkdir(os.path.join(self.top_dir,'test.MockIlluminaData'))
        os.mkdir(os.path.join(self.top_dir,'test.MockIlluminaData','fastqs'))
        for fq in ('PJ1_S1_L001_R1_001.fastq.gz',
                   'PJ1_S1_L001_R2_001.fastq.gz',
                   'PJ2_S2_L001_R1_001.fastq.gz',
                   'PJ2_S2_L001_R2_001.fastq.gz',):
            open(os.path.join(self.top_dir,
                              'test.MockIlluminaData',
                              'fastqs',fq),'w').write('')
        return os.path.join(self.top_dir,'test.MockIlluminaData')

    def makeNonIlluminaDataDirectoryWithNonCanonicalFastqs(self):
        # Create a non-bcl2fastq directory which contains
        # Fastq files with non-canonical-style names
        os.mkdir(os.path.join(self.top_dir,'test.MockIlluminaData'))
        os.mkdir(os.path.join(self.top_dir,'test.MockIlluminaData','fastqs'))
        for fq in ('PB04_S4_R1_unpaired.fastq.gz',
                   'PB04_trimmoPE_bowtie2_notHg38.1.fastq.gz'):
            open(os.path.join(self.top_dir,
                              'test.MockIlluminaData',
                              'fastqs',fq),'w').write('')
        return os.path.join(self.top_dir,'test.MockIlluminaData')

    def test_illumina_data_all_sample_ids_differ_from_sample_names(self):
        """Read bcl2fastq2 output when all sample ids differ from names

        """
        self.makeMockIlluminaDataIdsDiffer(ids_differ_for_all=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,2])

    def test_illumina_data_some_sample_ids_differ_from_sample_names(self):
        """Read bcl2fastq2 output when some sample ids differ from names

        """
        self.makeMockIlluminaDataIdsDiffer(ids_differ_for_all=False)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[1,2])

    def test_illumina_data_only_undetermined_fastqs(self):
        """Read bcl2fastq2 output with only undetermined fastqs
        """
        self.makeMockIlluminaDataOnlyUndetermined(no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

    def test_illumina_data_single_sample_no_undetermined_fastqs(self):
        """Read bcl2fastq2 output with single sample and no undetermined fastqs
        """
        self.makeMockIlluminaDataSingleSampleNoUndetermined(no_lane_splitting=True)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertIlluminaData(illumina_data,self.mock_illumina_data)
        self.assertEqual(illumina_data.format,'bcl2fastq2')
        self.assertEqual(illumina_data.lanes,[None,])

    def test_illumina_data_not_bcl2fastq2_output(self):
        """Reading non-bcl2fastq v2 output directory raises exception
        """
        # Attempt to read the directory as if it were the output
        # from bcl2fastq v2
        dirn = self.makeNonIlluminaDataDirectoryWithFastqs()
        self.assertRaises(IlluminaDataError,IlluminaData,
                          os.path.dirname(dirn),
                          unaligned_dir=os.path.basename(dirn))

    def test_illumina_data_not_bcl2fastq2_output_non_canonical_fastqs(self):
        """Reading non-bcl2fastq v2 output directory with non-canonical Fastqs raises exception
        """
        # Attempt to read the directory as if it were the output
        # from bcl2fastq v2
        dirn = self.makeNonIlluminaDataDirectoryWithNonCanonicalFastqs()
        self.assertRaises(IlluminaDataError,IlluminaData,
                          os.path.dirname(dirn),
                          unaligned_dir=os.path.basename(dirn))

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
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_with_path_and_extension(self):
        """Check extraction of name components with leading path and extension

        """
        fastq_name = '/home/galaxy/NA10831_ATCACG_L002_R1_001.fastq.gz'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),'NA10831_ATCACG_L002_R1_001')

    def test_illumina_fastq_r2(self):
        """Check extraction of fastq name components for R2 read

        """
        fastq_name = 'NA10831_ATCACG_L002_R2_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,2)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_no_index(self):
        """Check extraction of fastq name components without a barcode

        """
        fastq_name = 'NA10831_NoIndex_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_dual_index(self):
        """Check extraction of fastq name components with dual index

        """
        fastq_name = 'NA10831_ATCACG-GCACTA_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,None)
        self.assertEqual(fq.barcode_sequence,'ATCACG-GCACTA')
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_from_bcl2fastq2(self):
        """
        Check extraction of fastq name components for bcl2fastq2 output

        """
        fastq_name = 'NA10831_S7_L002_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,7)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,2)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_from_bcl2fastq2_no_lane(self):
        """
        Check extraction of fastq name components for bcl2fastq2 output (no lane)

        """
        fastq_name = 'NA10831_S7_R1_001'
        fq = IlluminaFastq(fastq_name)
        self.assertEqual(fq.fastq,fastq_name)
        self.assertEqual(fq.sample_name,'NA10831')
        self.assertEqual(fq.sample_number,7)
        self.assertEqual(fq.barcode_sequence,None)
        self.assertEqual(fq.lane_number,None)
        self.assertEqual(fq.read_number,1)
        self.assertEqual(fq.set_number,1)
        self.assertEqual(str(fq),fastq_name)

    def test_illumina_fastq_for_non_canonical_fastq_names(self):
        """
        Check non-canonical Fastq names raise IlluminaDataError
        """
        fastq_name = 'PB04_S4_R1_unpaired.fastq.gz'
        self.assertRaises(IlluminaDataError,IlluminaFastq,fastq_name)
        fastq_name = 'PB04_trimmoPE_bowtie2_notHg38.1.fastq.gz'
        self.assertRaises(IlluminaDataError,IlluminaFastq,fastq_name)

class TestSampleSheet(unittest.TestCase):
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
        self.casava_sample_sheet_content = """FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
DADA331XX,1,PhiX,PhiX control,,Control,,,Peter,Control
DADA331XX,2,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,3,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,4,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,5,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,6,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,7,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,8,PhiX,PhiX control,,Control,,,Peter,Control
"""
        self.hiseq_sample_sheet_id_and_name_differ_content = """[Header],,,,,,,,,,
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
1,PJB1,PJB1-1579,,,N701,CGATGTAT ,N501,TCTTTCCC,PeterBriggs,
1,PJB2,PJB2-1580,,,N702,TGACCAAT ,N502,TCTTTCCC,PeterBriggs,
"""

    def test_load_hiseq_sample_sheet(self):
        """SampleSheet: load a HiSEQ IEM-format sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        # Check format
        self.assertEqual(iem.format,'IEM')
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
        """SampleSheet: reconstruct a HiSEQ sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
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
        """SampleSheet: convert HISeq IEM4 sample sheet to CASAVA format

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        expected = """FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
FC0001,1,PJB1-1579,,CGATGTAT-TCTTTCCC,,,,,PeterBriggs
FC0001,1,PJB2-1580,,TGACCAAT-TCTTTCCC,,,,,PeterBriggs
"""
        for l1,l2 in zip(iem.show(fmt='CASAVA').split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_hiseq_predict_output(self):
        """SampleSheet: check predicted outputs for HISeq IEM4 sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        output = iem.predict_output()
        self.assertTrue('Project_PeterBriggs' in output)
        self.assertTrue('Sample_PJB1-1579' in output['Project_PeterBriggs'])
        self.assertTrue('Sample_PJB2-1580' in output['Project_PeterBriggs'])
        self.assertEqual(output['Project_PeterBriggs']['Sample_PJB1-1579'],
                         ['PJB1-1579_CGATGTAT-TCTTTCCC_L001',])
        self.assertEqual(output['Project_PeterBriggs']['Sample_PJB2-1580'],
                         ['PJB2-1580_TGACCAAT-TCTTTCCC_L001',])
    def test_hiseq_predict_output_bcl2fastq2(self):
        """SampleSheet: check predicted bcl2fastq2 outputs for HISeq IEM4 sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PeterBriggs' in output)
        self.assertEqual(output['PeterBriggs'],
                         ['PJB1-1579_S1_L001','PJB2-1580_S2_L001',])
    def test_load_miseq_sample_sheet(self):
        """SampleSheet: load a MiSEQ sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        # Check format
        self.assertEqual(iem.format,'IEM')
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
        """SampleSheet: reconstruct a MiSEQ sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        expected = self.miseq_sample_sheet_content
        for l1,l2 in zip(iem.show().split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_convert_miseq_sample_sheet_to_casava(self):
        """SampleSheet: convert MISeq IEM4 sample sheet to CASAVA format

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        expected = """FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
FC0001,1,A8,,TAAGGCGA-TAGATCGC,,,,,PJB
FC0001,1,B8,,CGTACTAG-TAGATCGC,,,,,PJB
"""
        for l1,l2 in zip(iem.show(fmt='CASAVA').split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_miseq_predict_output(self):
        """SampleSheet: check predicted outputs for MISeq IEM4 sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        output = iem.predict_output()
        self.assertTrue('Project_PJB' in output)
        self.assertTrue('Sample_A8' in output['Project_PJB'])
        self.assertTrue('Sample_B8' in output['Project_PJB'])
        self.assertEqual(output['Project_PJB']['Sample_A8'],
                         ['A8_TAAGGCGA-TAGATCGC_L001',])
        self.assertEqual(output['Project_PJB']['Sample_B8'],
                         ['B8_CGTACTAG-TAGATCGC_L001',])
    def test_miseq_predict_output_bcl2fastq2(self):
        """SampleSheet: check predicted bcl2fastq2 outputs for MISeq IEM4
        sample sheet

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PJB' in output)
        self.assertEqual(output['PJB'],
                         ['A8_S1','B8_S2',])
    def test_load_casava_sample_sheet(self):
        """SampleSheet: load a CASAVA-style sample sheet

        """
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        # Check format
        self.assertEqual(casava.format,'CASAVA')
        # Check header
        self.assertEqual(casava.header_items,[])
        # Check reads
        self.assertEqual(casava.reads,[])
        # Check settings
        self.assertEqual(casava.settings_items,[])
        # Check data
        self.assertEqual(casava.data.header(),['FCID','Lane',
                                               'SampleID','SampleRef',
                                               'Index','Description',
                                               'Control','Recipe',
                                               'Operator','SampleProject'])
        self.assertEqual(len(casava.data),8)
        self.assertEqual(casava.data[0]['FCID'],'DADA331XX')
        self.assertEqual(casava.data[0]['Lane'],1)
        self.assertEqual(casava.data[0]['SampleID'],'PhiX')
        self.assertEqual(casava.data[0]['SampleRef'],'PhiX control')
        self.assertEqual(casava.data[0]['Index'],'')
        self.assertEqual(casava.data[0]['Description'],'Control')
        self.assertEqual(casava.data[0]['Control'],'')
        self.assertEqual(casava.data[0]['Recipe'],'')
        self.assertEqual(casava.data[0]['Operator'],'Peter')
        self.assertEqual(casava.data[0]['SampleProject'],'Control')
        self.assertEqual(casava.data[1]['FCID'],'DADA331XX')
        self.assertEqual(casava.data[1]['Lane'],2)
        self.assertEqual(casava.data[1]['SampleID'],'884-1')
        self.assertEqual(casava.data[1]['SampleRef'],'PB-884-1')
        self.assertEqual(casava.data[1]['Index'],'AGTCAA')
        self.assertEqual(casava.data[1]['Description'],'RNA-seq')
        self.assertEqual(casava.data[1]['Control'],'')
        self.assertEqual(casava.data[1]['Recipe'],'')
        self.assertEqual(casava.data[1]['Operator'],'Peter')
        self.assertEqual(casava.data[1]['SampleProject'],'AR')
    def test_show_casava_sample_sheet(self):
        """SampleSheet: reconstruct a CASAVA sample sheet

        """
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        expected = self.casava_sample_sheet_content
        for l1,l2 in zip(casava.show().split(),expected.split()):
            self.assertEqual(l1,l2)
    def test_casava_predict_output(self):
        """SampleSheet: check predicted outputs for CASAVA sample sheet

        """
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        output = casava.predict_output()
        self.assertTrue('Project_Control' in output)
        self.assertTrue('Sample_PhiX' in output['Project_Control'])
        self.assertEqual(output['Project_Control']['Sample_PhiX'],
                         ['PhiX_NoIndex_L001',
                          'PhiX_NoIndex_L008'])
        self.assertTrue('Project_AR' in output)
        self.assertTrue('Sample_884-1' in output['Project_AR'])
        self.assertTrue('Sample_885-1' in output['Project_AR'])
        self.assertTrue('Sample_886-1' in output['Project_AR'])
        self.assertEqual(output['Project_AR']['Sample_884-1'],
                         ['884-1_AGTCAA_L002',
                          '884-1_AGTCAA_L005'])
        self.assertEqual(output['Project_AR']['Sample_885-1'],
                         ['885-1_AGTTCC_L003',
                          '885-1_AGTTCC_L006'])
        self.assertEqual(output['Project_AR']['Sample_886-1'],
                         ['886-1_ATGTCA_L004',
                          '886-1_ATGTCA_L007'])
    def test_hiseq_predict_output_bcl2fastq2_id_and_names_differ(self):
        """SampleSheet: check predicted bcl2fastq2 outputs for HISeq IEM4 sample sheet when id and names differ

        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_id_and_name_differ_content))
        output = iem.predict_output(fmt='bcl2fastq2')
        self.assertTrue('PeterBriggs' in output)
        self.assertEqual(output['PeterBriggs'],
                         ['PJB1/PJB1-1579_S1_L001','PJB2/PJB2-1580_S2_L001',])
    def test_len(self):
        """SampleSheet: test __len__ built-in

        """
        empty = SampleSheet()
        self.assertEqual(len(empty),0)
        hiseq = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(len(hiseq),2)
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        self.assertEqual(len(casava),8)
    def test_iter(self):
        """SampleSheet: test __iter__ built-in

        """
        hiseq = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        for line0,line1 in zip(hiseq,hiseq.data):
            self.assertEqual(line0,line1)
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        for line0,line1 in zip(casava,casava.data):
            self.assertEqual(line0,line1)
    def test_getitem(self):
        """SampleSheet: test __getitem__ built-in

        """
        hiseq = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(hiseq[0],hiseq.data[0])
        self.assertEqual(hiseq[1],hiseq.data[1])
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        self.assertEqual(casava[0],casava.data[0])
        self.assertEqual(casava[2],casava.data[2])
        self.assertEqual(casava[7],casava.data[7])
    def test_setitem(self):
        """SampleSheet: test __setitem__ built-in

        """
        hiseq = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        hiseq[0]['Sample_ID'] = 'NewSample1'
        self.assertEqual(hiseq[0]['Sample_ID'],'NewSample1')
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        casava[0]['SampleID'] = 'NewSample2'
        self.assertEqual(casava[0]['SampleID'],'NewSample2')
    def test_append(self):
        """SampleSheet: test append method

        """
        hiseq = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        self.assertEqual(len(hiseq),2)
        new_line = hiseq.append()
        self.assertEqual(len(hiseq),3)
    def test_write_iem(self):
        """SampleSheet: write out IEM formatted sample sheet

        """
        miseq = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        fp=cStringIO.StringIO()
        miseq.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.miseq_sample_sheet_content)
    def test_write_casava(self):
        """SampleSheet: write out CASAVA formatted sample sheet

        """
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        fp=cStringIO.StringIO()
        casava.write(fp=fp)
        self.assertEqual(fp.getvalue(),self.casava_sample_sheet_content)
    def test_bad_input_unrecognised_section(self):
        """SampleSheet: raises exception for input with unrecognised section

        """
        fp = cStringIO.StringIO("""[Header]
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaDataError,SampleSheet,fp=fp)
    def test_bad_input_not_sample_sheet(self):
        """SampleSheet: raises exception for non-IEM formatted input

        """
        fp = cStringIO.StringIO("""Something random
IEMFileVersion,4
Date,06/03/2014

[Footer]
This,isTheEnd
""")
        self.assertRaises(IlluminaDataError,SampleSheet,fp=fp)
    def test_duplicates_in_iem_format(self):
        """
        SampleSheet: check & fix duplicated names in IEM sample sheet

        """
        # Set up
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(iem.duplicated_names),0)
        # Create 3 duplicates by resetting lane numbers
        iem.data[1]['Sample_ID'] = iem.data[0]['Sample_ID']
        iem.data[1]['Sample_Name'] = iem.data[0]['Sample_Name']
        iem.data[1]['index'] = iem.data[0]['index']
        iem.data[1]['index2'] = iem.data[0]['index2']
        iem.data[1]['Sample_Project'] = iem.data[0]['Sample_Project']
        self.assertEqual(len(iem.duplicated_names),1)
        # Fix and check again (should be none)
        iem.fix_duplicated_names()
        self.assertEqual(iem.duplicated_names,[])
    def test_duplicates_in_iem_format_no_lanes(self):
        """
        SampleSheet: check & fix duplicated names in IEM sample sheet (no lanes)

        """
        # Set up
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(iem.duplicated_names),0)
        # Create duplicates by resetting sample names and projects
        iem.data[1]['Sample_ID'] = iem.data[0]['Sample_ID']
        iem.data[1]['Sample_Name'] = iem.data[0]['Sample_Name']
        iem.data[1]['index'] = iem.data[0]['index']
        iem.data[1]['index2'] = iem.data[0]['index2']
        iem.data[1]['Sample_Project'] = iem.data[0]['Sample_Project']
        self.assertEqual(len(iem.duplicated_names),1)
        # Fix and check again (should be none)
        iem.fix_duplicated_names()
        self.assertEqual(iem.duplicated_names,[])
    def test_illegal_names_in_iem_format(self):
        """
        SampleSheet: check for illegal characters in IEM sample sheet

        """
        # Set up and introduce bad names
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        iem.data[0]['Sample_ID'] = 'PJB1 1579'
        iem.data[0]['Sample_Name'] = 'PJB1 1579'
        iem.data[1]['Sample_Project'] = "PeterBriggs?"
        # Check for illegal names
        self.assertEqual(len(iem.illegal_names),2)
        # Fix and check again
        iem.fix_illegal_names()
        self.assertEqual(iem.illegal_names,[])
        # Verify that character replacement worked correctly
        self.assertEqual(iem.data[0]['Sample_ID'],'PJB1_1579')
        self.assertEqual(iem.data[0]['Sample_Name'],'PJB1_1579')
        self.assertEqual(iem.data[1]['Sample_Project'],"PeterBriggs")
    def test_empty_names_in_iem_format(self):
        """
        SampleSheet: check for empty sample/project names in IEM sample sheet

        """
        # Set up and introduce bad names
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        iem.data[0]['Sample_ID'] = ''
        iem.data[1]['Sample_Project'] = ''
        # Check for empty names
        self.assertEqual(len(iem.empty_names),2)
    def test_duplicates_in_casava_format(self):
        """
        SampleSheet: check and fix duplicated names in CASAVA sample sheet

        """
        # Set up
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        # Shouldn't find any duplicates when lanes are different
        self.assertEqual(len(casava.duplicated_names),0)
        # Create 3 duplicates by resetting lane numbers
        casava.data[4]['Lane'] = 2
        casava.data[5]['Lane'] = 3
        casava.data[6]['Lane'] = 4
        self.assertEqual(len(casava.duplicated_names),3)
        # Fix and check again (should be none)
        casava.fix_duplicated_names()
        self.assertEqual(casava.duplicated_names,[])
    def test_illegal_names_in_casava_format(self):
        """
        SampleSheet: check for illegal characters in CASAVA sample sheet

        """
        # Set up and introduce bad names
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        casava.data[3]['SampleID'] = '886 1'
        casava.data[4]['SampleProject'] = "AR?"
        # Check for illegal names
        self.assertEqual(len(casava.illegal_names),2)
        # Fix and check again
        casava.fix_illegal_names()
        self.assertEqual(casava.illegal_names,[])
        # Verify that character replacement worked correctly
        self.assertEqual(casava.data[3]['SampleID'],'886_1')
        self.assertEqual(casava.data[4]['SampleProject'],"AR")
    def test_empty_names_in_casava_format(self):
        """
        SampleSheet: check for empty sample/project names in CASAVA sample sheet

        """
        # Set up and introduce bad names
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        casava.data[3]['SampleID'] = ''
        casava.data[4]['SampleProject'] = ""
        # Check for illegal names
        self.assertEqual(len(casava.empty_names),2)
    def test_sample_sheet_with_missing_data_section(self):
        """SampleSheet: handle IEM sample sheet with missing 'Data' section

        """
        contents = """[Header]
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
"""
        iem = SampleSheet(fp=cStringIO.StringIO(contents))
        for l1,l2 in zip(iem.show().split(),contents.split()):
            self.assertEqual(l1,l2)
        self.assertEqual(iem.column_names,[])
        self.assertEqual(iem.duplicated_names,[])
        self.assertEqual(iem.illegal_names,[])
        self.assertEqual(iem.empty_names,[])
        self.assertFalse(iem.has_lanes)

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

class TestSampleSheetPredictor(unittest.TestCase):
    def setUp(self):
        self.hiseq_sample_sheet_content = """[Header]
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
2,PJB1-1579,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
2,PJB2-1580,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
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
        self.casava_sample_sheet_content = """FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,SampleProject
DADA331XX,1,PhiX,PhiX control,CTGCCT,Control,,,Peter,Control
DADA331XX,2,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,3,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,4,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,5,884-1,PB-884-1,AGTCAA,RNA-seq,,,Peter,AR
DADA331XX,6,885-1,PB-885-1,AGTTCC,RNA-seq,,,Peter,AR
DADA331XX,7,886-1,PB-886-1,ATGTCA,RNA-seq,,,Peter,AR
DADA331XX,8,PhiX,PhiX control,CTGCCT,Control,,,Peter,Control
"""
        self.hiseq_sample_sheet_id_and_name_differ_content = """[Header]
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
1,PJB1,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
1,PJB2,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
2,PJB1,PJB1-1579,,,N701,CGATGTAT,N501,TCTTTCCC,PeterBriggs,
2,PJB2,PJB2-1580,,,N702,TGACCAAT,N502,TCTTTCCC,PeterBriggs,
"""

        self.hiseq_sample_sheet_no_barcodes = """[Header]
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
1,PJB1,PJB1,,,,,,,PeterBriggs,
2,PJB2,PJB2,,,,,,,PeterBriggs,
"""

    def test_samplesheet_predictor_iem_with_lanes(self):
        """SampleSheetPredictor: handle IEM4 sample sheet with lanes
        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 with no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end
        predictor.set(package="bcl2fastq2",
                      paired_end=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1-1579_S1_L001_R2_001.fastq.gz",
                          "PJB1-1579_S1_L002_R1_001.fastq.gz",
                          "PJB1-1579_S1_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2-1580_S2_L001_R2_001.fastq.gz",
                          "PJB2-1580_S2_L002_R1_001.fastq.gz",
                          "PJB2-1580_S2_L002_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_S1_R1_001.fastq.gz",
                          "PJB1-1579_S1_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_S2_R1_001.fastq.gz",
                          "PJB2-1580_S2_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.dir_name,"Sample_PJB1")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_PJB2")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        predictor.set(package="casava",
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.dir_name,"Sample_PJB1")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L001_R2_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_PJB2")
        self.assertEqual(sample2.fastqs(),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L001_R2_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R2_001.fastq.gz"])

    def test_samplesheet_predictor_iem_no_lanes(self):
        """SampleSheetPredictor: handle IEM4 sample sheet with no lanes
        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.miseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PJB"])
        project = predictor.get_project("PJB")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["A8","B8"])
        sample1 = project.get_sample("A8")
        sample2 = project.get_sample("B8")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["TAAGGCGA-TAGATCGC"])
        self.assertEqual(sample2.barcode_seqs,["CGTACTAG-TAGATCGC"])
        self.assertEqual(sample1.lanes("TAAGGCGA-TAGATCGC"),[])
        self.assertEqual(sample2.lanes("CGTACTAG-TAGATCGC"),[])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 with no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_R1_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end
        predictor.set(package="bcl2fastq2",
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz",
                          "A8_S1_L001_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz",
                          "B8_S2_L001_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # no lane splitting
        predictor.set(package="bcl2fastq2",
                      no_lane_splitting=True,
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_R1_001.fastq.gz",
                          "A8_S1_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_R1_001.fastq.gz",
                          "B8_S2_R2_001.fastq.gz"])
        # Predict output fastqs bcl2fastq2 paired end with
        # explicitly specified lanes
        predictor.set(package="bcl2fastq2",
                      lanes=(1,2),
                      paired_end=True)
        self.assertEqual(project.dir_name,"PJB")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["A8_S1_L001_R1_001.fastq.gz",
                          "A8_S1_L001_R2_001.fastq.gz",
                          "A8_S1_L002_R1_001.fastq.gz",
                          "A8_S1_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["B8_S2_L001_R1_001.fastq.gz",
                          "B8_S2_L001_R2_001.fastq.gz",
                          "B8_S2_L002_R1_001.fastq.gz",
                          "B8_S2_L002_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(package="casava"),
                         ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        predictor.set(package="casava",
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L001_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(),
                         ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz",
                          "B8_CGTACTAG-TAGATCGC_L001_R2_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8* paired end
        # and explicitly specify lanes
        predictor.set(package="casava",
                      lanes=(1,2),
                      paired_end=True)
        self.assertEqual(project.dir_name,"Project_PJB")
        self.assertEqual(sample1.dir_name,"Sample_A8")
        self.assertEqual(sample1.fastqs(),
                         ["A8_TAAGGCGA-TAGATCGC_L001_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L001_R2_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L002_R1_001.fastq.gz",
                          "A8_TAAGGCGA-TAGATCGC_L002_R2_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_B8")
        self.assertEqual(sample2.fastqs(),
                          ["B8_CGTACTAG-TAGATCGC_L001_R1_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L001_R2_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L002_R1_001.fastq.gz",
                           "B8_CGTACTAG-TAGATCGC_L002_R2_001.fastq.gz"])

    def test_samplesheet_predictor_casava(self):
        """SampleSheetPredictor: handle CASAVA-style sample sheet
        """
        casava = SampleSheet(fp=cStringIO.StringIO(
            self.casava_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=casava)
        self.assertEqual(predictor.nprojects,2)
        self.assertEqual(predictor.project_names,["AR","Control"])
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get projects
        project1 = predictor.get_project("Control")
        project2 = predictor.get_project("AR")
        self.assertEqual(project1.sample_ids,["PhiX"])
        self.assertEqual(project2.sample_ids,["884-1","885-1","886-1"])
        # Get samples
        sample1 = project1.get_sample("PhiX")
        sample2 = project2.get_sample("884-1")
        sample3 = project2.get_sample("885-1")
        sample4 = project2.get_sample("886-1")
        self.assertRaises(KeyError,project1.get_sample,"DoesntExist")
        self.assertRaises(KeyError,project2.get_sample,"DoesntExist")
        # Check assigned barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CTGCCT"])
        self.assertEqual(sample2.barcode_seqs,["AGTCAA"])
        self.assertEqual(sample3.barcode_seqs,["AGTTCC"])
        self.assertEqual(sample4.barcode_seqs,["ATGTCA"])
        self.assertEqual(sample1.lanes("CTGCCT"),[1,8])
        self.assertEqual(sample2.lanes("AGTCAA"),[2,5])
        self.assertEqual(sample3.lanes("AGTTCC"),[3,6])
        self.assertEqual(sample4.lanes("ATGTCA"),[4,7])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        self.assertEqual(sample3.s_index,3)
        self.assertEqual(sample4.s_index,4)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project1.dir_name,"Control")
        self.assertEqual(project2.dir_name,"AR")
        self.assertEqual(sample1.dir_name,None)
        self.assertEqual(sample1.fastqs(),
                         ["PhiX_S1_L001_R1_001.fastq.gz",
                          "PhiX_S1_L008_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,None)
        self.assertEqual(sample2.fastqs(),
                         ["884-1_S2_L002_R1_001.fastq.gz",
                          "884-1_S2_L005_R1_001.fastq.gz"])
        self.assertEqual(sample3.dir_name,None)
        self.assertEqual(sample3.fastqs(),
                         ["885-1_S3_L003_R1_001.fastq.gz",
                          "885-1_S3_L006_R1_001.fastq.gz"])
        self.assertEqual(sample4.dir_name,None)
        self.assertEqual(sample4.fastqs(),
                         ["886-1_S4_L004_R1_001.fastq.gz",
                          "886-1_S4_L007_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project1.dir_name,"Project_Control")
        self.assertEqual(project2.dir_name,"Project_AR")
        self.assertEqual(sample1.dir_name,"Sample_PhiX")
        self.assertEqual(sample1.fastqs(),
                         ["PhiX_CTGCCT_L001_R1_001.fastq.gz",
                          "PhiX_CTGCCT_L008_R1_001.fastq.gz"])
        self.assertEqual(sample2.dir_name,"Sample_884-1")
        self.assertEqual(sample2.fastqs(),
                         ["884-1_AGTCAA_L002_R1_001.fastq.gz",
                          "884-1_AGTCAA_L005_R1_001.fastq.gz"])
        self.assertEqual(sample3.dir_name,"Sample_885-1")
        self.assertEqual(sample3.fastqs(),
                         ["885-1_AGTTCC_L003_R1_001.fastq.gz",
                          "885-1_AGTTCC_L006_R1_001.fastq.gz"])
        self.assertEqual(sample4.dir_name,"Sample_886-1")
        self.assertEqual(sample4.fastqs(),
                         ["886-1_ATGTCA_L004_R1_001.fastq.gz",
                          "886-1_ATGTCA_L007_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_id_and_names_differ(self):
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_id_and_name_differ_content))
        """SampleSheetPredictor: handle IEM4 sample sheet with lanes
        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_content))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1-1579","PJB2-1580"])
        sample1 = project.get_sample("PJB1-1579")
        sample2 = project.get_sample("PJB2-1580")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,["CGATGTAT-TCTTTCCC"])
        self.assertEqual(sample2.barcode_seqs,["TGACCAAT-TCTTTCCC"])
        self.assertEqual(sample1.lanes("CGATGTAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample2.lanes("TGACCAAT-TCTTTCCC"),[1,2])
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1/PJB1-1579_S1_L001_R1_001.fastq.gz",
                          "PJB1/PJB1-1579_S1_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2/PJB2-1580_S2_L001_R1_001.fastq.gz",
                          "PJB2/PJB2-1580_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1-1579_CGATGTAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB1-1579_CGATGTAT-TCTTTCCC_L002_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(package="casava"),
                         ["PJB2-1580_TGACCAAT-TCTTTCCC_L001_R1_001.fastq.gz",
                          "PJB2-1580_TGACCAAT-TCTTTCCC_L002_R1_001.fastq.gz"])

    def test_samplesheet_predictor_iem_no_barcodes(self):
        """SampleSheetPredictor: handle IEM4 sample sheet with lanes
        """
        iem = SampleSheet(fp=cStringIO.StringIO(
            self.hiseq_sample_sheet_no_barcodes))
        predictor = SampleSheetPredictor(sample_sheet=iem)
        # Get projects
        self.assertEqual(predictor.nprojects,1)
        self.assertEqual(predictor.project_names,["PeterBriggs"])
        project = predictor.get_project("PeterBriggs")
        self.assertRaises(KeyError,predictor.get_project,"DoesntExist")
        # Get samples
        self.assertEqual(project.sample_ids,["PJB1","PJB2"])
        sample1 = project.get_sample("PJB1")
        sample2 = project.get_sample("PJB2")
        self.assertRaises(KeyError,project.get_sample,"DoesntExist")
        # Check sample barcodes and lanes
        self.assertEqual(sample1.barcode_seqs,[])
        self.assertEqual(sample2.barcode_seqs,[])
        self.assertEqual(sample1.lanes(),(1,))
        self.assertEqual(sample2.lanes(),(2,))
        self.assertEqual(sample1.s_index,1)
        self.assertEqual(sample2.s_index,2)
        # Predict output fastqs bcl2fastq2
        predictor.set(package="bcl2fastq2")
        self.assertEqual(project.dir_name,"PeterBriggs")
        self.assertEqual(sample1.fastqs(),
                         ["PJB1_S1_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(),
                         ["PJB2_S2_L002_R1_001.fastq.gz"])
        # Predict output fastqs CASAVA/bcl2fastq 1.8*
        predictor.set(package="casava")
        self.assertEqual(project.dir_name,"Project_PeterBriggs")
        self.assertEqual(sample1.fastqs(package="casava"),
                         ["PJB1_NoIndex_L001_R1_001.fastq.gz"])
        self.assertEqual(sample2.fastqs(package="casava"),
                         ["PJB2_NoIndex_L002_R1_001.fastq.gz"])
    
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

class TestVerifyRunAgainstCasavaSampleSheet(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'casava',paired_end=True,
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
        """Verify sample sheet against a matching CASAVA run
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_project(self):
        """Verify sample sheet against a CASAVA run with a missing project
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "Project_AB"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_sample(self):
        """Verify sample sheet against a CASAVA run with a missing sample
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "Project_AB","Sample_AB1"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_fastq(self):
        """Verify sample sheet against a CASAVA run with a missing fastq file
        """
        os.remove(os.path.join(self.mock_illumina_data.dirn,
                               self.mock_illumina_data.unaligned_dir,
                               "Project_CDE","Sample_CDE4",
                               "CDE4_AGTCAA_L002_R2_001.fastq.gz"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

class TestVerifyRunAgainstBcl2fastq2SampleSheet(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'bcl2fastq2',paired_end=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_S1',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_S2',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3',lanes=(2,3))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4',lanes=(2,3))
        self.mock_illumina_data.add_undetermined(lanes=(1,2,3))
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""[Header]

[Reads]

[Settings]

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
1,AB1,AB1,,,N0,GCCAAT,AB,
1,AB2,AB2,,,N1,AGTCAA,AB,
2,CDE3,CDE3,,,N2,GCCAAT,CDE,
2,CDE4,CDE4,,,N3,AGTCAA,CDE,
3,CDE3,CDE3,,,N2,GCCAAT,CDE,
3,CDE4,CDE4,,,N3,AGTCAA,CDE,""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_sample_sheet(self):
        """Verify sample sheet against a matching bcl2fastq2 run
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_project(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing project
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "AB"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                         self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_sample(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing sample
        """
        for f in os.listdir(os.path.join(self.mock_illumina_data.dirn,
                                         self.mock_illumina_data.unaligned_dir,
                                         "AB")):
            print f
            if f.startswith("AB1"):
                fq = os.path.join(self.mock_illumina_data.dirn,
                                  self.mock_illumina_data.unaligned_dir,
                                  "AB",f)
                print "Removing %s" % fq
                os.remove(fq)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_fastq(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing fastq file
        """
        os.remove(os.path.join(self.mock_illumina_data.dirn,
                               self.mock_illumina_data.unaligned_dir,
                               "CDE","CDE4_S4_L002_R2_001.fastq.gz"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

class TestVerifyRunAgainstBcl2fastq2SampleSheetNoLaneSplitting(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'bcl2fastq2',
                                                   paired_end=True,
                                                   no_lane_splitting=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_S1')
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_S2')
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3')
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4')
        self.mock_illumina_data.add_undetermined()
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""[Header]

[Reads]

[Settings]

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
AB1,AB1,,,N0,GCCAAT,AB,
AB2,AB2,,,N1,AGTCAA,AB,
CDE3,CDE3,,,N2,GCCAAT,CDE,
CDE4,CDE4,,,N3,AGTCAA,CDE,""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_sample_sheet(self):
        """Verify sample sheet against a matching bcl2fastq2 run (--no-lane-splitting)
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_project(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing project (--no-lane-splitting)
        """
        shutil.rmtree(os.path.join(self.mock_illumina_data.dirn,
                                   self.mock_illumina_data.unaligned_dir,
                                   "AB"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                         self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_sample(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing sample (--no-lane-splitting)
        """
        for f in os.listdir(os.path.join(self.mock_illumina_data.dirn,
                                         self.mock_illumina_data.unaligned_dir,
                                         "AB")):
            print f
            if f.startswith("AB1"):
                fq = os.path.join(self.mock_illumina_data.dirn,
                                  self.mock_illumina_data.unaligned_dir,
                                  "AB",f)
                print "Removing %s" % fq
                os.remove(fq)
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

    def test_verify_run_against_sample_sheet_with_missing_fastq(self):
        """Verify sample sheet against a bcl2fastq2 run with a missing fastq file (--no-lane-splitting)
        """
        os.remove(os.path.join(self.mock_illumina_data.dirn,
                               self.mock_illumina_data.unaligned_dir,
                               "CDE","CDE4_S4_R2_001.fastq.gz"))
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertFalse(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

class TestVerifyRunAgainstBcl2fastq2MultiLaneSampleSheetNoLaneSplitting(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'bcl2fastq2',
                                                   no_lane_splitting=True,
                                                   paired_end=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_S1',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_S2',lanes=(1,))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3',lanes=(2,3))
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4',lanes=(2,3))
        self.mock_illumina_data.add_undetermined(lanes=(1,2,3))
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""[Header]

[Reads]

[Settings]

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
1,AB1,AB1,,,N0,GCCAAT,AB,
1,AB2,AB2,,,N1,AGTCAA,AB,
2,CDE3,CDE3,,,N2,GCCAAT,CDE,
2,CDE4,CDE4,,,N3,AGTCAA,CDE,
3,CDE3,CDE3,,,N2,GCCAAT,CDE,
3,CDE4,CDE4,,,N3,AGTCAA,CDE,""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_multi_lane_sample_sheet(self):
        """Verify multi-lane sample sheet against a matching bcl2fastq2 run (--no-lane-splitting)
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

class TestVerifyRunAgainstBcl2fastq2SampleSheetSampleNamesAreIntegers(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'bcl2fastq2',
                                                   paired_end=True,
                                                   no_lane_splitting=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('12970','12970','12970_S1')
        self.mock_illumina_data.add_fastq_batch('12513','12513','12513_S2')
        self.mock_illumina_data.add_undetermined()
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""[Header]

[Reads]

[Settings]

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
12970,12970,,,D711,AAAGATAC,D507,AAACCGTC,12970,
12513,12513,,,D710,TGGAGCTG,D508,AAACCGTC,12513,
""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_sample_sheet_names_are_integers(self):
        """Verify sample sheet against a matching bcl2fastq2 run (names are integers)
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))

class TestVerifyRunAgainstBcl2fastq2SampleSheetSpecialCases(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'bcl2fastq2',
                                                   paired_end=True,
                                                   no_lane_splitting=True,
                                                   top_dir=self.top_dir)
        self.mock_illumina_data.add_fastq_batch('AB','AB1','AB1_rep1_S1')
        self.mock_illumina_data.add_fastq_batch('AB','AB2','AB2_rep1_S2')
        self.mock_illumina_data.add_fastq_batch('CDE','CDE3','CDE3_S3')
        self.mock_illumina_data.add_fastq_batch('CDE','CDE4','CDE4_S4')
        self.mock_illumina_data.add_undetermined()
        self.mock_illumina_data.create()
        # Sample sheet
        fno,self.sample_sheet = tempfile.mkstemp()
        fp = os.fdopen(fno,'w')
        fp.write("""[Header]

[Reads]

[Settings]

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
AB1,AB1_rep1,,,N0,GCCAAT,AB,
AB2,AB2_rep1,,,N1,AGTCAA,AB,
CDE3,CDE3,,,N2,GCCAAT,CDE,
CDE4,CDE4,,,N3,AGTCAA,CDE,""")
        fp.close()

    def tearDown(self):
        # Remove the test directory
        if self.mock_illumina_data is not None:
            self.mock_illumina_data.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_run_against_sample_sheet_ids_and_names_differ(self):
        """Verify sample sheet against a matching bcl2fastq2 run (ids and names differ)
        """
        illumina_data = IlluminaData(self.mock_illumina_data.dirn)
        self.assertTrue(verify_run_against_sample_sheet(illumina_data,
                                                        self.sample_sheet))
    
class TestSummariseProjects(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_illumina_data = MockIlluminaData('test.MockIlluminaData',
                                                   'casava',paired_end=True,
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
                                                   'casava',paired_end=True,
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

class TestSampleSheetIndexSequence(unittest.TestCase):

    def test_casava_single_index(self):
        """samplesheet_index_sequence: check CASAVA sample sheet single index
        """
        line = TabDataLine(line="FC1,1,AB_control,,CGATGT,,,,,Control",
                           column_names=('FCID',
                                         'Lane',
                                         'SampleID',
                                         'SampleRef',
                                         'Index',
                                         'Description',
                                         'Control',
                                         'Recipe',
                                         'Operator',
                                         'SampleProject'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGATGT')

    def test_casava_dual_index(self):
        """samplesheet_index_sequence: check CASAVA sample sheet dual index
        """
        line = TabDataLine(line="FC1,1,C01,,TAAGGCGA-GCGTAAGA,,,,,KP",
                           column_names=('FCID',
                                         'Lane',
                                         'SampleID',
                                         'SampleRef',
                                         'Index',
                                         'Description',
                                         'Control',
                                         'Recipe',
                                         'Operator',
                                         'SampleProject'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'TAAGGCGA-GCGTAAGA')

    def test_iem_single_index(self):
        """samplesheet_index_sequence: check IEM4 sample sheet single index
        """
        line = TabDataLine(line="1,ABT1,ABT1,,,A002,CGATGT,AB,",
                           column_names=('Lane',
                                         'Sample_ID',
                                         'Sample_Name',
                                         'Sample_Plate',
                                         'Sample_Well',
                                         'I7_Index_ID',
                                         'index',
                                         'Sample_Project',
                                         'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGATGT')

    def test_iem_dual_index(self):
        """samplesheet_index_sequence: check IEM4 sample sheet dual index
        """
        line = TabDataLine(line="1,S1,S1,,,D701,CGTGTAGG,D501,GACCTGTA,HO,",
                           column_names=('Lane',
                                         'Sample_ID',
                                         'Sample_Name',
                                         'Sample_Plate',
                                         'Sample_Well',
                                         'I7_Index_ID',
                                         'index',
                                         'I5_Index_ID',
                                         'index2',
                                         'Sample_Project',
                                         'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),'CGTGTAGG-GACCTGTA')

    def test_iem_no_index(self):
        """samplesheet_index_sequence: check IEM4 sample sheet no index column
        """
        line = TabDataLine(line="PB2,PB2,,,PB,",
                         column_names=('Sample_ID',
                                       'Sample_Name',
                                       'Sample_Plate',
                                       'Sample_Well',
                                       'Sample_Project',
                                       'Description'),
                           delimiter=",")
        self.assertEqual(samplesheet_index_sequence(line),None)

class TestNormaliseBarcode(unittest.TestCase):
    def test_normalise_barcode(self):
        self.assertEqual(normalise_barcode('CGATGT'),'CGATGT')
        self.assertEqual(normalise_barcode('CGTGTAGG-GACCTGTA'),
                         'CGTGTAGGGACCTGTA')
        self.assertEqual(normalise_barcode('CGTGTAGG+GACCTGTA'),
                         'CGTGTAGGGACCTGTA')
        self.assertEqual(normalise_barcode('CGTGTAGGGACCTGTA'),
                         'CGTGTAGGGACCTGTA')

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
