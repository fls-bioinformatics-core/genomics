#######################################################################
# Tests for JobRunner.py module
#######################################################################
from JobRunner import *
import bcf_utils
import unittest
import tempfile
import shutil

class TestSimpleJobRunner(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to work in
        self.working_dir = tempfile.mkdtemp()
        self.log_dir = None

    def cleanUp(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def test_simple_job_runner(self):
        """Test SimpleJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        jobid = runner.run('test',self.working_dir,'echo','this is a test')
        while runner.isRunning(jobid):
            # Wait for job to finish
            pass
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)))
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_simple_job_runner_join_logs(self):
        """Test SimpleJobRunner joining stderr to stdout

        """
        # Create a runner and execute the echo command
        runner = SimpleJobRunner(join_logs=True)
        jobid = runner.run('test',self.working_dir,'echo','this is a test')
        while runner.isRunning(jobid):
            # Wait for job to finish
            pass
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
        self.log_dir = tempfile.mkdtemp()
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        # Reset the log directory
        runner.log_dir(self.log_dir)
        jobid = runner.run('test',self.working_dir,'echo','this is a test')
        while runner.isRunning(jobid):
            # Wait for job to finish
            pass
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
        self.log_dir = tempfile.mkdtemp()
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        # Reset the log directory
        runner.log_dir(self.log_dir)
        jobid1 = runner.run('test1',self.working_dir,'echo','this is a test')
        # Rest the log directory again and run second job
        runner.log_dir(self.working_dir)
        jobid2 = runner.run('test2',self.working_dir,'echo','this is a test')
        # Rest the log directory again and run 3rd job
        runner.log_dir(self.log_dir)
        jobid3 = runner.run('test3',self.working_dir,'echo','this is a test')
        while runner.isRunning(jobid1) \
              or runner.isRunning(jobid2) \
              or runner.isRunning(jobid3):
            # Wait for jobs to finish
            pass
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
        # Skip the test if Grid Engine not available
        if bcf_utils.find_program('qstat') is None:
            raise unittest.SkipTest("'qstat' not found, Grid Engine not available")
        # Create a temporary directory to work in
        self.working_dir = tempfile.mkdtemp(dir=os.getcwd())

    def cleanUp(self):
        shutil.rmtree(self.working_dir)

    def test_ge_job_runner(self):
        """Test GEJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner()
        try:
            jobid = runner.run('test',self.working_dir,'echo','this is a test')
        except OSError:
            self.cleanUp() # Not sure why but should do clean up manually
            self.fail("Unable to run GE job")
        poll_interval = 5
        ntries = 0
        while runner.isRunning(jobid) or not os.path.exists(runner.logFile(jobid)):
            # Wait for job to finish
            ntries += 1
            if ntries > 30:
                self.cleanUp() # Not sure why but should do clean up manually
                self.fail("Timed out waiting for test job")
            else:
                time.sleep(poll_interval)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
