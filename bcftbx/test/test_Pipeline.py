#######################################################################
# Tests for Pipeline.py module
#######################################################################
import os
import unittest
import tempfile
import shutil
import time
import bcftbx.utils
from bcftbx.JobRunner import SimpleJobRunner
from bcftbx.JobRunner import GEJobRunner
from bcftbx.Pipeline import Job
from bcftbx.Pipeline import GetSolidDataFiles
from bcftbx.Pipeline import GetSolidPairedEndFiles
from bcftbx.Pipeline import GetFastqFiles
from bcftbx.Pipeline import GetFastqGzFiles

class TestJobWithSimpleJobRunner(unittest.TestCase):
    """Unit tests for the the Job class using SimpleJobRunner

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

    def test_job_with_simplejobrunner(self):
        """Test Job using SimpleJobRunner to run basic shell command
        """
        # Create a job
        cmd = "sleep"
        args = ("2",)
        job = Job(SimpleJobRunner(),"shell_cmd",self.working_dir,cmd,args)
        # Check properties before starting
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,None)
        self.assertEqual(job.log,None)
        self.assertEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        # Check status
        self.assertFalse(job.isRunning())
        self.assertFalse(job.errorState())
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
        self.assertNotEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        self.assertTrue(job.isRunning())
        self.assertFalse(job.errorState())
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
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.isRunning())
        self.assertEqual(job.exit_status,0)
        self.assertFalse(job.errorState())
        self.assertEqual(job.status(),"Finished")

    def test_failing_job_with_simplejobrunner(self):
        """Test Job using SimpleJobRunner to run failing shell command
        """
        # Create a job
        cmd = "ls"
        args = ("*.whereisit",)
        job = Job(SimpleJobRunner(),"failing_cmd",self.working_dir,cmd,args)
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
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.isRunning())
        self.assertEqual(job.exit_status,2)
        self.assertFalse(job.errorState())
        self.assertEqual(job.status(),"Finished")

class TestJobWithGEJobRunner(unittest.TestCase):
    """Unit tests for the the Job class using GEJobRunner

    """
    def setUp(self):
        # Skip the test if Grid Engine not available
        if bcftbx.utils.find_program('qstat') is None:
            raise unittest.SkipTest("'qstat' not found, Grid Engine "
                                    "not available")
        # Create a temporary directory to work in
        # Nb can't make it in /tmp because that might not be
        # shared between submit host and the compute node
        # so check that TMPDIR is set and skip test if not
        try:
            tmpdir = os.environ['TMPDIR']
        except KeyError:
            raise unittest.SkipTest("'TMPDIR' environment variable not set - "
                                    "set this to point to a temporary dir "
                                    "shared by submit and compute nodes")
        # Set up working dir
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None

    def tearDown(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp()

    def test_job_with_gejobrunner(self):
        """Test Job using GEJobRunner to run basic shell command
        """
        # Create a job
        cmd = "sleep"
        args = ("2",)
        job = Job(GEJobRunner(),"shell_cmd",self.working_dir,cmd,args)
        # Check properties before starting
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,None)
        self.assertEqual(job.log,None)
        self.assertEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        # Check status
        self.assertFalse(job.isRunning())
        self.assertFalse(job.errorState())
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
        self.assertNotEqual(job.start_time,None)
        self.assertEqual(job.end_time,None)
        self.assertEqual(job.exit_status,None)
        self.assertTrue(job.isRunning())
        self.assertFalse(job.errorState())
        self.assertEqual(job.status(),"Running")
        # Wait for job to complete and check last time
        ntries = 1
        timeout = 20
        while job.isRunning() and ntries < timeout:
            ntries += 1
            time.sleep(1)
        self.assertEqual(job.name,"shell_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,job_id)
        self.assertNotEqual(job.log,None)
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.isRunning())
        self.assertEqual(job.exit_status,0)
        self.assertFalse(job.errorState())
        self.assertEqual(job.status(),"Finished")

    def test_failing_job_with_gejobrunner(self):
        """Test Job using GeJobRunner to run failing shell command
        """
        # Create a job
        cmd = "ls"
        args = ("*.whereisit",)
        job = Job(GEJobRunner(),"failing_cmd",self.working_dir,cmd,args)
        # Start the job
        job_id = job.start()
        # Wait to let job complete and check
        ntries = 1
        timeout = 20
        while job.isRunning() and ntries < timeout:
            ntries += 1
            time.sleep(1)
        self.assertEqual(job.name,"failing_cmd")
        self.assertEqual(job.working_dir,self.working_dir)
        self.assertEqual(job.script,cmd)
        self.assertEqual(job.args,args)
        self.assertEqual(job.label,None)
        self.assertEqual(job.group_label,None)
        self.assertEqual(job.job_id,job_id)
        self.assertNotEqual(job.log,None)
        self.assertNotEqual(job.start_time,None)
        self.assertNotEqual(job.end_time,None)
        self.assertFalse(job.isRunning())
        self.assertEqual(job.exit_status,2)
        self.assertFalse(job.errorState())
        self.assertEqual(job.status(),"Finished")

class TestGetSolidDataFiles(unittest.TestCase):
    """Unit tests for GetSolidDataFiles function

    """

    def test_get_solid_files(self):
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_PB1_QV.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_PB2_QV.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_PB1_QV.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_PB2_QV.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_old_qual_naming(self):
        file_list = ['solid0123_20131023_PB1.csfasta',
                     'solid0123_20131023_QV_PB1.qual',
                     'solid0123_20131023_PB2.csfasta',
                     'solid0123_20131023_QV_PB2.qual',
                     'out.log',
                     'README']
        expected = [('solid0123_20131023_PB1.csfasta','solid0123_20131023_QV_PB1.qual'),
                    ('solid0123_20131023_PB2.csfasta','solid0123_20131023_QV_PB2.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_ignore_filtered_files(self):
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
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

    def test_get_solid_files_short_names(self):
        file_list = ['PB1.csfasta',
                     'PB1.qual',
                     'PB2.csfasta',
                     'PB2.qual',
                     'out.log',
                     'README']
        expected = [('PB1.csfasta','PB1.qual'),
                    ('PB2.csfasta','PB2.qual')]
        data_files = GetSolidDataFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for filepair1,filepair2 in zip(expected,data_files):
            self.assertEqual(filepair1,filepair2)

class TestGetSolidPairedEndFiles(unittest.TestCase):
    """Unit tests for GetSolidPairedEndFiles function

    """

    def test_get_solid_files_paired_end(self):
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
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_files_paired_end_ignore_filtered_files(self):
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
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

    def test_get_solid_files_paired_end_shortened_names(self):
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
        data_files = GetSolidPairedEndFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(data_files))
        for fileset1,fileset2 in zip(expected,data_files):
            self.assertEqual(fileset1,fileset2)

class TestGetFastqFiles(unittest.TestCase):
    """Unit tests for GetFastqFiles function

    """

    def test_get_fastq_files(self):
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample3.fastq',),
                    ('sample4.fastq',)]
        fastqs = GetFastqFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_files_paired_end(self):
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
        fastqs = GetFastqFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqs))
        for fq1,fq2 in zip(expected,fastqs):
            self.assertEqual(fq1,fq2)

class TestGetFastqGzFiles(unittest.TestCase):
    """Unit tests for GetFastqGzFiles function

    """

    def test_get_fastq_gz_files(self):
        file_list = ['sample1.fastq.gz',
                     'sample2.fastq.gz',
                     'sample3.fastq',
                     'sample4.fastq',
                     'out.log',
                     'README']
        expected = [('sample1.fastq.gz',),
                    ('sample2.fastq.gz',)]
        fastqgzs = GetFastqGzFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

    def test_get_fastq_gz_files_paired_end(self):
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
        fastqgzs = GetFastqGzFiles('test',file_list=file_list)
        self.assertEqual(len(expected),len(fastqgzs))
        for fq1,fq2 in zip(expected,fastqgzs):
            self.assertEqual(fq1,fq2)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
