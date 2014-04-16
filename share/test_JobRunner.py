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
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None

    def cleanUp(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp()

    def run_job(self,runner,*args):
        return runner.run(*args)

    def wait_for_jobs(self,runner,*args):
        ntries = 0
        while ntries < 100:
            for jobid in args:
                # If we find one job still running then loop round
                if runner.isRunning(jobid):
                    ntries += 1
                    continue
                # All jobs finished
                return
        # At this point we've reach the timeout limit
        self.cleanUp() # Not sure why but should do clean up manually
        self.fail("Timed out waiting for test job")

    def test_simple_job_runner(self):
        """Test SimpleJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = SimpleJobRunner()
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
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
        # Skip the test if Grid Engine not available
        if bcf_utils.find_program('qstat') is None:
            raise unittest.SkipTest("'qstat' not found, Grid Engine not available")
        # Create a temporary directory to work in
        self.working_dir = self.make_tmp_dir()
        self.log_dir = None

    def cleanUp(self):
        shutil.rmtree(self.working_dir)
        if self.log_dir is not None:
            shutil.rmtree(self.log_dir)

    def make_tmp_dir(self):
        return tempfile.mkdtemp(dir=os.getcwd())

    def run_job(self,runner,*args):
        try:
            return runner.run(*args)
        except OSError:
            self.cleanUp() # Not sure why but should do clean up manually
            self.fail("Unable to run GE job")

    def wait_for_jobs(self,runner,*args):
        poll_interval = .1
        ntries = 0
        while ntries < 100:
            for jobid in args:
                # If we find one job still running then loop round
                if runner.isRunning(jobid) or not os.path.exists(runner.logFile(jobid)):
                    ntries += 1
                    time.sleep(poll_interval)
                    continue
                # All jobs finished
                return
        # At this point we've reach the timeout limit
        self.cleanUp() # Not sure why but should do clean up manually
        self.fail("Timed out waiting for test job")

    def test_ge_job_runner(self):
        """Test GEJobRunner with basic shell command

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner()
        jobid = self.run_job(runner,'test',self.working_dir,'echo',('this is a test',))
        self.wait_for_jobs(runner,jobid)
        # Check outputs
        self.assertEqual(runner.name(jobid),'test')
        self.assertTrue(os.path.isfile(runner.logFile(jobid)))
        self.assertTrue(os.path.isfile(runner.errFile(jobid)))
        # Check log files are in the working directory
        self.assertEqual(os.path.dirname(runner.logFile(jobid)),self.working_dir)
        self.assertEqual(os.path.dirname(runner.errFile(jobid)),self.working_dir)

    def test_ge_job_runner_join_logs(self):
        """Test GEJobRunner with '-j y' option (i.e. join stderr and stdout)

        """
        # Create a runner and execute the echo command
        runner = GEJobRunner(ge_extra_args=['-j','y'])
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
        runner = GEJobRunner()
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
        runner = GEJobRunner()
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

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Turn off most logging output for tests
    logging.getLogger().setLevel(logging.CRITICAL)
    # Run tests
    unittest.main()
