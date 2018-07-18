#######################################################################
# Tests for JobRunner.py module
#######################################################################
from bcftbx.JobRunner import *
from bcftbx.mockGE import setup_mock_GE
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

class TestGEJobRunner(unittest.TestCase):

    def setUp(self):
        # Set up mockGE utilities
        self.database_dir = self.make_tmp_dir()
        self.bin_dir = self.make_tmp_dir()
        self.old_path = os.environ['PATH']
        os.environ['PATH'] = self.bin_dir + os.pathsep + self.old_path
        setup_mock_GE(bindir=self.bin_dir,
                      database_dir=self.database_dir,
                      debug=False)
        # Create a temporary directory to work in
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None
        # Extra arguments: edit this for local setup requirements
        self.ge_extra_args = []

    def tearDown(self):
        os.environ['PATH'] = self.old_path
        shutil.rmtree(self.database_dir)
        shutil.rmtree(self.bin_dir)
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp(dir=os.getcwd())

    def run_job(self,runner,*args):
        try:
            return runner.run(*args)
        except OSError:
            self.fail("Unable to run GE job")

    def wait_for_jobs(self,runner,*args):
        poll_interval = 0.1
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
        for jobid in args:
            # Terminate jobs
            if runner.isRunning(jobid):
                runner.terminate(jobid)
        self.fail("Timed out waiting for test job")

    def test_ge_job_runner(self):
        """Test GEJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=self.ge_extra_args)
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
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
        jobid = self.run_job(runner,'test',self.working_dir,'echo','this is a test')
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

class TestFetchRunnerFunction(unittest.TestCase):
    """Tests for the fetch_runner function
    """

    def test_fetch_simple_job_runner(self):
        """fetch_runner returns a SimpleJobRunner
        """
        runner = fetch_runner("SimpleJobRunner")
        self.assertTrue(isinstance(runner,SimpleJobRunner))

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
