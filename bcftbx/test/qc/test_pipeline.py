#######################################################################
# Tests for qc/pipeline.py module
#######################################################################


import unittest
import tempfile
import shutil
import time
from bcftbx.jobs.runners import LocalRunner
from bcftbx.qc.pipeline import Job
from bcftbx.qc.pipeline import PipelineRunner
from bcftbx.qc.pipeline import get_solid_data_files
from bcftbx.qc.pipeline import get_solid_paired_end_files
from bcftbx.qc.pipeline import get_fastq_files
from bcftbx.qc.pipeline import get_fastq_gz_files


class TestJobWithLocalRunner(unittest.TestCase):
    """
    Unit tests for the Job class using 'LocalRunner'
    """
    def setUp(self):
        # Create a temporary directory to work in
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None

    def tearDown(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp()

    def test_job_with_local_runner(self):
        """
        qc.pipeline.Job: use 'LocalRunner' to run basic shell command
        """
        # Create a job
        cmd = "sleep"
        args = ("2",)
        job = Job(LocalRunner(),"shell_cmd",self.working_dir,cmd,args)
        # Check properties before starting
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,None)
        self.assertEqual(job.log,None)
        self.assertEqual(job.err,None)
        self.assertEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        # Check status
        self.assertFalse(job.is_running())
        self.assertFalse(job.error_state())
        self.assertEqual(job.status(),"Waiting")
        # Start the job and check
        job_id = job.start()
        time.sleep(1)
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,job_id)
        self.assertNotEqual(job.log,None)
        self.assertNotEqual(job.err,None)
        self.assertNotEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        self.assertTrue(job.is_running())
        self.assertFalse(job.error_state())
        self.assertEqual(job.status(),"Running")
        # Wait to let job complete and check last time
        time.sleep(2)
        job.update()
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,job_id)
        self.assertNotEqual(job.log,None)
        self.assertNotEqual(job.err,None)
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.is_running())
        self.assertEqual(job.exit_status,0)
        self.assertFalse(job.error_state())
        self.assertEqual(job.status(),"Finished")

    def test_failing_job_with_local_runner(self):
        """
        qc.pipeline.Job: use 'LocalRunner' to run failing shell command
        """
        # Create a job
        cmd = "ls"
        args = ("*.whereisit",)
        job = Job(LocalRunner(),"failing_cmd",self.working_dir,cmd,args)
        # Start the job
        job_id = job.start()
        # Wait to let job complete and check
        time.sleep(1)
        job.update()
        self.assertEqual(job.name,"failing_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,job_id)
        self.assertNotEqual(job.log,None)
        self.assertNotEqual(job.err,None)
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.is_running())
        self.assertEqual(job.exit_status,2)
        self.assertFalse(job.error_state())
        self.assertEqual(job.status(),"Finished")

    def test_job_wait_with_local_runner(self):
        """
        qc.pipeline.Job: wait for a running job to finish
        """
        job = Job(LocalRunner(),"wait_cmd",self.working_dir,"sleep",("1",))
        job.start()
        job.wait()
        self.assertFalse(job.is_running())
        self.assertEqual(job.exit_status,0)
        self.assertEqual(job.status(),"Finished")

    def test_job_terminate_with_local_runner(self):
        """
        qc.pipeline.Job: terminate a running job
        """
        job = Job(LocalRunner(),"term_cmd",self.working_dir,"sleep",("10",))
        job.start()
        self.assertTrue(job.is_running())
        job.terminate()
        job.wait()
        self.assertTrue(job.terminated)
        self.assertFalse(job.is_running())
        self.assertEqual(job.status(),"Terminated")


class TestPipelineRunner(unittest.TestCase):

    def setUp(self):
        # Set up working dir
        self.working_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.working_dir)

    def test_pipelinerunner(self):
        """
        bcftbx.qc.pipeline: run simple shell command
        """
        pr = PipelineRunner(LocalRunner(), poll_interval=1)
        pr.queue_job(self.working_dir,'ls','-l')
        pr.run(blocking=True)


class TestGetSolidDataFiles(unittest.TestCase):
    """
    Unit tests for 'get_solid_data_files' function
    """
    def test_get_solid_files(self):
        """
        get_solid_data_files: basic test
        """
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_PB1_QV.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_PB2_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_PB1_QV.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_PB2_QV.qual')]
        data_files = get_solid_data_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_old_qual_naming(self):
        """
        get_solid_data_files: test handling of old QUAL file naming convention
        """
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_QV_PB1.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_QV_PB2.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_QV_PB1.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_QV_PB2.qual')]
        data_files = get_solid_data_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_ignore_filtered_files(self):
        """
        get_solid_data_files: test filtered data files are ignored
        """
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_PB1_QV.qual',
                     'solid0123_20131023_PB1_T_F3.csfasta',
                     'solid0123_20131023_PB1_T_F3_QV.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_PB2_QV.qual',
                     'solid0123_20131023_PB2_T_F3.csfasta',
                     'solid0123_20131023_PB2_T_F3_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_PB1_QV.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_PB2_QV.qual')]
        data_files = get_solid_data_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_short_names(self):
        """
        get_solid_data_files: test handling of 'short' file names
        """
        file_list = ['PB1.csfasta',
                     'PB1.qual',
                     'PB2.csfasta',
                     'PB2.qual',
                     'out.log',
                     'README']
        expected = [('PB1.csfasta','PB1.qual'),
                    ('PB2.csfasta','PB2.qual')]
        data_files = get_solid_data_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)


class TestGetSolidPairedEndFiles(unittest.TestCase):
    """
    Unit tests for get_solid_paired_end_files function
    """
    def test_get_solid_files_paired_end(self):
        """
        get_solid_paired_end_files: test paired end files are returned
        """
        file_list = ['solid0123_20131023_F3_PB1.csfasta',
                     'solid0123_20131023_F3_PB1_QV.qual',
                     'solid0123_20131023_F5-BC_PB1.csfasta',
                     'solid0123_20131023_F5-BC_PB1_QV.qual',
                     'solid0123_20131023_F3_PB2.csfasta',
                     'solid0123_20131023_F3_PB2_QV.qual',
                     'solid0123_20131023_F5-BC_PB2.csfasta',
                     'solid0123_20131023_F5-BC_PB2_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_F3_PB1.csfasta',
                     'solid0123_20131023_F3_PB1_QV.qual',
                     'solid0123_20131023_F5-BC_PB1.csfasta',
                     'solid0123_20131023_F5-BC_PB1_QV.qual'),
                    ('solid0123_20131023_F3_PB2.csfasta',
                     'solid0123_20131023_F3_PB2_QV.qual',
                     'solid0123_20131023_F5-BC_PB2.csfasta',
                     'solid0123_20131023_F5-BC_PB2_QV.qual')]
        data_files = get_solid_paired_end_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_paired_end_files_ignore_filtered_files(self):
        """
        get_solid_paired_end_files: test ignoring filtered files
        """
        file_list = ['solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual',
                     'solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual',
                     'solid0123_20131023_PB1_F3_T_F3.csfasta',
                     'solid0123_20131023_PB1_F3_T_F3_QV.qual',
                     'solid0123_20131023_PB1_F5_T_F3.csfasta',
                     'solid0123_20131023_PB1_F5_T_F3_QV.qual',
                     'solid0123_20131023_PB2_F3_T_F3.csfasta',
                     'solid0123_20131023_PB2_F3_T_F3_QV.qual',
                     'solid0123_20131023_PB2_F5_T_F3.csfasta',
                     'solid0123_20131023_PB2_F5_T_F3_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual'),
                    ('solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual')]
        data_files = get_solid_paired_end_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_files_paired_end_shortened_names(self):
        """
        get_solid_paired_end_files: test handling shortened file names
        """
        file_list = ['solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual',
                     'solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1_F3.csfasta',
                     'solid0123_20131023_PB1_F3_QV.qual',
                     'solid0123_20131023_PB1_F5.csfasta',
                     'solid0123_20131023_PB1_F5_QV.qual'),
                    ('solid0123_20131023_PB2_F3.csfasta',
                     'solid0123_20131023_PB2_F3_QV.qual',
                     'solid0123_20131023_PB2_F5.csfasta',
                     'solid0123_20131023_PB2_F5_QV.qual')]
        data_files = get_solid_paired_end_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)


class TestGetFastqFiles(unittest.TestCase):
    """
    Unit tests for GetFastqFiles function
    """
    def test_get_fastq_files(self):
        """
        get_fastq_files: basic test
        """
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample3.fastq',),
                    ('sample4.fastq',)]
        fastqs = get_fastq_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_files_paired_end(self):
        """
        get_fastq_files: handle paired end files
        """
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3_R1.fastq',
                     'sample3_R2.fastq',
                     'sample4_R1.fastq',
                     'sample4_R2.fastq',
                     'out.log',
                     'README']
        expected = [('sample3_R1.fastq',),
                    ('sample3_R2.fastq',),
                    ('sample4_R1.fastq',),
                    ('sample4_R2.fastq',)]
        fastqs = get_fastq_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_files_fq_extension(self):
        """
        get_fastq_files: handle .fq extension
        """
        file_list = ['sample1.fq.gz',
                     'sample2.fq.gz',
                     'sample3_R1.fq',
                     'sample3_R2.fq',
                     'sample4_R1.fq',
                     'sample4_R2.fq',
                     'out.log',
                     'README']
        expected = [('sample3_R1.fq',),
                    ('sample3_R2.fq',),
                    ('sample4_R1.fq',),
                    ('sample4_R2.fq',)]
        fastqs = get_fastq_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)


class TestGetFastqGzFiles(unittest.TestCase):
    """
    Unit tests for 'get_fastq_gz_files' function
    """
    def test_get_fastq_gz_files(self):
        """
        get_fastq_gz_files: basic test
        """
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample1.fastq.gz',),
                    ('sample2.fastq.gz',)]
        fastqgzs = get_fastq_gz_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_gz_files_paired_end(self):
        """
        get_fastq_gz_files: handle paired end files
        """
        file_list = ['sample1_R1.fastq.gz',
                     'sample1_R2.fastq.gz',
                     'sample2_R1.fastq.gz',
                     'sample2_R2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample1_R1.fastq.gz',),
                    ('sample1_R2.fastq.gz',),
                    ('sample2_R1.fastq.gz',),
                    ('sample2_R2.fastq.gz',)]
        fastqgzs = get_fastq_gz_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_gz_files_fq_extension(self):
        """
        get_fastq_gz_files: handle .fq.gz extension
        """
        file_list = ['sample1_R1.fq.gz',
                     'sample1_R2.fq.gz',
                     'sample2_R1.fq.gz',
                     'sample2_R2.fq.gz',
                     'sample3.fq',
                     'sample4.fq',
                     'out.log',
                     'README']
        expected = [('sample1_R1.fq.gz',),
                    ('sample1_R2.fq.gz',),
                    ('sample2_R1.fq.gz',),
                    ('sample2_R2.fq.gz',)]
        fastqgzs = get_fastq_gz_files('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)