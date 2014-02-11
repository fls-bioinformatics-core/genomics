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

    def cleanUp(self):
        shutil.rmtree(self.working_dir)

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
