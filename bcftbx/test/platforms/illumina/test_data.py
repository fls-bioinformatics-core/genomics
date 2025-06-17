#######################################################################
# Tests for illumina.data.py module
#######################################################################

from bcftbx.platforms.illumina.data import *
from bcftbx.platforms.illumina.samplesheet import SampleSheet
from bcftbx.mock import MockIlluminaRun
from bcftbx.mock import MockFastqDir
from bcftbx.mock import RunInfoXml
from bcftbx.mock import RunParametersXml
import unittest
import tempfile
import shutil

class TestRunDir(unittest.TestCase):
    """
    Tests for RunDir class
    """
    def setUp(self):
        # Create a temporary working directory
        self.top_dir = tempfile.mkdtemp()
        # Create a mock Illumina run directory
        self.mock_illumina_run = None

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.top_dir)
        except Exception:
            pass

    def test_rundir_miseq(self):
        """
        RunDir: test for MiSEQ run
        """
        # Make a mock run directory for MISeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_M00879_0001_000000000-ABCDE1','miseq',
            top_dir=self.top_dir)
        self.mock_illumina_run.create()
        # Load into an RunDir object
        run = RunDir(self.mock_illumina_run.dirn)
        # Check the properties
        self.assertEqual(run.path, self.mock_illumina_run.dirn)
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
        self.assertEqual(run.runparameters_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunParameters.xml'))
        self.assertTrue(isinstance(run.sample_sheet, SampleSheet))
        self.assertTrue(isinstance(run.runinfo, RunInfo))
        self.assertEqual(run.runinfo.run_id,
                         '151125_M00879_0001_000000000-ABCDE1')
        self.assertEqual(run.runinfo.instrument, 'M00879')
        self.assertEqual(run.runinfo.date, '151125')
        self.assertEqual(run.runinfo.run_number, '0001')
        self.assertEqual(run.runinfo.flowcell, '000000000-ABCDE1')
        self.assertTrue(isinstance(run.runparameters,
                                   RunParameters))
        self.assertEqual(run.runparameters.flowcell_mode, None)
        self.assertEqual(run.bcl_extension, ".bcl")
        self.assertEqual(run.lanes, [1,])
        self.assertEqual(run.cycles, 218)

    def test_rundir_hiseq(self):
        """
        RunDir: test for HiSEQ run
        """
        # Make a mock run directory for HISeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_SN700511R_0002_000000000-ABCDE1XX','hiseq',
            top_dir=self.top_dir)
        self.mock_illumina_run.create()
        # Load into an RunDir object
        run = RunDir(self.mock_illumina_run.dirn)
        # Check the properties
        self.assertEqual(run.path, self.mock_illumina_run.dirn)
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data', 'Intensities', 'BaseCalls'))
        self.assertEqual(run.sample_sheet_csv,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data', 'Intensities', 'BaseCalls',
                                      'SampleSheet.csv'))
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.runparameters_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunParameters.xml'))
        self.assertTrue(isinstance(run.sample_sheet, SampleSheet))
        self.assertTrue(isinstance(run.runinfo, RunInfo))
        self.assertEqual(run.runinfo.run_id,
                         '151125_SN700511R_0002_000000000-ABCDE1XX')
        self.assertEqual(run.runinfo.instrument, 'SN700511R')
        self.assertEqual(run.runinfo.date, '151125')
        self.assertEqual(run.runinfo.run_number, '0002')
        self.assertEqual(run.runinfo.flowcell, '000000000-ABCDE1XX')
        self.assertTrue(isinstance(run.runparameters, RunParameters))
        self.assertEqual(run.runparameters.flowcell_mode, None)
        self.assertEqual(run.bcl_extension, ".bcl.gz")
        self.assertEqual(run.lanes, [1,2,3,4,5,6,7,8])
        self.assertEqual(run.cycles, 218)

    def test_rundir_nextseq(self):
        """
        RunDir: test for NextSeq run
        """
        # Make a mock run directory for NextSeq format
        self.mock_illumina_run = MockIlluminaRun(
            '151125_NB500968_0003_000000000-ABCDE1XX','nextseq',
            top_dir=self.top_dir)
        self.mock_illumina_run.create()
        # Load into an RunDir object
        run = RunDir(self.mock_illumina_run.dirn)
        # Check the properties
        self.assertEqual(run.path, self.mock_illumina_run.dirn)
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data', 'Intensities', 'BaseCalls'))
        self.assertEqual(run.sample_sheet_csv,None)
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.runparameters_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunParameters.xml'))
        self.assertEqual(run.sample_sheet,None)
        self.assertTrue(isinstance(run.runinfo, RunInfo))
        self.assertEqual(run.runinfo.run_id,
                         '151125_NB500968_0003_000000000-ABCDE1XX')
        self.assertEqual(run.runinfo.instrument, 'NB500968')
        self.assertEqual(run.runinfo.date, '151125')
        self.assertEqual(run.runinfo.run_number, '0003')
        self.assertEqual(run.runinfo.flowcell, '000000000-ABCDE1XX')
        self.assertTrue(isinstance(run.runparameters, RunParameters))
        self.assertEqual(run.runparameters.flowcell_mode, None)
        self.assertEqual(run.bcl_extension, ".bcl.bgzf")
        self.assertEqual(run.lanes, [1,2,3,4])
        self.assertEqual(run.cycles, 158)

    def test_rundir_novaseq(self):
        """
        RunDir: test for NovaSeq run
        """
        # Make a mock run directory for NovaSeq format
        self.mock_illumina_run = MockIlluminaRun(
            '221125_A500968_0038_ABCDE1XX',
            'novaseq',
            top_dir=self.top_dir)
        self.mock_illumina_run.create()
        # Load into an RunDir object
        run = RunDir(self.mock_illumina_run.dirn)
        # Check the properties
        self.assertEqual(run.path, self.mock_illumina_run.dirn)
        self.assertEqual(run.basecalls_dir,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'Data', 'Intensities', 'BaseCalls'))
        self.assertEqual(run.sample_sheet_csv, None)
        self.assertEqual(run.runinfo_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunInfo.xml'))
        self.assertEqual(run.runparameters_xml,
                         os.path.join(self.mock_illumina_run.dirn,
                                      'RunParameters.xml'))
        self.assertEqual(run.sample_sheet, None)
        self.assertTrue(isinstance(run.runinfo, RunInfo))
        self.assertEqual(run.runinfo.run_id,
                         '221125_A500968_0038_ABCDE1XX')
        self.assertEqual(run.runinfo.instrument, 'A500968')
        self.assertEqual(run.runinfo.date, '221125')
        self.assertEqual(run.runinfo.run_number, '0038')
        self.assertEqual(run.runinfo.flowcell, 'BCDE1XX')
        self.assertTrue(isinstance(run.runparameters, RunParameters))
        self.assertEqual(run.runparameters.flowcell_mode, 'SP')
        self.assertEqual(run.bcl_extension, ".bcl.bgzf")
        self.assertEqual(run.lanes, [1,2])
        self.assertEqual(run.cycles, 158)

    def test_rundir_missing_directory(self):
        """
        RunDir: test missing run directory raises IlluminaError
        """
        # Check we can handle RunDir when MISeq directory is missing
        self.assertRaises(
            IlluminaError,
            RunDir,
            '/does/not/exist/151125_M00879_0001_000000000-ABCDE1')


class TestRunInfo(unittest.TestCase):
    """
    Tests for the RunInfo class
    """
    def setUp(self):
        # Create a temporary working directory
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_runinfo(self):
        """
        RunInfo: check data is extracted
        """
        run_info_xml = os.path.join(self.tmpdir, "RunInfo.xml")
        with open(run_info_xml, "wt") as fp:
            fp.write(RunInfoXml.create(
                run_name="151125_NB500968_0003_000000000-ABCDE1XX",
                bases_mask="y101,I8,I8,y101",
                nlanes=8,
                tilecount=16))
        run_info = RunInfo(run_info_xml)
        self.assertEqual(run_info.run_id,
                         "151125_NB500968_0003_000000000-ABCDE1XX")
        self.assertEqual(run_info.date, '151125')
        self.assertEqual(run_info.instrument, 'NB500968')
        self.assertEqual(run_info.run_number, '0003')
        self.assertEqual(run_info.flowcell, '000000000-ABCDE1XX')
        self.assertEqual(run_info.lane_count, '8')
        self.assertEqual(run_info.bases_mask, "y101,I8,I8,y101")
        self.assertEqual(len(run_info.reads), 4)
        self.assertEqual(run_info.reads[0]['number'], '1')
        self.assertEqual(run_info.reads[0]['num_cycles'], '101')
        self.assertEqual(run_info.reads[0]['is_indexed_read'], 'N')
        self.assertEqual(run_info.reads[1]['number'], '2')
        self.assertEqual(run_info.reads[1]['num_cycles'], '8')
        self.assertEqual(run_info.reads[1]['is_indexed_read'], 'Y')
        self.assertEqual(run_info.reads[2]['number'], '3')
        self.assertEqual(run_info.reads[2]['num_cycles'], '8')
        self.assertEqual(run_info.reads[2]['is_indexed_read'], 'Y')
        self.assertEqual(run_info.reads[3]['number'], '4')
        self.assertEqual(run_info.reads[3]['num_cycles'], '101')
        self.assertEqual(run_info.reads[3]['is_indexed_read'], 'N')


class TestRunParameters(unittest.TestCase):
    """
    Tests for the RunParameters class
    """
    def setUp(self):
        # Create a temporary working directory
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the test directory
        try:
            os.rmdir(self.tmpdir)
        except Exception:
            pass

    def test_runparameters_rta_2_11_4_0(self):
        """
        RunParameters: check data is extracted (RTA 2.11.4.0)
        """
        run_parameters_xml = os.path.join(self.tmpdir,
                                          "RunParameters.xml")
        with open(run_parameters_xml,'wt') as fp:
            fp.write(RunParametersXml.create(
                run_name="151125_NB500968_0003_000000000-ABCDE1XX",
                bases_mask="y101,I8,I8,y101",
                rta_version="2.11.4.0"))
        run_parameters = RunParameters(run_parameters_xml)
        self.assertEqual(run_parameters.flowcell_mode, None)

    def test_runparameters_rta_v3_4_4(self):
        """
        RunParameters: check data is extracted (RTA v3.4.4)
        """
        run_parameters_xml = os.path.join(self.tmpdir,
                                          "RunParameters.xml")
        with open(run_parameters_xml,'wt') as fp:
            fp.write(RunParametersXml.create(
                run_name="151125_NB500968_0003_000000000-ABCDE1XX",
                bases_mask="y101,I8,I8,y101",
                flowcell_mode="S1",
                rta_version="v3.4.4"))
        run_parameters = RunParameters(run_parameters_xml)
        self.assertEqual(run_parameters.flowcell_mode, "S1")



class BaseTestFastqDir(unittest.TestCase):
    """
    Base class for testing FastqDir, FastqDirProject & FastqDirSample

    Test methods use the following pattern:

    1. Invoke makeMockFastqDir factory method to produce a variant
       of an artificial directory structure mimicking that produced
       by the bcl to fastq conversion process
    2. Populate a FastqDir object from the resulting directory
       structure
    3. Invoke the assertFastqDir method to check that the FastqDir
       object is correct.

    assertFastqDir in turn invokes assertProject and
    assertUndetermined; assertProject invokes assertSample.

    Tests of FastqDir for different styles of processing software
    output can be based on this class. The subclass needs to implement
    its own 'test_...' methods but can use the assert methods here to
    verify that the results are correct.
    """
    def setUp(self):
        # Create a mock Illumina Fastq directory
        self.mock_fastq_dir = None

    def tearDown(self):
        # Remove the test directory
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()

    def assertFastqDir(self, fastq_dir, mock_fastq_dir):
        """
        Verify that a FastqDir object matches a MockFastqDir object
        """
        # Check top-level attributes
        self.assertEqual(fastq_dir.path,
                         mock_fastq_dir.path,
                         "Directories differ: %s != %s" %
                         (fastq_dir.path, mock_fastq_dir.path))
        self.assertEqual(fastq_dir.paired_end, mock_fastq_dir.paired_end,
                         "Paired ended-ness differ: %s != %s" %
                         (fastq_dir.paired_end, mock_fastq_dir.paired_end))
        # Check projects
        for project, pname in zip(fastq_dir.projects,
                                  mock_fastq_dir.projects):
            self.assertProject(project, mock_fastq_dir, pname)
        # Check undetermined indices
        self.assertUndetermined(fastq_dir.undetermined,
                                mock_fastq_dir)

    def assertProject(self, project, mock_fastq_dir, project_name):
        """
        Verify that FastqDirProject object matches MockFastqDir object
        """
        # Check top-level attributes
        self.assertEqual(project.name, project_name)
        self.assertEqual(project.paired_end, mock_fastq_dir.paired_end)
        # Check samples within projects
        for sample, sname in zip(project.samples,
                                 mock_fastq_dir.samples_in_project(
                                     project_name)):
            self.assertSample(sample, mock_fastq_dir, project_name, sname)

    def assertSample(self, sample, mock_fastq_dir, project_name,
                     sample_name):
        """
        Verify that a Sample object matches a MockFastqDir object
        """
        # Check top-level attributes
        self.assertEqual(sample.name, sample_name)
        self.assertEqual(sample.paired_end, mock_fastq_dir.paired_end)
        # Check fastqs
        for fastq, fq in zip(sample.fastq,
                             mock_fastq_dir.fastqs_in_sample(
                                 project_name,
                                 sample_name)):
            self.assertEqual(fastq, fq)
        # Check fastqs exist
        for fastq in sample.fastq:
            fq = os.path.join(sample.dirn, fastq)
            self.assertTrue(os.path.exists(fq),
                            "missing fastq: %s" % fq)
        # Check fastq subsets
        r1_fastqs = sample.fastq_subset(read_number=1)
        r2_fastqs = sample.fastq_subset(read_number=2)
        self.assertEqual(len(r1_fastqs)+len(r2_fastqs), len(sample.fastq))
        if not sample.paired_end:
            # For single end data all fastqs are R1 and there are no R2
            for fastq, fq in zip(sample.fastq, r1_fastqs):
                self.assertEqual(fastq, fq)
            self.assertEqual(len(r2_fastqs), 0)
        else:
            # For paired end data check R1 and R2 files match up
            for fastq_r1, fastq_r2 in zip(r1_fastqs, r2_fastqs):
                fqr1 = IlluminaFastq(fastq_r1)
                fqr2 = IlluminaFastq(fastq_r2)
                self.assertEqual(fqr1.read_number,1)
                self.assertEqual(fqr2.read_number,2)
                self.assertEqual(fqr1.sample_name, fqr2.sample_name)
                self.assertEqual(fqr1.barcode_sequence, fqr2.barcode_sequence)
                self.assertEqual(fqr1.lane_number, fqr2.lane_number)
                self.assertEqual(fqr1.set_number, fqr2.set_number)

    def assertUndetermined(self, undetermined, mock_fastq_dir):
        """
        Verify that "Undetermined" project matches MockFastqDir
        """
        self.assertEqual((undetermined is not None),
                         mock_fastq_dir.has_undetermined)
        if undetermined is not None:
            # Delegate checking to assertProject
            self.assertProject(undetermined,
                               mock_fastq_dir,
                               undetermined.name)


class TestFastqDirForCasava(BaseTestFastqDir):
    """
    Test FastqDir, FastqDirProject and FastqDirSample for CASAVA-style
    output
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

    def makeMockFastqDir(self,paired_end=False,
                         multiple_projects=False,
                         multiplexed_run=False):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "unaligned"),
                                      "casava",
                                      paired_end=paired_end)
        # Add first project with two samples
        mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_GCCAAT', lanes=(1,))
        mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_AGTCAA', lanes=(1,))
        # Additional projects?
        if multiplexed_run:
            lanes = (1,4,5)
            mock_fastq_dir.add_fastq_batch("CDE", "CDE3", "CDE3_GCCAAT",
                                           lanes=lanes)
            mock_fastq_dir.add_fastq_batch("CDE", "CDE4", "CDE4_AGTCAA",
                                           lanes=lanes)
            mock_fastq_dir.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def test_fastq_dir(self):
        """
        FastqDir: CASAVA-style output with single project
        """
        self.makeMockFastqDir()
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_paired_end(self):
        """
        FastqDir: CASAVA-style output with single project & paired-end data
        """
        self.makeMockFastqDir(paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects(self):
        """
        FastqDir: CASAVA-style output with multiple projects
        """
        self.makeMockFastqDir(multiple_projects=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects_paired_end(self):
        """
        FastqDir: CASAVA-style output with multiple projects & paired-end data
        """
        self.makeMockFastqDir(multiple_projects=True, paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects_multiplexed(self):
        """
        FastqDir: CASAVA-style output with multiple projects & multiplexing
        """
        self.makeMockFastqDir(multiple_projects=True, multiplexed_run=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,4,5,])

    def test_fastq_dir_multiple_projects_multiplexed_paired_end(self):
        """
        FastqDir: CASAVA-style output with multiple projects, multiplexing & paired-end data
        """
        self.makeMockFastqDir(multiple_projects=True, multiplexed_run=True,
                              paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "casava")
        self.assertEqual(fastq_dir.lanes, [1,4,5,])


class TestFastqDirForBcl2fastq2(BaseTestFastqDir):
    """
    Tests for FastqDir, FastqDirProject and FastqDirSample for
    bcl2fastq2-style output
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

    def makeMockFastqDir(self,paired_end=False,
                         multiple_projects=False,
                         multiplexed_run=False,
                         no_lane_splitting=False):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=paired_end,
                                      no_lane_splitting=no_lane_splitting)
        # Lanes to add
        if not no_lane_splitting:
            if multiplexed_run:
                lanes=(1,4,5)
            else:
                lanes=(1,)
        else:
            lanes = None
        # Add first project with two samples
        mock_fastq_dir.add_fastq_batch('AB', 'AB1', 'AB1_S1', lanes=lanes)
        mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_S2', lanes=lanes)
        # Additional projects
        if multiplexed_run:
            mock_fastq_dir.add_fastq_batch('CDE', 'CDE3', 'CDE3_S3',
                                           lanes=lanes)
            mock_fastq_dir.add_fastq_batch('CDE', 'CDE4', 'CDE4_S4',
                                           lanes=lanes)
        # Undetermined reads
        mock_fastq_dir.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def test_fastq_dir(self):
        """
        FastqDir: bcl2fastq2-style with single project
        """
        self.makeMockFastqDir()
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_paired_end(self):
        """
        FastqDir: bcl2fastq2-style with single project & paired-end data
        """
        self.makeMockFastqDir(paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects
        """
        self.makeMockFastqDir(multiple_projects=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects_paired_end(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects & paired-end data
        """
        self.makeMockFastqDir(multiple_projects=True,
                              paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,])

    def test_fastq_dir_multiple_projects_multiplexed(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects & multiplexing
        """
        self.makeMockFastqDir(multiple_projects=True,
                              multiplexed_run=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,4,5,])

    def test_fastq_dir_multiple_projects_multiplexed_paired_end(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects, multiplexing & paired-end data
        """
        self.makeMockFastqDir(multiple_projects=True,
                              multiplexed_run=True,
                              paired_end=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,4,5,])

    def test_fastq_dir_no_lane_splitting(self):
        """
        FastqDir: Read bcl2fastq2-style output with single project (--no-lane-splitting)

        """
        self.makeMockFastqDir(no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])

    def test_fastq_dir_paired_end_no_lane_splitting(self):
        """
        FastqDir: bcl2fastq2-style with single project & paired-end data (--no-lane-splitting)
        """
        self.makeMockFastqDir(paired_end=True,
                              no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])

    def test_fastq_dir_multiple_projects_no_lane_splitting(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects (--no-lane-splitting)
        """
        self.makeMockFastqDir(multiple_projects=True,
                              no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])

    def test_fastq_dir_multiple_projects_paired_end_no_lane_splitting(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects & paired-end data (--no-lane-splitting)
        """
        self.makeMockFastqDir(multiple_projects=True,
                              paired_end=True,
                              no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])


class TestFastqDirForBcl2fastq2SpecialCases(BaseTestFastqDir):
    """
    Tests for FastqDir, FastqDirProject and FastqDirSample for special
    cases of bcl2fastq2-style output
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

    def makeMockFastqDirSampleDirs(self):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=True)
        lanes=(1,2,)
        mock_fastq_dir.add_fastq_batch("AB", "AB1", "AB1/AB1_S1",
                                       lanes=lanes)
        mock_fastq_dir.add_fastq_batch("AB", "AB2", "AB2/AB2_S2",
                                       lanes=lanes)
        mock_fastq_dir.add_fastq_batch("CDE", "CDE3", "CDE3/CDE3_S3",
                                       lanes=lanes)
        mock_fastq_dir.add_fastq_batch("CDE", "CDE4", "CDE4/CDE4_S4",
                                       lanes=lanes)
        # Undetermined reads
        mock_fastq_dir.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def makeMockFastqDirIdsDiffer(self, ids_differ_for_all=False):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=True)
        lanes=(1,2,)
        # Add projects
        mock_fastq_dir.add_fastq_batch("AB", "AB1", "AB1_input_S1",
                                       lanes=lanes)
        mock_fastq_dir.add_fastq_batch("AB", "AB2", "AB2_chip_S2",
                                       lanes=lanes)
        if ids_differ_for_all:
            mock_fastq_dir.add_fastq_batch("CDE", "CDE3", "CDE3_rep1_S3",
                                           lanes=lanes)
            mock_fastq_dir.add_fastq_batch("CDE", "CDE4", "CDE4_rep2_S4",
                                           lanes=lanes)
        else:
            mock_fastq_dir.add_fastq_batch("CDE", "CDE3", "CDE3_S3",
                                           lanes=lanes)
            mock_fastq_dir.add_fastq_batch("CDE", "CDE4", "CDE4_S4",
                                           lanes=lanes)
        # Undetermined reads
        mock_fastq_dir.add_undetermined(lanes=lanes)
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def makeMockFastqDirOnlyUndetermined(self, no_lane_splitting=False):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=True,
                                      no_lane_splitting=
                                      no_lane_splitting)
        # Add undetermined reads
        mock_fastq_dir.add_undetermined(lanes=[1,2,3,4])
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def makeMockFastqDirSingleSampleNoUndetermined(self,
                                                       no_lane_splitting=False):
        # Create initial mock dir
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=True,
                                      no_lane_splitting=
                                      no_lane_splitting)
        # Add projects
        mock_fastq_dir.add_fastq_batch("KL", "KL_all", "KL_all_S1",
                                       lanes=[1,2,3,4])
        # Create and finish
        self.mock_fastq_dir = mock_fastq_dir
        self.mock_fastq_dir.create()

    def makeNonBcl2FastqDirectoryWithFastqs(self):
        # Create a non-bcl2fastq directory which looks like
        # a BCF-style 'analysis project'
        os.mkdir(os.path.join(self.top_dir, "notbcl2fastq"))
        os.mkdir(os.path.join(self.top_dir, "notbcl2fastq", "fastqs"))
        for fq in ("PJ1_S1_L001_R1_001.fastq.gz",
                   "PJ1_S1_L001_R2_001.fastq.gz",
                   "PJ2_S2_L001_R1_001.fastq.gz",
                   "PJ2_S2_L001_R2_001.fastq.gz",):
            with open(os.path.join(self.top_dir,
                                   "notbcl2fastq",
                                   "fastqs", fq), "wt") as fp:
                fp.write(u'')
        return os.path.join(self.top_dir, "notbcl2fastq")

    def makeNonBcl2FastqDirectoryWithNonCanonicalFastqs(self):
        # Create a non-bcl2fastq directory which contains
        # Fastq files with non-canonical-style names
        os.mkdir(os.path.join(self.top_dir, "notbcl2fastq"))
        os.mkdir(os.path.join(self.top_dir, "notbcl2fastq", "fastqs"))
        for fq in ("PB04_S4_R1_unpaired.fastq.gz",
                   "PB04_trimmoPE_bowtie2_notHg38.1.fastq.gz"):
            with open(os.path.join(self.top_dir,
                                   "notbcl2fastq",
                                   "fastqs", fq), "wt") as fp:
                fp.write(u'')
        return os.path.join(self.top_dir, "notbcl2fastq")

    def makeFastqDirWithMixedLaneAndNoLaneSplitting(self):
        # Create initial dir with lane splitting
        mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq"),
                                      "bcl2fastq2",
                                      paired_end=True,
                                      no_lane_splitting=False)
        mock_fastq_dir.add_fastq_batch("AB", "AB1", "AB1_S1", lanes=(1,2))
        mock_fastq_dir.add_fastq_batch("AB", "AB2", "AB2_S2", lanes=(1,2))
        mock_fastq_dir.add_fastq_batch("CDE", "CDE3", "CDE3_S3",
                                       lanes=(3,4))
        mock_fastq_dir.add_fastq_batch("CDE", "CDE4", "CDE4_S4",
                                       lanes=(3,4))
        mock_fastq_dir.add_undetermined(lanes=(1,2))
        mock_fastq_dir.create()
        # Create second dir with no lane splitting
        mock_fastq_dir2 = MockFastqDir(os.path.join(self.top_dir,
                                                   "bcl2fastq2"),
                                       "bcl2fastq2",
                                       paired_end=True,
                                       no_lane_splitting=True)
        mock_fastq_dir2.add_fastq_batch("CDE", "CDE3", "CDE3_S3",
                                        lanes=(3,4))
        mock_fastq_dir2.add_fastq_batch("CDE", "CDE4", "CDE4_S4",
                                        lanes=(3,4))
        mock_fastq_dir2.add_undetermined(lanes=(3,4))
        mock_fastq_dir2.create()
        # Move no lane splitting project into first dir
        shutil.rmtree(os.path.join(mock_fastq_dir.path, "CDE"))
        shutil.move(os.path.join(mock_fastq_dir2.path, "CDE"),
                    mock_fastq_dir.path)
        for f in ("Undetermined_S0_R1_001.fastq.gz",
                  "Undetermined_S0_R2_001.fastq.gz"):
            shutil.move(os.path.join(mock_fastq_dir2.path, f),
                        mock_fastq_dir.path)
        # Finish
        self.mock_fastq_dir = mock_fastq_dir

    def test_fastq_dir_all_sample_ids_differ_from_sample_names(self):
        """
        FastqDir: bcl2fastq2-style when all sample ids differ from names
        """
        self.makeMockFastqDirIdsDiffer(ids_differ_for_all=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,2])

    def test_fastq_dir_some_sample_ids_differ_from_sample_names(self):
        """
        FastqDir: bcl2fastq2-style when some sample ids differ from names
        """
        self.makeMockFastqDirIdsDiffer(ids_differ_for_all=False)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,2])

    def test_fastq_dir_sample_subdirs(self):
        """
        FastqDir: bcl2fastq-style when samples are in subdirs
        """
        self.makeMockFastqDirSampleDirs()
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,2])

    def test_fastq_dir_only_undetermined_fastqs(self):
        """
        FastqDir: bcl2fastq2-style with only undetermined fastqs
        """
        self.makeMockFastqDirOnlyUndetermined(no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])

    def test_fastq_dir_single_sample_no_undetermined_fastqs(self):
        """
        FastqDir: bcl2fastq2-style with single sample & no undetermined fastqs
        """
        self.makeMockFastqDirSingleSampleNoUndetermined(
            no_lane_splitting=True)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFastqDir(fastq_dir, self.mock_fastq_dir)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [None,])

    def test_fastq_dir_not_bcl2fastq2_output(self):
        """
        FastqDir: non-bcl2fastq2-style directory raises exception
        """
        # Attempt to read the directory as if it were the output
        # from bcl2fastq v2
        dirn = self.makeNonBcl2FastqDirectoryWithFastqs()
        self.assertRaises(IlluminaError,
                          FastqDir,
                          dirn)

    def test_fastq_dir_not_bcl2fastq2_output_non_canonical_fastqs(self):
        """
        FastqDir: non-bcl2fastq2-style with non-canonical Fastqs raises exception
        """
        # Attempt to read the directory as if it were the output
        # from bcl2fastq v2
        dirn = self.makeNonBcl2FastqDirectoryWithNonCanonicalFastqs()
        self.assertRaises(IlluminaError,
                          FastqDir,
                          dirn)

    def test_fastq_dir_multiple_projects_paired_end_mixed_lane_splitting(self):
        """
        FastqDir: bcl2fastq2-style with multiple projects & paired-end data (mixture of lanes and no-lane-splitting)
        """
        # Make a mock Illumina data directory with mixture of
        # lane-split and non-lane-split Fastqs
        self.makeFastqDirWithMixedLaneAndNoLaneSplitting()
        # Check that FastqDir can handle it
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        for p, p_name in zip(fastq_dir.projects,
                             self.mock_fastq_dir.projects):
            self.assertEqual(p.name, p_name)
            for s, s_name in zip(p.samples,
                                 self.mock_fastq_dir.samples_in_project(
                                     p_name)):
                self.assertEqual(s.name, s_name)
        self.assertEqual(fastq_dir.format, "bcl2fastq2")
        self.assertEqual(fastq_dir.lanes, [1,2])
        # Also check undetermined Fastqs are not double counted
        undetermined_fastqs = []
        for sample in fastq_dir.undetermined.samples:
            for fq in sample.fastq:
                self.assertFalse(fq in undetermined_fastqs,
                                 "%s: Fastq appears multiple times" % fq)
                undetermined_fastqs.append(fq)

    
class TestSummariseProjects(unittest.TestCase):

    def setUp(self):
        # Create a mock Fastq directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                        "fastqs"),
                                           "casava",
                                           paired_end=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_GCCAAT',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_AGTCAA',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',lanes=(2,3))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',lanes=(2,3))
        self.mock_fastq_dir.add_undetermined(lanes=(1,2,3))
        self.mock_fastq_dir.create()

    def tearDown(self):
        # Remove the test directory
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)

    def test_summarise_projects_paired_end_run(self):
        """
        summarise_projects: paired end run
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(summarise_projects(fastq_dir),
                         "Paired end: AB (2 samples); CDE (2 samples)")


class TestDescribeProject(unittest.TestCase):

    def setUp(self):
        # Create a mock Fastq directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "fastqs"),
                                               "casava",
                                               paired_end=True)
        self.mock_fastq_dir.add_fastq_batch('AB', 'AB1', 'AB1_GCCAAT',
                                                lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('AB', 'AB2', 'AB2_AGTCAA',
                                                lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('CDE', 'CDE3', 'CDE3_GCCAAT',
                                                lanes=(2,3))
        self.mock_fastq_dir.add_fastq_batch('CDE', 'CDE4', 'CDE4_AGTCAA',
                                                lanes=(2,3))
        self.mock_fastq_dir.add_undetermined(lanes=(1,2,3))
        self.mock_fastq_dir.create()

    def tearDown(self):
        # Remove the test directory
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)

    def test_describe_project_paired_end_run(self):
        """
        describe_project: generate descriptions for projects in a paired end run
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(describe_project(fastq_dir.projects[0]),
                         "AB: AB1-2 (2 paired end samples)")
        self.assertEqual(describe_project(fastq_dir.projects[1]),
                         "CDE: CDE3-4 (2 paired end samples, multiple "
                         "fastqs per sample)")

class TestVerifyAgainstCasavaSampleSheet(unittest.TestCase):

    def setUp(self):
        # Create a mock Fastq directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "fastqs"),
                                           "casava",
                                           paired_end=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_GCCAAT',
                                            lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_AGTCAA',
                                            lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_GCCAAT',
                                            lanes=(2,3))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_AGTCAA',
                                            lanes=(2,3))
        self.mock_fastq_dir.add_undetermined(lanes=(1,2,3))
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_sample_sheet(self):
        """
        verify_against_sample_sheet: verify CASAVA run
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir,
                                             self.sample_sheet), [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_project(self):
        """
        verify_against_sample_sheet: verify CASAVA run with missing project
        """
        shutil.rmtree(os.path.join(self.mock_fastq_dir.path, "Project_AB"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["Project_AB/Sample_AB1/AB1_GCCAAT_L001_R1_001.fastq.gz",
                          "Project_AB/Sample_AB1/AB1_GCCAAT_L001_R2_001.fastq.gz",
                          "Project_AB/Sample_AB2/AB2_AGTCAA_L001_R1_001.fastq.gz",
                          "Project_AB/Sample_AB2/AB2_AGTCAA_L001_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_sample(self):
        """
        verify_against_sample_sheet: verify CASAVA run with missing sample
        """
        shutil.rmtree(os.path.join(self.mock_fastq_dir.path,
                                   "Project_AB",
                                   "Sample_AB1"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["Project_AB/Sample_AB1/AB1_GCCAAT_L001_R1_001.fastq.gz",
                          "Project_AB/Sample_AB1/AB1_GCCAAT_L001_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_fastq(self):
        """
        verify_against_sample_sheet: verify CASAVA run with missing Fastq file
        """
        os.remove(os.path.join(self.mock_fastq_dir.path,
                               "Project_CDE",
                               "Sample_CDE4",
                               "CDE4_AGTCAA_L002_R2_001.fastq.gz"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["Project_CDE/Sample_CDE4/CDE4_AGTCAA_L002_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))


class TestVerifyAgainstBcl2fastq2SampleSheet(unittest.TestCase):

    def setUp(self):
        # Create a mock Fastq directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "bcl2fastq"),
                                               "bcl2fastq2",
                                               paired_end=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_S1',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_S2',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_S3',lanes=(2,3))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_S4',lanes=(2,3))
        self.mock_fastq_dir.add_undetermined(lanes=(1,2,3))
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_sample_sheet(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_project(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing project
        """
        shutil.rmtree(os.path.join(self.mock_fastq_dir.path, "AB"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["AB/AB1_S1_L001_R1_001.fastq.gz",
                          "AB/AB1_S1_L001_R2_001.fastq.gz",
                          "AB/AB2_S2_L001_R1_001.fastq.gz",
                          "AB/AB2_S2_L001_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_sample(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing sample
        """
        for f in os.listdir(os.path.join(self.mock_fastq_dir.path, "AB")):
            print(f)
            if f.startswith("AB1"):
                fq = os.path.join(self.mock_fastq_dir.path, "AB", f)
                print("Removing %s" % fq)
                os.remove(fq)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["AB/AB1_S1_L001_R1_001.fastq.gz",
                          "AB/AB1_S1_L001_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_fastq(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing Fastq
        """
        os.remove(os.path.join(self.mock_fastq_dir.path,
                               "CDE",
                               "CDE4_S4_L002_R2_001.fastq.gz"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["CDE/CDE4_S4_L002_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

class TestVerifyAgainstBcl2fastq2SampleSheetNoLaneSplitting(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "bcl2fastq"),
                                               "bcl2fastq2",
                                               paired_end=True,
                                               no_lane_splitting=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_S1')
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_S2')
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_S3')
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_S4')
        self.mock_fastq_dir.add_undetermined()
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_sample_sheet(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run (--no-lane-splitting)
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_project(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing project (--no-lane-splitting)
        """
        shutil.rmtree(os.path.join(self.mock_fastq_dir.path, "AB"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["AB/AB1_S1_R1_001.fastq.gz",
                          "AB/AB1_S1_R2_001.fastq.gz",
                          "AB/AB2_S2_R1_001.fastq.gz",
                          "AB/AB2_S2_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_sample(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing sample (--no-lane-splitting)
        """
        for f in os.listdir(os.path.join(self.mock_fastq_dir.path, "AB")):
            print(f)
            if f.startswith("AB1"):
                fq = os.path.join(self.mock_fastq_dir.path, "AB", f)
                print("Removing %s" % fq)
                os.remove(fq)
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         ["AB/AB1_S1_R1_001.fastq.gz",
                          "AB/AB1_S1_R2_001.fastq.gz"])
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))

    def test_verify_against_sample_sheet_with_missing_fastq(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run with missing Fastq (--no-lane-splitting)
        """
        os.remove(os.path.join(self.mock_fastq_dir.path,
                               "CDE",
                               "CDE4_S4_R2_001.fastq.gz"))
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertFalse(verify_against_sample_sheet(fastq_dir,
                                                     self.sample_sheet))


class TestVerifyAgainstBcl2fastq2MultiLaneSampleSheetNoLaneSplitting(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "bcl2fastq"),
                                               "bcl2fastq2",
                                               paired_end=True,
                                               no_lane_splitting=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_S1',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_S2',lanes=(1,))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_S3',lanes=(2,3))
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_S4',lanes=(2,3))
        self.mock_fastq_dir.add_undetermined(lanes=(1,2,3))
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_multi_lane_sample_sheet(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run (multi-lane, --no-lane-splitting)
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))


class TestVerifyAgainstBcl2fastq2SampleSheetSampleNamesAreIntegers(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "bcl2fastq"),
                                               "bcl2fastq2",
                                               paired_end=True,
                                               no_lane_splitting=True)
        self.mock_fastq_dir.add_fastq_batch('12970','12970','12970_S1')
        self.mock_fastq_dir.add_fastq_batch('12513','12513','12513_S2')
        self.mock_fastq_dir.add_undetermined()
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_sample_sheet_names_are_integers(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run (names are integers)
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))


class TestVerifyAgainstBcl2fastq2SampleSheetSpecialCases(unittest.TestCase):

    def setUp(self):
        # Create a mock Illumina directory
        self.top_dir = tempfile.mkdtemp()
        self.mock_fastq_dir = MockFastqDir(os.path.join(self.top_dir,
                                                            "bcl2fastq"),
                                               "bcl2fastq2",
                                               paired_end=True,
                                               no_lane_splitting=True)
        self.mock_fastq_dir.add_fastq_batch('AB','AB1','AB1_rep1_S1')
        self.mock_fastq_dir.add_fastq_batch('AB','AB2','AB2_rep1_S2')
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE3','CDE3_S3')
        self.mock_fastq_dir.add_fastq_batch('CDE','CDE4','CDE4_S4')
        self.mock_fastq_dir.add_undetermined()
        self.mock_fastq_dir.create()
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
        if self.mock_fastq_dir is not None:
            self.mock_fastq_dir.remove()
        os.rmdir(self.top_dir)
        os.remove(self.sample_sheet)

    def test_verify_against_sample_sheet_ids_and_names_differ(self):
        """
        verify_against_sample_sheet: verify bcl2fastq2 run (ids & names differ)
        """
        fastq_dir = FastqDir(self.mock_fastq_dir.path)
        self.assertEqual(list_missing_fastqs(fastq_dir, self.sample_sheet),
                         [])
        self.assertTrue(verify_against_sample_sheet(fastq_dir,
                                                    self.sample_sheet))
