#######################################################################
# Tests for JobRunner.py module
#######################################################################
from bcftbx.JobRunner import *
from bcftbx.mockGE import setup_mock_GE
from bcftbx.mockGE import MockGE
from bcftbx.mockslurm import setup_mock_slurm
from bcftbx.mockslurm import MockSlurm
import bcftbx.utils
import unittest
import tempfile
import time
import shutil

class TestSimpleJobRunner(unittest.TestCase):

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

    def run_job(self,runner,*args):
        return runner.run(*args)

    def wait_for_jobs(self,runner,*args):
        poll_interval = 0.01
        ntries = 0
        running_jobs = True
        # Check running jobs
        while ntries < 100 and running_jobs:
            running_jobs = False
            for jobid in args:
                if runner.isRunning(jobid):
                    running_jobs = True
            if running_jobs:
                time.sleep(poll_interval)
                ntries += 1
        # All jobs finished
        if not running_jobs:
            return
        # Otherwise we've reached the timeout limit
        self.fail("Timed out waiting for test job")

    def test_simple_job_runner(self):
        """Test SimpleJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.assertEqual(runner.exit_status(jobid),None)
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_simple_job_runner_exit_status(self):
        """Test SimpleJobRunner returns correct exit status
        """
        # Create a runner and execute commands with known exit codes
        runner = SimpleJobRunner()
        jobid_ok = self.run_job(runner,'test_ok',self.working_dir,
                                       '/bin/bash',('-c','exit 0',))
        jobid_error = self.run_job(runner,'test_error',self.working_dir,
                                   '/bin/bash',('-c','exit 1',))
        self.wait_for_jobs(runner,jobid_ok,jobid_error)
        # Check exit codes
        self.assertEqual(runner.exit_status(jobid_ok),0)
        self.assertEqual(runner.exit_status(jobid_error),1)

    def test_simple_job_runner_termination(self):
        """Test SimpleJobRunner can terminate a running job

        """
        # Create a runner and execute the sleep command
        runner = SimpleJobRunner()
        jobid = self.run_job(runner,'test',self.working_dir,'sleep',('60s',))
        # Wait for job to start
        ntries = 0
        while ntries < 100:
            if runner.isRunning(jobid):
                break
            ntries += 1
        self.assertTrue(runner.isRunning(jobid))
        # Terminate job
        runner.terminate(jobid)
        self.assertFalse(runner.isRunning(jobid))
        self.assertNotEqual(runner.exit_status(jobid),0)

    def test_simple_job_runner_join_logs(self):
        """Test SimpleJobRunner joining stderr to stdout

        """
        # Create a runner and execute the echo command
        runner = SimpleJobRunner(join_logs=True)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertEqual(runner.errFile(jobid),None)
        # Check log file is in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)

    def test_simple_job_runner_set_log_dir(self):
        """Test SimpleJobRunner explicitly setting log directory

        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)))
        # Check log files are the log directory, not the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.log_dir)

    def test_simple_job_runner_set_log_dir_multiple_times(self):
        """Test SimpleJobRunner explicitly setting log directory multiple times

        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid1 = self.run_job(runner,'test1',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run second job
        runner.set_log_dir(self.working_dir)
        jobid2 = self.run_job(runner,'test2',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run 3rd job
        runner.set_log_dir(self.log_dir)
        jobid3 = self.run_job(runner,'test3',self.working_dir,'echo',('this is a test',))
        # Wait for jobs to finish
        self.wait_for_jobs(runner,jobid1,jobid2,jobid3)
        # Check outputs
        self.assertEqual(runner.name(jobid1),'test1')
        self.assertTrue(os.path.isfile(runner.logFile(jobid1)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid1)))
        self.assertEqual(runner.name(jobid2),'test2')
        self.assertTrue(os.path.isfile(runner.logFile(jobid2)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid2)))
        self.assertEqual(runner.name(jobid3),'test3')
        self.assertTrue(os.path.isfile(runner.logFile(jobid3)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid3)))
        # Check log files are in the correct directories
        self.assertEqual(os.path.dirname(runner.logFile(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.logFile(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.logFile(jobid3)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid3)),self.log_dir)

    def test_simple_job_runner_nslots(self):
        """Test SimpleJobRunner sets BCFTBX_RUNNER_NSLOTS

        """
        # Create a runner and check default nslots
        runner = SimpleJobRunner()
        self.assertEqual(runner.nslots,1)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = SimpleJobRunner(nslots=8)
        self.assertEqual(runner.nslots,8)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())

    def test_simple_job_runner_repr(self):
        """Test SimpleJobRunner '__repr__' built-in
        """
        self.assertEqual(str(SimpleJobRunner()),
                         'SimpleJobRunner(join_logs=False)')
        self.assertEqual(str(SimpleJobRunner(nslots=8)),
                         'SimpleJobRunner(nslots=8 join_logs=False)')
        self.assertEqual(str(SimpleJobRunner(join_logs=True)),
                         'SimpleJobRunner(join_logs=True)')
        self.assertEqual(str(SimpleJobRunner(nslots=8,join_logs=True)),
                         'SimpleJobRunner(nslots=8 join_logs=True)')

class TestGEJobRunner(unittest.TestCase):

    def setUp(self):
        # Set up mockGE utilities
        self.database_dir = self.make_tmp_dir()
        self.bin_dir = self.make_tmp_dir()
        self.old_path = os.environ['PATH']
        os.environ['PATH'] = self.bin_dir + os.pathsep + self.old_path
        setup_mock_GE(bindir=self.bin_dir,
                      database_dir=self.database_dir,
                      qsub_delay=0.4,
                      qacct_delay=15.0,
                      debug=False)
        self.mock_ge = MockGE(database_dir=self.database_dir)
        # Create a temporary directory to work in
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None
        # Extra arguments: edit this for local setup requirements
        self.ge_extra_args = []

    def tearDown(self):
        self.mock_ge.stop()
        os.environ['PATH'] = self.old_path
        shutil.rmtree(self.database_dir)
        shutil.rmtree(self.bin_dir)
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp(dir=os.getcwd())

    def update_jobs(self,timeout=1.0):
        poll_interval = 0.1
        ntries = 0
        while (ntries*poll_interval < timeout):
            time.sleep(poll_interval)
            ntries += 1
            self.mock_ge.update_jobs()

    def run_job(self,runner,*args):
        try:
            return runner.run(*args)
        except OSError:
            self.fail("Unable to run GE job")

    def wait_for_jobs(self,runner,*args):
        poll_interval = 0.1
        timeout = 10.0
        ntries = 0
        running_jobs = True
        # Check running jobs
        while (ntries*poll_interval < timeout) and running_jobs:
            self.mock_ge.update_jobs()
            running_jobs = False
            for jobid in args:
                if runner.isRunning(jobid):
                    running_jobs = True
            if running_jobs:
                time.sleep(poll_interval)
                ntries += 1
        # All jobs finished
        if not running_jobs:
            return
        # Otherwise we've reached the timeout limit
        for jobid in args:
            # Terminate jobs
            if runner.isRunning(jobid):
                runner.terminate(jobid)
        self.fail("Timed out waiting for test job")

    def test_ge_job_runner_fast_command(self):
        """Test GEJobRunner with fast shell command

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a quick test',))
        self.assertTrue(runner.isRunning(jobid))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_ge_job_runner_fast_command_with_initial_delay(self):
        """Test GEJobRunner with fast shell command & initial delay

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a quick test',))
        # Do some updates so the job finishes before the
        # first check
        self.update_jobs()
        self.assertTrue(runner.isRunning(jobid))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_ge_job_runner_slow_command(self):
        """Test GEJobRunner with a slow shell command

        """
        # Create a runner and execute the sleep command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'sleep',('5',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_ge_job_runner_exit_status(self):
        """Test GEJobRunner returns correct exit status
        """
        # Create a runner and execute commands with known exit codes
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid_ok = self.run_job(runner,'test_ok',self.working_dir,
                                       '/bin/bash',('-c','exit 0',))
        jobid_error = self.run_job(runner,'test_error',self.working_dir,
                                   '/bin/bash',('-c','exit 1',))
        self.wait_for_jobs(runner,jobid_ok,jobid_error)
        # Check exit codes
        self.assertEqual(runner.exit_status(jobid_ok),0)
        self.assertEqual(runner.exit_status(jobid_error),1)

    def test_ge_job_runner_termination(self):
        """Test GEJobRunner can terminate a running job

        """
        # Create a runner and execute the sleep command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'sleep',('60s',))
        # Wait for job to start
        ntries = 0
        while ntries < 100:
            if runner.isRunning(jobid):
                break
            ntries += 1
        self.assertTrue(runner.isRunning(jobid))
        # Terminate job
        runner.terminate(jobid)
        self.update_jobs()
        self.assertFalse(runner.isRunning(jobid))
        self.assertNotEqual(runner.exit_status(jobid),0)

    def test_ge_job_runner_join_logs(self):
        """Test GEJobRunner with '-j y' option (i.e. join stderr and stdout)

        """
        # Create a runner and execute the echo command
        self.ge_extra_args.extend(('-j','y'))
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        self.assertEqual(runner.ge_extra_args,self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertFalse(os.path.isfile(runner.errFile(jobid)))
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)

    def test_ge_job_runner_set_log_dir(self):
        """Test GEJobRunner explicitly setting log directory

        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)))
        # Check log files are the log directory, not the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.log_dir)

    def test_ge_job_runner_set_log_dir_multiple_times(self):
        """Test GEJobRunner explicitly setting log directory multiple times

        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        # Reset the log directory
        runner.set_log_dir(self.log_dir)
        jobid1 = self.run_job(runner,'test1',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run second job
        runner.set_log_dir(self.working_dir)
        jobid2 = self.run_job(runner,'test2',self.working_dir,'echo',('this is a test',))
        # Rest the log directory again and run 3rd job
        runner.set_log_dir(self.log_dir)
        jobid3 = self.run_job(runner,'test3',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid1,jobid2,jobid3)
        # Check outputs
        self.assertEqual(runner.name(jobid1),'test1')
        self.assertTrue(os.path.isfile(runner.logFile(jobid1)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid1)))
        self.assertEqual(runner.name(jobid2),'test2')
        self.assertTrue(os.path.isfile(runner.logFile(jobid2)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid2)))
        self.assertEqual(runner.name(jobid3),'test3')
        self.assertTrue(os.path.isfile(runner.logFile(jobid3)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid3)))
        # Check log files are in the correct directories
        self.assertEqual(os.path.dirname(runner.logFile(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid1)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.logFile(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid2)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.logFile(jobid3)),self.log_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid3)),self.log_dir)

    def test_ge_job_runner_error_state(self):
        """Test GEJobRunner detects job in error state
        """
        # Create a runner and execute a command in a non-existent
        # working directory
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test_eqw',
                             '/non/existent/dir',
                             'echo',('this should fail',))
        # Wait for job to go into error state
        ntries = 0
        while ntries < 100:
            if runner.errorState(jobid):
                # Success - job errored
                return
            time.sleep(0.1)
            ntries += 1
        self.fail("Job failed to go into error state")

    def test_ge_job_runner_queue(self):
        """Test GEJobRunner fetches the queue of running job
        """
        # Create a runner and execute the sleep command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test_queue',
                             self.working_dir,
                             'sleep',('10s',))
        # Wait for job to return queue
        ntries = 0
        while ntries < 100:
            self.update_jobs()
            if runner.isRunning(jobid):
                queue = runner.queue(jobid)
                if queue is not None:
                    self.assertEqual(queue,"mock.q")
                    return
            time.sleep(0.1)
            ntries += 1
        self.fail("Job failed to return queue before time out")

    def test_ge_job_runner_queue_after_completion(self):
        """Test GEJobRunner fetches the queue of completed job
        """
        # Create a runner and execute the sleep command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test_queue',
                             self.working_dir,
                             'sleep',('1s',))
        # Wait for job to finish
        self.wait_for_jobs(runner,jobid)
        # Check the queue
        self.assertEqual(runner.queue(jobid),"mock.q")

    def test_ge_job_runner_nslots(self):
        """Test GEJobRunner sets BCFTBX_RUNNER_NSLOTS (-pe smp.pe)
        """
        # Create a runner and check default nslots
        runner = GEJobRunner()
        self.assertEqual(runner.nslots,1)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = GEJobRunner(ge_extra_args=['-pe','smp.pe','8'])
        self.assertEqual(runner.nslots,8)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())

    def test_ge_job_runner_nslots_amd_pe(self):
        """Test GEJobRunner sets BCFTBX_RUNNER_NSLOTS (-pe amd.pe)
        """
        # Create a runner and check default nslots
        runner = GEJobRunner()
        self.assertEqual(runner.nslots,1)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = GEJobRunner(ge_extra_args=['-pe','amd.pe','8'])
        self.assertEqual(runner.nslots,8)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())

class TestSlurmRunner(unittest.TestCase):

    def setUp(self):
        # Set up mockSLURM utilities
        self.database_dir = self.make_tmp_dir()
        self.bin_dir = self.make_tmp_dir()
        self.old_path = os.environ['PATH']
        os.environ['PATH'] = self.bin_dir + os.pathsep + self.old_path
        setup_mock_slurm(bindir=self.bin_dir,
                         database_dir=self.database_dir,
                         sbatch_delay=0.4,
                         debug=False)
        self.mock_slurm = MockSlurm(database_dir=self.database_dir,
                                    debug=True)
        # Create a temporary directory to work in
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None

    def tearDown(self):
        self.mock_slurm.stop()
        os.environ['PATH'] = self.old_path
        shutil.rmtree(self.database_dir)
        shutil.rmtree(self.bin_dir)
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp(dir=os.getcwd())

    def update_jobs(self, timeout=1.0):
        poll_interval = 0.1
        ntries = 0
        while (ntries*poll_interval < timeout):
            time.sleep(poll_interval)
            ntries += 1
            self.mock_slurm.update_jobs()

    def run_job(self,runner,*args):
        try:
            return runner.run(*args)
        except OSError:
            self.fail("Unable to run Slurm job")

    def wait_for_jobs(self,runner,*args):
        poll_interval = 0.1
        timeout = 10.0
        ntries = 0
        running_jobs = True
        # Check running jobs
        while (ntries*poll_interval < timeout) and running_jobs:
            self.mock_slurm.update_jobs()
            running_jobs = False
            for jobid in args:
                if runner.isRunning(jobid):
                    running_jobs = True
            if running_jobs:
                time.sleep(poll_interval)
                ntries += 1
        # All jobs finished
        if not running_jobs:
            return
        # Otherwise we've reached the timeout limit
        for jobid in args:
            # Terminate jobs
            if runner.isRunning(jobid):
                runner.terminate(jobid)
        self.fail("Timed out waiting for test job")

    def test_slurm_runner_fast_command(self):
        """
        Test SlurmRunner with fast shell command
        """
        # Create a runner
        runner = SlurmRunner()
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Execute simple command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'echo', ('this is a quick test',))
        self.assertTrue(runner.isRunning(jobid))
        self.wait_for_jobs(runner, jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid), "slurm_test")
        expected_log = os.path.join(self.working_dir, f"slurm_test.o{jobid}")
        self.assertEqual(expected_log, runner.logFile(jobid))
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid))
        expected_err = os.path.join(self.working_dir, f"slurm_test.e{jobid}")
        self.assertEqual(expected_err, runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        # Check exit status of completed job
        self.assertEqual(runner.exit_status(jobid), 0)

    def test_slurm_runner_fast_command_with_initial_delay(self):
        """
        Test SlurmRunner with fast shell command & initial delay
        """
        # Create a runner
        runner = SlurmRunner()
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Execute "echo" command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             "echo", ("this is a quick test",))
        # Do some updates so the job finishes before the
        # first check
        self.update_jobs()
        self.assertTrue(runner.isRunning(jobid))
        self.wait_for_jobs(runner, jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid), "slurm_test")
        expected_log = os.path.join(self.working_dir, f"slurm_test.o{jobid}")
        self.assertEqual(expected_log, runner.logFile(jobid))
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.errFile(jobid))
        expected_err = os.path.join(self.working_dir, f"slurm_test.e{jobid}")
        self.assertEqual(expected_err, runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        self.assertEqual(runner.exit_status(jobid),0)
        # Check exit status of completed job
        self.assertEqual(runner.exit_status(jobid), 0)

    def test_slurm_runner_slow_command(self):
        """
        Test SlurmRunner with a slow shell command
        """
        # Create a runner
        runner = SlurmRunner()
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Execute sleep command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'sleep', ('5',))
        self.assertTrue(runner.isRunning(jobid))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),"slurm_test")
        expected_log = os.path.join(self.working_dir, f"slurm_test.o{jobid}")
        self.assertEqual(expected_log, runner.logFile(jobid))
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid))
        expected_err = os.path.join(self.working_dir, f"slurm_test.e{jobid}")
        self.assertEqual(expected_err, runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))
        # Check exit status of completed job
        self.assertEqual(runner.exit_status(jobid), 0)

    def test_slurm_runner_exit_status(self):
        """
        Test SlurmRunner returns correct exit status
        """
        # Create a runner
        runner = SlurmRunner()
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Execute commands with known exit codes
        jobid_ok = self.run_job(runner,
                                "slurm_ok",
                                self.working_dir,
                                '/bin/bash', ('-c','exit 0',))
        self.assertTrue(runner.isRunning(jobid_ok))
        jobid_error = self.run_job(runner,
                                   "slurm_error",
                                   self.working_dir,
                                   '/bin/bash', ('-c','exit 1',))
        self.assertTrue(runner.isRunning(jobid_error))
        self.wait_for_jobs(runner,jobid_ok,jobid_error)
        # Check exit codes
        self.assertEqual(runner.exit_status(jobid_ok), 0)
        self.assertEqual(runner.exit_status(jobid_error), 1)

    def test_slurm_runner_termination(self):
        """
        Test SlurmRunner can terminate a running job
        """
        # Create a runner
        runner = SlurmRunner()
        # Execute sleep command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'sleep', ('60s',))
        # Wait for job to start
        ntries = 0
        while ntries < 100:
            if runner.isRunning(jobid):
                break
            ntries += 1
        self.assertTrue(runner.isRunning(jobid))
        # Terminate job before it completes
        runner.terminate(jobid)
        self.update_jobs()
        self.assertFalse(runner.isRunning(jobid))
        self.assertNotEqual(runner.exit_status(jobid), 0)

    def test_slurm_runner_join_logs(self):
        """
        Test SlurmRunner with 'join_logs'
        """
        # Create a runner with join_logs set
        runner = SlurmRunner(join_logs=True)
        self.assertTrue(runner.join_logs)
        # Execute the echo command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'echo', ('this is a test',))
        self.wait_for_jobs(runner, jobid)
        # Check log and err files are the same
        self.assertEqual(runner.name(jobid), "slurm_test")
        expected_log = os.path.join(self.working_dir, f"slurm_test.o{jobid}")
        self.assertEqual(expected_log, runner.logFile(jobid))
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid))
        self.assertEqual(runner.logFile(jobid), runner.errFile(jobid))
        # Check exit status of completed job
        self.assertEqual(runner.exit_status(jobid), 0)

    def test_slurm_runner_extra_args_sets_nslots(self):
        """
        Test SlurmRunner extra arguments: '-n' implicitly sets nslots
        """
        runner = SlurmRunner(slurm_extra_args=("-n", "8"))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.slurm_extra_args, None)
        # Exception if try to set it twice
        self.assertRaises(Exception,
                          SlurmRunner,
                          nslots=8,
                          slurm_extra_args=("-n", "8"))

    def test_slurm_runner_extra_args_sets_partition(self):
        """
        Test SlurmRunner extra arguments: '-p' implicitly sets partition
        """
        runner = SlurmRunner(slurm_extra_args=("-p", "default"))
        self.assertEqual(runner.partition, "default")
        self.assertEqual(runner.slurm_extra_args, None)
        # Exception if try to set it twice
        self.assertRaises(Exception,
                          SlurmRunner,
                          partition="default",
                          slurm_extra_args=("-p", "default"))

    def test_slurm_runner_extra_args_doesnt_allow_setting_log_files(self):
        """
        Test SlurmRunner extra arguments: '-o' and '-e' not allowed
        """
        self.assertRaises(Exception,
                          SlurmRunner,
                          slurm_extra_args=("-o", "slurm-%j.out"))
        self.assertRaises(Exception,
                          SlurmRunner,
                          slurm_extra_args=("-e",
                                            "slurm-%j.err",
                                            "-o",
                                            "slurm-%j.out"))

    def test_slurm_runner_extra_args_doesnt_allow_setting_export(self):
        """
        Test SlurmRunner extra arguments: '--export' not allowed
        """
        self.assertRaises(Exception,
                          SlurmRunner,
                          slurm_extra_args=("--export", "ALL"))
        self.assertRaises(Exception,
                          SlurmRunner,
                          slurm_extra_args=("--export=ALL",))

    def test_slurm_runner_extra_args_preserves_unreserved_options(self):
        """
        Test SlurmRunner extra arguments: preserves unreserved options
        """
        runner = SlurmRunner(slurm_extra_args=("-n", "8", "-l"))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.slurm_extra_args, ["-l"])

    def test_slurm_runner_set_log_dir(self):
        """
        Test SlurmRunner explicitly setting log directory
        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner with custom log directory
        runner = SlurmRunner(log_dir=self.log_dir)
        self.assertEqual(runner.log_dir, self.log_dir)
        # Execute the echo command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'echo', ('this is a test',))
        self.wait_for_jobs(runner, jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid), "slurm_test")
        expected_log = os.path.join(self.log_dir, f"slurm_test.o{jobid}")
        self.assertEqual(expected_log, runner.logFile(jobid))
        self.assertTrue(os.path.isfile(runner.logFile(jobid)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid))
        expected_err = os.path.join(self.log_dir, f"slurm_test.e{jobid}")
        self.assertEqual(expected_err, runner.errFile(jobid))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid))

    def test_slurm_runner_set_log_dir_multiple_times(self):
        """
        Test SlurmRunner explicitly setting log directory multiple times
        """
        # Create a temporary log directory
        self.log_dir = self.make_tmp_dir()
        # Create a runner with custom log directory
        runner = SlurmRunner(log_dir=self.log_dir)
        self.assertEqual(runner.log_dir, self.log_dir)
        # Execute the echo command
        jobid1 = self.run_job(runner,
                              "slurm_test1",
                              self.working_dir,
                              'echo', ('this is a test',))
        # Reset the log directory and run second job
        runner.set_log_dir(self.working_dir)
        jobid2 = self.run_job(runner,
                              "slurm_test2",
                              self.working_dir,
                              'echo', ('this is a test',))
        # Reset the log directory again and run 3rd job
        runner.set_log_dir(self.log_dir)
        jobid3 = self.run_job(runner,
                              "slurm_test3",
                              self.working_dir,
                              'echo',('this is a test',))
        self.wait_for_jobs(runner, jobid1, jobid2, jobid3)
        # Check outputs for job #1
        self.assertEqual(runner.name(jobid1), "slurm_test1")
        expected_log = os.path.join(self.log_dir, f"slurm_test1.o{jobid1}")
        self.assertEqual(expected_log, runner.logFile(jobid1))
        self.assertTrue(os.path.isfile(runner.logFile(jobid1)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid1))
        expected_err = os.path.join(self.log_dir, f"slurm_test1.e{jobid1}")
        self.assertEqual(expected_err, runner.errFile(jobid1))
        self.assertTrue(os.path.isfile(runner.errFile(jobid1)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid1))
        # Check outputs for job #2
        self.assertEqual(runner.name(jobid2), "slurm_test2")
        expected_log = os.path.join(self.working_dir, f"slurm_test2.o{jobid2}")
        self.assertEqual(expected_log, runner.logFile(jobid2))
        self.assertTrue(os.path.isfile(runner.logFile(jobid2)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid2))
        expected_err = os.path.join(self.working_dir, f"slurm_test2.e{jobid2}")
        self.assertEqual(expected_err, runner.errFile(jobid2))
        self.assertTrue(os.path.isfile(runner.errFile(jobid2)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid2))
        # Check outputs for job #3
        self.assertEqual(runner.name(jobid3), "slurm_test3")
        expected_log = os.path.join(self.log_dir, f"slurm_test3.o{jobid3}")
        self.assertEqual(expected_log, runner.logFile(jobid3))
        self.assertTrue(os.path.isfile(runner.logFile(jobid3)),
                        "Stdout file '%s': not a file" %
                        runner.logFile(jobid3))
        expected_err = os.path.join(self.log_dir, f"slurm_test3.e{jobid3}")
        self.assertEqual(expected_err, runner.errFile(jobid3))
        self.assertTrue(os.path.isfile(runner.errFile(jobid3)),
                        "Stderr file '%s': not a file" %
                        runner.errFile(jobid3))

    @unittest.skip("don't know what error state looks like for Slurm")
    def test_slurm_runner_error_state(self):
        """
        Test SlurmRunner detects job in error state
        """
        # Create a runner and execute a command in a non-existent
        # working directory
        runner = SlurmRunner(slurm_extra_args=self.slurm_extra_args)
        jobid = self.run_job(runner,'test_eqw',
                             '/non/existent/dir',
                             'echo', ('this should fail',))
        # Wait for job to go into error state
        ntries = 0
        while ntries < 100:
            if runner.errorState(jobid):
                # Success - job errored
                return
            time.sleep(0.1)
            ntries += 1
        self.fail("Job failed to go into error state")

    def test_slurm_runner_repr(self):
        """
        Test SlurmRunner __repr__ method
        """
        self.assertEqual("SlurmRunner", str(SlurmRunner()))
        self.assertEqual("SlurmRunner(nslots=8)",
                         str(SlurmRunner(nslots=8)))
        self.assertEqual("SlurmRunner(join_logs=True)",
                         str(SlurmRunner(join_logs=True)))

    def test_slurm_runner_nslots(self):
        """
        Test SlurmRunner sets BCFTBX_RUNNER_NSLOTS
        """
        # Create a runner and check default nslots
        runner = SlurmRunner()
        self.assertEqual(runner.nslots, 1)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"1\n",fp.read())
        # Create a runner with multiple nslots
        runner = SlurmRunner(nslots=8)
        self.assertEqual(runner.nslots, 8)
        jobid = self.run_job(runner,
                             'test',
                             self.working_dir,
                             '/bin/bash',
                             ('-c','echo $BCFTBX_RUNNER_NSLOTS',))
        self.wait_for_jobs(runner,jobid)
        with io.open(runner.logFile(jobid),'rt') as fp:
            self.assertEqual(u"8\n",fp.read())

    def test_slurm_runner_externally_terminated_job(self):
        """
        Test SlurmRunner handles job terminated externally
        """
        # Create a runner
        runner = SlurmRunner(poll_interval=1.0)
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Start sleep command
        jobid = self.run_job(runner,
                             "slurm_test",
                             self.working_dir,
                             'sleep', ('5s',))
        self.assertTrue(runner.isRunning(jobid))
        # Terminate the job outside the runner
        # (runner will still think it's running)
        self.mock_slurm.scancel(["-v", jobid])
        self.update_jobs()
        # Wait for runner to finalise externally terminated job
        self.wait_for_jobs(runner, jobid)
        # Check exit status of job
        self.assertEqual(runner.name(jobid), "slurm_test")
        self.assertEqual(runner.exit_status(jobid), 127)

    def test_slurm_runner_externally_terminated_job_with_normal_job(self):
        """
        Test SlurmRunner handles job terminated externally alongside normal job
        """
        # Create a runner
        runner = SlurmRunner(poll_interval=1.0)
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        # Start sleep commands
        jobid1 = self.run_job(runner,
                              "slurm_test_1",
                              self.working_dir,
                              'sleep', ('5s',))
        self.assertTrue(runner.isRunning(jobid1))
        jobid2 = self.run_job(runner,
                              "slurm_test_2",
                              self.working_dir,
                              'sleep', ('5s',))
        self.assertTrue(runner.isRunning(jobid2))
        # Terminate one of the jobs outside the runner
        # (runner will still think it's running)
        self.mock_slurm.scancel(["-v", jobid1])
        # Wait for runner to finalise all jobs
        self.wait_for_jobs(runner, jobid1, jobid2)
        # Check exit status of jobs
        self.assertEqual(runner.name(jobid1), "slurm_test_1")
        self.assertEqual(runner.exit_status(jobid1), 127)
        self.assertEqual(runner.name(jobid2), "slurm_test_2")
        self.assertEqual(runner.exit_status(jobid2), 0)


class TestResourceLock(unittest.TestCase):
    """
    Tests for the ResourceLock class
    """
    def test_resource_lock(self):
        """
        ResourceLock: check acquiring and releasing a lock
        """
        resource_lock = ResourceLock()
        self.assertFalse(resource_lock.is_locked("test"))
        lock = resource_lock.acquire("test")
        self.assertEqual(lock.split('@')[0],"test")
        self.assertTrue(resource_lock.is_locked("test"))
        resource_lock.release(lock)
        self.assertFalse(resource_lock.is_locked("test"))

    def test_resource_lock_timeout(self):
        """
        ResourceLock: check lock acquisition timeout
        """
        resource_lock = ResourceLock()
        # Get a lock
        lock = resource_lock.acquire("test")
        self.assertTrue(resource_lock.is_locked("test"))
        # Try to acquire a second lock without releasing
        # the first, specifying a timeout
        self.assertRaises(Exception,
                          resource_lock.acquire,
                          "test",
                          timeout=1.0)

class TestFetchRunnerFunction(unittest.TestCase):
    """Tests for the fetch_runner function
    """

    def test_fetch_simple_job_runner(self):
        """fetch_runner returns a SimpleJobRunner
        """
        runner = fetch_runner("SimpleJobRunner")
        self.assertTrue(isinstance(runner,SimpleJobRunner))
        self.assertEqual(runner.nslots,1)

    def test_fetch_simple_job_runner_with_nslots(self):
        """fetch_runner returns a SimpleJobRunner with nslots
        """
        runner = fetch_runner("SimpleJobRunner(nslots=8)")
        self.assertTrue(isinstance(runner,SimpleJobRunner))
        self.assertEqual(runner.nslots,8)

    def test_fetch_simple_job_runner_with_join_logs(self):
        """fetch_runner returns a SimpleJobRunner with join_logs
        """
        runner = fetch_runner("SimpleJobRunner(join_logs=False)")
        self.assertTrue(isinstance(runner,SimpleJobRunner))
        self.assertEqual(runner.nslots,1)

    def test_fetch_ge_job_runner(self):
        """fetch_runner returns a GEJobRunner
        """
        runner = fetch_runner("GEJobRunner")
        self.assertTrue(isinstance(runner,GEJobRunner))

    def test_fetch_ge_job_runner_with_extra_args(self):
        """fetch_runner returns a GEJobRunner with additional arguments
        """
        runner = fetch_runner("GEJobRunner(-j y)")
        self.assertTrue(isinstance(runner,GEJobRunner))
        self.assertEqual(runner.ge_extra_args,['-j','y'])

    def test_fetch_slurm_runner(self):
        """fetch_runner returns a SlurmRunner
        """
        runner = fetch_runner("SlurmRunner")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)

    def test_fetch_slurm_runner_with_nslots(self):
        """fetch_runner returns a SlurmRunner with nslots
        """
        runner = fetch_runner("SlurmRunner(nslots=8)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)

    def test_fetch_slurm_runner_with_partition(self):
        """fetch_runner returns a SlurmRunner with partition
        """
        runner = fetch_runner("SlurmRunner(partition=default)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, "default")
        self.assertFalse(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)

    def test_fetch_slurm_runner_with_join_logs(self):
        """fetch_runner returns a SlurmRunner with join_logs
        """
        runner = fetch_runner("SlurmRunner(join_logs=True)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 1)
        self.assertEqual(runner.partition, None)
        self.assertTrue(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)

    def test_fetch_slurm_runner_with_extra_args(self):
        """fetch_runner returns a SlurmRunner with additional arguments
        """
        # Extra args that set nslots and partition
        runner = fetch_runner("SlurmRunner(-n 8 -p default)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.partition, "default")
        self.assertFalse(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)
        # Extra args plus join_logs
        runner = fetch_runner("SlurmRunner(-n 8 -p default join_logs=y)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.partition, "default")
        self.assertTrue(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args, None)
        # Arbitrary non-reserved extra args
        runner = fetch_runner("SlurmRunner(-n 8 --mail-type=ALL --mail-user=emailaddr@manchester.ac.uk join_logs=n)")
        self.assertTrue(isinstance(runner, SlurmRunner))
        self.assertEqual(runner.nslots, 8)
        self.assertEqual(runner.partition, None)
        self.assertFalse(runner.join_logs)
        self.assertEqual(runner.slurm_extra_args,
                         ["--mail-type=ALL",
                          "--mail-user=emailaddr@manchester.ac.uk"])

    def test_fetch_bad_runner_raises_exception(self):
        """fetch_runner raises exception for unknown runner
        """
        self.assertRaises(Exception,fetch_runner,"SimpleRunner")

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
